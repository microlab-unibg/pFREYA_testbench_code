#!/usr/bin/python

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import UART_definitions as UARTdef
import pFREYA_tester_processing as pYtp

# Directory di output
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

# Livello DAC corrispondente a ~1.25 V in ingresso all'ADC (per CS1 e CS2)
DAC_LEVEL_1V25 = 32500


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


def set_dac_code(code, cs2=False):
    """Invia un codice digitale al DAC selezionato."""
    dac_packet = pYtp.create_dac_packet_auto(code)
    pYtp.send_uart_dac_auto(dac_packet, cs2=cs2)
    print(f"Invio DAC code = {code}")
    print(f"Packet = {dac_packet}")


#gui
class GUI(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Invio livelli DAC')
        self.running = False

        #var
        self.step     = tk.StringVar(self.parent, value='1000')
        self.settling = tk.StringVar(self.parent, value='0.5')

        #grafica
        row = 0

        ttk.Label(self.parent, text='Step (0-65535):').grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(self.parent, textvariable=self.step, width=8).grid(
            row=row, column=1, columnspan=2, sticky=tk.E, padx=5)
        row += 1

        #button
        self.buttonLaunch = ttk.Button(self.parent, text='Avvia', command=self.launch)
        self.buttonLaunch.grid(row=row, column=2, sticky=tk.E, padx=5, pady=5)
        self.buttonStop = ttk.Button(self.parent, text='Stop', command=self.stop)
        row += 1

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
            self.buttonStop.grid(row=1, column=1, sticky=tk.E, padx=5, pady=5)

        else:
            messagebox.showerror(
                message='Invio in corso. Ferma per avviarne uno nuovo.')

    def launch_t(self):
        step          = int(self.step.get())
        settling_time = float(self.settling.get())

        #PER PRENDERE TUTTI I 65535 LIVELLI
        #codes = np.arange(0, 2**UARTdef.DAC_BITS, step)
        #if codes[-1] != 2**UARTdef.DAC_BITS - 1:
        #    codes = np.append(codes, 2**UARTdef.DAC_BITS - 1)

        # CS1:  crescente da 0 a ~1.25V (livello DAC_LEVEL_1V25)
        # CS2:  decrescente da ~1.25V (livello DAC_LEVEL_1V25) a 0
        # Entrambi inviati in contemporanea, stesso numero di punti.
        codes_cs1 = np.arange(0, DAC_LEVEL_1V25 + 1, step)
        if codes_cs1[-1] != DAC_LEVEL_1V25:
            codes_cs1 = np.append(codes_cs1, DAC_LEVEL_1V25)

        codes_cs2 = codes_cs1[::-1]  # CS2 parte da 1.25V e scende a 0

        total = len(codes_cs1)
        print(f'\n--- Invio livelli CS1+CS2 simultaneo | {total} punti | step={step} ---')

        clock_cfg = ClockConfig(self.parent)

        try:
            init_fpga(clock_cfg)

            for i in range(total):
                if not self.running:
                    print('Interrotto dall\'utente.')
                    break

                code_cs1 = codes_cs1[i]
                code_cs2 = codes_cs2[i]

                # Invio contemporaneo dei due codici
                set_dac_code(code_cs1, cs2=False)
                set_dac_code(code_cs2, cs2=True)

                time.sleep(settling_time)

                print(f'  [{i+1}/{total}] CS1={code_cs1:>5d} CS2={code_cs2:>5d}')

            print('Invio CS1+CS2 completato.')
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
            print('Fatto.\n')


if __name__ == '__main__':
    root = tk.Tk()
    GUI(root)
    root.mainloop()