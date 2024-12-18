import time
import pandas as pd
import TeledyneLeCroyPy
from datetime import datetime
import config
import pFREYA_tester_processing as pYtp

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


# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    [1, 1, 1, 1, 1, 1, 1],  # Configurazione 5  keV
    [1, 0, 1, 1, 1, 1, 1],  # Configurazione 18 keV
    [0, 1, 1, 1, 1, 1, 1],  # Configurazione 9  keV
    [0, 0, 1, 1, 1, 1, 1],  # Configurazione 25 keV
]
'''
Iterazione sulle configurazioni di setup:
    -Per ogni elemento nella lista config_bits_list, trovo il valore di keV con get_energy_level() 
    -configurazione dell'oscilloscopio con la funzione config.lecroy andando a definire i parametri di divisione 
    verticale/orizzontale.
    -analisi su diversi livelli di corrente:
        -per ogni livello di corrente definito in config.current_lev viene impostato un valore del ps.
        -calcolo il segnale corretto in base al guadagno e all'attenuazione, normalizzando rispetto al valore iniziale.
    -Elaborazione e salvataggio dati in .tsv e plot
'''
for item in config_bits_list:
    # Ottenere il livello di energia
    energy_level = get_energy_level(item)
    print(f"energy level {energy_level}Kev")
    # Configurazione del setup,cfg_bits cambia per ogni configurazione utilizzata per ogni passo
    config.config(channel='csa', lemo='none', n_steps=8, cfg_bits=item, cfg_inst=True, active_probes=False)
    pYtp.send_slow_ctrl_auto(item,0)
    # 100 mV/div e -611mV
    config.lecroy.set_vdiv(channel=1,vdiv='100e-3')
    config.lecroy.set_voffset(channel=1,voffset='-611e-3')
    config.lecroy.set_tdiv(tdiv='100NS')
    config.lecroy.set_toffset(toffset='-240e-9')
    config.ps.write(':SOUR:CURR:LEV -0.0e-6')
    config.ps.write(':OUTP:STAT ON')

    #corrente iniziale
    
    time.sleep(2)

    
    channel_name = config.channel_name
    lemo_name = config.lemo_name
    gain = config.lemo_gain
    attenuation = config.attenuation
    gain_lane = 1 / attenuation if config.active_prbs else gain

    
    df = pd.DataFrame()

    #itero diversi livelli di corrente
    for i, cl in enumerate(config.current_lev):
        # Imposta il livello di corrente
        config.ps.write(f':SOUR:CURR:LEV {cl}')
        time.sleep(1)
        # N sample to average and extract std from
        data = pd.DataFrame.from_dict(
            config.lecroy.get_channel(channel_name='C', n_channel=config.channel_num)['waveforms'][0]
        )
        
        data['Amplitude (V)'] = (data['Amplitude (V)'] - data['Amplitude (V)'][0]) / gain_lane
        
        data.insert(0, 'Current level step', i)
        data.insert(1, 'Current level (A)', cl)
        df = pd.concat((df, data))

    #salvataggio misura
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
    if config.active_prbs: 
        str_type='active_prbs' 
    else: 
        str_type = ''
    
    df['Time (s)'] = df['Time (s)'] + 200e-9
    df.to_csv(f'G:/Shared drives/FALCON/measures/new/transient/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t')
    
    print(f"Misura completata per cfg_bits {item} con livello di energia {energy_level:} A")

    #PRELEVO DATI DA MISURAZIONI VECCHIE RIGUARDANTI LA STESSA CONFIGURAZIONE DI BIT
    import numpy as np
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import time
    from datetime import datetime
    import matplotlib.colors as mcolors
    path=(f'G:/Shared drives/FALCON/measures/new/transient/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv')
    df = pd.read_csv(path, sep = '\t')
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
    arr_split = path.split('/')
    channel_name = arr_split[6]
    config_bits_str = arr_split[-1].split('_')[1]
    config_bits = [int(x) for x in config_bits_str]
    config.config(channel='csa',n_steps=8,cfg_bits=item,cfg_inst=False,lemo=False)

    #PLOT UNICO PER OGNI CONFIGURAZIONE

    t_s = 300e-9 if config.channel_name == 'csa' else -100e-9 #300
    t_e = 900e-9 if config.channel_name == 'csa' else 1.8e-6    #900e-9
    sub_df = df[df['Time (s)'].between(t_s, t_e)]

    colours = list(mcolors.TABLEAU_COLORS.keys())
    fig, ax = plt.subplots()
    fig.set_figheight(4)
    fig.set_figwidth(5)
    for i, cl in enumerate(config.current_lev):
        ax.plot(
            sub_df[sub_df['Current level step'] == i]['Time (s)']*10**6 - t_s*10**6,
            sub_df[sub_df['Current level step'] == i]['Amplitude (V)'],
            '-', linewidth=1, color=colours[i])
    ax.set_xlabel('Time [$\\mu$s]')
    ax.set_ylabel(f'{channel_name.upper() if channel_name == 'csa' else 'Shaper'} output voltage [V]')
    ax.tick_params(right=True, top=True, direction='in')
    ax.autoscale(enable=True, axis='x', tight=True)

    ax.legend(np.linspace(0,256,8).astype(int),
            title=f"$\\gamma$ @ {config.photon_energy} keV",
            frameon=False)
    if channel_name == 'shap':
        ax.text(.01,.01,f'$t_p$ = {config.peaking_time} ns',ha='left',va='bottom',transform=ax.transAxes)

    plt.savefig(f'G:/Shared drives/FALCON/measures/new/transient/csa/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.pdf',dpi=300)

