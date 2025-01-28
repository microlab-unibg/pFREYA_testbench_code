
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
'''
funzione per determinare keV sulla base della configurazione dei bit passata come parametro, sulla base delle prime due cifre
della configurazione
'''
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


config_bits_list = [
    [1, 1, 1, 1, 1, 1, 1],  # Configurazione 5 keV
    [0, 1, 1, 1, 1, 1, 1],  # Configurazione 9 keV
    [1, 0, 1, 1, 1, 1, 1],  # Configurazione 18 keV
    [0, 0, 1, 1, 1, 1, 1],  # Configurazione 25 keV
]

'''
dizionario per salvare dati di configurazione
'''
dati = {
    'energy level [keV]': [],
    'Offset [mV]': [],
    'Slope [mV/#$\\gamma$]': [],
    'INL [%]': [],
    'R$^2$': []
}
tsv_files = []

'''
per ogni configigurazione presente nella lista:
-configurazione dei parametri
-slow control del monitor
-definizione dei parametri temporali
-definizione di un dizionario (mis) dove vengono memorizzati i dati prelevati durante l'analisi

-itero sui diversi livelli di corrente, dove per ogni step prelevo:
    -Indice del livello di corrente (i)
    -Valore della corrente (level)
    -Carica iniettata (iinj_int)
    -Fotoni equivalenti (eq_ph)

    -vengono prelevati "N_samples" campioni
    -calcolo media e deviazione standard
    -plot
'''

import config

for item in config_bits_list:
    config.config(channel='monitor',lemo='none',n_steps=20,cfg_bits=item,cfg_inst=True, active_probes=False)

    config.lecroy.write(f'C3:CRS HREL')
    pYtp.send_slow_ctrl_auto(item,0)
    
    # 100 mV/div e -611mV
    # config.lecroy.set_vdiv(channel=1,vdiv='100e-3')
    # config.lecroy.set_voffset(channel=1,voffset='-611e-3')
    config.lecroy.set_vdiv(channel=3,vdiv='112e-3')
    config.lecroy.set_voffset(channel=3,voffset='-402e-3')
    config.lecroy.set_tdiv(tdiv='100NS')
    config.lecroy.set_toffset(toffset='-240e-9')
    
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')

    #corrente iniziale
    
    time.sleep(5)
    ndiv = 10 # positive and negative around delay
    tdelay = -240  #ns +20ns respect to time base
    tdiv = 100 # ns/div
    osc_ts = 300 # ns
    osc_te = osc_ts + config.peaking_time + 10 # 10 ns to avoid switching time
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    if config.channel_name == 'shap':
        div_e = (osc_te - osc_offset)/tdiv
    else:
        div_e = (-10 - osc_offset)/tdiv
    config.lecroy.write(f'C3:CRST HDIF,{div_s},HREF,{div_e}')
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    gain_mon = config.gain_mon
    N_samples = config.N_samples

    # set proper time division for this analysis
    # suppress channel for noise stuff
    #config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    #config.lecroy.write(f'C3:CRS HREL')
    # reset inj

    mis = {
        #'CSA Bits': [],
        'Current Level Step': [],
        'Current Level (A)': [],
        'iinj_int (C)': [],
        'Equivalent Photons': [],
        'Voltage output average (V)': [],
        'Voltage output average no ofs (V)': [],
        'Voltage output std (V)': []
    }


    for i, level in enumerate(config.current_lev):
        config.ps.write(f':SOUR:CURR:LEV {level}')
        time.sleep(2)
        print(f'{i} : {level}')
        #mis['CSA Bits'].append(config)
        mis['Current Level Step'].append(i)
        mis['Current Level (A)'].append(level)
        mis['iinj_int (C)'].append(config.iinj_int[i])
        mis['Equivalent Photons'].append(config.eq_ph[i])      
        data = []
        for _ in range(N_samples):
            data.append(float(config.lecroy.query(f'C{config.channel_num_mon}:CRVA? HREL').split(',')[4]))
            time.sleep(0.05)
        
        # Calcola la media e la deviazione standard e memorizza nel DataFrame i diversi valori di tensione
        mis['Voltage output average (V)'].append(np.average(data)/gain_mon)
        mis['Voltage output std (V)'].append(np.std(data) / gain_mon)
    if channel_name == 'csa':
        mis['Voltage output average (V)'] = [-1* x for x in mis['Voltage output average (V)']]
        #mis['Voltage output average (V)'] = -1*mis['Voltage output average (V)']
    
    offset = mis['Voltage output average (V)'][0]
    mis['Voltage output average no ofs (V)'] = mis['Voltage output average (V)'] - offset

    df = pd.DataFrame(mis)
    datetime_str = datetime.now().strftime('%Y%m%d%H%M')

    df.to_csv(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t', index=False)
    tsv_files.append(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv')
    print("File tsv salvato con successo.")

    
    photon_span = np.linspace(0, 256, 20)
 
    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(5)

    ax.errorbar(photon_span, df['Voltage output average no ofs (V)'],
                xerr=np.tile(1, df.shape[0]), yerr=df['Voltage output std (V)'],
                fmt='s', markersize=1, capsize=3)
    ax.set_xlabel('Equivalent input photons [#]')
    ax.set_ylabel(f'{channel_name.upper()} output voltage, no offset [V]')
    ax.tick_params(right=True, top=True, direction='in')
    from scipy.stats import linregress
    ln = linregress(photon_span, df['Voltage output average no ofs (V)'].astype(float))
    linear_output = ln.intercept + ln.slope * np.linspace(0, 256, 20)
    ax.plot(photon_span, linear_output)
    max_diff = np.max(df['Voltage output average no ofs (V)'] - linear_output)
    inl = 100 * np.abs(max_diff) / ln.slope / 256
    print(ln)

    ax.table(cellText=[
        ['$\\gamma$ energy [keV]', f'{config.photon_energy}'],  # Sostituisci N/A con {config.photon_energy}
        ['Offset [mV]', f'{np.round(offset*10**3,3)}'],  # sostituisci 318 con {config.peaking_time}
        ['Slope [mV/#$\\gamma$]', f'{np.round(ln.slope*10**3,3)}'],
        ['INL [%]', f'{np.round(inl, 2)}'],
        ['R$^2$', f'{np.round(ln.rvalue**2, 3)}']
    ], colWidths=[.33, .2], loc='lower right')


    #salvataggio valori misurati su nel dataframe dati, in maniera che li salvi in un .tsv
    dati['energy level [keV]'].append(f'{config.photon_energy}')
    dati['Offset [mV]'].append(f'{np.round(offset*10**3,3)}')
    dati['Slope [mV/#$\\gamma$]'].append(f'{np.round(ln.slope*10**3,3)}')
    dati['INL [%]'].append(f'{np.round(inl, 2)}')
    dati['R$^2$'].append(f'{np.round(ln.rvalue**2, 3)}')

    # Salva il grafico
    try:
        output_file = f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.pdf'
        plt.savefig(output_file, dpi=300)
        plt.close(fig)  # Chiude il grafico corrente per liberare risorse
        print(f"File plot salvato con successo: {output_file}")
    except Exception as e:
        print(f"Errore durante il salvataggio del file plot: {e}")

data = pd.DataFrame(dati)
data.to_csv(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/data/{channel_name}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t', index=False)



#grafico totale delle 4 modalità:
# Colori per ogni configurazione
colours = list(mcolors.TABLEAU_COLORS.keys())

# Modalità di energia (aggiorna con i tuoi dati)
modes = [5, 9, 18, 25]

# Caricamento dei DataFrame
dfs = [pd.read_csv(file, sep='\t') for file in tsv_files]

#plot
datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
fig, ax = plt.subplots()
fig.set_figheight(4)
fig.set_figwidth(5)

photon_span = np.linspace(0, 256, 20)

for i in range(4):
    ax.errorbar(
        photon_span,
        dfs[i]['Voltage output average no ofs (V)'],
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

#dizionario per risultati totali
data_summary ={
    'Mode [keV]': [],
    'Offset [mV]': [],
    'Gain [mV/γ]': [],
    'Gain [mV/fC]': [],
    'INL [%]': []
}
# Esegui la regressione lineare e aggiungi i risultati al grafico
for i in range(4):
    from scipy.stats import linregress
    lns.append(linregress(
        photon_span,
        dfs[i]['Voltage output average no ofs (V)'].astype(float)
    ))
    linear_outputs.append(lns[i].intercept + lns[i].slope * np.linspace(0, 256, 20))
    ax.plot(
        photon_span,
        linear_outputs[i],
        color=colours[i]
    )
    max_diffs.append(np.max(dfs[i]['Voltage output average no ofs (V)'] - linear_outputs[i]))
    inls.append(100 * np.abs(max_diffs[i]) / lns[i].slope / 256)
    offset = dfs[i]['Voltage output average (V)'][0]

    #per ogni configurazione di KeV salvo dati
    data_summary['Mode [keV]'].append(f'{modes[i]}')
    data_summary['Offset [mV]'].append(f'{np.round(offset*10**3, 3)}')
    data_summary['Gain [mV/γ]'].append(f'{np.round(lns[i].slope*10**3, 3)}')
    data_summary['Gain [mV/fC]'].append(f'{np.round(lns[i].slope*10**3/modes[i]*config.conv_kev_c*10**-15, 3)}')
    data_summary['INL [%]'].append(f'{np.round(inls[i], 2)}')

summary =pd.DataFrame(data_summary)
summary.to_csv(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/summary/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv',sep='\t', index=False)

ax.table(cellText=[
    ['Mode [keV]', f'{modes[0]}', f'{modes[1]}', f'{modes[2]}', f'{modes[3]}'],
    ['Offset [mV]', f'{data_summary['Offset [mV]'][0]}', f'{data_summary['Offset [mV]'][1]}', f'{data_summary['Offset [mV]'][2]}', f'{data_summary['Offset [mV]'][3]}'],
    ['Gain [mV/γ]', f'{np.round(lns[0].slope*10**3, 3)}', f'{np.round(lns[1].slope*10**3, 3)}', f'{np.round(lns[2].slope*10**3, 3)}', f'{np.round(lns[3].slope*10**3, 3)}'],
    ['Gain [mV/fC]', f'{np.round(lns[0].slope*10**3/modes[0]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[1].slope*10**3/modes[1]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[2].slope*10**3/modes[2]*config.conv_kev_c*10**-15, 3)}', f'{np.round(lns[3].slope*10**3/modes[3]*config.conv_kev_c*10**-15, 3)}'],
    ['INL [%]', f'{np.round(inls[0], 2)}', f'{np.round(inls[1], 2)}', f'{np.round(inls[2], 2)}', f'{np.round(inls[3], 2)}'],
], colWidths=[.25, .11, .11, .11, .11], loc='lower right')


ax.legend([f'{x} keV' for x in modes],
          title='γ energy',
          frameon=False)

plt.savefig(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/monitor/summary/{channel_name}_nominal_{lemo_name}_{datetime_str}.pdf')
