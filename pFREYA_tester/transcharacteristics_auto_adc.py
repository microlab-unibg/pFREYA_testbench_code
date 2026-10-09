#!/usr/bin/python
"""
Clock, timing e pixel sono fissi. Per ogni livello dello shaper in SHAPER_MODES:
  1. slow control della configurazione
  2. selezione pixel, CSA_RESET_N, SH_PHI1D_INF/SUP, ADC_START, sync_time_bases
  3. sweep sui 20 livelli di config.current_lev; per ogni livello N_SAMPLES codici ADC
     letti con send_VAL e riportati su linspace(0, 256, 20) fotoni equivalenti
  4. CSV e PDF del livello salvati appena il suo sweep e' finito
"""

import os
import sys
import csv
import time
import threading
import traceback
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import pyvisa
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as backend_tkagg
from scipy.stats import linregress

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pFREYA_tester_processing as pYtp
import config
from dac_out_adc_in_autoread import TesterConfig, init_fpga, select_pixel

OUTPUT_DIR = r'C:/Users/giorg/Desktop/tesi/pFREYA_testbench_code/data/shap'

FIXED_CLOCKS = {'slow_ck': '4000', 'sel_ck': '4000', 'adc_ck': '20',
                'inj_stb': '1', 'ser_ck': '100', 'dac_sck': '100'}
FIXED_SLOW_CTRL = {'csa_mode_n': '01', 'inj_en_n': '1', 'ch_en': '1',
                   'inj_mode_n': '1', 'pixel_to_inj': '5'}
FIXED_PIXEL = {'pixel_row': '5', 'pixel_col': '0'}
FIXED_TIMING = {   # FP: delay, high, low
    'csa_reset_n':  ('104', '60', '9940'),
    'sh_phi1d_inf': ('1204', '8956', '1044'),
    'sh_phi1d_sup': ('1170', '9040', '960'),
    'adc_start':    ('404', '4', '9996'),
}

FIXED_AUTO_READ_DELAY = '400'

CSA_MODE = [int(b) for b in FIXED_SLOW_CTRL['csa_mode_n']]
SHAPER_MODES = [         
    [0, 0],                # tp 240 ns
    [0, 1],                # tp 330 ns
    [1, 0],                # tp 420 ns
    [1, 1],                # tp 510 ns
]
CONFIG_BITS_LIST = [[*CSA_MODE, 1, *shap, 1, 1] for shap in SHAPER_MODES]

N_STEPS = 20                                  # livelli di corrente 
PHOTON_SPAN = np.linspace(0, 256, N_STEPS)    # asse fotoni equivalenti dei grafici
N_SAMPLES = 5           # letture VAL per livello di corrente
ADC_BITS = 10
ADC_VREF = 2.5                                # V
ADC_MAX_CODE = 2**ADC_BITS - 1
ADC_LSB_MV = ADC_VREF / 2**ADC_BITS * 1e3     # 2.44 mV/LSB
FIRST_SETTLE_S = 5      # attesa al primo livello di ogni configurazione
SETTLE_S = 2            # attesa dopo ogni cambio di corrente (s)


def cfg_name(bits):
    return ''.join(map(str, bits))


# Funzioni per determinare energia e peaking time dalla configurazione dei bit
def get_energy_level(cfg_bits):
    if cfg_bits[0] == 1 and cfg_bits[1] == 1:
        return 5  # 5 keV
    elif cfg_bits[0] == 1 and cfg_bits[1] == 0:
        return 18  # 18 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 1:
        return 9 # 9 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 0:
        return 25 # 25 keV
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


PS_ADDRESSES = ('GPIB0::23::INSTR', 'GPIB1::23::INSTR')
PS_IDLE_LEVEL = -0.09e-6

def apply_fixed_config(cfg):
    for name, value in FIXED_CLOCKS.items():
        getattr(cfg, name).set(value)
    for name, value in {**FIXED_SLOW_CTRL, **FIXED_PIXEL}.items():
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
        raise RuntimeError(f'Generatore di corrente non trovato su {PS_ADDRESSES}. '
                           f'Strumenti visibili: {rm.list_resources()}')
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


def linear_fit(x, y):
    x, y = np.asarray(x), np.asarray(y)
    if len(x) < 3:
        return None
    ln = linregress(x, y)
    n = len(x)
    adj_r2 = 1 - (1 - ln.rvalue**2) * (n - 1) / (n - 2)
    residual = y - (ln.intercept + ln.slope * x)
    span = abs(ln.slope) * (x.max() - x.min())
    inl = 100 * np.max(np.abs(residual)) / span if span > 0 else float('nan')
    return ln, adj_r2, inl


def plot_cfg(ax, bits, data, table=False):

    ax.set_xlabel('Equivalent photons[#]')
    ax.set_ylabel('ADC output code ')
    ax.set_title(f'CSA {get_energy_level(bits)} keV, shaper tp {get_shap_bits(bits)} ns')
    ax.set_xlim(0, PHOTON_SPAN[-1] * 1.05)
    ax.set_ylim(0, ADC_MAX_CODE + 1)
    if not data['x']:
        return
    x, y = np.asarray(data['x']), np.asarray(data['y'])
    ax.plot(x, y, 's', color='tab:olive', markersize=5, label='ADC output')
    fit = linear_fit(x, y) if data.get('done') else None

    decreasing = (fit[0].slope < 0) if fit is not None else (len(y) > 1 and y[-1] < y[0])
    legend_loc, table_loc = ('upper right', 'lower left') if decreasing else ('upper left', 'lower right')
    if fit is not None:
        ln, adj_r2, inl = fit
        xf = np.array([0, ax.get_xlim()[1]])
        ax.plot(xf, ln.intercept + ln.slope * xf, '-', color='tab:red', linewidth=1, label='Fit')
        if table:
            rows = [['Mode [keV]', f'{get_energy_level(bits)}'],
                    ['Peaking time [ns]', f'{get_shap_bits(bits)}'],
                    ['R-Square', f'{adj_r2:.3f}'],
                    ['Slope [LSB/ph]', f'{ln.slope:.2f}'],
                    ['Slope [mV/ph]', f'{ln.slope * ADC_LSB_MV:.2f}'],
                    ['INL [%]', f'{inl:.1f}']]
            tab = ax.table(cellText=rows, colLabels=['fit', ''], colWidths=[.3, .14],
                           loc=table_loc, cellLoc='right')
            tab.auto_set_font_size(False)
            tab.set_fontsize(8)
    ax.legend(loc=legend_loc, frameon=False)


class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Transcaratteristica ADC per livello dello shaper')
        self.running = False
        self.cfg = TesterConfig(self.parent)
        apply_fixed_config(self.cfg)

        ttk.Button(self.parent, text='Start', command=self.launch).grid(row=0, column=0, padx=5, pady=5)

        # un grafico per modalita' dello shaper (ordine di CONFIG_BITS_LIST)
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
            plot_cfg(ax, bits, self.data.get(cfg_name(bits), {'x': []}))
        self.figure.tight_layout()
        self.canvas.draw()

    def launch(self):
        if self.running:
            return
        self.running = True
        # daemon: chiudendo la finestra la misura si interrompe
        threading.Thread(target=self.measure, daemon=True).start()

    def measure(self):
        cfg = self.cfg
        pixel = int(FIXED_SLOW_CTRL['pixel_to_inj'])
        self.data = {}
        ps = None
        timestamp = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
        base = os.path.join(OUTPUT_DIR, f'transchar_adc_px{pixel}_{timestamp}')
        try:
            ps = open_power_supply()
            init_fpga(cfg)

            for bits in CONFIG_BITS_LIST:
                if not self.running:
                    break
                name = cfg_name(bits)
                print(f'\n=== cfg {name}: {get_energy_level(bits)} keV, tp {get_shap_bits(bits)} ns ===')
                config.config(channel='shap', lemo='none', n_steps=N_STEPS, cfg_bits=bits, cfg_inst=False)
                current_lev, eq_ph, iinj_int = config.current_lev, config.eq_ph, config.iinj_int

                pYtp.send_slow_ctrl_auto(bits, pixel)
                select_pixel(cfg)
                pYtp.send_CSA_RESET_N(cfg)
                pYtp.send_SH_PHI1D_INF(cfg)
                pYtp.send_SH_PHI1D_SUP(cfg)
                pYtp.send_ADC_START(cfg)
                pYtp.send_sync_time_bases()

                ps.write(f':SOUR:CURR:LEV {current_lev[0]}')
                time.sleep(FIRST_SETTLE_S)

                data = self.data[name] = {'x': [], 'y': []}
                rows = []
                try:
                    for i, level in enumerate(current_lev):
                        if not self.running:
                            print('Interrotto dall\'utente.')
                            break
                        ps.write(f':SOUR:CURR:LEV {level}')
                        time.sleep(SETTLE_S)
                        codes = []
                        for _ in range(N_SAMPLES):
                            time.sleep(0.05)
                            result = pYtp.send_VAL(cfg)
                            if result is not None:
                                codes.append(int(result[0], 2))

                        rows.append({
                            'pixel': pixel, 'config_bits': name,
                            'energy_keV': get_energy_level(bits), 'peaking_time_ns': get_shap_bits(bits),
                            'step': i, 'current_A': level,
                            'iinj_int_C': iinj_int[i], 'eq_photons': eq_ph[i],
                            'photon_span': PHOTON_SPAN[i],
                            'adc_code_mean': np.mean(codes) if codes else float('nan'),
                            'adc_code_std': np.std(codes) if codes else float('nan'),
                            'adc_codes': ' '.join(map(str, codes)),
                        })
                        print(f'  [{i+1}/{N_STEPS}] I={level:.3e} A ph={PHOTON_SPAN[i]:.1f} '
                              + (f'codice ADC = {np.mean(codes):.1f}' if codes else 'codice ADC = ERRORE'))
                        if codes:
                            data['x'].append(PHOTON_SPAN[i])
                            data['y'].append(float(np.mean(codes)))
                        self.parent.after(0, self.update_plot)
                finally:
                    data['done'] = True
                    self.parent.after(0, self.update_plot)
                    if rows:
                        save_cfg(base, timestamp, bits, rows, data)

        except BaseException as err:
            print(f'Errore: {err}')
            traceback.print_exc()

        finally:
            self.running = False
            if ps is not None:
                try:
                    ps.write(f':SOUR:CURR:LEV {PS_IDLE_LEVEL}')
                except Exception:
                    pass


def save_cfg(base, timestamp, bits, rows, data):
    """Salva CSV e PDF di una configurazione appena il suo sweep e' finito."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = f'{base}_{cfg_name(bits)}_{get_energy_level(bits)}keV_tp{get_shap_bits(bits)}'
    with open(path + '.csv', 'w', newline='') as f:
        f.write(f'# Transcaratteristica ADC, cfg {cfg_name(bits)} '
                f'({get_energy_level(bits)} keV, tp {get_shap_bits(bits)} ns)\n')
        f.write(f'# Pixel: {FIXED_PIXEL}, pixel iniettato: {FIXED_SLOW_CTRL["pixel_to_inj"]}\n')
        f.write(f'# Timing (delay, high, low) [FP]: {FIXED_TIMING}, auto read delay: {FIXED_AUTO_READ_DELAY}\n')
        f.write(f'# Livelli di corrente: {N_STEPS}, campioni VAL per livello: {N_SAMPLES}\n')
        f.write(f'# ADC: {ADC_BITS} bit, Vref {ADC_VREF} V ({ADC_LSB_MV:.3f} mV/LSB)\n')
        f.write(f'# Timestamp: {timestamp}\n')
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f'Risultati salvati in: {path}.csv')

    fig = plt.Figure(figsize=(7, 5))
    plot_cfg(fig.add_subplot(111), bits, data, table=True)
    fig.tight_layout()
    fig.savefig(path + '.pdf', dpi=300, bbox_inches='tight')
    print(f'Grafico salvato in: {path}.pdf')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()
