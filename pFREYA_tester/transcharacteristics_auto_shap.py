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
        return 530  
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 340 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 440 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 250 
    else:
        raise ValueError("Configurazione shap_bits non valida")

# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    [0, 1, 1, 1, 0, 1, 1],  [0, 1, 1, 0, 0, 1, 1],  [0, 1, 1, 0, 1, 1, 1],  [0, 1, 1, 1, 1, 1, 1],  # 9 keV
    [0, 0, 1, 1, 0, 1, 1],  [0, 0, 1, 0, 0, 1, 1],  [0, 0, 1, 0, 1, 1, 1],  [0, 0, 1, 1, 1, 1, 1],  # 25 keV
    [1, 0, 1, 1, 0, 1, 1],  [1, 0, 1, 0, 0, 1, 1],  [1, 0, 1, 0, 1, 1, 1],  [1, 0, 1, 1, 1, 1, 1],  # 18 keV
    [1, 1, 1, 1, 0, 1, 1],  [1, 1, 1, 0, 0, 1, 1],  [1, 1, 1, 0, 1, 1, 1],  [1, 1, 1, 1, 1, 1, 1],  # 5 keV
]

#dizionario utilizzato per salvare dati di ogni configurazione
dati = {
    'energy level [keV]': [],
    'Peaking time [ns]': [],
    'Slope [mV/#$\\gamma$]': [],
    'INL [%]': [],
    'R$^2$': []
}
# Elenco dei livelli di energia (da associare ai rispettivi gruppi di configurazioni)
energy_levels = [18, 25, 9, 5]
groups = {18:[] ,9: [], 25: [], 5: []}

# Raggruppa i file TSV per energia
for item in config_bits_list:
    config.config(channel='shap', lemo='none', n_steps=20, cfg_bits=item, cfg_inst=True, active_probes=False)
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    pYtp.send_slow_ctrl_auto(item,1)
    
    # 100 mV/div e -611mV
    config.lecroy.set_vdiv(channel=2,vdiv='100e-3')
    config.lecroy.set_voffset(channel=2,voffset='-466e-3')
    config.lecroy.set_tdiv(tdiv='200NS')
    config.lecroy.set_toffset(toffset='-400e-9')
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)


    # set proper time division for this analysis
    # suppress channel for noise stuff
    #config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    #config.lecroy.write(f'C2:CRS HREL')
    # reset inj
    ndiv = 10 # positive and negative around delay
    tdelay = -400 # ns
    tdiv = 200 # ns/div
    osc_ts = 298 # ns
    osc_te = 298 + config.peaking_time 
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    div_e = (osc_te - osc_offset)/tdiv
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
        'Voltage output std (V)': []
          }
    
    for i, level in enumerate(config.current_lev):
        config.ps.write(f':SOUR:CURR:LEV {level}')
        print(f'{i} : {level}')
        time.sleep(1)
        mis['Current Level Step'].append(i)
        mis['Current Level (A)'].append(level)
        mis['iinj_int (C)'].append(config.iinj_int[i])
        mis['Equivalent Photons'].append(config.eq_ph[i])
        data=[]
        for _ in range(N_samples):
            data.append(float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2]))
            time.sleep(0.05)
        mis['Voltage output average (V)'].append(np.average(data)/config.lemo_gain)
        mis['Voltage output std (V)'].append(np.std(data) / config.lemo_gain)

    df = pd.DataFrame(mis)
    datetime_str = datetime.now().strftime('%Y%m%d%H%M')
    output_file = f'G:/Shared drives/FALCON/measures/new/transcharacteristics/shap/{config.channel_name}_{config.config_bits_str}_nominal_{config.lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv'
    df.to_csv(output_file, sep='\t', index=False)
    print("File tsv salvato con successo.")
    # Aggiungi il file al gruppo di energia corrispondente per il grafico totale, cosi poi plotto dalla lista corrispondente
    groups[energy_level].append(df)
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

    #salvataggio valori misurati su nel dataframe dati, in maniera che li salvi in un .tsv
    dati['energy level [keV]'].append(f'{config.photon_energy}')
    dati['Peaking time [ns]'].append(f'{config.peaking_time}')
    dati['Slope [mV/#$\\gamma$]'].append(f'{np.round(ln.slope*10**3,3)}')
    dati['INL [%]'].append(f'{np.round(inl, 2)}')
    dati['R$^2$'].append(f'{np.round(ln.rvalue**2, 3)}')

    # Salva il grafico
    try:
        output_file = f'G:/Shared drives/FALCON/measures/new/transcharacteristics/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf'
        plt.savefig(output_file, dpi=300)
        plt.close(fig)  # Chiude il grafico corrente per liberare risorse
        print(f"File plot salvato con successo: {output_file}")
    except Exception as e:
        print(f"Errore durante il salvataggio del file plot: {e}")
data = pd.DataFrame(dati)
data.to_csv(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/shap/data/{channel_name}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv', sep='\t', index=False)
###summary###
colours = list(mcolors.TABLEAU_COLORS.keys())
for energy_level, dataframes in groups.items():  # Sostituisci con i percorsi reali
    dfs = dataframes

    # Configurazione della figura
    datetime_str = datetime.now().strftime('%d%m%y_%H%M%S')
    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(5)

    photon_span = np.linspace(0, 256, 20)
    pt = [234, 332, 432, 535]  # Tempi di picco per ciascun file (modifica come necessario)

    # Grafico dei dati con errore
    for i in range(4):
        ax.errorbar(
            photon_span,
            dfs[i]['Voltage output average (V)'],
            xerr=np.tile(1, dfs[i].shape[0]),
            yerr=dfs[i]['Voltage output std (V)'],
            fmt='s', markersize=1, capsize=3,
            color=colours[i]
        )

    ax.set_xlabel('Equivalent input photons')
    ax.set_ylabel(f'Shaper peak-to-peak amplitude [V]')
    ax.tick_params(right=True, top=True, direction='in')

    # Regressione lineare e calcolo delle statistiche
    lns = []
    linear_outputs = []
    max_diffs = []
    inls = []
    #dizionario per risultati totali
    data_summary ={
        'Mode [ns]': [],
        'Gain [mV/#$\\gamma$]': [],
        'Gain [mV/fC]': [],
        'INL [%]': []
    }
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
        data_summary['Mode [ns]'].append(f'{pt[i]}')
        data_summary['Gain [mV/#$\\gamma$]'].append(f'{np.round(lns[i].slope*10**3, 3)}')
        data_summary['Gain [mV/fC]'].append(f'{np.round(lns[i].slope*10**3/pt[i]*config.conv_kev_c*10**-15, 3)}')
        data_summary['INL [%]'].append(f'{np.round(inls[i], 2)}')

    #per ogni configurazione di shap salvo dati
    summary =pd.DataFrame(data_summary)
    summary.to_csv(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/shap/summary/{channel_name}_{energy_level}_keV_{datetime_str}.tsv',sep='\t', index=False)
    
    # Tabella dei risultati
    ax.table([
        ['Mode [ns]', f'{pt[0]}', f'{pt[1]}', f'{pt[2]}', f'{pt[3]}'],
        ['Gain [mV/#$\\gamma$]', f'{np.round(lns[0].slope * 10**3, 3)}', f'{np.round(lns[1].slope * 10**3, 3)}', f'{np.round(lns[2].slope * 10**3, 3)}', f'{np.round(lns[3].slope * 10**3, 3)}'],
        ['Gain [mV/fC]', f'{np.round(lns[0].slope * 10**3 / pt[0]*config.conv_kev_c * 10**-15, 3)}', f'{np.round(lns[1].slope * 10**3 / pt[1] * config.conv_kev_c * 10**-15, 3)}', f'{np.round(lns[2].slope * 10**3 / pt[2] * config.conv_kev_c * 10**-15, 3)}', f'{np.round(lns[3].slope * 10**3 / pt[3] * config.conv_kev_c * 10**-15, 3)}'],
        ['INL [%]', f'{np.round(inls[0], 2)}', f'{np.round(inls[1], 2)}', f'{np.round(inls[2], 2)}', f'{np.round(inls[3], 2)}'],
    ], colWidths=[.25, .11, .11, .11, .11], loc='lower right')

    # Testo con l'energia fotonica
    ax.text(.77, .25, f'$\\gamma$ @ {energy_level} keV', ha='left', va='bottom', transform=ax.transAxes)

    # Legenda
    ax.legend([f'{x} ns' for x in pt], title=f"Peaking time", frameon=False)

    # Salvataggio del grafico
    plt.savefig(f'G:/Shared drives/FALCON/measures/new/transcharacteristics/shap/summary/shap_summary_nominal_{energy_level}_keV_{datetime_str}.pdf', dpi=300)
    print(f"Grafico salvato per {energy_level} keV")