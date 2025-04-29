import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
# from datetime import datetime
# import time
# import glob
import config
# import pFREYA_tester_processing as pYtp
# import pFREYA_tester as freya
import sys
import json
import grafici


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

def send_current_level2(current):
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

    return current


#MAIN
json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

with open(json_file, "r") as f:
    gui_data = json.load(f)


current_level = gui_data["INJ"]["current_level"]
print(f"Livello corrente: {current_level}")

dict = {
    'Current level' : [],
    'AVG SOT': [],
    '% SOT' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

count = 0
data = []
for i in np.arange(0.0, -2.0, -0.0025):
    #QUI INVIARE LA CORRENTE (i)
    data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
    dict['Current level'].append(i)
    








# x = [dict['Current level']]
# y = [dict['% SOT']]
# label = 'null'
# xlabel = 'Current [μA]'
# ylabel = 'Scatti [%]'
# title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

# grafici.creaGrafico(x, y, label, xlabel, ylabel, title)

