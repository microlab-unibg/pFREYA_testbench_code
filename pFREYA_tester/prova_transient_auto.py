import time
import pandas as pd
from ..pFREYA_analysis import config
from datetime import datetime

# Definizione delle configurazioni dei livelli di energia in base ai cfg_bits
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
    [1, 1, 0, 1, 1, 1, 1],  # Configurazione 5 keV
    [1, 0, 0, 1, 1, 1, 1],  # Configurazione 9 keV
    [0, 1, 0, 1, 1, 1, 1],  # Configurazione 18 keV
    [0, 0, 0, 1, 1, 1, 1],  # Configurazione 25 keV
]

# Loop per ogni configurazione di cfg_bits
for cfg_bits in config_bits_list:
    # Ottenere il livello di energia
    energy_level = get_energy_level(cfg_bits)

    # Configurazione del setup,cfg_bits cambia per ogni configurazione utilizzata per ogni passo
    config.config(channel='shap', lemo='none', n_steps=8, cfg_bits=cfg_bits, active_probes=False)
    
    
    config.ps.write(':SOUR:CURR:LEV -0.0e-6')
    config.ps.write(':OUTP:STAT ON')
    config.pg.write(':OUTP2 OFF')

    #corrente iniziale
    config.ps.write(f':SOUR:CURR:LEV {-0.07e-6}')
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
        time.sleep(10)
        # N sample to average and extract std from
        data = pd.DataFrame.from_dict(
            config.lecroy.get_channel(channel_name='C', n_channel=config.channel_num)['waveforms'][0]
        )
        
        data['Amplitude (V)'] = (data['Amplitude (V)'] - data['Amplitude (V)'][0]) / gain_lane
        
        data.insert(0, 'Current level step', i)
        data.insert(1, 'Current level (A)', cl)
        df = pd.concat((df, data), ignore_index=True)

    #salvataggio misura
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
    if config.active_prbs: 
        str_type='active_prbs' 
    else: 
        str_type = ''
    df.to_csv(f'G:/My Drive/PHD/FALCON/measures/transient/{channel_name}/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t')

    # Feedback verifica su output
    print(f"Misura completata per cfg_bits {cfg_bits} con livello di energia {energy_level:} A")

    #PRELEVO DATI DA MISURAZIONI VECCHIE RIGUARDANTI LA STESSA CONFIGURAZIONE DI BIT
    import numpy as np
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import time
    from datetime import datetime
    import matplotlib.colors as mcolors
    import config

    path = '' #aggiungere percorso
    df = pd.read_csv(path, sep = '\t')
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
    arr_split = path.split('/')
    channel_name = arr_split[6]
    config_bits_str = arr_split[-1].split('_')[1]
    config_bits = [int(x) for x in config_bits_str]
    config.config(channel=channel_name,n_steps=8,cfg_bits=config_bits,cfg_inst=False,lemo=False)

    #PLOT UNICO PER OGNI CONFIGURAZIONE

    t_s = 300e-9 if config.channel_name == 'csa' else -100e-9
    t_e = 900e-9 if config.channel_name == 'csa' else 1.8e-6
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

    # if config.active_prbs:
    # 	str_type = 'active_prbs'
    # else:
    # 	if gain < 3:
    # 		'LEMOLOW'
    # 	else:
    # 		'LEMOHIGH'
    plt.savefig(f'G:/My Drive/PHD/FALCON/measures/transient/csa/{channel_name}_{config.config_bits_str}_nominal_{datetime_str}.pdf',dpi=300)

#devo cambiare i percorsi dove salvare e prelevare i file