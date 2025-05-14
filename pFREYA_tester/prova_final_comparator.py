import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
# from datetime import datetime
import time
# import glob
import config
from TeledyneLeCroyPy import TeledyneLeCroyPy
# import pFREYA_tester_processing as pYtp
# import pFREYA_tester as freya 
import sys
import json
import grafici


rm = None
ps = None
rm = pyvisa.ResourceManager()
ps = rm.open_resource('GPIB1::23::INSTR')
print(ps.query('*IDN?'))
crt = 0

ps.write(':OUTP:LOW FLO')
ps.write(':OUTP:OFF:AUTO ON')
ps.write(':OUTP:PROT ON')
ps.write(':OUTP:RES:MODE FIX')
ps.write(':OUTP:RES:SHUN DEF')
ps.write(':SOUR:FUNC:MODE CURR')
ps.write(':SOUR:CURR:MODE FIX')
ps.write(f':SOUR:CURR:LEV {crt}E-6')
ps.write(':DISP:ENAB OFF')
ps.write(':DISP:TEXT:DATA "pFREYA16"')
ps.write(':DISP:TEXT:STAT ON')
ps.write(':OUTP:STAT ON')


json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

with open(json_file, "r") as f:
    gui_data = json.load(f)

# current_level = gui_data["INJ"]["current_level"]
# print(f"Livello corrente: {current_level}")



data = []
current_level = []
avg_sot = []
# perc_sot = []
max_sot = []
min_sot = []

config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)

# for i in np.arange(-0.20, -0.35, -0.0025):
for i in np.arange(-0.20, -0.35, -0.01):
    ps.write(f':SOUR:CURR:LEV {i}E-6')
    #data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
    
    current_level.append(i)
    
    print("Current: " + str(i))
    config.lecroy.set_tdiv(tdiv='100us')
    time.sleep(1)
    config.lecroy.set_tdiv(tdiv='200us')
    time.sleep(1)

    #
    #
    #
    # LETTURA E SALVATAGGIO DATI DALL'OSCILLOSCOPIO 
    # avg_sot.append( istruzioneLetturaLecroy )
    # stessa cosa per max_sot e min_sot
    #
    #

    time.sleep(1)



dict = {
    'Current level' : [],
    'AVG SOT': [],
    '% SOT' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

dict['Current level'] = np.array(current_level)
dict['AVG SOT'] = np.array(avg_sot)
dict['% SOT'] = np.array(dict['AVG SOT'] / 715)
# dict['Max #SOT'] = np.array(max_sot)
# dict['Min #SOT'] = np.array(min_sot)


x = [dict['Current level']]
y = [dict['% SOT']]
label = 'null'
xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

grafici.errorFunct(x, y, label, xlabel, ylabel, title)














# USANDO IL CONFIG!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)

crt = 0
ps.write(f':SOUR:CURR:LEV {crt}E-6')


json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

with open(json_file, "r") as f:
    gui_data = json.load(f)

# current_level = gui_data["INJ"]["current_level"]
# print(f"Livello corrente: {current_level}")



data = []
current_level = []
avg_sot = []
# perc_sot = []
max_sot = []
min_sot = []


# for i in np.arange(-0.20, -0.35, -0.0025):
for i in np.arange(-0.20, -0.35, -0.01):
    config.ps.write(f':SOUR:CURR:LEV {i}E-6')
    #data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
    
    current_level.append(i)
    
    print("Current: " + str(i))
    config.lecroy.set_tdiv(tdiv='100us')
    time.sleep(1)
    config.lecroy.set_tdiv(tdiv='200us')
    time.sleep(1)

    #
    #
    #
    # LETTURA E SALVATAGGIO DATI DALL'OSCILLOSCOPIO 
    # avg_sot.append( istruzioneLetturaLecroy )
    # stessa cosa per max_sot e min_sot
    #
    #

    time.sleep(1)



dict = {
    'Current level' : [],
    'AVG SOT': [],
    '% SOT' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

dict['Current level'] = np.array(current_level)
dict['AVG SOT'] = np.array(avg_sot)
dict['% SOT'] = np.array(dict['AVG SOT'] / 715)
# dict['Max #SOT'] = np.array(max_sot)
# dict['Min #SOT'] = np.array(min_sot)


x = [dict['Current level']]
y = [dict['% SOT']]
label = 'null'
xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

grafici.errorFunct(x, y, label, xlabel, ylabel, title)
