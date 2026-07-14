#!/usr/bin/python

import os
import sys
import csv
import time
import serial
import threading
import traceback
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
#OUTPUT_DIR = f'G:/Shared drives/FALCON/measures/new/adc'


#per clock senza gui principale
class ClockConfig:
    def __init__(self, root, dac_sck_period='100'):
        self.slow_ck = tk.StringVar(root, value='4000')
        self.sel_ck = tk.StringVar(root, value='4000')
        self.adc_ck = tk.StringVar(root, value='20')
        self.inj_stb = tk.StringVar(root, value='1')
        self.ser_ck = tk.StringVar(root, value='400')
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

        #selezione pixel  
        self.pixel_row = tk.StringVar(root, value='4')
        self.pixel_col = tk.StringVar(root, value='0')

        # timing adc
        self.adc_start = {
            'delay': tk.StringVar(root, value='604'),
            'high':  tk.StringVar(root, value='2'),
            'low':   tk.StringVar(root, value='262141')
        }

def init_fpga(clock_cfg):
    """Reset FPGA e configura SPI clock."""
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
    """Invia un codice digitale al DAC selezionato.
    
    Se ser è fornito, usa la porta seriale persistente (senza aprire/chiudere).
    Altrimenti usa la funzione originale.
    """
    dac_packet = pYtp.create_dac_packet_auto(code)
    if ser is not None:
        pYtp.send_uart_dac_auto_persistent(ser, dac_packet, cs2=cs2)
    else:
        pYtp.send_uart_dac_auto(dac_packet, cs2=cs2)
    print(f"Invio DAC code = {code}")
    print(f"Packet = {dac_packet}\n")


# selezione del pixel
def select_pixel(cfg, ser=None):
    """Seleziona il pixel attivo sull'ASIC, stessa sequenza della GUI.

    Se ser è fornito, usa la porta seriale persistente (senza aprire/chiudere).
    """
    print('Selezione pixel...')
    if ser is not None:
        ret = pYtp.send_pixel_persistent(ser, cfg)
    else:
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

#gui
class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Invio livelli DAC')
        self.running = False

        #var
        self.step     = tk.StringVar(self.parent, value='100')
        self.settling = tk.StringVar(self.parent, value='1')

        # numero di campioni ADC per livello DAC
        self.n_samples = tk.StringVar(self.parent, value='5')

        # estremi della scansione (CS1). Se min == max viene acquisito un solo livello e posso impostare diversi campioni.
        self.level_min = tk.StringVar(self.parent, value='0')
        self.level_max = tk.StringVar(self.parent, value='31500')

        #grafica
        row = 0

        ttk.Label(self.parent, text='Step (0-31500):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.step, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        # estremi scansione: se uguali, acquisisce un solo livello, i livelli vengono impostati del dac1 perchè quello del dac2 lo calcolo 31500-dac1
        ttk.Label(self.parent, text='Livello min (DAC1):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.level_min, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        ttk.Label(self.parent, text='Livello max (DAC1):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.level_max, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        # numero campioni ADC per livello (default 6)
        ttk.Label(self.parent, text='N campioni ADC:').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.n_samples, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        #button
        self.buttonLaunch = ttk.Button(self.parent, text='Avvia', command=self.launch)
        self.buttonLaunch.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)
        self.buttonStop = ttk.Button(self.parent, text='Stop', command=self.stop)
        row += 1
        self.stop_button_row = row

        #plot
        self.figure = plt.Figure(figsize=(8, 5), dpi=100)
        self.axes   = self.figure.add_subplot(111)
        self.axes.tick_params(axis='both', which='both',
                              labeltop=False, labelright=True,
                              labelbottom=True, labelleft=True,
                              top=True, right=True, bottom=True, left=True)
        self.axes.minorticks_on()
        self.axes.set_title('Caratteristica  ADC')
        self.axes.set_xlabel('Vin(V)')
        self.axes.set_ylabel('Codice ADC')
        self.axes.grid(True, alpha=0.3)
        self.canvas = backend_tkagg.FigureCanvasTkAgg(self.figure, self.parent)
        self.canvas.draw()
        
        self.canvas.get_tk_widget().grid(row=row, column=0, rowspan=4, columnspan=3,
                                         sticky=(tk.N, tk.S, tk.E, tk.W), padx=15, pady=15)
        row += 4

        self.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))


    def update_plot(self):
        self.axes.clear()

        # Grafico a gradini (staircase) della caratteristica ADC
        if len(self.x_steps) > 0:
            self.axes.step(self.x_steps, self.y_steps, color='red', where='post', label='Caratteristica ADC')

        # Singoli campioni ADC sovrapposti come marker
        if len(self.x_samples) > 0:
            self.axes.plot(self.x_samples, self.y_samples, 'g.', markersize=6, alpha=0.6, label='Campioni')

        self.axes.set_title('Caratteristica di Trasferimento ADC')
        self.axes.set_xlabel('Vin differenziale (V)')
        # Asse Y in codici ADC DECIMALI (0–1023 per 10 bit)
        self.axes.set_ylabel('Codice ADC (decimale)')
        self.axes.grid(True, alpha=0.3)
        self.axes.legend(loc='upper left')

        self.canvas.draw()


    def stop(self):
        if self.running:
            self.running = False
            self.buttonStop.grid_forget()
            
    def launch(self):
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
        settling_time = float(self.settling.get())
        n_samples     = int(self.n_samples.get())
        level_min     = int(self.level_min.get())
        level_max     = int(self.level_max.get())

        # CS1: crescente da level_min a level_max
        # CS2: decrescente (fondo scala DAC fisso a 31500, indipendente dagli estremi di scansione)
        dac_max = 31500
        codes_cs1 = np.arange(level_min, level_max + 1, step)
        if len(codes_cs1) > 0 and codes_cs1[-1] != level_max:
            codes_cs1 = np.append(codes_cs1, level_max)

        codes_cs2 = dac_max - codes_cs1

        total = len(codes_cs1)
        # se min == max (un solo punto), è un'acquisizione a livello singolo
        single_level = total == 1
        print(f'\n--- Invio livelli CS1+CS2 differenziale | {total} punti | step={step} | n_samples={n_samples} ---')

        clock_cfg = ClockConfig(self.parent)
        # risultati ADC
        results = []

        # Variabili per il grafico real-time
        self.x_samples = []
        self.y_samples = []
        self.x_steps = []
        self.y_steps = []
        self.x_steps_med = []
        self.y_steps_med = []

        ser = None

        try:
            # 1. invio clock
            init_fpga(clock_cfg)

            # 2. avvio ADC  configura il segnale ADC_START nella FPGA
            pYtp.send_ADC_START(clock_cfg)

            # .3 selezioni pixel
            select_pixel(clock_cfg)

            # 4. sincronizzazione allinea le basi tempi dei segnali generati
            pYtp.send_sync_time_bases()

            # Apertura porta seriale persistente per tutta la sessione di misura
            ser = serial.Serial(UARTdef.COM_PORT, UARTdef.BAUD_RATE, timeout=10)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            print(f'Porta seriale {UARTdef.COM_PORT} aperta (persistente per la sessione).\n')

            t_start = time.perf_counter()

            for i in range(total):
                if not self.running:
                    print('Interrotto dall\'utente.')
                    break

                code_cs1 = codes_cs1[i]
                code_cs2 = codes_cs2[i]

                # Rinvio clock, selezione pixel, ADC start ad ogni livello (ora tutti commentati)
                # per garantire che il dato arrivi effettivamente ogni volta
                #pYtp.send_clocks_persistent(ser, clock_cfg)
                #pYtp.send_ADC_START_persistent(ser, clock_cfg)
                #select_pixel(clock_cfg, ser=ser)

                # invio dato sul primo dac
                set_dac_code(code_cs1, cs2=False, ser=ser)
                # invio dato sul secondo dac 
                set_dac_code(code_cs2, cs2=True, ser=ser)
                
                # 6. attesa di stabilizzazione dell'uscita analogica dei DAC
                time.sleep(settling_time)

                step_adc_values = []
                
                # 7. lettura dati ADC  n_samples letture per ogni livello DAC
                for s in range(n_samples):
                    # sync inviato prima di ogni singolo campione
                    pYtp.send_sync_time_bases_persistent(ser)
                    result = pYtp.send_READ_DATA_persistent(ser, clock_cfg)
                    time.sleep(0.05) #attesa tra un campione e l'altro
                    if result != 1:
                        adc_data, sot = result
                        adc_value = int(adc_data, 2)
                        results.append({
                            'step': i,
                            'sample': s,
                            'cs1_code': int(code_cs1),
                            'cs2_code': int(code_cs2),
                            'adc_raw': adc_data,
                            'adc_value': adc_value,
                            'sot': sot
                        })

                        v_in = (code_cs1 - code_cs2) * (2.5 / 65535.0)
                        self.x_samples.append(v_in)
                        self.y_samples.append(adc_value)
                        step_adc_values.append(adc_value)
                        print(f'  [{i+1}/{total}][s{s+1}] CS1={code_cs1:>5d} CS2={code_cs2:>5d} ADC={adc_value} (raw={adc_data})\n')
                    else:
                        print(f'  [{i+1}/{total}][s{s+1}] CS1={code_cs1:>5d} CS2={code_cs2:>5d} ADC=ERRORE\n')

                if step_adc_values:
                    v_in = (code_cs1 - code_cs2) * (2.5 / 65535.0)
                    self.x_steps.append(v_in)
                    self.y_steps.append(int(np.round(np.mean(step_adc_values))))
                
                self.x_steps_med.append(np.median(v_in))
                self.y_steps_med.append(np.median((reject_outliers(np.array(step_adc_values)))))

                # 8. aggiornamento grafico real-time
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
                set_dac_code(0, cs2=False, ser=ser)
                set_dac_code(0, cs2=True, ser=ser)
                print('DAC CS1 e CS2 azzerati.')
            except Exception:
                pass

            # Chiusura porta seriale persistente
            try:
                ser.close()
                print(f'Porta seriale {UARTdef.COM_PORT} chiusa.')
            except Exception:
                pass

            # salvo dati e grafico
            if results:
                timestamp = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')

                if single_level:
                    # acquisizione a livello singolo: salvo in data/singleLevel con dettagli sulla misura
                    level_value = int(codes_cs1[0])
                    single_level_dir = os.makedirs(OUTPUT_DIR, exist_ok=True)

                    filename = os.path.join(single_level_dir, f'single_level_{level_value}_{timestamp}.csv')
                    with open(filename, 'w', newline='') as f:
                        f.write('# Acquisizione a livello singolo\n')
                        f.write(f'# Livello (codice CS1): {level_value}\n')
                        f.write(f'# Codice CS2 corrispondente: {int(codes_cs2[0])}\n')
                        f.write(f'# Numero di campioni: {n_samples}\n')
                        f.write(f'# Step: {step}\n')
                        f.write(f'# Tempo di settling (s): {settling_time}\n')
                        f.write(f'# Timestamp: {timestamp}\n')
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                    print(f'Risultati livello singolo salvati in: {filename}')

                    fig_filename = os.path.join(single_level_dir, f'single_level_{level_value}_{timestamp}.pdf')
                    self.figure.savefig(fig_filename, dpi=300)
                    print(f'Grafico salvato in: {fig_filename}')
                else:
                    os.makedirs(OUTPUT_DIR, exist_ok=True)

                    filename = os.path.join(OUTPUT_DIR, f'dac_adc_scan_{timestamp}.csv')
                    with open(filename, 'w', newline='') as f:
                        f.write('# Acquisizione a range di livelli\n')
                        f.write(f'# Livello minimo (codice CS1): {level_min}\n')
                        f.write(f'# Livello massimo (codice CS1): {level_max}\n')
                        f.write(f'# Numero di punti: {total}\n')
                        f.write(f'# Numero di campioni: {n_samples}\n')
                        f.write(f'# Step: {step}\n')
                        f.write(f'# Tempo di settling (s): {settling_time}\n')
                        f.write(f'# Timestamp: {timestamp}\n')
                        writer = csv.DictWriter(f, fieldnames=results[0].keys())
                        writer.writeheader()
                        writer.writerows(results)
                    print(f'Risultati salvati in: {filename}')

                    fig_filename = os.path.join(OUTPUT_DIR, f'dac_adc_scan_{timestamp}.pdf')
                    self.figure.savefig(fig_filename, dpi=300)
                    print(f'Grafico salvato in: {fig_filename}')
            else:
                print('Nessun risultato ADC da salvare.')

            print('Fatto.\n')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()

