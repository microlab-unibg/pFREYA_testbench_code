#!/usr/bin/python

import os
import sys
import csv
import time
import threading
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import pyvisa
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.backends.backend_tkagg as backend_tkagg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pFREYA_tester_processing as pYtp
import config
from dac_out_adc_in_autoread import TesterConfig, init_fpga, select_pixel

#OUTPUT_DIR = r'C:/Users/giorg/Desktop/tesi/pFREYA_testbench_code/data/shap'
OUTPUT_DIR = r'G:/Shared drives/FALCON/measures/new/transient/adc'

FIXED_CLOCKS = {'slow_ck': '4000', 'sel_ck': '4000', 'adc_ck': '20',
                'inj_stb': '1', 'ser_ck': '100', 'dac_sck': '100'}
FIXED_SLOW_CTRL = {'csa_mode_n': '01', 'inj_en_n': '1', 'ch_en': '1',
                   'inj_mode_n': '1', 'pixel_to_inj': '5'}
FIXED_PIXEL = {'pixel_row': '5', 'pixel_col': '0'}
FIXED_TIMING = {   # delay, high, low
    'csa_reset_n':  ('104', '60', '9940'),
    'sh_phi1d_inf': ('1204', '8956', '1044'),
    'sh_phi1d_sup': ('1120', '9040', '960'),
    'adc_start':    ('404', '4', '9996'),
}
FIXED_AUTO_READ_DELAY = '400'

CSA_MODE = [int(b) for b in FIXED_SLOW_CTRL['csa_mode_n']]
SHAPER_MODES = [
    [0, 0],     # 240 ns
    [0, 1],     # 330 ns
    [1, 0],     # 420 ns
    [1, 1],     # 510 ns
]
CONFIG_BITS_LIST = [[*CSA_MODE, 1, *shap, 1, 1] for shap in SHAPER_MODES]

N_STEPS = 8
PHOTON_SPAN = np.linspace(0, 256, N_STEPS)
N_SAMPLES = 5

# SUP fisso, sweep del delay di INF (1 tick = 5 ns)
TICK_NS = 5
INF_DELAYS = range(1204, 1425, 4)

FIRST_SETTLE_S = 5
SETTLE_S = 2

PS_ADDRESSES = ('GPIB0::23::INSTR', 'GPIB1::23::INSTR')
PS_IDLE_LEVEL = -0.09e-6


def cfg_name(bits):
    return ''.join(map(str, bits))


def get_energy_level(cfg_bits):
    if cfg_bits[0] == 1 and cfg_bits[1] == 1:
        return 5
    elif cfg_bits[0] == 1 and cfg_bits[1] == 0:
        return 18
    elif cfg_bits[0] == 0 and cfg_bits[1] == 1:
        return 9
    elif cfg_bits[0] == 0 and cfg_bits[1] == 0:
        return 25
    else:
        raise ValueError("Configurazione cfg_bits non valida")

def get_shap_bits(cfg_bits):
    if cfg_bits[3] == 1 and cfg_bits[4] == 1:
        return 510
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 330
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 420
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 240
    else:
        raise ValueError("Configurazione shap_bits non valida")


def apply_fixed_config(cfg):
    for name, value in {**FIXED_CLOCKS, **FIXED_SLOW_CTRL, **FIXED_PIXEL}.items():
        getattr(cfg, name).set(value)
    for name, (delay, high, low) in FIXED_TIMING.items():
        sig = getattr(cfg, name)
        sig['delay'].set(delay)
        sig['high'].set(high)
        sig['low'].set(low)
    cfg.auto_read_delay.set(FIXED_AUTO_READ_DELAY)


def open_power_supply():
    rm = pyvisa.ResourceManager()
    for address in PS_ADDRESSES:
        try:
            ps = rm.open_resource(address)
            print(f'{address}: {ps.query("*IDN?").strip()}')
            break
        except pyvisa.errors.VisaIOError:
            continue
    else:
        raise RuntimeError(f'Generatore di corrente non trovato su {PS_ADDRESSES}')
    ps.write(':OUTP:LOW FLO')
    ps.write(':OUTP:OFF:AUTO ON')
    ps.write(':OUTP:PROT ON')
    ps.write(':OUTP:RES:MODE FIX')
    ps.write(':OUTP:RES:SHUN DEF')
    ps.write(':SOUR:FUNC:MODE CURR')
    ps.write(':SOUR:CURR:MODE FIX')
    ps.write(f':SOUR:CURR:LEV {PS_IDLE_LEVEL}')
    ps.write(':DISP:ENAB OFF')
    ps.write(':DISP:TEXT:DATA "pFREYA16"')
    ps.write(':DISP:TEXT:STAT ON')
    ps.write(':OUTP:STAT ON')
    return ps


def hold_tick(name, delay):
    return int(delay) + int(FIXED_TIMING[name][1])


def shift_ns(inf_delay):
    return (hold_tick('sh_phi1d_inf', inf_delay) - hold_tick('sh_phi1d_sup', FIXED_TIMING['sh_phi1d_sup'][0])) * TICK_NS


def plot_cfg(ax, bits, curves):
    ax.set_xlabel(r'Time [$\mu$s]')
    ax.set_ylabel('ADC output code')
    ax.tick_params(right=True, top=True, direction='in')
    ax.text(.01, .01, f'$t_p$ = {get_shap_bits(bits)} ns', ha='left', va='bottom', transform=ax.transAxes)
    ax.set_xlim(shift_ns(INF_DELAYS[0]) / 1e3, shift_ns(INF_DELAYS[-1]) / 1e3)
    colours = list(mcolors.TABLEAU_COLORS.keys())
    for step, data in sorted(curves.items()):
        ax.plot(np.asarray(data['x']) / 1e3, data['y'], '-', linewidth=1,
                color=colours[step], label=f'{int(PHOTON_SPAN[step])}')
    if curves:
        ax.legend(title=rf'$\gamma$ @ {get_energy_level(bits)} keV', frameon=False)


class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Transiente shaper da ADC')
        self.running = False
        self.cfg = TesterConfig(self.parent)
        apply_fixed_config(self.cfg)

        ttk.Button(self.parent, text='Start', command=self.launch).grid(row=0, column=0, padx=5, pady=5)

        self.figure = plt.Figure(figsize=(11, 8), dpi=100)
        self.axes = dict(zip(map(cfg_name, CONFIG_BITS_LIST), self.figure.subplots(2, 2).flat))
        self.canvas = backend_tkagg.FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas.get_tk_widget().grid(row=1, column=0, padx=10, pady=10)
        self.data = {}
        self.update_plot()

        self.grid(row=0, column=0)

    def update_plot(self):
        for bits in CONFIG_BITS_LIST:
            ax = self.axes[cfg_name(bits)]
            ax.clear()
            plot_cfg(ax, bits, self.data.get(cfg_name(bits), {}))
        self.figure.tight_layout()
        self.canvas.draw()

    def launch(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self.measure, daemon=True).start()

    def measure(self):
        cfg = self.cfg
        pixel = int(FIXED_SLOW_CTRL['pixel_to_inj'])
        self.data = {}
        ps = None
        timestamp = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
        base = os.path.join(OUTPUT_DIR, f'transient_adc_px{pixel}_{timestamp}')
        try:
            ps = open_power_supply()
            init_fpga(cfg)

            for bits in CONFIG_BITS_LIST:
                if not self.running:
                    break
                name = cfg_name(bits)
                print(f'\n=== cfg {name}: {get_energy_level(bits)} keV, tp {get_shap_bits(bits)} ns ===')
                config.config(channel='shap', lemo='none', n_steps=N_STEPS, cfg_bits=bits, cfg_inst=False)
                current_lev = config.current_lev

                cfg.sh_phi1d_inf['delay'].set(str(INF_DELAYS[0]))
                pYtp.send_slow_ctrl_auto(bits, pixel)
                select_pixel(cfg)
                pYtp.send_CSA_RESET_N(cfg)
                pYtp.send_SH_PHI1D_INF(cfg)
                pYtp.send_SH_PHI1D_SUP(cfg)
                pYtp.send_ADC_START(cfg)
                pYtp.send_sync_time_bases()

                curves = self.data[name] = {}
                rows = []
                for step, level in enumerate(current_lev):
                    if not self.running:
                        break
                    print(f'livello {step+1}/{N_STEPS}: I={level:.3e} A, {int(PHOTON_SPAN[step])} fotoni')
                    ps.write(f':SOUR:CURR:LEV {level}')
                    time.sleep(FIRST_SETTLE_S if step == 0 else SETTLE_S)
                    data = curves[step] = {'x': [], 'y': []}

                    for delay in INF_DELAYS:
                        if not self.running:
                            break
                        cfg.sh_phi1d_inf['delay'].set(str(delay))
                        pYtp.send_SH_PHI1D_INF(cfg)
                        pYtp.send_sync_time_bases()
                        time.sleep(0.1)
                        codes = []
                        for _ in range(N_SAMPLES):
                            time.sleep(0.05)
                            result = pYtp.send_VAL(cfg)
                            if result is not None:
                                codes.append(int(result[0], 2))
                        if not codes:
                            print(f'  INF delay={delay}: errore lettura')
                            continue

                        t = shift_ns(delay)
                        code = float(np.mean(codes))
                        rows.append({'current_step': step, 'current_A': level, 'photons': int(PHOTON_SPAN[step]),
                                     'inf_delay': delay, 'time_ns': t, 'adc_code': code,
                                     'adc_codes': ' '.join(map(str, codes))})
                        print(f'  INF delay={delay} t={t} ns codice ADC = {code:.1f}')
                        data['x'].append(t)
                        data['y'].append(code)
                        self.parent.after(0, self.update_plot)

                if rows:
                    save_cfg(base, bits, rows, curves)

        except Exception as err:
            print(f'Errore: {err}')

        finally:
            self.running = False
            if ps is not None:
                ps.write(f':SOUR:CURR:LEV {PS_IDLE_LEVEL}')


def save_cfg(base, bits, rows, curves):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f'{base}_{cfg_name(bits)}_{get_energy_level(bits)}keV_tp{get_shap_bits(bits)}'
    with open(path + '.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    fig = plt.Figure(figsize=(5, 4))
    plot_cfg(fig.add_subplot(111), bits, curves)
    fig.tight_layout()
    fig.savefig(path + '.pdf', dpi=300)
    print(f'Salvato: {path}')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()
