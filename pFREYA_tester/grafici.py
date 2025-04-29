import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
from scipy.optimize import curve_fit
from scipy.special import erf



def sin():
    x = np.linspace(0, 2*np.pi, 200)
    #linspace crea un array dandogli inizio, fine e granularità dei valori. Tra 0 e 2*np.pi ci devono essere 200 valori
    y = np.sin(x)

    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.show()

def fun():
    x = np.linspace(-100, 100, 2020)
    y = x*x

    fig, ax = plt.subplots()
    ax.plot(x, y)
    plt.show()

def dots():
    np.random.seed(19680802)  # seed the random number generator.
    data = {'a': np.arange(1, 50), #crea un array che va da 1 a 50
            'c': np.random.randint(0, 50, 50),
            'd': np.random.randn(50)}
    data['b'] = data['a'] + 10 * np.random.randn(50)
    data['d'] = np.abs(data['d']) * 100

    fig, ax = plt.subplots(figsize=(5, 2.7), layout='constrained')
    ax.scatter('a', 'b', c='c', s='d', data=data)
    ax.set_xlabel('entry a')
    ax.set_ylabel('entry b')

    plt.show()


def dati():
    x258 = np.array([
        600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619,
        620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639,
        640, 641, 642, 643, 645, 648, 651, 654, 657, 661, 664, 666, 668, 670, 672, 675, 678, 681, 684, 687,
        690, 693, 696, 700, 703, 706, 710, 714, 718, 722, 726, 730, 734, 738, 742, 746, 750, 756, 760, 764,
        765
    ])
    y258 = np.array([
        0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.54, 0.56, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.67, 0.69, 0.69, 0.71, 0.72,
        0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.77, 0.78, 0.82, 0.83, 0.85, 0.86, 0.87, 0.88, 0.90, 0.91, 0.92, 0.93,
        0.94, 0.96, 0.98, 0.99, 1.02, 1.06, 1.10, 1.15, 1.20, 1.27, 1.32, 1.37, 1.41, 1.47, 1.53, 1.62, 1.73, 1.86, 1.89, 1.92,
        1.94, 1.96, 2.00, 2.04, 2.07, 2.10, 2.17, 2.22, 2.29, 2.36, 2.42, 2.50, 2.57, 2.64, 2.75, 2.89, 3.04, 3.40, 3.78, 4.42,
        4.64
    ])

    x327 = np.array([
        600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 612, 614, 616, 618, 620, 622, 624, 626, 628,
        630, 632, 635, 638, 641
    ])
    y327 = np.array([
        0.37, 0.36, 0.36, 0.36, 0.35, 0.35, 0.35, 0.34, 0.34, 0.34, 0.33, 0.33, 0.32, 0.31, 0.31, 0.30, 0.29, 0.28, 0.28, 0.27,
        0.26, 0.25, 0.24, 0.23, 0.20
    ])

    x307 = np.array([
        600, 602, 604, 606, 608, 610, 612, 614, 616, 618
    ])
    y307 = np.array([
        0.27, 0.26, 0.25, 0.24, 0.24, 0.23, 0.22, 0.21, 0.20, 0.19
    ])

    negativo(y258)
    negativo(y327)
    negativo(y307)

    return [x258, y258, x327, y327, x307, y307]

def negativo(w):
    for i in range(len(w)):
        w[i] = -w[i]


def simpleGraph():
    app = dati()
    x258 = app[0]
    y258 = app[1]
    x327 = app[2]
    y327 = app[3]
    x307 = app[4]
    y307 = app[5]

    x = [x258, x327, x307]

    y = [y258, y327, y307]

    label = ['Threfgen 258mV', 'Threfgen 327mV', 'Threfgen 307mV']
    xlabel = 'Vthrp [mV]'
    ylabel = 'Current [μA]'
    title = 'Max current level SOT=0 always'

    creaGrafico(x, y, label, xlabel, ylabel, title)

def creaGrafico(x, y, label, xLabel, yLabel, title):

    fig, ax = plt.subplots()  # Create a figure containing a single Axes.

    for i in range(len(x)):
        if label != 'null':
            ax.plot(x[i], y[i], label=label[i]) # Plot some data on the Axes.
        else:
            ax.plot(x[i], y[i])

    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    ax.set_title(title)

    if label != 'null':
        plt.legend()      #mostra le label

    plt.show()  # Show the figure.


    return 0


def thrgen_ref():
    thrgenRef = np.array([
        258, 260, 262, 264, 266, 268, 270, 272, 274, 276,
        278, 280, 282, 284, 285, 286, 287, 288, 289, 290,
        292, 294, 296, 298, 300, 302, 304, 306, 308, 310,
        312, 314, 316, 318, 320, 322, 324, 326, 328, 330,
        332, 334, 336, 338, 340
    ])

    current = np.array([
        0.56, 0.54, 0.52, 0.49, 0.47, 0.45, 0.43, 0.40, 0.38, 0.36,
        0.33, 0.31, 0.28, 0.26, 0.25, 0.03, 0.00, 0.00, 0.00, 0.00,
        0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.28, 0.30, 0.30, 0.31,
        0.32, 0.33, 0.34, 0.35, 0.35, 0.36, 0.37, 0.37, 0.38, 0.39,
        0.40, 0.41, 0.42, 0.42, 0.43
    ])

    x = [thrgenRef]
    y = [current]
    label = 'null'
    xlabel = 'Thrgen_ref [mV]'
    ylabel = 'Current [μA]'
    title = 'Max current level SOT=0 always (Vthrp=601, Vthrp=599)'

    creaGrafico(x, y, label, xlabel, ylabel, title)


def curva_s():

    current = np.array([
        -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100,
        -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
        -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450,
        -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
        -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
    ])

    negativo(current)

    mean = np.array([
        0, 0, 0, 0, 0, 0, 0, 0.002, 0.006, 0.029, 0.143, 0.86, 1.97, 5.35, 21.2, 46.6, 90.2, 148.5, 284.6, 384.7, 450.2, 546.3, 639.4, 685.5, 691, 705.5, 711.1, 713.3, 713.6, 714.07, 714.09, 714.1, 714.12, 714.11, 714.12
    ])

    scatti = np.array([
        0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517, 12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870, 99.873, 99.874, 99.877, 99.876, 99.877
    ])

    min_scatti = np.array([
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 7, 18, 19, 62, 104, 191, 286, 486, 620, 618, 676, 689, 705, 709, 712, 713, 714, 714, 714, 714
    ])

    max_scatti = np.array([
        0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 5, 10, 14, 34, 72, 296, 314, 480, 593, 637, 657, 680, 712, 713, 714, 714, 715, 715, 715, 715, 715, 715, 715, 715, 715
    ])

    x = [current]
    y = [scatti]
    label = 'null'
    xlabel = 'Current [μA]'
    ylabel = 'Scatti [%]'
    title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

    creaGrafico(x, y, label, xlabel, ylabel, title)


def errorFunction():
    current = np.array([
        -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100, -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
        -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450, -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
        -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
    ])
    negativo(current)

    scatti = np.array([
        0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517,
        12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870,
        99.873, 99.874, 99.877, 99.876, 99.877
    ])

    # Dati
    x = current
    y = scatti / 100  # normalizza le percentuali in [0,1]

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

    plt.xlabel('Current (μA)')
    plt.ylabel('Scatti (% normalizzata)')
    plt.title('Curva ad S con Error Function')

    plt.grid(True)
    plt.legend()
    plt.show()
    return 0


#sin()
#fun()
#dots()
#simpleGraph()
#thrgen_ref()
#curva_s()
# errorFunction()