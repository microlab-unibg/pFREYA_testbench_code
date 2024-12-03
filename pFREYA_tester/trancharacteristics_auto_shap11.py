
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

def get_shap_bits(cfg_bits):
    if cfg_bits[3] == 1 and cfg_bits[4] == 1:
        return 535  
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 432 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 332 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 234 
    else:
        raise ValueError("Configurazione cfg_bits non valida")
    
# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    # Configurazione da 9 a 25 keV 
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    [0, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns 
    [0, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns   
    [0, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 25 keV
    [0, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [0, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [0, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [0, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 9 keV
    [1, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [1, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [1, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [1, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # Configurazione 5 keV
    [1, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    [1, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    [1, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    [1, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
]


tsv_files = []

#cfg_bits_template = [0, 1, 0, 0, 0, 1, 1]  lo utilizzo per definire un template base per poi iterare le diverse config di bits
# Creazione del DataFrame
for item in config_bits_list:
    
    import config
    config.config(channel='shap',lemo='none',n_steps=20,cfg_bits=item,cfg_inst=True, active_probes=False)
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    config.ps.write(':SOUR:CURR:LEV -.0e-6')
    pYtp.send_slow_ctrl_auto(item,1)


    # set proper time division for this analysis
    # suppress channel for noise stuff
    #config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    #config.lecroy.write(f'C2:CRS HREL')
    # reset inj
    time.sleep(2)
    ndiv = 10 # positive and negative around delay
    tdelay = -400 # ns
    tdiv = 200 # ns/div
    osc_ts = 298 # ns
    osc_te = 550 
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    div_e = (osc_te - osc_offset)/tdiv
    config.lecroy.write(f'C1:CRST HDIF,{div_s},HREF,{div_e}')
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    N_samples = config.N_samples
    mis = {
        #'CSA Bits': [],
        'Current Level Step': [],
        'Current Level (A)': [],
        'iinj_int (C)': [],
        'Equivalent Photons': [],
        'Voltage output average (V)': [],
        'Voltage output std (V)': []
    }

    for i, level in enumerate(config.current_lev):
        config.ps.write(f':SOUR:CURR:LEV {level}')
        #mis['CSA Bits'].append(config)
        mis['Current Level Step'].append(i)
        mis['Current Level (A)'].append(level)
        mis['iinj_int (C)'].append(config.iinj_int[i])
        mis['Equivalent Photons'].append(config.eq_ph[i])      
        data = []
        for _ in range(N_samples):
            #test funzionamento
            #random_voltage = np.random.normal(loc=0.5, scale=0.05)  # media=0.5V e deviazione standard=0.05V
            #data.append(random_voltage)
            data.append(float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2]))
            time.sleep(0.03)
        
        # Calcola la media e la deviazione standard e memorizza nel DataFrame i diversi valori di tensione
        mis['Voltage output average (V)'].append(np.average(data)/gain)
        mis['Voltage output std (V)'].append(np.std(data) / gain)
    df = pd.DataFrame(mis)
    datetime_str = datetime.now().strftime('%Y%m%d%H%M')

    # Sostituire percorso del drive e salvare il file
    df.to_csv(f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv', sep='\t', index=False)
    tsv_files.append(f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv')
    print("File tsv salvato con successo.")

    # Controlla la lunghezza dei dati
    photon_span = np.linspace(0, 256, 20)

    # Genera il grafico
    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(5)

    ax.errorbar(photon_span, df['Voltage output average (V)'],
                xerr=np.tile(1, df.shape[0]), yerr=df['Voltage output std (V)'],
                fmt='s', markersize=1, capsize=3)
    ax.set_xlabel('Equivalent input photons [#]')
    ax.set_ylabel(f'{channel_name.upper()} output voltage [V]')
    ax.tick_params(right=True, top=True, direction='in')
    from scipy.stats import linregress
    ln = linregress(photon_span, df['Voltage output average (V)'].astype(float))
    linear_output = ln.intercept + ln.slope * np.linspace(0, 256, 20)
    ax.plot(photon_span, linear_output)
    max_diff = np.max(df['Voltage output average (V)'] - linear_output)
    inl = 100 * np.abs(max_diff) / ln.slope / 256
    print(ln)

    # Aggiungi tabella informativa
    ax.table(cellText=[
        ['$\\gamma$ energy [keV]', f'{config.photon_energy}'],  # Sostituisci N/A con {config.photon_energy}
        ['Peaking time [ns]', f'{config.peaking_time}'],  # sostituisci 318 con {config.peaking_time}
        ['Slope [mV/#$\\gamma$]', f'{np.round(ln.slope*10**3,3)}'],
        ['INL [%]', f'{np.round(inl, 2)}'],
        ['R$^2$', f'{np.round(ln.rvalue**2, 3)}']
    ], colWidths=[.33, .2], loc='lower right')

    # Salva il grafico
    try:
        output_file = f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf'
        plt.savefig(output_file, dpi=300)
        plt.close(fig)  # Chiude il grafico corrente per liberare risorse
        print(f"File plot salvato con successo: {output_file}")
    except Exception as e:
        print(f"Errore durante il salvataggio del file plot: {e}")

#ordino i file per tempo di salvataggio e li divido in 4 gruppi (diverse config di Kev)
tsv_files_sorted = sorted(tsv_files, key=os.path.getctime)
groups = [tsv_files_sorted[i:i + 4] for i in range(0, len(tsv_files_sorted), 4)]
colours = list(mcolors.TABLEAU_COLORS.keys())

# Modelli di energia (aggiorna con i tuoi dati)
modes = [5, 9, 18, 25]

# Caricamento dei DataFrame
dfs = [pd.read_csv(file, sep='\t') for file in groups]

# Creazione del grafico
datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
fig, ax = plt.subplots()
fig.set_figheight(4)
fig.set_figwidth(5)

photon_span = np.linspace(0, 256, 20)

# Creazione dei grafici per ciascuna configurazione
for i in range(4):
    ax.errorbar(
        photon_span,
        dfs[i]['Voltage output average (V)'],
        xerr=np.tile(1, dfs[i].shape[0]),
        yerr=dfs[i]['Voltage output std (V)'],
        fmt='s',
        markersize=1,
        capsize=3,
        color=colours[i]
    )

ax.set_xlabel('Equivalent input photons')
ax.set_ylabel('|CSA reset amplitude| [V]')
ax.tick_params(right=True, top=True, direction='in')

lns = []
linear_outputs = []
max_diffs = []
inls = []

# Esegui la regressione lineare e aggiungi i risultati al grafico
for i in range(4):
    from scipy.stats import linregress
    lns.append(linregress(
        photon_span,
        dfs[i]['Voltage output average (V)'].astype(float)
    ))
    linear_outputs.append(lns[i].intercept + lns[i].slope * np.linspace(0, 256, 20))
    ax.plot(
        photon_span,
        linear_outputs[i],
        color=colours[i]
    )
    max_diffs.append(np.max(dfs[i]['Voltage output average (V)'] - linear_outputs[i]))
    inls.append(100 * np.abs(max_diffs[i]) / lns[i].slope / 256)

# Aggiungi la tabella con i parametri
ax.table(cellText=[
    ['Mode [keV]', f'{modes[0]}', f'{modes[1]}', f'{modes[2]}', f'{modes[3]}'],
    ['Gain [mV/γ]', f'{np.round(lns[0].slope*10**3, 3)}', f'{np.round(lns[1].slope*10**3, 3)}', f'{np.round(lns[2].slope*10**3, 3)}', f'{np.round(lns[3].slope*10**3, 3)}'],
    ['Gain [mV/fC]', f'{np.round(lns[0].slope*10**3/modes[0]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[1].slope*10**3/modes[1]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[2].slope*10**3/modes[2]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[3].slope*10**3/modes[3]*config.conv_kev_c*10**-15, 3)}'],
    ['INL [%]', f'{np.round(inls[0], 2)}', f'{np.round(inls[1], 2)}', f'{np.round(inls[2], 2)}', f'{np.round(inls[3], 2)}'],
], colWidths=[.25, .11, .11, .11, .11], loc='lower right')

# Aggiungi la legenda
ax.legend([f'{x} keV' for x in modes],
        title='γ energy',
        frameon=False)
plt.savefig(f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf')
