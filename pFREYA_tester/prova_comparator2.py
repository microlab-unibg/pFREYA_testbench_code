import matplotlib.pyplot as plt
import numpy as np
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

mis = {
    'Current level' : [],
    '% SOT' : []
}

mis['Current level'] = np.array([
        -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100, -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
        -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450, -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
        -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
    ])

mis['% SOT'] = np.array([
        0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517,
        12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870,
        99.873, 99.874, 99.877, 99.876, 99.877
    ])

x = [mis['Current level']]
y = [mis['% SOT']]
label = 'null'
xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

grafici.creaGrafico(x, y, label, xlabel, ylabel, title)

