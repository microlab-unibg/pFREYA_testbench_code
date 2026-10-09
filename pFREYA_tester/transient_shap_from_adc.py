#!/usr/bin/python
"""
Ricostruzione temporale dello shaper tramite sfasamento tra SH_PHI1D_INF e SH_PHI1D_SUP.
Clock, timing, pixel e corrente iniettata sono fissi. Per ogni livello dello shaper in SHAPER_MODES:
  1. slow control della configurazione
  2. selezione pixel, CSA_RESET_N, SH_PHI1D_INF/SUP, ADC_START, sync_time_bases
  3. sweep del solo delay del segnale scelto con SWEEP (high/low e l'altro S&H invariati); ad ogni
     passo send del segnale + sync_time_bases e N_SAMPLES codici ADC letti con send_VAL
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

#OUTPUT_DIR = r'C:/Users/giorg/Desktop/tesi/pFREYA_testbench_code/data/shap'
OUTPUT_DIR = r'G:/Shared drives/FALCON/measures/new/transient/adc'

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
N_SAMPLES = 5           # letture VAL per posizione dello sweep

# Segnale sweepato: 'inf' -> SH_PHI1D_SUP fisso e sweep di SH_PHI1D_INF; 'sup' -> il contrario
SWEEP = 'inf'
SWEPT, HELD = ('sh_phi1d_inf', 'sh_phi1d_sup') if SWEEP == 'inf' else ('sh_phi1d_sup', 'sh_phi1d_inf')

# L'hold e' il fronte di discesa (delay + high). Il segnale fisso tiene a HOLD_START, quello
# sweepato da HOLD_START a HOLD_STOP; ADC_START sale a 404+10000 = 10404.
TICK_NS = 5
HOLD_START = 10160      
HOLD_STOP = 10380       
HOLD_STEP = 4           
HELD_DELAY = HOLD_START - int(FIXED_TIMING[HELD][1])     # 'inf': SUP 1120, 'sup': INF 1204
SWEEP_DELAYS = range(HOLD_START - int(FIXED_TIMING[SWEPT][1]),
                     HOLD_STOP - int(FIXED_TIMING[SWEPT][1]) + 1, HOLD_STEP)
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


def shift_tick(delay):
    """Sfasamento dell'hold del segnale sweepato rispetto a quello del segnale fisso [tick]."""
    return hold_tick(SWEPT, delay) - hold_tick(HELD, HELD_DELAY)


def check_sweep():
    """Verifica i vincoli temporali dello sweep prima di toccare l'hardware."""
    periods = {n: int(h) + int(l) for n, (_, h, l) in FIXED_TIMING.items()}
    if len(set(periods.values())) != 1:
        raise ValueError(f'I fast control hanno periodi diversi: {periods}')
    period = periods['adc_start']
    adc_tick = int(FIXED_TIMING['adc_start'][0]) + period     # ADC_START che converte i campioni tenuti
    read_tick = int(FIXED_TIMING['adc_start'][0]) + int(FIXED_AUTO_READ_DELAY)
    for name, d in [(HELD, HELD_DELAY)] + [(SWEPT, d) for d in SWEEP_DELAYS]:
        label = name.upper()
        if not 1 <= d < 2**18:          # delay 0 blocca il segnale a 0, registri a 18 bit
            raise ValueError(f'delay {label} {d} fuori da [1, 2^18)')
        if hold_tick(name, d) + ADC_START_MARGIN > adc_tick:
            raise ValueError(f'delay {label} {d}: hold a {hold_tick(name, d)} tick, '
                             f'troppo vicino ad ADC_START ({adc_tick} tick)')
        if d <= read_tick:              # l'S&H deve restare in hold fino all'auto-read
            raise ValueError(f'delay {label} {d}: torna in track prima dell\'auto-read ({read_tick} tick)')


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
    # asse x in us: sfasamento dell'hold del segnale sweepato rispetto a quello fisso
    x_lim = [shift_tick(d) * TICK_NS / 1e3 for d in (SWEEP_DELAYS[0], SWEEP_DELAYS[-1])]
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
        self.parent.title(f'Transiente shaper da ADC (sweep {SWEPT.upper()}, {HELD.upper()} fisso)')
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
        base = os.path.join(OUTPUT_DIR, f'transient_adc_{SWEEP}sweep_px{pixel}_{timestamp}')
        send_swept = getattr(pYtp, f'send_{SWEPT.upper()}')
        try:
            check_sweep()
            ps = open_power_supply()
            init_fpga(cfg)
            cfg_held = getattr(cfg, HELD)
            cfg_swept = getattr(cfg, SWEPT)
            cfg_held['delay'].set(str(HELD_DELAY))
            cfg_swept['delay'].set(str(SWEEP_DELAYS[0]))

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
                    for i, delay in enumerate(SWEEP_DELAYS):
                        if not self.running:
                            print('Interrotto dall\'utente.')
                            break
                        # cambia solo il delay del segnale sweepato; il sync lo applica e riallinea l'altro S&H
                        cfg_swept['delay'].set(str(delay))
                        if send_swept(cfg):
                            raise RuntimeError(f'invio {SWEPT.upper()} fallito (delay {delay})')
                        pYtp.send_sync_time_bases()
                        time.sleep(STEP_SETTLE_S)
                        shift = shift_tick(delay)
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
                            'swept_signal': SWEPT, 'swept_delay_tick': delay,
                            'swept_hold_tick': hold_tick(SWEPT, delay),
                            'held_hold_tick': hold_tick(HELD, HELD_DELAY),
                            'shift_tick': shift, 'shift_ns': shift * TICK_NS,
                            'n_valid': len(codes),
                            'adc_code_mean': np.mean(codes) if codes else float('nan'),
                            'adc_code_std': np.std(codes) if codes else float('nan'),
                            'adc_codes': ' '.join(map(str, codes)),
                        })
                        print(f'  [{i+1}/{len(SWEEP_DELAYS)}] {SWEEP.upper()} delay={delay} shift={shift * TICK_NS} ns '
                              + (f'codice ADC = {np.mean(codes):.1f}' if codes else 'codice ADC = ERRORE'))
                        if codes:
                            data['x'].append(shift * TICK_NS)
                            data['y'].append(float(np.mean(codes)))
                            data['err'].append(float(np.std(codes)))
                        self.parent.after(0, self.update_plot)
                finally:
                    data['done'] = True
                    # posizioni iniziali per la prossima configurazione
                    cfg_swept['delay'].set(str(SWEEP_DELAYS[0]))
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
        f.write(f'# {HELD.upper()} fisso (delay {HELD_DELAY}, hold {hold_tick(HELD, HELD_DELAY)}); '
                f'sweep delay {SWEPT.upper()} [tick {TICK_NS} ns]: start {SWEEP_DELAYS[0]}, '
                f'stop {SWEEP_DELAYS[-1]}, step {HOLD_STEP}; campioni VAL per posizione: {N_SAMPLES}\n')
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
