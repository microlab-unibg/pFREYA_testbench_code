import serial
import serial.tools.list_ports
import pyvisa
import matplotlib.pyplot as plt
from TeledyneLeCroyPy import TeledyneLeCroyPy
import numpy as np
import pandas as pd
import time
from datetime import datetime
import matplotlib.colors as mcolors


def config_inst() -> None:
    """Function to initialise instruments
    """

    global rm, ps, pg, lecroy

    rm = pyvisa.ResourceManager()
    print(rm.list_resources())

    serial.tools.list_ports.comports(include_links=True)

    # to deal with already initialised oscilloscope
    lecroy = None
    ps = rm.open_resource('GPIB1::23::INSTR')
    print(ps.query('*IDN?'))

    ps.write(':OUTP:LOW FLO')
    ps.write(':OUTP:OFF:AUTO ON')
    ps.write(':OUTP:PROT ON')
    ps.write(':OUTP:RES:MODE FIX')
    ps.write(':OUTP:RES:SHUN DEF')
    ps.write(':SOUR:FUNC:MODE CURR')
    ps.write(':SOUR:CURR:MODE FIX')
    ps.write(':SOUR:CURR:LEV -2e-6')
    ps.write(':DISP:ENAB OFF')
    ps.write(':DISP:TEXT:DATA "pFREYA16"')
    ps.write(':DISP:TEXT:STAT ON')
    ps.write(':OUTP:STAT ON')

    print(f'''
    Low terminal: {ps.query(':OUTP:LOW?')[:-1]}
    Auto output off: {ps.query(':OUTP:OFF:AUTO?')[:-1]}
    Protection: {ps.query(':OUTP:PROT?')[:-1]}
    Resistance mode: {ps.query(':OUTP:RES:MODE?')[:-1]}
    Shunt resistance : {ps.query(':OUTP:RES:SHUN?')[:-1]}
    Output current mode: {ps.query(':SOUR:CURR:MODE?')[:-1]}
    Output current level: {ps.query(':SOUR:CURR:LEV?')[:-1]}
    Output voltage range: {ps.query(':SOUR:VOLT:RANG?')[:-1]}
    Output status: {ps.query(':OUTP:STAT?')[:-1]}
        ''')

    pg = rm.open_resource('GPIB1::9::INSTR')
    print(pg.query('*IDN?'))

    csa_reset_n_pattern = ''.join([f'{i}' for i in [1]*20 + [0]*980])
    csa_reset_n_length = str(len(csa_reset_n_pattern))
    csa_reset_n_length_length = str(len(str(len(csa_reset_n_pattern))))

    pg.write('*RST')
    pg.write(f':TRIG:COUN {csa_reset_n_length}')
    pg.write(f':TRIG:SOUR INT')
    pg.write(f':PULS:PER 15NS')
    pg.write(f':PULS:DCYC1 50PCT')
    pg.write(f':PULS:DCYC2 50PCT')
    pg.write(f':PULS:TRAN1 3NS')
    pg.write(f':PULS:TRAN2 3NS')
    pg.write(':DIG:STIM:PATTERN:STAT ON')
    pg.write(f':DIG:STIM:PATTERN:DATA1 #{csa_reset_n_length_length}{csa_reset_n_length}{csa_reset_n_pattern}')
    pg.write(f':DIG:STIM:PATTERN:PRES2 2,{csa_reset_n_length}')
    pg.write(f':DIG:STIM:PATTERN:DATA3 #{csa_reset_n_length_length}{csa_reset_n_length}{csa_reset_n_pattern}')
    pg.write(f':DIG:STIM:SIGN1:FORM NRZ')
    pg.write(f':DIG:STIM:SIGN2:FORM NRZ')
    pg.write(':OUTP1:IMP:INT 50OHM')
    pg.write(':OUTP1:IMP:EXT 100OHM')
    pg.write(':OUTP2:IMP:INT 50OHM')
    pg.write(':OUTP2:IMP:EXT 100OHM')
    pg.write(':VOLT1:LEV:HIGH 1.2V')
    pg.write(':VOLT1:LEV:LOW 0V')
    pg.write(':VOLT2:LEV:HIGH 1.2V')
    pg.write(':VOLT2:LEV:LOW 0V')
    pg.write(':OUTP1 ON')
    pg.write(':OUTP2 ON')

    print(f'''
    Number of pattern positions: {pg.query(':TRIG:COUN?')[:-1]}
    Source of the trigger: {pg.query(':TRIG:SOUR?')[:-1]}
    Period of the pulse: {pg.query(':PULS:PER?')[:-1]}
    Duty cycle of the pulse: {pg.query(':PULS:DCYC1?')[:-1]}
    Rise time of the pulse: {pg.query(':PULS:TRAN1?')[:-1]}
    Type of pulse: PATTERN
    CH1 data: 20 1's, 980 0's
    CH2 data: as the clock
    STRB data: 20 1's, 980 0's
    Type of the pulse: {pg.query(':DIG:STIM:SIGN1:FORM?')[:-1]}
    Internal impedance (source): {pg.query(':OUTP1:IMP:INT?')[:-1]}
    External impedance (termination): {pg.query(':OUTP1:IMP:EXT?')[:-1]}
    High level: {pg.query(':VOLT1:LEV:HIGH?')[:-1]}
    Low level: {pg.query(':VOLT1:LEV:LOW?')[:-1]}
    Output 1 status: {pg.query(':OUTP1?')[:-1]}
    Output 2 status: {pg.query(':OUTP2?')[:-1]}
        ''')

    if lecroy is None:
        lecroy = TeledyneLeCroyPy.LeCroyWaveRunner('TCPIP0::169.254.1.214::inst0::INSTR')
    print(lecroy.idn)

    # not setting the whole configuration for the time being, just doing the measurements
    #print(lecroy.query('TEMPLATE?'))

def config(channel: str, n_steps: int, cfg_bits: list) -> None:
    """Function to configure parameters for tests

    Parameters
    ----------
    channel : str
        Which channel is to be tested. Currently supporting 'csa' and 'shap'
    n_steps : int
        Number of steps in the sweeps
    cfg_bits : int
        Configuration bits of the mode under test
    """
    config_inst()

    # for each step set a current level, take some data
    # next plot everything and calculate statistics

    # The integral in the range is given by Iinj_int and should be converted to PH_EQ by means
    #  of the following eq: PH_EQ = Iinj_int*2.28e16 keV/C / 9 keV = Iinj_int * 2.53e15

    # The general integral for a trap(t-t_i,t_r,t_r,T), where t_i is the arrival time, t_r is the rise time and its the same as the fall time, T is the period
    #  of pulse + rest (50% duty cycle) is equal to T/2-t_r
    # Therefore Iinj_int = (T/2-t_r)*Iin = Qin

    # With 0 A there is actually a negative injection (yay!)
    #     Evaluating the offset (@ 9keV, sim) at 0 is 6.16 eq ph or 2.43fA. With a current of 0.02 uA it goes away. In real life it goes with 0.06 uA.
    # With max it is not perfect
    #     doing the same as above, one gets a correction factor of around 105.8fA/103.2fA
    global T, t_r, N_pulses, conv_kev_c, config_bits, csa_bits, shap_bits, photon_energy, offset_charge, \
        min_current, max_current, corr_fact, peaking_time, current_lev, iinj_int,  eq_ph, config_bits_str, \
        channel_name, channel_num, num_steps, config_bits

    channel_name = channel
    channel_num = 1 if channel_name == 'csa' else 2
    num_steps = n_steps
    config_bits = cfg_bits
    T = 30e-9 # s
    t_r = 3e-9 # s
    N_pulses = 10 # adimensional
    conv_kev_c = 3.65/1000 * 1/1.602e-19 # Energy in silicon for e-/h * no of electrons per coulomb [keV/e-] * [e-/C]
    csa_bits = config_bits[0:2]
    shap_bits = config_bits[3:5]
    match csa_bits:
        case [0,1]:
            photon_energy = 9 # keV
            offset_charge = 8.5e-15 # C *tentative
            min_current = .07e-6 # A
            max_current = 1.8e-6 # A
            corr_fact = 1 #105.8/103.2
        case [0,0]:
            photon_energy = 25 # keV
            offset_charge = 8.5e-15 # C *tentative
            min_current = .07e-6 # A
            max_current = 4.3e-6 #3.5e-6 # A
            corr_fact = 1 #105.8/103.2
        case [1,0]:
            photon_energy = 18 # keV
            offset_charge = 8.5e-15 # C *tentative
            min_current = .07e-6 # A
            max_current = 3.5e-6 # A
            corr_fact = 1 #105.8/103.2
        case [1,1]:
            photon_energy = 5 # keV
            offset_charge = 0 #8.5e-15 # C *tentative
            min_current = .07e-6 # A
            max_current = 1e-6 # A
            corr_fact = 1 #105.8/103.2
    match shap_bits:
        case [1,0]: 
            peaking_time = 405 # ns (from mean dyn), 432 ns (from max dyn), 432 ns (from theory)
            shap_corr_fact = .9
        case [0,0]: 
            peaking_time = 220 # ns (from mean dyn), 261 ns (from max dyn), 234 ns (from theory)
            shap_corr_fact = .9
        case [0,1]: 
            peaking_time = 308 # ns (from mean dyn), 343 ns (from max dyn), 332 ns (from theory)
            shap_corr_fact = .9
        case [1,1]: 
            peaking_time = 493 # ns (from mean dyn), 535 ns (from max dyn), 535 ns (from theory)
            shap_corr_fact = .9

    if channel_name == 'csa':
        current_lev = -1 * np.linspace(min_current,max_current,n_steps)
    else:
        current_lev = -1 * np.linspace(min_current,max_current,n_steps) * shap_corr_fact
    iinj_int = current_lev * (T/2-t_r) * N_pulses + offset_charge
    eq_ph = -1 * iinj_int * corr_fact * conv_kev_c / photon_energy
    config_bits_str = ''.join([str(x) for x in config_bits])
    print(f'current range: {current_lev[0]}, {current_lev[-1]}')
    print(f'Injection integral (min and max): {iinj_int[0]}, {iinj_int[-1]}')
    print(f'photon energy @ {photon_energy} keV: {eq_ph[0]}, {eq_ph[-1]}')
    print(f'Peaking time: {peaking_time} ns')
    print(f'Config bits: {config_bits_str}')
    print(f'Channel to be tested: {channel_name}')