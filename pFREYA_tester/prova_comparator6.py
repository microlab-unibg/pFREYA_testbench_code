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

def list_active_measures7(lecroy):
    pid = "P5"

    #   PROVARE LE ISTRUZIONI SIA IN MINUSCOLO CHE CON LE INIZIALI MAIUSCOLE

    # lecroy.write(r"""vbs 'app.measure.showmeasure = true ' """)
    # lecroy.write(r"""vbs 'app.measure.statson = true ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.view = true ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.paramengine = "<value>" ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.source1 = "C1" ' """)

    # lecroy.write("VBS 'app.Measure.ShowMeasure = true'")
    # lecroy.write("VBS 'app.Measure.StatsOn = true'")
    # lecroy.write("VBS 'app.Measure.P1.View = true'")

    mean  = lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'")
    mean2 = lecroy.query(f"VBS? 'return=app.Measure.{pid}.Statistics(\"mean\").Result.Value'")
    print(mean)
    print(mean2)


config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)


# list_active_measures7(config.lecroy)

pid = "P5"
data = []
current_level = []
avg_sot = []
sdev_sot = []
max_sot = []
min_sot = []


# for i in np.arange(-0.20, -0.35, -0.0025):
for i in np.arange(-0.25, -0.33, -0.01):

    config.ps.write(f':SOUR:CURR:LEV {i}E-6')
    print("Current: " + str(i))
    time.sleep(1)

    #data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)
    
    current_level.append(i)
    
    config.lecroy.set_tdiv(tdiv='100us')
    time.sleep(1)
    config.lecroy.set_tdiv(tdiv='200us')
    time.sleep(3)

    #
    #
    #
    # LETTURA E SALVATAGGIO DATI DALL'OSCILLOSCOPIO 
    # avg_sot.append( istruzioneLetturaLecroy )
    # stessa cosa per max_sot e min_sot
    #
    #
    avg_sot.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'"))
    sdev_sot.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Sdev.Result.Value'"))    
    # max_sot.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Max.Result.Value'"))
    # min_sot.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Min.Result.Value'"))

    time.sleep(1)



results = {
    'Current level' : [],
    'Mean': [],
    '% SOT' : [],
    'Sdev' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

results['Current level'] = np.array(current_level*(-1))
results['Mean'] = np.array(avg_sot, dtype=float)
results['% SOT'] = np.array(results['Mean'] / 715, dtype=float)
results['Sdev'] = np.array(avg_sot, dtype=float)
# results['Max #SOT'] = np.array(max_sot)
# results['Min #SOT'] = np.array(min_sot)

# print(results['Mean'])
# print(results['% SOT'])

x = results['Current level']
y = results['% SOT']
label = 'null'
xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

grafici.errorFunct(x, y, xlabel, ylabel, title)