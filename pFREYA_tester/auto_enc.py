import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
from datetime import datetime
import matplotlib.colors as mcolors
import pFREYA_tester_processing as pYtp

import config
gain = []
'''
specifico percorso alla cartella a cui devo accedere
ordino la cartella in maniera tale che il file più recente sia il primo 
accedo al file .tsv piu recente
'''
config_bits_list = [
    # Configurazione da 18 keV
    [1, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns
    [1, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns
    [1, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    [1, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns
    # Configurazione 25 keV
    [0, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns
    [0, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns
    [0, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    [0, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns
    # Configurazione 9 keV
    [0, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns
    [0, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    [0, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns
    # Configurazione 5 keV
    [1, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns
    [1, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns
    [1, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    [1, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns
]
'''
vado a leggere l'ultimo file salvato sulla cartella drive in maniera tale da prelevare i guadagni di una determinata 
configurazione del csa sulle 4 configurazioni[ns] dello shaper
'''
def select_configurations(file_name, config_bits_list):
    energy_level = file_name.split('_')[1]  
    energy_to_config_map = {
        '5': config_bits_list[12:16],  # Configurazioni per 5 keV (indice 12-15)
        '9': config_bits_list[8:12],   # Configurazioni per 9 keV (indice 8-11)
        '25': config_bits_list[4:8],   # Configurazioni per 25 keV (indice 4-7)
        '18': config_bits_list[0:4]    # Configurazioni per 18 keV (indice 0-3)
    }
    selected_configs = energy_to_config_map.get(energy_level, [])
    return selected_configs

def keV(bits):
    if bits[0] == 1 and bits[1] == 1:
        return 5000  # 5 keV
    elif bits[0] == 1 and bits[1] == 0:
        return 18000  # 18 keV
    elif bits[0] == 0 and bits[1] == 1:
        return 9000 # 9 keV
    elif bits[0] == 0 and bits[1] == 0:
        return 25000 # 25 keV

# Percorso alla cartella contenente i file(primo:mio pc, secondo: lab)
#folder = f'G:Drive condivisi/FALCON/measures/new/transcharacteristics/shap/summary'
folder = f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/summary'


tsv_files = [f for f in os.listdir(folder) if f.endswith('.tsv')]
if tsv_files:
    tsv_files = sorted(
        (os.path.join(folder, f) for f in tsv_files),
        key=os.path.getmtime,
        reverse=True
    )

    latest_file = tsv_files[3]
    print(f"L'ultimo file .tsv salvato è: {latest_file}")

    df = pd.read_csv(latest_file, sep='\t')  
    print(f"\nFile TSV letto:\n{df}")

    if 'Gain [mV/#$\gamma$]' in df.columns:
        for i in range(4):
            gain.append(float(df['Gain [mV/#$\gamma$]'][i]))  
        print(f"\nguadagni prelevati:\n{gain}\n")
        selected_configs = select_configurations(latest_file, config_bits_list)
        print(f"\nConfigurazioni selezionate:\n{selected_configs}")

for gain_item, cfg_item in zip(gain, selected_configs):

    config.config(channel='shap', lemo='none', n_steps=20, cfg_bits=cfg_item, cfg_inst=True, active_probes=False)
    pYtp.send_slow_ctrl_auto(cfg_item, 1)
    

    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain_shap = gain_item
    N_samples = 500

    # 2 mV/div e -351.8mV
    config.lecroy.set_vdiv(channel=1,vdiv='2e-3')
    config.lecroy.set_voffset(channel=1,voffset='-351e-3')
    ndiv = 10
    tdelay = -908  # ns
    tdiv = 200  # ns/div
    osc_ts = 329  # ns
    osc_te = osc_ts + config.peaking_time  
    osc_offset = - ndiv / 2 * tdiv - tdelay
    div_s = (osc_ts - osc_offset) / tdiv
    if config.channel_name == 'shap':
        div_e = (osc_te - osc_offset) / tdiv
    else:
        div_e = (432 - osc_offset) / tdiv


    config.ps.write(':SOUR:CURR:LEV 0')
    config.ps.write(':OUTP:STAT OFF')

    N_repetitions = 16

    config.lecroy.write(f'C2:CRS HREL')
    config.lecroy.write(f'C2:CRST HDIF,{div_s},HREF,{div_e}')

    data = np.empty((N_samples, N_repetitions))
    for i in range(N_repetitions):
        for j in range(N_samples):
            data[j, i] = float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2])

    data = data * 10 ** 3  

    noise_std = np.mean(np.std(data, axis=0))
    noise_std_std = np.std(np.std(data, axis=0))
    noise_rms = np.mean(np.sqrt(np.mean(np.square(data), axis=0)))
    noise_rms_std = np.std(np.sqrt(np.mean(np.square(data), axis=0)))
    
    enc_std = np.sqrt(noise_std ** 2) / gain_shap * keV(cfg_item) / 3.65
    enc_std_std = noise_std_std / gain_shap * keV(cfg_item) / 3.65
    enc_rms = np.sqrt(noise_rms ** 2) / gain_shap * keV(cfg_item) / 3.65
    enc_rms_std = noise_rms_std / gain_shap * keV(cfg_item) / 3.65

    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
    df = pd.DataFrame([[
        noise_std,
        noise_std_std,
        noise_rms,
        noise_rms_std,
        enc_std,
        enc_std_std,
        enc_rms,
        enc_rms_std,
    ]], columns=[
        'noise std (mV)',
        'noise std std (mV)',
        'noise rms (mV)',
        'noise rms std (mV)',
        'ENC std (e-)',
        'ENC std std (e-)',
        'ENC rms (e-)',
        'ENC std std (e-)',
    ])
    #salvataggio e plot
    df.to_csv(f'G:Shared drives/FALCON/measures/new/enc/enc_{config.config_bits_str}_{datetime_str}_{lemo_name}.tsv', sep='\t')
    print(f"\nfile tsv enc per {cfg_item} salvato\n")
    colours = list(mcolors.TABLEAU_COLORS.keys())
    fig, ax = plt.subplots(4, 4)
    fig.set_figheight(8)
    fig.set_figwidth(8)
    for i in range(16):
        if i < N_repetitions:
            ax[i // 4, i % 4].hist(data[:, i], histtype='step', fill=False, bins=20)
        ax[i // 4, i % 4].tick_params(right=True, top=True, direction='in')
    
    fig.text(0.5, 0.04, 'Shaper output voltage [mV]', ha='center')
    fig.text(0.04, 0.5, 'Number of occurrences', va='center', rotation='vertical')

    fig.savefig(f'G:Shared drives/FALCON/measures/new/enc/distributions_{config.config_bits_str}_{datetime_str}_{lemo_name}.pdf', dpi=300)
    print(f"\nfile pdf distributions per {cfg_item} salvato\n")

