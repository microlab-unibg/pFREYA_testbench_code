import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import make_interp_spline
from scipy.optimize import curve_fit
from scipy.special import erf
from datetime import datetime

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

    plt.grid(False)
    plt.legend()
    plt.savefig("C:/Users/ITMACUR3/Downloads/aaaa/fig.pdf")
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
    plt.grid(False)
    plt.legend()
    plt.savefig("C:/Users/ITMACUR3/Downloads/aaaa/fig.pdf")
    plt.show()

    # opzionale: calcolo del χ² ridotto
    y_fit_at_x = erf_fit(x, mu_fit, sigma_fit)
    chi2 = np.sum(((y - y_fit_at_x)/yerr)**2)
    dof  = len(x) - len(popt)
    print(f"χ²/dof = {chi2:.1f}/{dof} = {chi2/dof:.2f}")
    
    return popt, perr


current = np.array([
    -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100, -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
    -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450, -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
    -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
])
current = current * (-1)


scatti = np.array([
    0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517,
    12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870,
    99.873, 99.874, 99.877, 99.876, 99.877
])
scatti = scatti / 100


sdev = np.array([
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.011826188788394225, 0.023529411764705882, 0.052729417452377174,
    0.4096289565190565, 0.6105166113934668, 0.9030813118356668, 1.8714326733912776, 2.935005590868147, 3.465979872407771,
    4.801822219357332, 6.146288497684594, 6.435729585183396, 6.420465304166904, 5.1718472300020215, 3.214503997302682,
    1.345318455217989, 0.9513193795992587, 0.6702594114047627, 0.5241582072001558, 0.35005401481710163, 0.3402797744874216,
    0.1310787464169484, 0.13160984935616013, 0.1310787464169484, 0.1310087464169484, 0.13100084935616013, 0.1310000464169484
])
sdev = sdev / 100

xlabel = 'Current [μA]'
ylabel = 'Scatti [%]'
title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrn = 599)'

results = {
    'Current level' : [],
    '% SOT' : [],
    'Sdev' : []
}
results['Current level'] = current
results['% SOT'] = scatti
results['Sdev'] = sdev

# data = pd.DataFrame(results)
# # data.to_csv("C:/Users/ITMACUR3/Downloads/aaaa/risultati.tsv",sep='\t', index=False)
# # data.to_csv("C:/Users/ITMACUR3/Downloads/aaaa/risultati.csv", sep=',', index=False)
# data.to_csv("C:/Users/ITMACUR3/Downloads/aaaa/risultati.csv", sep=';', index=False)

timestamp = datetime.now()
timestamp_str = timestamp.strftime("%Y-%m-%d_%H:%M")

print("Data e ora:", timestamp_str)

# errorFunct(current, scatti, xlabel, ylabel, title)
# errorFunctSdev(current, scatti, sdev, xlabel, ylabel, title)