import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
# from datetime import datetime
import time
# import glob
import config
# import pFREYA_tester_processing as pYtp
# import pFREYA_tester as freya 
import sys
import json
import grafici



rm = pyvisa.ResourceManager()
ps = rm.open_resource('GPIB1::23::INSTR')
print(ps.query('*IDN?'))


#MAIN
json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

with open(json_file, "r") as f:
    gui_data = json.load(f)


config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)


dict = {
    'Current level' : [],
    'AVG SOT': [],
    '% SOT' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

data = []
data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
# dict['Current level'].append(i)

# config.lecroy.set_tdiv(tdiv='100us')
# time.sleep(1)
# config.lecroy.set_tdiv(tdiv='200us')
# time.sleep(1)

# considerando che in un altra parte del codice per leggere dall'oscilloscopio ho questa funzione config.lecroy.query('C1:CRVA? HREL'), quindi questa istruzione config.lecroy.query("VBS? 'app.Measure.P5.value'") dovrebbe essere giusta?

while(True):
    time.sleep(0.7)
    val = config.lecroy.query("VBS? 'app.Measure.P5.Value'")
    time.sleep(0.3)
    print(str(val))








# x = [dict['Current level']]
# y = [dict['% SOT']]
# label = 'null'
# xlabel = 'Current [μA]'
# ylabel = 'Scatti [%]'
# title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

# grafici.creaGrafico(x, y, label, xlabel, ylabel, title)


