import time
import pandas as pd
import TeledyneLeCroyPy
from datetime import datetime
import config
import pFREYA_tester_processing as pYtp
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.colors as mcolors

# Loop per ogni configurazione di cfg_bits
for item in config.config_bits_list_shap:
    # Ottenere il livello di energia
    energy_level = config.get_energy_level(item)
    shap_bits = config.get_shap_bits(item)
    print(f"energy level {energy_level}Kev")
    # Configurazione del setup,cfg_bits cambia per ogni configurazione utilizzata per ogni passo
    config.config(channel='shap', lemo='none', n_steps=8, cfg_bits=item, cfg_inst=True, active_probes=False)
    # 100 mV/div e -463mV
    config.lecroy.set_vdiv(channel=2,vdiv='305e-3')
    config.lecroy.set_voffset(channel=2,voffset='-415e-3')
    config.lecroy.set_tdiv(tdiv='200NS')
    config.lecroy.set_toffset(toffset='-820e-9')
    pYtp.send_slow_ctrl_auto(item,1)
    
    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)
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
        print(f'{i}:{cl}')
        time.sleep(5)
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
