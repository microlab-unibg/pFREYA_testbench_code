# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
# from datetime import datetime
# import time
# import glob
# import config
# import pFREYA_tester_processing as pYtp
# import pFREYA_tester as freya
import sys
import json

#665 schiaccio bottone sen INJ e vedo quale procedura richiama
# ttk.Button(ts_lframe, text="Send INJ", command=lambda: pYtp.send_current_level(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[115,0], sticky=SE)

# gui = freya.pFREYA_gui
# pYtp.send_current_level(gui)


def send_current_level(current):
    rm = pyvisa.ResourceManager()
    ps = rm.open_resource('GPIB1::23::INSTR')
    print(ps.query('*IDN?'))

    ps.write(':OUTP:LOW FLO')
    ps.write(':OUTP:OFF:AUTO ON')
    ps.write(':OUTP:PROT ON')
    ps.write(':OUTP:RES:MODE FIX')
    ps.write(':OUTP:RES:SHUN DEF')
    ps.write(':SOUR:FUNC:MODE CURR')
    ps.write(':SOUR:CURR:MODE FIX')
    ps.write(f':SOUR:CURR:LEV {current}E-6')
    ps.write(':DISP:ENAB OFF')
    ps.write(':DISP:TEXT:DATA "pFREYA16"')
    ps.write(':DISP:TEXT:STAT ON')
    ps.write(':OUTP:STAT ON')

    print(f'''
        Low terminal: {ps.query(':OUTP:LOW?')[:-1]}
        Auto output off: {ps.query(':OUTP:OFF:AUTO?')[:-1]}
        Protection: {ps.query(':OUTP:PROT?')[:-1]}
        Resistance mode: {ps.query(':OUTP:RES:MODE?')[:-1]}
        Shunt resistance : {ps.query(':OUTP:RES:SHUN?')[:-1]}
        Output current mode: {ps.query(':SOUR:CURR:MODE?')[:-1]}
        Output current level: {ps.query(':SOUR:CURR:LEV?')[:-1]}
        Output voltage range: {ps.query(':SOUR:VOLT:RANG?')[:-1]}
        Output status: {ps.query(':OUTP:STAT?')[:-1]}
        ''')
    return current

#MAIN
json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

with open(json_file, "r") as f:
    gui_data = json.load(f)


current_level = gui_data["INJ"]["current_level"]
print(f"Livello corrente: {current_level}")

send_current_level(current_level)