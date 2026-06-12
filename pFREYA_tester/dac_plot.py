#!/usr/bin/python
"""Script per la caratterizzazione del DAC (CS1 / CS2).
Genera file TSV e grafico PDF della curva ingresso/uscita.
Comunicazione con multimetro Agilent 34461A via USB (USBTMC).
"""
import os
import sys
import time
import threading
import traceback
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as backend_tkagg
import pyvisa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import UART_definitions as UARTdef
import pFREYA_tester_processing as pYtp

# Indirizzo VISA del multimetro via USB (USBTMC).

MULTIMETER_VISA_ADDR = 'USB0::0x0957::0x1C07::MY53202489::INSTR'

# Directory di output
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


#per clock senza gui principale
class ClockConfig:
    def __init__(self, root, dac_sck_period='100'):
        self.slow_ck = tk.StringVar(root, value='40')
        self.sel_ck = tk.StringVar(root, value='262143')
        self.adc_ck = tk.StringVar(root, value='262143')
        self.inj_stb = tk.StringVar(root, value='1')
        self.ser_ck = tk.StringVar(root, value='262143')
        self.dac_sck = tk.StringVar(root, value=dac_sck_period)
        
        self.clock_map = {
            UARTdef.SLOW_CTRL_CK_CODE: self.slow_ck,
            UARTdef.SEL_CK_CODE:       self.sel_ck,
            UARTdef.ADC_CK_CODE:       self.adc_ck,
            UARTdef.INJ_STB_CODE:      self.inj_stb,
            UARTdef.DAC_SCK_CODE:      self.dac_sck,
            UARTdef.SER_CK_CODE:       self.ser_ck
        }
        self.slow_ck_sent = False
        self.sel_ck_sent  = False
        self.dac_sck_sent = False

def init_fpga(clock_cfg):
    """Reset FPGA e configura SPI clock."""
    print('Reset FPGA...')
    pYtp.send_reset_FPGA()
    time.sleep(2)
    print('Invio di tutti i clock necessari...')
    for ck_code in [UARTdef.SLOW_CTRL_CK_CODE, UARTdef.SEL_CK_CODE, UARTdef.ADC_CK_CODE, 
                    UARTdef.INJ_STB_CODE, UARTdef.DAC_SCK_CODE, UARTdef.SER_CK_CODE]:
        pYtp.send_clock_single(clock_cfg, ck_code)
    time.sleep(1)
    print('FPGA pronta.')


def init_multimeter(visa_addr):
    """Apre e configura il multimetro Agilent 34461A via USBTMC."""
    rm = pyvisa.ResourceManager()
    print(f'Risorse VISA disponibili: {rm.list_resources()}')

    multi = rm.open_resource(visa_addr)
    
    # Su USBTMC basta impostare timeout e terminatori.
    multi.timeout           = 10000   # ms
    multi.read_termination  = '\n'
    multi.write_termination = '\n'

    idn = multi.query('*IDN?').strip()
    print(f'Multimetro identificato: {idn}')

    multi.write('*RST')
    time.sleep(1)                        # attesa per reset
    multi.write('CONF:VOLT:DC 0.1')
    multi.write('VOLT:DC:RANGE:AUTO ON')
    multi.query('READ?') 
    multi.write('INP:IMP:AUTO ON')       # Deve essere inviato DOPO CONF, altrimenti viene sovrascritto

    print('Multimetro configurato.')
    return rm, multi


#misure
def measure_voltage(multimeter, n_samples):
    """Legge n_samples tensioni DC e ritorna media e std."""
    readings = np.empty(n_samples, dtype=float)
    for j in range(n_samples):
        readings[j] = float(multimeter.query('READ?'))
    return float(np.mean(readings)), float(np.std(readings))


def set_dac_code(code, cs2=False):
    """Invia un codice digitale al DAC selezionato."""
    dac_packet = pYtp.create_dac_packet_auto(code)
    pYtp.send_uart_dac_auto(dac_packet, cs2=cs2)
    print(f"Invio DAC code = {code}")
    print(f"Packet = {dac_packet}")
#salva e plot
def save_results(df, dac_id, output_dir):
    """Salva i risultati in un file TSV."""
    os.makedirs(output_dir, exist_ok=True)
    dt_str   = datetime.now().strftime('%Y%m%d_%H%M')
    filepath = os.path.join(output_dir, f'dac_characterization_{dac_id}_{dt_str}.tsv')
    df.to_csv(filepath, sep='\t', index=False)
    print(f'Dati salvati: {filepath}')
    return filepath


def plot_results(df, dac_id, output_dir, fig=None, ax=None):
    """Genera e salva il grafico della caratteristica del DAC."""
    os.makedirs(output_dir, exist_ok=True)
    dt_str   = datetime.now().strftime('%Y%m%d_%H%M')
    filepath = os.path.join(output_dir, f'dac_characterization_{dac_id}_{dt_str}.pdf')

    if fig is None or ax is None:
        fig_s, ax_s = plt.subplots(figsize=(8, 5))
    else:
        fig_s, ax_s = fig, ax
        ax_s.clear()

    ax_s.errorbar(df['dac_code'], df['measured_voltage'],
                  yerr=df['voltage_std'], fmt='s', markersize=3, capsize=2,
                  label=f'{dac_id} misurato')

    codes_arr = np.array(df['dac_code'])
    ax_s.plot(codes_arr, codes_arr / 65535.0 * 2.5, '--', color='grey',
              alpha=0.6, label='Ideale (VREF=2.5 V)')

    ax_s.set_xlabel('Codice DAC')
    ax_s.set_ylabel('Tensione misurata [V]')
    ax_s.set_title(f'Caratteristica DAC -- {dac_id}')
    ax_s.legend(loc='upper left')
    ax_s.tick_params(right=True, top=True, direction='in')
    ax_s.minorticks_on()
    ax_s.grid(True, alpha=0.3)
    fig_s.tight_layout()
    fig_s.savefig(filepath, dpi=300)
    print(f'Grafico salvato: {filepath}')

    if fig is None:
        plt.close(fig_s)
    return filepath


#gui
class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Caratterizzazione DAC')
        self.running = False

        #var
        self.dac_select      = tk.StringVar(self.parent, value='1')
        self.step            = tk.StringVar(self.parent, value='1000')
        self.samples         = tk.StringVar(self.parent, value='5')
        self.settling        = tk.StringVar(self.parent, value='0.5')
        self.multimeter_addr = tk.StringVar(self.parent, value=MULTIMETER_VISA_ADDR)

        #grafica
        row = 0

        ttk.Label(self.parent, text='DAC:').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        dac_frame = ttk.Frame(self.parent)
        dac_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(dac_frame, text='CS1', variable=self.dac_select,
                        value='1').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(dac_frame, text='CS2', variable=self.dac_select,
                        value='2').pack(side=tk.LEFT, padx=5)
        row += 1

        ttk.Label(self.parent, text='Step (0-65535):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.step, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1
        ttk.Label(self.parent, text='N samples:').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.samples, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1



        #button
        self.buttonLaunch = ttk.Button(self.parent, text='Avvia', command=self.launch)
        self.buttonLaunch.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)
        self.buttonStop = ttk.Button(self.parent, text='Stop', command=self.stop)
        row += 1

        #plot
        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.axes   = self.figure.add_subplot(111)
        self.axes.tick_params(axis='both', which='both',
                              labeltop=True, labelright=True,
                              labelbottom=True, labelleft=True,
                              top=True, right=True, bottom=True, left=True)
        self.axes.minorticks_on()
        self.canvas = backend_tkagg.FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas.draw()

        ttk.Label(self.parent, text='Caratteristica DAC').grid(
            row=row, column=0, sticky=tk.W, padx=15)
        row += 1
        self.canvas.get_tk_widget().grid(row=row, column=0, rowspan=4, columnspan=3,
                                         sticky=(tk.N, tk.S, tk.E, tk.W), padx=15, pady=15)

        self.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    def stop(self):
        if self.running:
            self.running = False
            self.buttonStop.grid_forget()

    def launch(self):
        if not self.running:
            self.thread = threading.Thread(target=self.launch_t)
            self.thread.start()
            self.running = True
            self.buttonStop.grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)

        else:
            messagebox.showerror(
                message='Misura in corso. Ferma per avviarne una nuova.')

    def launch_t(self):
        cs2           = (int(self.dac_select.get()) == 2)
        dac_id        = 'CS2' if cs2 else 'CS1'
        step          = int(self.step.get())
        n_samples     = int(self.samples.get())
        settling_time = 0.2
        visa_addr     = self.multimeter_addr.get()

        #PER PRENDERE TUTTI I 65535 LIVELLI
        #codes = np.arange(0, 2**UARTdef.DAC_BITS, step)
        #if codes[-1] != 2**UARTdef.DAC_BITS - 1:
        #    codes = np.append(codes, 2**UARTdef.DAC_BITS - 1)

        #PER PRENDERE DA 0 A 1.5[V] circa da livello 0 a 39000, dato che ci interess prendere il livello 1.2 di entrambi i cs1 e cs2
        codes = np.arange(0, 32501, step)
        if codes[-1] != 32500:
            codes = np.append(codes, 32500)

        total = len(codes)
        print(f'\n--- Caratterizzazione {dac_id} | {total} punti | step={step} '
              f'| porta={visa_addr} ---')

        clock_cfg = ClockConfig(self.parent)
        rm        = None
        multi     = None

        try:
            init_fpga(clock_cfg)
            rm, multi = init_multimeter(visa_addr)

            results = {
                'dac_id':            [],
                'dac_code':          [],
                'measured_voltage':  [],
                'voltage_std':       [],
            }

            for i, code in enumerate(codes):
                if not self.running:
                    print('Interrotto dall\'utente.')
                    break

                set_dac_code(code, cs2=cs2)
                time.sleep(settling_time)
                #metodo per verificare che sia settato auto sul multimetro ad ogni codice
                multi.write('CONF:VOLT:DC 0.1')
                multi.write('VOLT:DC:RANGE:AUTO ON')
                multi.write('INP:IMP:AUTO ON')

                v_mean, v_std = measure_voltage(multi, n_samples)

                results['dac_id'].append(dac_id)
                results['dac_code'].append(int(code))
                results['measured_voltage'].append(v_mean)
                results['voltage_std'].append(v_std)

                print(f'  [{i+1}/{total}] code={code:>5d}  V={v_mean:+.6f}  std={v_std:.2e}')

            df = pd.DataFrame(results)
            print(f'Sweep {dac_id} completato.')

            save_results(df, dac_id, OUTPUT_DIR)
            plot_results(df, dac_id, OUTPUT_DIR, fig=self.figure, ax=self.axes)
            self.parent.after(0, self.canvas.draw)
            self.stop()

        except BaseException as err:
            print(f'Errore: {err}')
            traceback.print_exc()
            raise

        finally:
            print('Pulizia risorse...')
            try:
                set_dac_code(0, cs2=cs2)
                print(f'DAC {dac_id} azzerato.')
            except Exception:
                pass
            if multi is not None:
                try:
                    multi.write('DISP:TEXT:CLE')
                    multi.close()
                except Exception:
                    pass
            if rm is not None:
                try:
                    rm.close()
                except Exception:
                    pass
            print('Fatto.\n')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()