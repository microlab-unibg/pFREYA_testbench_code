import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
from datetime import datetime
import matplotlib.colors as mcolors

import config
config.config(channel='shap',lemo='none',n_steps=20,cfg_bits=[0,1,0,0,0,1,1])
channel_name = config.channel_name
lemo_name = config.lemo_name#
gain = config.lemo_gain
N_samples = config.N_samples

df = pd.DataFrame()
df['Current level step'] = np.arange(len(config.current_lev))
df['Current level (A)'] = config.current_lev
df['Equivalent photons'] = config.eq_ph
df['Voltage output average (V)'] = None
df['Voltage output std (V)'] = None

# set proper time division for this analysis
config.lecroy.write('TDIV 200NS')
# suppress channel for noise stuff
#config.lecroy.write('F3:TRA OFF')
# set cursor positions
#config.lecroy.write(f'C2:CRS HREL')
# reset inj
config.ps.write(':SOUR:CURR:LEV -0.07e-6')
time.sleep(2)
# in future one must set vdiv, hdiv, ... TODO
# current: tdiv = 200 ns/div,, delay = -908 ns
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

for i, cl in enumerate(config.current_lev):
	# set current level
	config.ps.write(f':SOUR:CURR:LEV {cl}')
	time.sleep(0.005)
	data = []
	# N sample to average and extract std from
	for _ in range(N_samples):
		data.append(float(config.lecroy.query(f'C{config.channel_num}:CRVA? HREL').split(',')[2]))
		time.sleep(0.03)
	
	df.loc[i,'Voltage output average (V)'] = np.average(data)/gain
	df.loc[i,'Voltage output std (V)'] = np.std(data)/gain

datetime_str = datetime.strftime(datetime.now(), '%d%m%y_%H%M%S')
if channel_name == 'csa':
	df['Voltage output average (V)'] = -1*df['Voltage output average (V)']

df.to_csv(f'C:/Users/giorg/Desktop/ts/mis{channel_name}/{channel_name}_{config.config_bits_str}_nominal_{lemo_name}_{datetime_str}.tsv', sep='\t')