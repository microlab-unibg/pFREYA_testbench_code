#iniziare da transient
#recupera valore di channel 1 e 2
    #sull 1 c'è l'alto 
    #sull 2 c'è il basso
    #plottare e verificare con l'oscillo se combaciano
#loop per i vari livelli di energia 
#plotta i due canali e salva su falcon
    #verificare come impostare la scala di misura e come farla
    #provare il plot su un singolo file, altrimenti per ciascun canale crea un file 
#transcaratteristica
#seleziona intervallo configurando PtP e PtN (prendere V esatta(?) a quel tempo) + diff
#plot del differenziale 
#funzione per muovere intervallo
#grafico degli intervalli mossi?
from TeledyneLeCroyPy import TeledyneLeCroyPy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
from datetime import datetime
import config
import pFREYA_tester_processing as pYtp
import matplotlib.colors as mcolors

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
        return 510  
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 420 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 330 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 240 
    else:
        raise ValueError("Configurazione shap_bits non valida")
    
def print_differential(path_low, path_high, shap_bits, datetime_str, config_bits_str, lemo_name, channel_name):
    # Funzione per calcolare e stampare il differenziale
    #set variables for differential
    df_low = pd.read_csv(path_low, sep='\t')
    df_high = pd.read_csv(path_high, sep='\t')

    colours = list(mcolors.TABLEAU_COLORS.keys())
    fig, ax = plt.subplots(figsize=(7, 5))
    t_s = -324e-9  # Offset time in seconds

    for i,cl, in enumerate(config.current_lev):

        df_low_step = df_low[df_low['Current level step'] == i]
        df_high_step = df_high[df_high['Current level step'] == i]

        time = df_low_step['Time (s)'].values
        diff = df_high_step['Amplitude (V)'].values - df_low_step['Amplitude (V)'].values
        ax.plot(
            time * 1e-6- t_s * 1e6,
            diff,
            '-', linewidth=1, color=colours[i], label=f'step {i} ({cl} A)'
        )
    ax.set_xlabel('Time [$\\mu$s]')
    ax.set_ylabel(f'Differential output voltage [V]')
    ax.tick_params(right=True, top=True, direction='in')
    ax.autoscale(enable=True, axis='x', tight=True)
    ax.legend(title=f'Current step', frameon=False)
    plt.title(f'Differential for configuration: {config_bits_str}, Shaper Bits: {shap_bits} ns\n ')
    plt.tight_layout()
    plt.savefig(f'G:Shared drives/FALCON/measures/new/transient/SH/Combined Plot/diff_{config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf', dpi=300)
    plt.show()
    plt.close()

    
config_bits_list = [
    # Configurazione da 9 keV
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    #da espandere alle altre configurazioni una volta accertato che il cod funzioni
]


#loop for every configuration for channel 1 and 2
for item in config_bits_list:
    #get energy level
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    dfs = {}
    file_paths = {}
   
    for channel in ['csa', 'shap']:
        #setup configuration for channel 1
        config.config(
            channel=channel,
            lemo='none',
            n_steps=8,
            cfg_bits=item,
            cfg_inst=True,
            active_probes=False,
        )
        if channel == 'csa':
            config.lecroy.set_vdiv(channel=1, vdiv='230e-3')
            config.lecroy.set_voffset(channel=1, voffset='690e-3')
            subfolder = 'Low'
        else:
            config.lecroy.set_vdiv(channel=2, vdiv='230e-3')
            config.lecroy.set_voffset(channel=2, voffset='690e-3')
            subfolder = 'High'
        config.lecroy.set_tdiv(tdiv='100NS')
        config.lecroy.set_toffset(toffset='-240e-9')
        pYtp.send_slow_ctrl_auto(item, 0 if channel == 'csa' else 1)
        config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
        config.ps.write(':OUTP:STAT ON')
        time.sleep(5)

        channel_name = config.channel_name
        lemo_name = config.lemo_name
        gain = config.lemo_gain
        attenuation = config.attenuation
        gain_lane = 1 / attenuation if config.active_prbs else gain

        df = pd.DataFrame()
    
        #current levels iteration
        for i, cl in enumerate(config.current_lev):
            #set current level
            config.ps.write(f':SOUR:CURR:LEV {cl}')
            print(f'{i}: {cl}')
            time.sleep(5)
            
            data = pd.DataFrame.from_dict(
                config.lecroy.get_channel(channel_name='X', n_channel=config.channel_num)['waveform'][0]
            )

            data['amplitude'] = (data['amplitude(V)'] - data['amplitude(V)'][0]) / gain_lane
            data.insert(0,'Current level step', i )
            data.insert(1,'Current level (A)', cl)
            df = pd.concat((df, data))

        #save data
        datetime_str = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        if config.active_prbs:
            str_type = 'active_prbs'
        else:
            str_type = ''
        
        df_path = f'G:Shared drives/FALCON/measures/new/transient/SH/{subfolder}/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv' 
        df.to_csv(df_path, sep='\t')

        print(f"Measurment for cfg_bits {item} with energy level {energy_level:}A.")

        #plot for each channel
        t_s = -324e-9
        colours = list(mcolors.TABLEAU_COLORS.keys())
        fig, ax = plt.subplots(figsize=(5, 4))
        for i, cl in enumerate(config.current_lev):
            ax.plot(
                df[df['Current level step'] == i]['Time (s)']*10**6 - t_s*10**6,
                df[df['Current level step'] == i]['Amplitude (V)'],
                '-', linewidth=1, color=colours[i]
            )
        ax.set_xlabel('Time [$\\mu$s]')
        ax.set_ylabel(f'{channel_name.upper() if channel_name == "csa" else "Shaper"} output voltage [V]')
        ax.tick_params(right=True, top=True, direction='in')
        ax.autoscale(enable=True, axis='x', tight=True)
        ax.legend(
            np.linspace(0, 256, 8).astype(int),
            title=f"$\\gamma$ @ {config.photon_energy} keV",
            frameon=False
        )
        if channel_name == 'shap':
            ax.text(.01, .01, f'$t_p$ = {config.peaking_time} ns', ha='left', va='bottom', transform=ax.transAxes)
            plt.tight_layout
        plt.savefig(f'G:Shared drives/FALCON/measures/new/transient/SH/{subfolder}/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.pdf', dpi=300)            
        plt.close()

path_low = f'G:Shared drives/FALCON/measures/new/transient/SH/Low/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv'
path_high = f'G:Shared drives/FALCON/measures/new/transient/SH/High/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_shapconfig_{shap_bits}_{datetime_str}.tsv'
print_differential(path_low, path_high, shap_bits, datetime_str, config.config_bits_str, lemo_name, channel_name)




    