import time
import pandas as pd
import TeledyneLeCroyPy
from datetime import datetime
import config
import pFREYA_tester_processing as pYtp

# Definizione delle configurazioni dei livelli di energia in base ai primi 2 bit di cfg_bits
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
        return 535  
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 432 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 332 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 234 
    else:
        raise ValueError("Configurazione shap_bits non valida")


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

# Loop per ogni configurazione di cfg_bits
for item in config_bits_list:
    # Ottenere il livello di energia
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    print(f"energy level {energy_level}Kev")
    # Configurazione del setup,cfg_bits cambia per ogni configurazione utilizzata per ogni passo
    config.config(channel='shap', lemo='none', n_steps=8, cfg_bits=item, cfg_inst=True, active_probes=False)
    config.lecroy.set_tdiv(tdiv='200NS')
    config.lecroy.set_toffset(toffset='-400e-9')
    pYtp.send_slow_ctrl_auto(item,1)
    
    time.sleep(5)
    config.ps.write(':OUTP:STAT ON')

    #corrente iniziale
    
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
        time.sleep(0.5)
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
    df.to_csv(f'G:Shared drives/FALCON/measures/new/transient/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv', sep='\t')
    
    print(f"Misura completata per cfg_bits {item} con livello di energia {energy_level:} A")

    #PRELEVO DATI DA MISURAZIONI VECCHIE RIGUARDANTI LA STESSA CONFIGURAZIONE DI BIT
    import numpy as np
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import time
    from datetime import datetime
    import matplotlib.colors as mcolors
    path=(f'G:Shared drives/FALCON/measures/new/transient/shap/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv')
    df = pd.read_csv(path, sep = '\t')
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
    arr_split = path.split('/')
    channel_name = arr_split[6]
    config_bits_str = arr_split[-1].split('_')[1]
    config_bits = [int(x) for x in config_bits_str]
    config.config(channel='shap',n_steps=8,cfg_bits=item,cfg_inst=False,lemo=False)

    #PLOT UNICO PER OGNI CONFIGURAZIONE

    t_s = -324e-9 #300
    t_e = 900e-9    #900e-9
    sub_df = df

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
    
    plt.savefig(f'G:Shared drives/FALCON/measures/new/transient/shap/shap_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf',dpi=300)
