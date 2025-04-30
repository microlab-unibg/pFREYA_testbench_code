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
    global rm, ps
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

# current_level = gui_data["INJ"]["current_level"]
# print(f"Livello corrente: {current_level}")

print("Current: " + send_current_level(0))

dict = {
    'Current level' : [],
    'AVG SOT': [],
    '% SOT' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

count = 0
data = []
for i in np.arange(-0.0025, -0.80, -0.0025):
    ps.write(f':SOUR:CURR:LEV {i}E-6')
    #data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
    dict['Current level'].append(i)
    








# x = [dict['Current level']]
# y = [dict['% SOT']]
# label = 'null'
# xlabel = 'Current [μA]'
# ylabel = 'Scatti [%]'
# title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

# grafici.creaGrafico(x, y, label, xlabel, ylabel, title)


