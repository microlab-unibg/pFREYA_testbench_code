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


def errorFunctSdev(x, y, yerr, xLabel, yLabel, title):
    # definizione modello
    def erf_fit(x, mu, sigma):
        return 0.5*(1 + erf((x-mu)/(sigma*np.sqrt(2))))
    
    # FIT pesato
    popt, pcov = curve_fit(
        erf_fit, x, y,
        sigma=yerr,
        absolute_sigma=True,
        p0=[0.35, 0.01]
    )
    mu_fit, sigma_fit = popt
    perr = np.sqrt(np.diag(pcov))   # incertezze su mu, sigma

    # preparazione curva “liscia”
    x_smooth = np.linspace(x.min(), x.max(), 500)
    y_erf    = erf_fit(x_smooth, mu_fit, sigma_fit)

    # plot dati + barre d’errore
    plt.errorbar(x, y, yerr=yerr, fmt='o', label='Dati (±σ)')
    plt.plot(x_smooth, y_erf, '-', 
             label=f'Fit erf\nμ={mu_fit:.5f}±{perr[0]:.5f}, σ={sigma_fit:.5f}±{perr[1]:.5f}')
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.show()

    # opzionale: calcolo del χ² ridotto
    y_fit_at_x = erf_fit(x, mu_fit, sigma_fit)
    chi2 = np.sum(((y - y_fit_at_x)/yerr)**2)
    dof  = len(x) - len(popt)
    print(f"χ²/dof = {chi2:.1f}/{dof} = {chi2/dof:.2f}")
    
    return popt, perr



config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)

pid = "P5"
current_level = []
avg_lecroy = []
sdev_lecroy = []
max_lecroy = []
min_lecroy = []


# for i in np.arange(-0.20, -0.35, -0.0025):
# for i in np.arange(-0.23, -0.34, -0.0025):

#     config.ps.write(f':SOUR:CURR:LEV {i}E-6')

#     print("Current: " + str(i))
#     time.sleep(1)
    
#     current_level.append(i)
    
#     config.lecroy.set_tdiv(tdiv='100us')
#     time.sleep(1)
#     config.lecroy.set_tdiv(tdiv='200us')
#     time.sleep(3)

#     # LETTURA E SALVATAGGIO DATI DALL'OSCILLOSCOPIO 
#     avg_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'"))
#     sdev_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Sdev.Result.Value'"))    
#     max_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Max.Result.Value'"))
#     min_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Min.Result.Value'"))

#     time.sleep(1)

k = -0.23
cont = 0
tempMean = 0
tempSdev = 0
while True:
    config.ps.write(f':SOUR:CURR:LEV {k}E-6')

    print("Current: " + str(k))
    time.sleep(1)
    
    current_level.append(k)
    
    config.lecroy.set_tdiv(tdiv='100us')
    time.sleep(1)
    config.lecroy.set_tdiv(tdiv='200us')
    time.sleep(3)

    # LETTURA E SALVATAGGIO DATI DALL'OSCILLOSCOPIO 
    avg_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'"))
    sdev_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Sdev.Result.Value'"))    
    max_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Max.Result.Value'"))
    min_lecroy.append(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Min.Result.Value'"))

    time.sleep(1)
    tempMean = (float)(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'"))
    tempSdev = (float)(config.lecroy.query(f"VBS? 'return=app.Measure.{pid}.Sdev.Result.Value'"))
    if tempMean < 0.01 and tempSdev < 0.01:
        k = k - 0.01
    else:
        k = k - 0.001
    
    if tempMean > 713:
        cont = cont + 1
        if cont >= 5:
            break

    

current = np.array(current_level)
current = current * (-1)

avg = np.array(avg_lecroy, dtype=float)
percScatti = np.array(avg / 715, dtype=float)

sdev = np.array(sdev_lecroy, dtype=float)
max = np.array(max_lecroy, dtype=float)
min = np.array(min_lecroy, dtype=float)


# results = {
#     'Current level' : [],
#     'Mean': [],
#     '% SOT' : [],
#     'Sdev' : [],
#     'Max #SOT': [],
#     'Min #SOT': []
# }
# results['Current level'] = current
# results['Mean'] = avg
# results['% SOT'] = percScatti
# results['Sdev'] = sdev
# results['Max #SOT'] = max
# results['Min #SOT'] = min

x = current
y = percScatti
xlabel = 'Current [μA]'
ylabel = 'Hit probability'

thrgenRef = 280
Vthrp = 601
Vthrn = 599
title = f'S Curve (Thrgen_ref={thrgenRef}, Vthrp = {Vthrp}, Vthrn = {Vthrn})'

errorFunct(current, percScatti, xlabel, ylabel, title)
# errorFunctSdev(current, percScatti, sdev, xlabel, ylabel, title)