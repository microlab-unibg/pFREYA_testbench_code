
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyvisa
import matplotlib.colors as mcolors
from datetime import datetime
import time
import glob
import config
T = 30e-9 # s
t_r = 3e-9 # s
N_pulses = 10 # adimensional
conv_kev_c = 3.65/1000 * 1/1.602e-19 # Energy in silicon for e-/h * no of electrons per coulomb [keV/e-] * [e-/C]


current_levels = []
iinj_int_results = []
eq_ph_results = []
csa_configs = [
    {'csa_bits': [0, 1], 'photon_energy': 9, 'offset_charge': 8.5e-15, 'min_current': 0.07e-6, 'max_current': 1.55e-6, 'corr_fact': 1},
    {'csa_bits': [0, 0], 'photon_energy': 25, 'offset_charge': 8.5e-15, 'min_current': 0.07e-6, 'max_current': 3.8e-6, 'corr_fact': 1},
    {'csa_bits': [1, 0], 'photon_energy': 18, 'offset_charge': 8.5e-15, 'min_current': 0.07e-6, 'max_current': 3.3e-6, 'corr_fact': 1},
    {'csa_bits': [1, 1], 'photon_energy': 5, 'offset_charge': 0, 'min_current': 0.065e-6, 'max_current': 0.83e-6, 'corr_fact': 1}
]
def get_csa_bits(index):
    return csa_configs[index]['csa_bits']

def get_min_current(index):
    return csa_configs[index]['min_current']

def get_max_current(index):
    return csa_configs[index]['max_current']

def get_photon_energy(index):
    return csa_configs[index]['photon_energy']

def get_offset_charge(index):
    return csa_configs[index]['offset_charge']

def get_corr_fact(index):
    return csa_configs[index]['corr_fact'] #1

def auto_current_level_csa(n_steps):
    for index in range(len(csa_configs)):
        min_current = get_min_current(index)
        max_current = get_max_current(index)
        current_lev = -1 * np.linspace(min_current, max_current, n_steps)
        current_levels.append(current_lev) 

def auto_iinj_int(): 
    for index, item in enumerate(current_levels):
        # Calculate iinj_int for each value of current_lev
        iinj_int = item * (T/2 - t_r) * N_pulses + get_offset_charge(index)
        iinj_int_results.append(iinj_int)

def auto_eq_ph():
    for index, item in enumerate(iinj_int_results):
        eq_ph = -1 * item * get_corr_fact(index) * conv_kev_c / get_photon_energy(index)
        eq_ph_results.append(eq_ph)

# test
n_steps = 5
auto_current_level_csa(n_steps)
auto_iinj_int()
auto_eq_ph()


cfg_bits_template = [0, 1, 0, 0, 0, 1, 1] # lo utilizzo per definire un template base per poi iterare le diverse config di bits
# Creazione del DataFrame
for index, config in enumerate(csa_configs):
    config_bits = cfg_bits_template.copy() 
    config_bits[0], config_bits[1] = config['csa_bits']
    import config
    config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=config_bits)
    
    config.ps.write(':SOUR:CURR:LEV -.0e-6')
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    N_samples = config.N_samples

    # set proper time division for this analysis
    config.lecroy.write('TDIV 200NS')
    # suppress channel for noise stuff
    #config.lecroy.write('F3:TRA OFF')
    # set cursor positions
    #config.lecroy.write(f'C2:CRS HREL')
    # reset inj
    config.ps.write(':SOUR:CURR:LEV -0.07e-6')
    time.sleep(2)

    ndiv = 10 # positive and negative around delay
    tdelay = -648 # ns
    tdiv = 200 # ns/div
    osc_ts = 318 # ns
    osc_te = osc_ts + config.peaking_time + 10 # 10 ns to avoid switching time
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    if config.channel_name == 'shap':
        div_e = (osc_te - osc_offset)/tdiv
    else:
        div_e = (432 - osc_offset)/tdiv
    config.lecroy.write(f'C1:CRST HDIF,{div_s},HREF,{div_e}')

    measures = {
        #'CSA Bits': [],
        'Current Level Step': [],
        'Current Level (A)': [],
        'iinj_int (C)': [],
        'Equivalent Photons': [],
        'Voltage output average (V)': [],
        'Voltage output std (V)': []
    }

    current_lev=current_levels[index]
    for i, level in enumerate(current_lev):
        import config
        #measures['CSA Bits'].append(config['csa_bits'])
        measures['Current Level Step'].append(i)
        measures['Current Level (A)'].append(level)
        measures['iinj_int (C)'].append(iinj_int_results[index][i])
        measures['Equivalent Photons'].append(eq_ph_results[index][i])      
        data = []
        for _ in range(N_samples):
            #test funzionamento
            #random_voltage = np.random.normal(loc=0.5, scale=0.05)  # media=0.5V e deviazione standard=0.05V
            #data.append(random_voltage)
            data.append(float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2]))
            time.sleep(0.03)
        
        # Calcola la media e la deviazione standard e memorizza nel DataFrame i diversi valori di tensione
        measures['Voltage output average (V)'].append(np.average(data) / gain)
        measures['Voltage output std (V)'].append(np.std(data) / gain)

    if channel_name == 'csa':
           #measures['Voltage output average (V)'] = [-1 * x for x in measures['Voltage output average (V)']]
            measures['Voltage output average (V)'] = -1*measures['Voltage output average (V)']
    df = pd.DataFrame(measures)
    datetime_str = datetime.now().strftime('%Y%m%d%H%M')

    # Sostituire percorso del drive e salvare il file
    df.to_csv(f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t', index=False)
    print("File tsv salvato con successo.")

#GRAFICI( per ogni configurazione di bit plot di tensione media e fotoni equivalenti)
"""
def get_voltage_output_avg(csa_bits, df):
# Filtra il DataFrame per ottenere solo le righe con i csa_bits corrispondente a vout media
    df_filtered = df[df['CSA Bits'].apply(lambda x: tuple(x) == tuple(csa_bits))]
    return df_filtered['Voltage output average (V)'].tolist()

def get_equivalent_photons(csa_bits, df):
# Filtra il DataFrame per ottenere solo le righe con i csa_bits corrispondente a 
    df_filtered = df[df['CSA Bits'].apply(lambda x: tuple(x) == tuple(csa_bits))]
    return df_filtered['Equivalent Photons'].tolist()
"""                 
#fino a qua ho commentato tutti i valori dei dispositivi
def generate_plots():
    # Trova tutti i file .tsv nella cartella specificata
    tsv_files = glob.glob(f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv')

    for index, tsv_file in enumerate(tsv_files):
        # Leggi il DataFrame dal file .tsv
        df = pd.read_csv(tsv_file, sep='\t')

        # Controlla la lunghezza dei dati
        length = len(df['Voltage output average (V)'])
        photon_span = np.linspace(0, 256, length)

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
        linear_output = ln.intercept + ln.slope * np.linspace(0, 256, length)
        ax.plot(photon_span, linear_output)
        max_diff = np.max(df['Voltage output average (V)'] - linear_output)
        inl = 100 * np.abs(max_diff) / ln.slope / 256
        print(ln)
        
        # Aggiungi tabella informativa
        ax.table(cellText=[
            ['$\\gamma$ energy [keV]', f'{config.photon_energy}'],  # Sostituisci N/A con {config.photon_energy}
            ['Peaking time [ns]', f'{config.peaking_time}'],  # sostituisci 318 con {config.peaking_time}
            ['Slope [mV/#$\\gamma$]', f'{np.round(ln.slope * 10**3, 3)}'],
            ['INL [%]', f'{np.round(inl, 2)}'],
            ['R$^2$', f'{np.round(ln.rvalue**2, 3)}']
        ], colWidths=[.33, .2], loc='lower right')

        # Salva il grafico
        try:
            output_file = f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.pdf'
            plt.savefig(output_file, dpi=300)
            plt.close(fig)  # Chiude il grafico corrente per liberare risorse
            print(f"File plot salvato con successo: {output_file}")
        except Exception as e:
            print(f"Errore durante il salvataggio del file plot: {e}")

# Esegui la funzione
generate_plots()
#plt.show()


#grafico totale delle 4 modalità:

colours = list(mcolors.TABLEAU_COLORS.keys())

# Percorsi dei file .tsv (aggiorna con i tuoi percorsi)
path = [ 
        f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{0}_nominal_{lemo_name}_{datetime_str}.tsv',
        f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{1}_nominal_{lemo_name}_{datetime_str}.tsv',
        f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{2}_nominal_{lemo_name}_{datetime_str}.tsv', 
        f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{3}_nominal_{lemo_name}_{datetime_str}.tsv' 
]
# Modelli di energia (aggiorna con i tuoi dati)
modes = [5, 9, 18, 25]

# Caricamento dei DataFrame
dfs = []
for p in path:
    dfs.append(pd.read_csv(p, sep='\t'))

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
ax.set_ylabel(f'|CSA reset amplitude| [V]')
ax.tick_params(right=True, top=True, direction='in')

lns = []
linear_outputs = []
max_diffs = []
inls = []
import scipy as s
# Esegui la regressione lineare e aggiungi i risultati al grafico
for i in range(4):
    lns.append(s.linregress(
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
    #manca tabella con parametri
plt.savefig(f'G:/Shared drives/PHD/FALCON/measures/new/transcharacteristics/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.pdf')

