#!/usr/bin/python
"""
Ricostruzione temporale dello shaper tramite sfasamento SH_PHI1D_SUP rispetto a SH_PHI1D_INF.
Clock, timing, pixel e corrente iniettata sono fissi. Per ogni livello dello shaper in SHAPER_MODES:
  1. slow control della configurazione
  2. selezione pixel, CSA_RESET_N, SH_PHI1D_INF/SUP, ADC_START, sync_time_bases
  3. sweep del solo delay di SH_PHI1D_SUP (high/low e SH_PHI1D_INF invariati); ad ogni passo
     send_SH_PHI1D_SUP + sync_time_bases e N_SAMPLES codici ADC letti con send_VAL
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
INJ_STEP = 10          
N_SAMPLES = 5           # letture VAL per posizione di SH_PHI1D_SUP

# Sweep del delay di SH_PHI1D_SUP. L'hold e' il fronte di discesa (fine della fase HIGH):
# con FIXED_TIMING, INF tiene a 1204+8956 = 10160 e ADC_START sale a 404+10000 = 10404.
TICK_NS = 5
SUP_DELAY_START = 1120  # 1120+9040 = 10160 -> sfasamento 0 rispetto a SH_PHI1D_INF
SUP_DELAY_STOP = 1340   # 1340+9040 = 10380 -> sfasamento 220 tick = 1.1 us
SUP_DELAY_STEP = 4      # 20 ns
SUP_DELAYS = range(SUP_DELAY_START, SUP_DELAY_STOP + 1, SUP_DELAY_STEP)
ADC_START_MARGIN = 20   
STEP_SETTLE_S = 0.1     
ADC_BITS = 10
ADC_VREF = 2.5                                # V
ADC_MAX_CODE = 2**ADC_BITS - 1
ADC_LSB_MV = ADC_VREF / 2**ADC_BITS * 1e3     # 2.44 mV/LSB
FIRST_SETTLE_S = 5      # attesa al primo livello di ogni configurazione
SETTLE_S = 2            # attesa dopo ogni cambio di corrente 


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


def hold_tick(name, delay):
    """Istante (dal sync, in tick) del primo fronte di discesa = hold del S&H."""
    return int(delay) + int(FIXED_TIMING[name][1])


def shift_tick(sup_delay):
    """Sfasamento dell'hold di SH_PHI1D_SUP rispetto a quello di SH_PHI1D_INF (fisso) [tick]."""
    return hold_tick('sh_phi1d_sup', sup_delay) - hold_tick('sh_phi1d_inf', FIXED_TIMING['sh_phi1d_inf'][0])


def check_sweep():
    """Verifica i vincoli temporali dello sweep prima di toccare l'hardware."""
    periods = {n: int(h) + int(l) for n, (_, h, l) in FIXED_TIMING.items()}
    if len(set(periods.values())) != 1:
        raise ValueError(f'I fast control hanno periodi diversi: {periods}')
    period = periods['adc_start']
    adc_tick = int(FIXED_TIMING['adc_start'][0]) + period     # ADC_START che converte i campioni tenuti
    read_tick = int(FIXED_TIMING['adc_start'][0]) + int(FIXED_AUTO_READ_DELAY)
    for d in SUP_DELAYS:
        if not 1 <= d < 2**18:          # delay 0 blocca il segnale a 0, registri a 18 bit
            raise ValueError(f'delay SH_PHI1D_SUP {d} fuori da [1, 2^18)')
        if hold_tick('sh_phi1d_sup', d) + ADC_START_MARGIN > adc_tick:
            raise ValueError(f'delay SH_PHI1D_SUP {d}: hold a {hold_tick("sh_phi1d_sup", d)} tick, '
                             f'troppo vicino ad ADC_START ({adc_tick} tick)')
        if d <= read_tick:              # SUP deve restare in hold fino all'auto-read
            raise ValueError(f'delay SH_PHI1D_SUP {d}: torna in track prima dell\'auto-read ({read_tick} tick)')


def find_peak(data):
    """Massimo globale tra i punti validi dello sweep (non il primo massimo locale)."""
    if not data['y']:
        return None
    i = int(np.argmax(data['y']))
    return data['x'][i], data['y'][i]


def plot_cfg(ax, bits, data, table=False):

    ax.set_xlabel(r'Time [$\mu$s]')
    ax.set_ylabel('ADC output code')
    ax.set_title(f'CSA {get_energy_level(bits)} keV, shaper tp {get_shap_bits(bits)} ns')
    ax.tick_params(direction='in', top=True, right=True)
    # asse x in us: sfasamento dell'hold di SH_PHI1D_SUP rispetto a SH_PHI1D_INF
    x_lim = [shift_tick(d) * TICK_NS / 1e3 for d in (SUP_DELAYS[0], SUP_DELAYS[-1])]
    ax.set_xlim(x_lim[0] - 0.02, x_lim[1] + 0.02)
    if not data['x']:
        ax.set_ylim(0, ADC_MAX_CODE + 1)
        return
    x, y = np.asarray(data['x']) / 1e3, np.asarray(data['y'])
    # curva etichettata con i fotoni equivalenti iniettati, come nei grafici da oscilloscopio
    ax.errorbar(x, y, yerr=data['err'], fmt='none', ecolor='tab:olive', elinewidth=0.6, capsize=1.5)
    ax.plot(x, y, '-', color='tab:olive', linewidth=1, label=f'{PHOTON_SPAN[INJ_STEP]:.0f}')
    # asse y sui dati, con spazio libero in alto per la legenda
    y_lo = y.min() - np.max(data['err'], initial=0)
    y_hi = y.max() + np.max(data['err'], initial=0)
    span = max(y_hi - y_lo, 10)
    ax.set_ylim(y_lo - 0.05 * span, y_lo + span / 0.75)
    ax.legend(loc='upper right', frameon=False, title=rf'$\gamma$ @ {get_energy_level(bits)} keV')


class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Transiente shaper da ADC (sfasamento SH_PHI1D_SUP)')
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
        base = os.path.join(OUTPUT_DIR, f'transient_adc_px{pixel}_{timestamp}')
        try:
            check_sweep()
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

                level = current_lev[INJ_STEP]
                ps.write(f':SOUR:CURR:LEV {level}')
                time.sleep(FIRST_SETTLE_S)

                data = self.data[name] = {'x': [], 'y': [], 'err': []}
                rows = []
                try:
                    for i, sup_delay in enumerate(SUP_DELAYS):
                        if not self.running:
                            print('Interrotto dall\'utente.')
                            break
                        # solo il delay di SUP cambia; il sync lo applica e riallinea INF con i suoi parametri fissi
                        cfg.sh_phi1d_sup['delay'].set(str(sup_delay))
                        if pYtp.send_SH_PHI1D_SUP(cfg):
                            raise RuntimeError(f'invio SH_PHI1D_SUP fallito (delay {sup_delay})')
                        pYtp.send_sync_time_bases()
                        time.sleep(STEP_SETTLE_S)
                        shift = shift_tick(sup_delay)
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
                            'iinj_int_C': iinj_int[INJ_STEP], 'eq_photons': eq_ph[INJ_STEP],
                            'sup_delay_tick': sup_delay,
                            'sup_hold_tick': hold_tick('sh_phi1d_sup', sup_delay),
                            'inf_hold_tick': hold_tick('sh_phi1d_inf', FIXED_TIMING['sh_phi1d_inf'][0]),
                            'shift_tick': shift, 'shift_ns': shift * TICK_NS,
                            'n_valid': len(codes),
                            'adc_code_mean': np.mean(codes) if codes else float('nan'),
                            'adc_code_std': np.std(codes) if codes else float('nan'),
                            'adc_codes': ' '.join(map(str, codes)),
                        })
                        print(f'  [{i+1}/{len(SUP_DELAYS)}] SUP delay={sup_delay} shift={shift * TICK_NS} ns '
                              + (f'codice ADC = {np.mean(codes):.1f}' if codes else 'codice ADC = ERRORE'))
                        if codes:
                            data['x'].append(shift * TICK_NS)
                            data['y'].append(float(np.mean(codes)))
                            data['err'].append(float(np.std(codes)))
                        self.parent.after(0, self.update_plot)
                finally:
                    data['done'] = True
                    cfg.sh_phi1d_sup['delay'].set(FIXED_TIMING['sh_phi1d_sup'][0])
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
        f.write(f'# Transiente shaper da ADC, cfg {cfg_name(bits)} '
                f'({get_energy_level(bits)} keV, tp {get_shap_bits(bits)} ns)\n')
        f.write(f'# Pixel: {FIXED_PIXEL}, pixel iniettato: {FIXED_SLOW_CTRL["pixel_to_inj"]}\n')
        f.write(f'# Timing (delay, high, low) [FP]: {FIXED_TIMING}, auto read delay: {FIXED_AUTO_READ_DELAY}\n')
        f.write(f'# Sweep delay SH_PHI1D_SUP [tick {TICK_NS} ns]: start {SUP_DELAY_START}, stop {SUP_DELAY_STOP}, '
                f'step {SUP_DELAY_STEP}; campioni VAL per posizione: {N_SAMPLES}\n')
        f.write(f'# Corrente iniettata: step {INJ_STEP}/{N_STEPS}, {rows[0]["current_A"]} A\n')
        peak = find_peak(data)
        if peak is not None:
            f.write(f'# Picco: shift {peak[0]} ns, codice ADC medio {peak[1]:.2f}\n')
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
