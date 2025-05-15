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
for i in np.arange(-0.25, -0.33, -0.0025):

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

current = np.array([
    -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100, -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
    -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450, -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
    -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
])

scatti = np.array([
    0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517,
    12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870,
    99.873, 99.874, 99.877, 99.876, 99.877
])

grafici.errorFunct(current, scatti, xlabel, ylabel, title)