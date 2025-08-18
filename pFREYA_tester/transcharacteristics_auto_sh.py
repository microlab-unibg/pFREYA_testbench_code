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

# Funzioni per determinare energia e peaking time dalla configurazione dei bit
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
        return 330 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 420 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 240 
    else:
        raise ValueError("Configurazione shap_bits non valida")


pt = [240, 330, 420, 510]  # Tempi di picco per ciascun file (modifica come necessario)

# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    # Configurazione da 9 keV 
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    # [0, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns 
    # [0, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns   
    # [0, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 25 keV
    # [0, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [0, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [0, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [0, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 18 keV
    # [1, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [1, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [1, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [1, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 5 keV
    # [1, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [1, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [1, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [1, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
]

#dizionario utilizzato per salvare dati di ogni configurazione
dati = {
    'energy level [keV]': [],
    'Peaking time [ns]': [],
    'Offset [mV]': [],
    'Slope [mV/#$\\gamma$]': [],
    'INL [%]': [],
    'R$^2$': []
}
# Elenco dei livelli di energia (da associare ai rispettivi gruppi di configurazioni)
energy_levels = [9, 25, 18, 5]
groups = {9:[] ,25: [], 18: [], 5: []}

# Raggruppa i file TSV per energia
for item in config_bits_list:
    config.config(channel='shap', lemo='none', n_steps=20, cfg_bits=item, cfg_inst=True, active_probes=False)
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    pYtp.send_slow_ctrl_auto(item,2)
    pYtp.send_sync_time_bases()
    
    # 100 mV/div e -611mV
    config.lecroy.set_vdiv(channel=1,vdiv='500e-3')
    config.lecroy.set_vdiv(channel=2,vdiv='500e-3')
    config.lecroy.set_voffset(channel=1,voffset='-35e-3')
    config.lecroy.set_voffset(channel=2,voffset='-35e-3')
    config.lecroy.set_tdiv(tdiv='1US')
    config.lecroy.set_toffset(toffset='-1.46e-6')
    
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)


    # set proper time division for this analysis
    # suppress channel for noise stuff
    #config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    #config.lecroy.write(f'C2:CRS HREL')
    # reset inj
    tdiv = 1e-6
    div_s = .3052e-6/tdiv + 10/2 - 1.46e-6/tdiv
    div_e = 1.5246e-6/tdiv + 10/2 - 1.46e-6/tdiv
    config.lecroy.write(f'C1:CRST HDIF,{div_s},HREF,{div_e}')
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    N_samples = config.N_samples

    # Raccogli i dati
    mis = {
        'Current Level Step': [],
        'Current Level (A)': [], 
        'iinj_int (C)': [], 
        'Equivalent Photons': [], 
        'Voltage output average (V)': [],
        'Voltage output std (V)': [],
        'Voltage output average 2 (V)': [],
        'Voltage output std 2 (V)': [],
        'Voltage output average diff (V)': [],
        'Voltage output std diff (V)': []
          }
    
    for i, level in enumerate(config.current_lev):
        config.ps.write(f':SOUR:CURR:LEV {level}')
        print(f'{i} : {level}')
        time.sleep(2)
        mis['Current Level Step'].append(i)
        mis['Current Level (A)'].append(level)
        mis['iinj_int (C)'].append(config.iinj_int[i])
        mis['Equivalent Photons'].append(config.eq_ph[i])
        sample_p=[]
        sample_n=[]
        data=[]
        for _ in range(N_samples):
            sample_p.append(float(config.lecroy.query(f'C1:CRVA? HREL').split(',')[2]))
            sample_n.append(float(config.lecroy.query(f'C2:CRVA? HREL').split(',')[2]))
            data.append(sample_p[-1]-sample_n[-1])
            time.sleep(0.05)
        mis['Voltage output average (V)'].append(np.average(sample_p))
        mis['Voltage output std (V)'].append(np.std(sample_p))
        mis['Voltage output average 2 (V)'].append(np.average(sample_n))
        mis['Voltage output std 2 (V)'].append(np.std(sample_n))
        mis['Voltage output average diff (V)'].append(np.average(data))
        mis['Voltage output std diff (V)'].append(np.std(data))


    df = pd.DataFrame(mis)
    datetime_str = datetime.now().strftime('%Y%m%d%H%M')
    output_file = f'G:/Shared drives/FALCON/measures/new/transcharacteristics/sh/sh_{config.config_bits_str}_{datetime_str}.tsv'
    df.to_csv(output_file, sep='\t', index=False)
    print("File tsv salvato con successo.")
    