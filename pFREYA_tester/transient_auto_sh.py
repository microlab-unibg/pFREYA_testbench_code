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
        return 510  
    elif cfg_bits[3] == 0 and cfg_bits[4] == 1:
        return 420 
    elif cfg_bits[3] == 1 and cfg_bits[4] == 0:
        return 330 
    elif cfg_bits[3] == 0 and cfg_bits[4] == 0:
        return 240 
    else:
        raise ValueError("Configurazione shap_bits non valida")


# Configurazione dei test per le diverse configurazioni di cfg_bits
config_bits_list = [
    # Configurazione da 9 keV 
    [0, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns
    # [0, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns 
    # [0, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns   
    # [0, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 25 keV
    # [0, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [0, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [0, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [0, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 18 keV
    # [1, 0, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [1, 0, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [1, 0, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [1, 0, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
    # # Configurazione 5 keV
    # [1, 1, 1, 1, 0, 1, 1],  #shaper tp = 432 ns  
    # [1, 1, 1, 0, 0, 1, 1],  #shaper tp = 234 ns  
    # [1, 1, 1, 0, 1, 1, 1],  #shaper tp = 332 ns  
    # [1, 1, 1, 1, 1, 1, 1],  #shaper tp = 535 ns  
]

# Loop per ogni configurazione di cfg_bits
for item in config_bits_list:
    # Ottenere il livello di energia
    energy_level = get_energy_level(item)
    shap_bits = get_shap_bits(item)
    print(f"energy level {energy_level}Kev")
    # Configurazione del setup,cfg_bits cambia per ogni configurazione utilizzata per ogni passo
    config.config(channel='shap', lemo='none', n_steps=8, cfg_bits=item, cfg_inst=True, active_probes=False)
    # 100 mV/div e -463mV
    config.lecroy.set_vdiv(channel=1,vdiv='500e-3')
    config.lecroy.set_vdiv(channel=2,vdiv='500e-3')
    config.lecroy.set_voffset(channel=1,voffset='-35e-3')
    config.lecroy.set_voffset(channel=2,voffset='-35e-3')
    config.lecroy.set_tdiv(tdiv='1US')
    config.lecroy.set_toffset(toffset='-1.46e-6')
    pYtp.send_slow_ctrl_auto(item,2)
    time.sleep(1)
    pYtp.send_sync_time_bases()
    
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
        data_p = pd.DataFrame.from_dict(
            config.lecroy.get_channel(channel_name='C', n_channel=1)['waveforms'][0]
        )
        data_n = pd.DataFrame.from_dict(
            config.lecroy.get_channel(channel_name='C', n_channel=2)['waveforms'][0]
        )
        
        # data['Amplitude (V)'] = (data['Amplitude (V)'] - data['Amplitude (V)'][0]) / gain_lane
        
        data_p.insert(0, 'Current level step', i)
        data_p.insert(1, 'Current level (A)', cl)
        data_p.insert(4, 'Time 2 (s)', data_n['Time (s)'].values)
        data_p.insert(5, 'Amplitude 2 (V)', data_n['Amplitude (V)'].values)
        df = pd.concat((df, data_p))

    #salvataggio misura
    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M')
    if config.active_prbs: 
        str_type='active_prbs' 
    else: 
        str_type = ''
    df.to_csv(f'G:Shared drives/FALCON/measures/new/transient/sh/sh_{config.config_bits_str}_{datetime_str}.tsv', sep='\t')
    
    print(f"Misura completata per cfg_bits {item} con livello di energia {energy_level:} A")