import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvisa
import matplotlib.colors as mcolors
from datetime import datetime
import time
import glob
import config
import pFREYA_tester_processing as pYtp
T = 30e-9 # s
t_r = 3e-9 # s
N_pulses = 10 # adimensional
conv_kev_c = 3.65/1000 * 1/1.602e-19 # Energy in silicon for e-/h * no of electrons per coulomb [keV/e-] * [e-/C]
def get_energy_level(cfg_bits):
    if cfg_bits[0] == 1 and cfg_bits[1] == 1:
        return 5  # 5 keV
    elif cfg_bits[0] == 1 and cfg_bits[1] == 0:
        return 9 # 9 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 1:
        return 18 # 18 keV
    elif cfg_bits[0] == 0 and cfg_bits[1] == 0:
        return 25 # 25 keV
    else:
        raise ValueError("Configurazione cfg_bits non valida")
    
# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    # Configurazione  da 9 keV a 25
    [0, 1, 0, 1, 0, 1, 1],  #shaper tp = 432 ns
    [0, 1, 0, 0, 0, 1, 1],  #shaper tp = 234 ns 
    [0, 1, 0, 0, 1, 1, 1],  #shaper tp = 332 ns   
    [0, 1, 0, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 25 keV
    [0, 0, 0, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [0, 0, 0, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [0, 0, 0, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [0, 0, 0, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 9 keV
    [1, 0, 0, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [1, 0, 0, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [1, 0, 0, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [1, 0, 0, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 5 keV
    [1, 1, 0, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [1, 1, 0, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [1, 1, 0, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [1, 1, 0, 1, 1, 1, 1],  #shaper tp = 535 ns  
]


#cfg_bits_template = [0, 1, 0, 0, 0, 1, 1]  lo utilizzo per definire un template base per poi iterare le diverse config di bits
# Creazione del DataFrame
for item in config_bits_list:
    
    import config
    config.config(channel='shap',lemo='none',n_steps=20,cfg_bits=item,cfg_inst=True, active_probes=False)
    pYtp.send_slow_ctrl_auto(item,1)
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    gain_shap = config.gain_shap
    N_samples = 500

    # set proper time division for this analysis
    #config.lecroy.write('TDIV 200NS')
    # suppress channel for noise stuff
    config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    # in future one must set vdiv, hdiv, ... TODO
    # current: tdiv = 200 ns/div,, delay = -908 ns
    ndiv = 10 # positive and negative around delay
    tdelay = -908 # ns
    tdiv = 200 # ns/div
    osc_ts = 329 # ns
    osc_te = osc_ts + config.peaking_time # TODO not ideal
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    if config.channel_name == 'shap':
        div_e = (osc_te - osc_offset)/tdiv
    else:
        div_e = (432 - osc_offset)/tdiv

    # no injection for noise (check withouth injection circuit TODO)
    # Set zero output
    config.ps.write(':OUTP1 ON')
    config.ps.write(':OUTP2 OFF')
    config.ps.write(':SOUR:CURR:LEV 0')
    #config.ps.write(':SOUR:CURR:LEV 0')
    #config.ps.write(':OUTP:STAT OFF')

    N_repetitions = 16
    background = False
    absolute = False
    if absolute:
        config.lecroy.write(f'C2:CRS HABS')
        config.lecroy.write(f'C2:CRST HABS,{div_e}')
    else:
        config.lecroy.write(f'C2:CRS HREL')
        config.lecroy.write(f'C2:CRST HDIF,{div_s},HREF,{div_e}')

    data = np.empty((N_samples, N_repetitions))
    for i in range(N_repetitions):
        # N sample to average and extract std from
        for j in range(N_samples):
            if absolute:
                data[j,i] = float(config.lecroy.query(f'C{config.channel_num}:CRVA? HABS').split(',')[2])
            else:
                data[j,i] = float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2])

    data = data*10**3
    noise_std      = np.mean(np.std(data,axis=0))
    noise_std_std  = np.std(np.std(data,axis=0))
    noise_rms      = np.mean(np.sqrt(np.mean(np.square(data),axis=0)))
    noise_rms_std  = np.std(np.sqrt(np.mean(np.square(data),axis=0)))
    enc_std        = np.sqrt(noise_std**2)/gain/gain_shap*9000/3.65
    enc_std_std    = noise_std_std/gain/gain_shap*9000/3.65
    enc_rms        = np.sqrt(noise_rms**2)/gain/gain_shap*9000/3.65
    enc_rms_std    = noise_rms_std/gain/gain_shap*9000/3.65

    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
    df = pd.DataFrame([[
        noise_std    ,
        noise_std_std,
        noise_rms    ,
        noise_rms_std,
        enc_std      ,
        enc_std_std  ,
        enc_rms      ,
        enc_rms_std  ,
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
    # cambia percorso
    df.to_csv(f'G:/Shared drives/PHD/FALCON/measures/new/enc/enc_{config.config_bits_str}_{datetime_str}_{lemo_name}_{'background_' if background else ''}{'absolute' if absolute else ''}.tsv', sep='\t')

np.std(data,axis=0)
colours = list(mcolors.TABLEAU_COLORS.keys())
fig, ax = plt.subplots(4,4)
fig.set_figheight(8)
fig.set_figwidth(8)
for i in range(16):
	if (i < N_repetitions):
		ax[i//4,i%4].hist(
			data[:,i],
			histtype='step', fill=False, bins=20)
	ax[i//4,i%4].tick_params(right=True, top=True, direction='in')
fig.text(0.5, 0.04, 'Shaper output voltage [mV]', ha='center')
fig.text(0.04, 0.5, 'Number of occurrencies', va='center', rotation='vertical')

fig.savefig(f'G:/Shared drives/PHD/FALCON/measures/new/enc/distributions_{config.config_bits_str}_{datetime_str}_{lemo_name}{'_background' if background else ''}{'_absolute' if absolute else ''}.pdf',dpi=300)