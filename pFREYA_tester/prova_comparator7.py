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
from scipy.interpolate import make_interp_spline
from scipy.optimize import curve_fit
from scipy.special import erf

def errorFunct(x, y, xLabel, yLabel, title):

    # Definizione della funzione error function
    def erf_fit(x, mu, sigma):
        return 0.5 * (1 + erf((x - mu) / (sigma * np.sqrt(2))))

    # Fit dei dati
    popt, _ = curve_fit(erf_fit, x, y, p0=[0.35, 0.01])  # stima iniziale

    # Valori stimati
    mu_fit, sigma_fit = popt

    # Genera curva smooth per il plot
    x_smooth = np.linspace(np.min(x), np.max(x), 500)
    y_erf = erf_fit(x_smooth, mu_fit, sigma_fit)

    plt.plot(x, y, 'o', label='Dati originali')         #'o' mette solo i punti nel grafico, non crea la spezzata

    #{mu_fit:.4f} permette di mettere una var e di (.4f) specificarne il numero di decimali (5)
    plt.plot(x_smooth, y_erf, '-', label=f'Fit erf\nμ={mu_fit:.5f}, σ={sigma_fit:.5f}')

    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)

    plt.grid(True)
    plt.legend()
    plt.show()
    return 0


config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)

pid = "P5"
current_level = []
avg_lecroy = []
sdev_lecroy = []
max_lecroy = []
min_lecroy = []


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
    avg_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'"))
    sdev_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Sdev.Result.Value'"))    
    # max_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Max.Result.Value'"))
    # min_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Min.Result.Value'"))

    time.sleep(1)
    



results = {
    'Current level' : [],
    'Mean': [],
    '% SOT' : [],
    'Sdev' : [],
    'Max #SOT': [],
    'Min #SOT': []
}

current = np.array(current_level)
current = current * (-1)
avg = np.array(avg_lecroy, dtype=float)
percScatti = np.array(avg / 715, dtype=float)

# results['Current level'] = np.array(current_level)
# results['Mean'] = np.array(avg_sot, dtype=float)
# results['% SOT'] = np.array(results['Mean'] / 715, dtype=float)
# results['Sdev'] = np.array(avg_sot, dtype=float)
# results['Max #SOT'] = np.array(max_sot)
# results['Min #SOT'] = np.array(min_sot)

x = current
y = percScatti
label = 'null'
xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrn = 599)'

errorFunct(current, percScatti, xlabel, ylabel, title)