import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
from datetime import datetime
import matplotlib.colors as mcolors
import pFREYA_tester_processing as pYtp

import config
gain = []


def keV(bits):
    if bits[0] == 1 and bits[1] == 1:
        return 5000  # 5 keV
    elif bits[0] == 1 and bits[1] == 0:
        return 18000  # 18 keV
    elif bits[0] == 0 and bits[1] == 1:
        return 9000 # 9 keV
    elif bits[0] == 0 and bits[1] == 0:
        return 25000 # 25 keV

# Percorso alla cartella contenente i file(primo:mio pc, secondo: lab)
#folder = f'G:Drive condivisi/FALCON/measures/new/transcharacteristics/shap/summary'
folder = f'G:Shared drives/FALCON/measures/new/transcharacteristics/shap/summary'


tsv_files = [f for f in os.listdir(folder) if f.endswith('.tsv')]
if tsv_files:
    tsv_files = sorted(
        (os.path.join(folder, f) for f in tsv_files),
        key=os.path.getmtime,
        reverse=True
    )

    latest_file = tsv_files[2] # change here
    print(f"L'ultimo file .tsv salvato è: {latest_file}")

    df = pd.read_csv(latest_file, sep='\t')  
    print(f"\nFile TSV letto:\n{df}")

    if 'Gain [mV/fC]' in df.columns:
        for i in range(4):
            gain.append(float(df['Gain [mV/fC]'][i]))  
        print(f"\nguadagni prelevati:\n{gain}\n")
        selected_configs = config.select_configurations(latest_file, config.config_bits_list_enc)
        print(f"\nConfigurazioni selezionate:\n{selected_configs}")

for gain_item, cfg_item in zip(gain, selected_configs):

    config.config(channel='shap', lemo='none', n_steps=20, cfg_bits=cfg_item, cfg_inst=True, active_probes=False)
    pYtp.send_slow_ctrl_auto(cfg_item, 0) # dont send injection    

    channel_name = config.channel_name
    lemo_name = config.lemo_name
    elem_charge = config.elem_charge
    gain = config.lemo_gain
    gain_shap_fC = gain_item
    N_samples = 100

    # 2 mV/div e -351.8mV
    config.lecroy.set_vdiv(channel=2,vdiv='10e-3') # reset measures
    config.lecroy.set_vdiv(channel=2,vdiv='5e-3')
    config.lecroy.set_voffset(channel=2,voffset='0')
    config.lecroy.set_tdiv(tdiv='200NS')
    config.lecroy.set_toffset(toffset='-820e-9')
    ndiv = 10 # positive and negative around delay
    tdelay = -820 # ns
    tdiv = 200 # ns/div
    osc_ts = 300 # ns
    osc_te = osc_ts + config.peaking_time 
    osc_offset = - ndiv/2*tdiv - tdelay
    div_s = (osc_ts - osc_offset)/tdiv
    div_e = (osc_te - osc_offset)/tdiv


    config.ps.write(f':SOUR:CURR:LEV {config.current_lev[0]}')
    config.ps.write(':OUTP:STAT ON')
    time.sleep(5)

    N_repetitions = 1

    config.lecroy.write(f'C2:CRS HREL')
    config.lecroy.write(f'C2:CRST HDIF,{div_s},HREF,{div_e}')

    diffstd_osc = np.empty(N_repetitions)
    hstd_osc = np.empty(N_repetitions)
    data = np.empty((N_samples, N_repetitions))
    for i in range(N_repetitions):
        time.sleep(0.01)
        print(f'Rep n. {i}')
        for j in range(N_samples):
            data[j, i] = float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2])/gain
            time.sleep(0.001)
        
        # they might take time to calculate so better here
        diffstd_osc[i] = float(config.lecroy.query(f'PAST? CUST,AVG,P3').split(',')[5])/gain
        hstd_osc[i] = float(config.lecroy.query(f'PAST? CUST,AVG,P4').split(',')[5])/gain

    data = data * 10 ** 3
    diffstd_osc = diffstd_osc * 10**3
    hstd_osc = hstd_osc * 10**3

    noise_std = np.mean(np.std(data, axis=0))
    noise_std_std = np.std(np.std(data, axis=0))
    noise_rms = np.mean(np.sqrt(np.mean(np.square(data), axis=0)))
    noise_rms_std = np.std(np.sqrt(np.mean(np.square(data), axis=0)))
    noise_diff = np.mean(diffstd_osc)
    noise_diff_std = np.std(diffstd_osc)
    noise_hstd = np.mean(hstd_osc)
    noise_hstd_std = np.std(hstd_osc)
    
    enc_std = noise_std / gain_shap_fC / elem_charge * 10**-15 # [mV] * [fC/mV] * [e-/fC]
    enc_std_std = noise_std_std / gain_shap_fC
    enc_rms = noise_rms / gain_shap_fC / elem_charge * 10**-15
    enc_rms_std = noise_rms_std / gain_shap_fC
    enc_diff = noise_diff / gain_shap_fC / elem_charge * 10**-15
    enc_diff_std = noise_diff_std / gain_shap_fC
    enc_hstd = noise_hstd / gain_shap_fC / elem_charge * 10**-15
    enc_hstd_std = noise_hstd_std / gain_shap_fC

    datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
    df = pd.DataFrame([[
        noise_std,
        noise_std_std,
        noise_rms,
        noise_rms_std,
        noise_diff,
        noise_diff_std,
        noise_hstd,
        noise_hstd_std,
        enc_std,
        enc_std_std,
        enc_rms,
        enc_rms_std,
        enc_diff,
        enc_diff_std,
        enc_hstd,
        enc_hstd_std,
    ]], columns=[
        'noise std (mV)',
        'noise std std (mV)',
        'noise rms (mV)',
        'noise rms std (mV)',
        'noise diff osc (mV)',
        'noise diff osc std (mV)',
        'noise hstd osc (mV)',
        'noise hstd osc std (mV)',
        'ENC std (e-)',
        'ENC std std (e-)',
        'ENC rms (e-)',
        'ENC rms std (e-)',
        'ENC diff osc (e-)',
        'ENC diff osc std (e-)',
        'ENC hstd osc (e-)',
        'ENC hstd osc std (e-)',
    ])
    #salvataggio e plot
    df.to_csv(f'G:Shared drives/FALCON/measures/new/enc/enc_{config.config_bits_str}_{datetime_str}_{lemo_name}.tsv', sep='\t')
    print(f"\nfile tsv enc per {cfg_item} salvato\n")


