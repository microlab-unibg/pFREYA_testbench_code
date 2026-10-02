#!/usr/bin/python
"""
Caratteristica di trasferimento ADC con autoread.

Per ogni livello DAC (differenziale CS1/CS2):
  1. Imposta il livello DAC
  3. Fa sync_time_bases (triggera un ciclo di acquisizione)
  4. Legge N campioni con send_VAL 
"""

import os
import sys
import csv
import time
import json
import threading
import traceback
import serial
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as backend_tkagg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import UART_definitions as UARTdef
import pFREYA_tester_processing as pYtp

# Directory di output
OUTPUT_DIR = r'C:/Users/giorg/Desktop/tesi/pFREYA_testbench_code/data'


class TesterConfig:
    def __init__(self, root, dac_sck_period='100'):
        self.slow_ck = tk.StringVar(root, value='4000')
        self.sel_ck = tk.StringVar(root, value='4000')
        self.adc_ck = tk.StringVar(root, value='20')
        self.inj_stb = tk.StringVar(root, value='1')
        self.ser_ck = tk.StringVar(root, value='100')
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

        # slow control
        self.csa_mode_n = tk.StringVar(root, value='10')
        self.inj_en_n = tk.StringVar(root, value='1')
        self.shap_mode = tk.StringVar(root, value='10')
        self.ch_en = tk.StringVar(root, value='1')
        self.inj_mode_n = tk.StringVar(root, value='1')
        self.pixel_to_inj = tk.StringVar(root, value='4')

        # selezione pixel
        self.pixel_row = tk.StringVar(root, value='4')
        self.pixel_col = tk.StringVar(root, value='0')

        # timing asic
        self.csa_reset_n = {
            'delay': tk.StringVar(root, value='104'),
            'high':  tk.StringVar(root, value='60'),
            'low':   tk.StringVar(root, value='9940')
        }
        self.sh_phi1d_inf = {
            'delay': tk.StringVar(root, value='1204'),
            'high':  tk.StringVar(root, value='8956'),
            'low':   tk.StringVar(root, value='1044')
        }
        self.sh_phi1d_sup = {
            'delay': tk.StringVar(root, value='1204'),
            'high':  tk.StringVar(root, value='9040'),
            'low':   tk.StringVar(root, value='960')
        }
        self.adc_start = {
            'delay': tk.StringVar(root, value='404'),
            'high':  tk.StringVar(root, value='4'),
            'low':   tk.StringVar(root, value='9996')
        }
        self.ser_read = {
            'delay': tk.StringVar(root, value='10'),
            'high':  tk.StringVar(root, value='10'),
            'low':   tk.StringVar(root, value='10')
        }

        # Caricamento da config JSON
        auto_delay_val = '200'
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pFREYA_tester_config.json')
        try:
            with open(json_path, 'r') as f:
                j = json.load(f)
                
                clocks = j.get("clocks", {})
                self.slow_ck.set(clocks.get("slow_ck", self.slow_ck.get()))
                self.sel_ck.set(clocks.get("sel_ck", self.sel_ck.get()))
                self.adc_ck.set(clocks.get("adc_ck", self.adc_ck.get()))
                self.inj_stb.set(clocks.get("inj_stb", self.inj_stb.get()))
                self.ser_ck.set(clocks.get("ser_ck", self.ser_ck.get()))
                self.dac_sck.set(clocks.get("dac_sck", self.dac_sck.get()))

                slow_ctrl = j.get("slow_ctrl", {})
                self.csa_mode_n.set(slow_ctrl.get("csa_mode_n", self.csa_mode_n.get()))
                self.inj_en_n.set(slow_ctrl.get("inj_en_n", self.inj_en_n.get()))
                self.shap_mode.set(slow_ctrl.get("shap_mode", self.shap_mode.get()))
                self.ch_en.set(slow_ctrl.get("ch_en", self.ch_en.get()))
                self.inj_mode_n.set(slow_ctrl.get("inj_mode_n", self.inj_mode_n.get()))
                self.pixel_to_inj.set('4') # Override da richiesta (pixel to inject = 4)

                pixel_sel = j.get("pixel_sel", {})
                self.pixel_row.set(pixel_sel.get("pixel_row", self.pixel_row.get()))
                self.pixel_col.set(pixel_sel.get("pixel_col", self.pixel_col.get()))

                asic_ctrl = j.get("asic_ctrl", {})
                auto_delay_val = asic_ctrl.get("auto_read_delay", '100')
                
                csa_rn = asic_ctrl.get("csa_reset_n", {})
                self.csa_reset_n['delay'].set(csa_rn.get("delay", self.csa_reset_n['delay'].get()))
                self.csa_reset_n['high'].set(csa_rn.get("high", self.csa_reset_n['high'].get()))
                self.csa_reset_n['low'].set(csa_rn.get("low", self.csa_reset_n['low'].get()))

                sh_inf = asic_ctrl.get("sh_phi1d_inf", {})
                self.sh_phi1d_inf['delay'].set(sh_inf.get("delay", self.sh_phi1d_inf['delay'].get()))
                self.sh_phi1d_inf['high'].set(sh_inf.get("high", self.sh_phi1d_inf['high'].get()))
                self.sh_phi1d_inf['low'].set(sh_inf.get("low", self.sh_phi1d_inf['low'].get()))

                sh_sup = asic_ctrl.get("sh_phi1d_sup", {})
                self.sh_phi1d_sup['delay'].set(sh_sup.get("delay", self.sh_phi1d_sup['delay'].get()))
                self.sh_phi1d_sup['high'].set(sh_sup.get("high", self.sh_phi1d_sup['high'].get()))
                self.sh_phi1d_sup['low'].set(sh_sup.get("low", self.sh_phi1d_sup['low'].get()))

                adc_s = asic_ctrl.get("adc_start", {})
                self.adc_start['delay'].set(adc_s.get("delay", self.adc_start['delay'].get()))
                self.adc_start['high'].set(adc_s.get("high", self.adc_start['high'].get()))
                self.adc_start['low'].set(adc_s.get("low", self.adc_start['low'].get()))
                
                ser_r = asic_ctrl.get("ser_read", {})
                self.ser_read['delay'].set(ser_r.get("delay", self.ser_read['delay'].get()))
                self.ser_read['high'].set(ser_r.get("high", self.ser_read['high'].get()))
                self.ser_read['low'].set(ser_r.get("low", self.ser_read['low'].get()))
        except Exception:
            pass
            
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--delay', type=str, help='Auto Read Delay override')
        args, _ = parser.parse_known_args()
        if args.delay:
            auto_delay_val = args.delay

        self.auto_read_delay = tk.StringVar(root, value=auto_delay_val)


def init_fpga(clock_cfg):
    """Reset FPGA e configura clock."""
    print('Reset FPGA...')
    pYtp.send_reset_FPGA()
    time.sleep(0.2)
    print('Invio di tutti i clock necessari...')
    for ck_code in [UARTdef.SLOW_CTRL_CK_CODE, UARTdef.SEL_CK_CODE, UARTdef.ADC_CK_CODE,
                    UARTdef.INJ_STB_CODE, UARTdef.DAC_SCK_CODE, UARTdef.SER_CK_CODE]:
        pYtp.send_clock_single(clock_cfg, ck_code)
    time.sleep(0.1)
    print('FPGA pronta.\n')


def set_dac_code(code, cs2=False, ser=None):
    """Invia un codice digitale al DAC selezionato."""
    dac_packet = pYtp.create_dac_packet_auto(code)
    pYtp.send_uart_dac_auto(dac_packet, cs2=cs2)
    print(f"Invio DAC code = {code}")
    print(f"Packet = {dac_packet}\n")


def select_pixel(cfg):
    """Seleziona il pixel attivo sull'ASIC."""
    print('Selezione pixel...')
    ret = pYtp.send_pixel(cfg)
    if ret != 0:
        raise RuntimeError('Errore nella selezione del pixel.')
    time.sleep(0.1)
    print(f'Pixel selezionato: row={cfg.pixel_row.get()}, col={cfg.pixel_col.get()}\n')


# Source - https://stackoverflow.com/a/11686764
# Posted by eumiro, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-17, License - CC BY-SA 3.0
def reject_outliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]


class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Caratteristica ADC — Auto-Read Pura')
        self.running = False

        self.clock_cfg = TesterConfig(self.parent)

        # Variabili di configurazione
        self.step     = tk.StringVar(self.parent, value='100')
        self.n_samples = tk.StringVar(self.parent, value='5')
        self.level_min = tk.StringVar(self.parent, value='0')
        self.level_max = tk.StringVar(self.parent, value='31500')

        # --- Layout ---
        row = 0

        ttk.Label(self.parent, text='Step (0-31500):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.step, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        ttk.Label(self.parent, text='Livello min (DAC1):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.level_min, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        ttk.Label(self.parent, text='Livello max (DAC1):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.level_max, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        ttk.Label(self.parent, text='N campioni VAL per livello:').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.n_samples, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1


        # Auto read delay READ ONLY, che viene prelevato da config
        ttk.Label(self.parent, text='Auto Read Delay:').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.clock_cfg.auto_read_delay, width=8, state='readonly').grid(
            row=row, column=1, sticky=tk.E, padx=5)
        ttk.Label(self.parent, text='FP').grid(row=row, column=2, sticky=tk.W)
        row += 1

        # Bottoni
        self.buttonLaunch = ttk.Button(self.parent, text='Avvia', command=self.launch)
        self.buttonLaunch.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)
        self.buttonStop = ttk.Button(self.parent, text='Stop', command=self.stop)
        row += 1
        self.stop_button_row = row

        # Plot
        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.axes   = self.figure.add_subplot(111)
        self.axes.tick_params(axis='both', which='both',
                              labeltop=False, labelright=True,
                              labelbottom=True, labelleft=True,
                              top=True, right=True, bottom=True, left=True)
        self.axes.minorticks_on()
        self.axes.set_title('Caratteristica ADC — Auto-Read')
        self.axes.set_xlabel('Vin differenziale (V)')
        self.axes.set_ylabel('Codice ADC (decimale)')
        self.axes.grid(True, alpha=0.3)
        self.canvas = backend_tkagg.FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas.draw()

        self.canvas.get_tk_widget().grid(row=row, column=0, rowspan=4, columnspan=3,
                                         sticky=(tk.N, tk.S, tk.E, tk.W), padx=15, pady=15)
        row += 4

        self.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

    def update_plot(self):
        self.axes.clear()

        # Caratteristica media a gradini
        if len(self.x_steps) > 0:
            self.axes.step(self.x_steps, self.y_steps, color='red', where='post',
                           label='Media (step)')

        # Singoli campioni VAL sovrapposti
        if len(self.x_samples) > 0:
            self.axes.plot(self.x_samples, self.y_samples, 'g.', markersize=6, alpha=0.6,
                           label='Campioni VAL (auto-read)')

        self.axes.set_title('Caratteristica ADC — Auto-Read Pura')
        self.axes.set_xlabel('Vin differenziale (V)')
        self.axes.set_ylabel('Codice ADC (decimale)')
        self.axes.grid(True, alpha=0.3)
        self.axes.legend(loc='upper left')

        self.canvas.draw()

    def stop(self):
        if self.running:
            self.running = False
            self.buttonStop.grid_forget()

    def launch(self):
        try:
            delay_ok = int(self.clock_cfg.auto_read_delay.get()) > 0
        except ValueError:
            delay_ok = False
        if not delay_ok:
            messagebox.showerror(
                message='Auto Read Delay deve essere > 0: con delay 0 l\'auto-read è disabilitato e VAL non si aggiorna.')
            return
        if not self.running:
            self.thread = threading.Thread(target=self.launch_t)
            self.thread.start()
            self.running = True
            self.buttonStop.grid(row=self.stop_button_row, column=1, sticky=tk.E, padx=5, pady=5)
        else:
            messagebox.showerror(
                message='Invio in corso. Ferma per avviarne uno nuovo.')

    def launch_t(self):
        step          = int(self.step.get())
        n_samples     = int(self.n_samples.get())
        level_min     = int(self.level_min.get())
        level_max     = int(self.level_max.get())

        dac_max = 31500
        codes_cs1 = np.arange(level_min, level_max + 1, step)
        if len(codes_cs1) > 0 and codes_cs1[-1] != level_max:
            codes_cs1 = np.append(codes_cs1, level_max)

        codes_cs2 = dac_max - codes_cs1

        total = len(codes_cs1)
        single_level = total == 1
        auto_rd_delay = self.clock_cfg.auto_read_delay.get()
        print(f'\n--- Auto-Read Sweep | {total} punti | step={step} | '
              f'n_samples={n_samples} | auto_read_delay={auto_rd_delay} ---')

        clock_cfg = self.clock_cfg
        results = []

        # Variabili per il grafico real-time
        self.x_samples = []
        self.y_samples = []
        self.x_steps = []
        self.y_steps = []
        try:
            # 1. Inizializzazione FPGA e clock
            init_fpga(clock_cfg)

            # 2. Invio slow control
            print('Invio slow control...')
            pYtp.send_slow_ctrl(clock_cfg)

            # 3. Selezione pixel
            select_pixel(clock_cfg)

            # 4. Invio segnali ASIC
            print('Invio segnali ASIC...')
            pYtp.send_CSA_RESET_N(clock_cfg)
            pYtp.send_SH_PHI1D_INF(clock_cfg)
            pYtp.send_SH_PHI1D_SUP(clock_cfg)

            #se viene messo ad ogni misurazione causa letture sbagliate e lentezza nella lettura del dato.
            pYtp.send_sync_time_bases()

            t_start = time.perf_counter()

            for i in range(total):
                if not self.running:
                    print('Interrotto dall\'utente.')
                    break

                code_cs1 = codes_cs1[i]
                code_cs2 = codes_cs2[i]

                # Imposta livelli DAC (differenziale)
                set_dac_code(code_cs1, cs2=False)
                set_dac_code(code_cs2, cs2=True)


                # E con il delay impostato: send adc start
                pYtp.send_ADC_START(clock_cfg)

                step_adc_values = []

                # Letture VAL: leggono il dato già auto-campionato
                # dall'FPGA tramite auto_read_delay. L'auto-read si ripete
                # ad ogni impulso adc_start.
                for s in range(n_samples):
                    # attesa per il settling del DAC e per nuovi frame auto-read
                    time.sleep(0.05)

                    result = pYtp.send_VAL(clock_cfg)

                    if result is not None:
                        adc_data, sot = result
                        adc_value = int(adc_data, 2)
                        results.append({
                            'step': i,
                            'sample': s,
                            'cs1_code': int(code_cs1),
                            'cs2_code': int(code_cs2),
                            'adc_raw': adc_data,
                            'adc_value': adc_value,
                            'sot': sot,
                            'auto_read_delay': auto_rd_delay,
                            'mode': 'auto_read_val'
                        })

                        v_in = (code_cs1 - code_cs2) * (2.5 / 65535.0)
                        self.x_samples.append(v_in)
                        self.y_samples.append(adc_value)
                        step_adc_values.append(adc_value)
                        print(f'  [{i+1}/{total}][s{s+1}] CS1={code_cs1:>5d} CS2={code_cs2:>5d} '
                              f'ADC={adc_value} (raw={adc_data})\n')
                    else:
                        print(f'  [{i+1}/{total}][s{s+1}] CS1={code_cs1:>5d} CS2={code_cs2:>5d} '
                              f'ADC=ERRORE\n')

                if step_adc_values:
                    v_in = (code_cs1 - code_cs2) * (2.5 / 65535.0)
                    self.x_steps.append(v_in)
                    self.y_steps.append(int(np.round(np.mean(step_adc_values))))

                # Aggiornamento grafico real-time
                self.parent.after(0, self.update_plot)

            t_end = time.perf_counter()
            print(f'Scansione completata in {t_end - t_start:.1f} secondi.')
            self.stop()

        except BaseException as err:
            print(f'Errore: {err}')
            traceback.print_exc()
            raise

        finally:
            print('Pulizia risorse...')
            try:
                set_dac_code(0, cs2=False)
                set_dac_code(0, cs2=True)
                print('DAC CS1 e CS2 azzerati.')
            except Exception:
                pass

            # Salvataggio dati e grafico
            if results:
                timestamp = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
                os.makedirs(OUTPUT_DIR, exist_ok=True)

                if single_level:
                    level_value = int(codes_cs1[0])
                    filename = os.path.join(OUTPUT_DIR, f'autoread_single_{level_value}_{timestamp}.csv')
                    with open(filename, 'w', newline='') as f:
                        f.write('# Caratteristica Auto-Read - Livello singolo\n')
                        f.write(f'# Livello (codice CS1): {level_value}\n')
                        f.write(f'# Codice CS2 corrispondente: {int(codes_cs2[0])}\n')
                        f.write(f'# Numero di campioni: {n_samples}\n')
                        f.write(f'# Auto Read Delay: {auto_rd_delay}\n')
                        f.write(f'# Modalità: auto-read pura (1 sync per livello, N letture VAL)\n')
                        f.write(f'# Timestamp: {timestamp}\n')
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                    print(f'Risultati salvati in: {filename}')

                    fig_filename = os.path.join(OUTPUT_DIR, f'autoread_single_{level_value}_{timestamp}.pdf')
                    self.figure.savefig(fig_filename, dpi=300)
                    print(f'Grafico salvato in: {fig_filename}')
                else:
                    filename = os.path.join(OUTPUT_DIR, f'autoread_scan_{timestamp}.csv')
                    with open(filename, 'w', newline='') as f:
                        f.write('# Caratteristica Auto-Read - Sweep DAC\n')
                        f.write(f'# Livello minimo (codice CS1): {level_min}\n')
                        f.write(f'# Livello massimo (codice CS1): {level_max}\n')
                        f.write(f'# Numero di punti: {total}\n')
                        f.write(f'# Numero di campioni VAL per livello: {n_samples}\n')
                        f.write(f'# Step: {step}\n')
                        f.write(f'# Auto Read Delay: {auto_rd_delay}\n')
                        f.write(f'# Modalità: auto-read pura (1 sync per livello, N letture VAL)\n')
                        f.write(f'# Timestamp: {timestamp}\n')
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                    print(f'Risultati salvati in: {filename}')

                    fig_filename = os.path.join(OUTPUT_DIR, f'autoread_scan_{timestamp}.pdf')
                    self.figure.savefig(fig_filename, dpi=300)
                    print(f'Grafico salvato in: {fig_filename}')
            else:
                print('Nessun risultato ADC da salvare.')

            print('Fatto.\n')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()
