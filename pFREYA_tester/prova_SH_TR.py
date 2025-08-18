import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvisa
import matplotlib.colors as mcolors
from datetime import datetime
import time
import glob
import config
import os
import pFREYA_tester_processing as pYtp
from scipy.stats import linregress

def get_energy_level(cfg_bits):
    if cfg_bits[0] == 1 and cfg_bits[1] == 1:
        return 5  # 5 keV
    elif cfg_bits[0] == 1 and cfg_bits[1] == 0:
        return 18  # 18 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 1:
        return 9 # 9 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 0:
        return 25 # 25 keV
    else:
        raise ValueError("Configurazione cfg_bits non valida")

def get_shap_bits(cfg_bits):
    if cfg_bits[3] == 1 and cfg_bits[4] == 1:
        return 510  
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 420 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 330 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 240 
    else:
        raise ValueError("Configurazione shap_bits non valida")

def print_differential(path_low, path_high, shap_bits, datetime_str, config_bits_str, lemo_name, channel_name):
    #Stampa il differenziale dei segnali
    df_low = pd.read_csv(path_low, sep='\t')
    df_high = pd.read_csv(path_high, sep='\t')

    colours = list(mcolors.TABLEAU_COLORS.keys())
    fig, ax = plt.subplots(figsize=(7, 5))
    #finire dopo la logica

config_bits_list = [
    # Configurazione da 9 keV
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    #da espandere alle altre configurazioni una volta accertato che il cod funzioni
]

peak = [240, 330, 420, 510]
energy_level  = [ 9, 18, 25, 5]
group = {9:[] ,25: [], 18: [], 5: []}

data = {
    'energy level [keV]': [],
    'Peaking time [ns]': [],
    'Offset [mV]': [],
    'Slope [mV/#$\\gamma$]': [],
    'INL [%]': [],
    'R$^2$': []
}


for item in config_bits_list:

    config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=item,cfg_inst=True, active_probes=False)

    config.lecroy.set_vdiv(channel=1,vdiv='230e-3')
    config.lecroy.set_voffset(channel=1,voffset='690e-3')
    config.lecroy.set_tdiv(tdiv='100NS')
    config.lecroy.set_toffset(toffset='-240e-9')
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)

    config.config(channel='shap', lemo='none', n_steps=20, cfg_bits=item, cfg_inst=True, active_probes=False)
    
    config.lecroy.set_vdiv(channel=2,vdiv='305e-3')
    config.lecroy.set_voffset(channel=2,voffset='-415e-3')
    config.lecroy.set_tdiv(tdiv='200NS')
    config.lecroy.set_toffset(toffset='-820e-9')
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)



    energy = get_energy_level(item)
    shap_bits = get_shap_bits(item)


