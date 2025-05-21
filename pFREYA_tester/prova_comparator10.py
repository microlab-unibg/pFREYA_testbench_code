import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
from datetime import datetime
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

def stima_p0(x, y):
    """
    Stima iniziale dei parametri [mu, sigma] per fit con error function.

    Parametri:
    - x: array di ascisse
    - y: array di ordinate (normalizzate tra 0 e 1)

    Ritorna:
    - p0: lista [mu, sigma]
    """

    # μ ~ punto dove y ≈ 0.5
    idx_mu = np.argmin(np.abs(y - 0.5))
    mu0 = x[idx_mu]

    # σ ~ (x_90 - x_10) / (2 * sqrt(2))
    try:
        x_10 = x[np.argmin(np.abs(y - 0.1))]
        x_90 = x[np.argmin(np.abs(y - 0.9))]
        sigma0 = (x_90 - x_10) / (2 * np.sqrt(2))
    except:
        # fallback se non riesce
        sigma0 = 0.02 * np.ptp(x)

    return [mu0, sigma0]


def errorFunct(x, y, xLabel, yLabel, title, timestamp_str):

    # Definizione della funzione error function
    def erf_fit(x, mu, sigma):
        return 0.5 * (1 + erf((x - mu) / (sigma * np.sqrt(2))))

    # Fit dei dati
    p0 = stima_p0(x, y)
    # p0 = [np.mean(x), 0.02 * np.ptp(x)]   stima semplificata
    popt, _ = curve_fit(erf_fit, x, y, p0)

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

    plt.grid(False)
    plt.legend()

    # plt.savefig(f'G:/Shared drives/FALCON/measures/new/discriminationChain/{timestamp_str}_plot.pdf')
    plt.savefig(f'C:/Users/Paolo Lazzaroni/Desktop/prova/{timestamp_str}_plot.pdf')

    plt.show()


    return 0


def errorFunctSdev(x, y, yerr, xLabel, yLabel, title, timestamp_str):
    # definizione modello
    def erf_fit(x, mu, sigma):
        return 0.5*(1 + erf((x-mu)/(sigma*np.sqrt(2))))
    
    # FIT pesato
    popt, pcov = curve_fit(
        erf_fit, x, y,
        sigma=yerr,
        absolute_sigma=True,
        p0=stima_p0(x, y)
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

    plt.grid(False)
    plt.legend()
    
    # plt.savefig(f'G:/Shared drives/FALCON/measures/new/discriminationChain/{timestamp_str}_plot.pdf')
    plt.savefig(f'C:/Users/Paolo Lazzaroni/Desktop/prova/{timestamp_str}_plot.pdf')

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
        # k = k - 0.001
        if tempMean < 713:
            k = k - 0.0005
        else:
            k = k - 0.01
            cont = cont + 1
            if cont >= 5:
                break

    

current = np.array(current_level)
current = current * (-1)

"""
x ph @ 9 KeV: 256[ph] / (1.64-0.13)[uA] * 2500 [e-/ph]                 -> [uA*e-] (da fare /1000 per ke-)
quindi fattore di conversione FC = 256 / (1.64-0.13) * 2500 / 1000     -> [Ke-/uA]
quindi FC[Ke-/uA] * current[uA]                                        -> [Ke-]
"""
FC = 256 / (1.64-0.13) * 2500 / 1000 # 423.84105960264907
charge = FC*current

avg = np.array(avg_lecroy, dtype=float)
percScatti = np.array(avg / 715, dtype=float)

sdev = np.array(sdev_lecroy, dtype=float)
max = np.array(max_lecroy, dtype=float)
min = np.array(min_lecroy, dtype=float)


results = {
    'Current level' : [],
    'Charge' : [],
    'Mean': [],
    '% SOT' : [],
    'Sdev' : [],
    'Max #SOT': [],
    'Min #SOT': []
}
results['Current level'] = current
results['Charge'] = charge
results['Mean'] = avg
results['% SOT'] = percScatti
results['Sdev'] = sdev
results['Max #SOT'] = max
results['Min #SOT'] = min

timestamp = datetime.now()
timestampStr = timestamp.strftime("%Y-%m-%d_%H.%M")

data = pd.DataFrame(results)
# data.to_csv(f"G:/Shared drives/FALCON/measures/new/discriminationChain/{timestampStr}_results.tsv",sep='\t', index=False)
# data.to_csv(f"G:/Shared drives/FALCON/measures/new/discriminationChain/{timestampStr}_results.csv", sep=';', index=False)
data.to_csv(f'C:/Users/Paolo Lazzaroni/Desktop/prova/{timestampStr}_results.csv', sep=';', index=False)


x = current
y = percScatti
xlabel = 'Current [μA]'
ylabel = 'Hit probability'
thrgenRef = 280
Vthrp = 601
Vthrn = 599
title = f'S Curve (Thrgen_ref={thrgenRef}, Vthrp = {Vthrp}, Vthrn = {Vthrn})'

errorFunct(x, y, xlabel, ylabel, title, timestampStr+"_current")
errorFunct(charge, y, "Charge [Ke-]", ylabel, title, timestampStr+"_charge")
# errorFunctSdev(x, y, sdev, xlabel, ylabel, title, timestampStr)