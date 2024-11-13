import pFREYA_tester_processing.UART_definitions as UARTdef
from utilities.bitstring_to_bytes import bitstring_to_bytes

import serial
import math
import time
import traceback

def send_UART(cmd='', data=''):
    """Function to send UART commands and data to FPGA

    Parameters
    ----------
    cmd : str
        Command to be sent on UART
    data : str, opt
        Data to be sent on UART
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    ser = serial.Serial(UARTdef.COM_PORT,UARTdef.BAUD_RATE)
    if (cmd != ''):
        ser.write(bitstring_to_bytes(cmd))
    if (data != ''):
        ser.write(bitstring_to_bytes(data))
    ser.close()

def create_cmd(cmd_name, signal_name):
    """Function to create a command byte starting from the command name and the signal name in string format

    Parameters
    ----------
    cmd_name : str
        command name
    signal_name : str
        signal name

    Returns
    -------
    str
        command packet
    """
    return UARTdef.CMD_PACKET + cmd_name + signal_name

def create_data(data):
    """Function to create a data byte starting from the data in string format

    Parameters
    ----------
    data : str
        data

    Returns
    -------
    str
        data packet
    """
    for i in range(math.floor(int(UARTdef.DATA_PACKET_LENGTH)/(int(UARTdef.DATA_UART_DATA_POS)+1)),0,-1):
        yield UARTdef.DATA_PACKET + \
            (UARTdef.LAST_UART_PACKET if i == 1 else UARTdef.NOTLAST_UART_PACKET) + \
            data[(i-1)*(UARTdef.DATA_UART_DATA_POS+1):i*(UARTdef.DATA_UART_DATA_POS+1)]

def create_data_slow(data):
    """Function to create a slow control packet byte starting from the data in string format

    Parameters
    ----------
    data : str
        data

    Returns
    -------
    str
        data packet
    """
    for i in range(math.floor(int(UARTdef.SLOW_CTRL_PACKET_LENGTH)/(int(UARTdef.SLOW_CTRL_UART_DATA_POS)+1)),0,-1):
        yield UARTdef.DATA_PACKET + \
            (UARTdef.LAST_UART_PACKET if i == 1 else UARTdef.NOTLAST_UART_PACKET) + \
            data[(i-1)*(UARTdef.SLOW_CTRL_UART_DATA_POS+1):i*(UARTdef.SLOW_CTRL_UART_DATA_POS+1)]

    #if (type == UARTdef.LAST_UART_PACKET):
    #    return UARTdef.DATA_PACKET + UARTdef.LAST_UART_PACKET + data
    #else:
    #    # the 8'd0 at the beginning is to set bits that are not useful
    #    return UARTdef.DATA_PACKET + UARTdef.NOTLAST_UART_PACKET + data

def convert_strvar_bin(strvar, n_bits):
    """Convert StrVar to string binary representation

    Parameters
    ----------
    strvar : StrVar
        strvar
    n_bits : int
        number of bits of binary representation

    Returns
    -------
    str
        String representation of strvar in binary format
    """
    s = '{0:0' + str(n_bits) + 'b}'
    return s.format(int(strvar.get()))

def convert_str_bin(s):
    """Convert str to binary representation

    Parameters
    ----------
    strvar : str
        str

    Returns
    -------
    bytes
        Binary representation of str
    """
    return bin(int(s))

def send_CSA_RESET_N(gui):
    """Function to set CSA_RESET_N fast control in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SET_DELAY_CMD, UARTdef.CSA_RESET_N_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.csa_reset_n['delay'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.CSA_RESET_N_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.csa_reset_n['high'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.CSA_RESET_N_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.csa_reset_n['low'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_SH_PHI1D_INF(gui):
    """Function to set SHI_PHI1D_INF fast control in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SET_DELAY_CMD, UARTdef.SH_INF_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_inf['delay'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.SH_INF_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_inf['high'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.SH_INF_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_inf['low'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_SH_PHI1D_SUP(gui):
    """Function to set SHI_PHI1D_SUP fast control in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SET_DELAY_CMD, UARTdef.SH_SUP_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_sup['delay'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.SH_SUP_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_sup['high'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.SH_SUP_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sh_phi1d_sup['low'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_ADC_START(gui):
    """Function to set ADC_START fast control in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SET_DELAY_CMD, UARTdef.ADC_START_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.adc_start['delay'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.ADC_START_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.adc_start['high'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.ADC_START_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.adc_start['low'],UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_clocks(gui):
    """Function to set clocks in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.SLOW_CTRL_CK_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.slow_ck,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        gui.slow_ck_sent = True
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.SEL_CK_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.sel_ck,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        gui.sel_ck_sent = True
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.ADC_CK_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.adc_ck,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.INJ_STB_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.inj_stb,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.DAC_SCK_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.dac_sck,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        gui.dac_sck_sent = True
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.SER_CK_CODE)
        send_UART(cmd,'')
        print('CMD sent: ',cmd)
        for data in create_data(convert_strvar_bin(gui.ser_ck,UARTdef.DATA_PACKET_LENGTH)):
            send_UART('', data)
            print('Data sent: ',data)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_asic_ctrl(gui):
    """Function to set ASIC controls (fast controls) in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    send_CSA_RESET_N(gui)
    time.sleep(1)
    send_SH_PHI1D_INF(gui)
    time.sleep(1)
    send_SH_PHI1D_SUP(gui)
    time.sleep(1)
    send_ADC_START(gui)
    time.sleep(1)

def send_pixel(gui):
    """Function to set and send pixel selection in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    if (not gui.sel_ck_sent):
        return 1
    
    try:
        pass
        # set row and col
        cmd = create_cmd(UARTdef.SET_PIXEL_CMD, UARTdef.PIXEL_ROW_CODE)
        data = create_data(convert_strvar_bin(gui.pixel_row,UARTdef.DATA_PACKET_LENGTH))
        send_UART(cmd, data)
        print('CMD sent: ',cmd,'Data sent: ',data)
        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_PIXEL_CMD, UARTdef.PIXEL_COL_CODE)
        data = create_data(convert_strvar_bin(gui.pixel_col,UARTdef.DATA_PACKET_LENGTH))
        send_UART(cmd, data)
        print('CMD sent: ',cmd,'Data sent: ',data)
        time.sleep(1)

        # send pixel sel
        cmd = create_cmd(UARTdef.SEND_PIXEL_SEL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def create_slow_ctrl_packet(gui):
    """Function to create the slow control packet needed in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.

    Returns
    ----------
    str
        Full slow control packet as a string representing a binary.
    """
    # for each pixel is the same
    slow_ctrl_packet = gui.csa_mode_n.get() + gui.inj_en_n.get() + gui.shap_mode.get() + \
                    gui.ch_en.get() + gui.inj_mode_n.get()
    #slow_ctrl_packet = '1111111'
    full_slow_ctrl_packet = ''
    for _ in range(0, UARTdef.PIXEL_N):
        full_slow_ctrl_packet = full_slow_ctrl_packet + slow_ctrl_packet

    # set pixel to be injected
    pixel_idx = int(gui.pixel_to_inj.get())*UARTdef.SLOW_CTRL_N_BITS+2 # shouldnt be hard coded
    full_slow_ctrl_packet = full_slow_ctrl_packet[:pixel_idx] + '0' + full_slow_ctrl_packet[pixel_idx+1:]
    # reach a dimension multiple of DATA_POS+1
    missing_bits = UARTdef.SLOW_CTRL_UART_DATA_POS - UARTdef.SLOW_CTRL_UART_DATA_LAST_POS
    full_slow_ctrl_packet = full_slow_ctrl_packet + '0'*missing_bits #trailing cause each 6 bits will be reversed when sending data

    return full_slow_ctrl_packet

def create_dac_packet(gui, type):
    """Function to create the slow control packet needed in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    type : str
        Type of DAC packet to be created as integer.

    Returns
    ----------
    str
        DAC packet as a string representing a binary.
    """
    if (type == UARTdef.DAC_CMD_CONFIG):
        dac_packet_data = UARTdef.DAC_CMD_PADDING + UARTdef.DAC_CMD_CONFIG + \
                          UARTdef.DAC_DATA_CONFIG_PADDING + convert_strvar_bin(gui.dac['source'],1) + \
                          UARTdef.DAC_DATA_CONFIG_PADDING + UARTdef.DAC_DATA_CONFIG_PWDWN_DIS
    elif (type == UARTdef.DAC_CMD_GAIN):
        dac_packet_data = UARTdef.DAC_CMD_PADDING + UARTdef.DAC_CMD_GAIN + \
                          UARTdef.DAC_DATA_GAIN_PADDING + convert_strvar_bin(gui.dac['divider'],1) + \
                          UARTdef.DAC_DATA_GAIN_PADDING + convert_strvar_bin(gui.dac['gain'],1)
    elif (type == UARTdef.DAC_CMD_DATA):
        dac_packet_data = UARTdef.DAC_CMD_PADDING + UARTdef.DAC_CMD_DATA + \
                          convert_strvar_bin(gui.dac['level'],12) + UARTdef.DAC_DATA_REGISTER_PADDING
    else:
        raise RuntimeError('Not a known DAC command or not implemented.')

    #remove word divider
    dac_packet_data = dac_packet_data.replace('_','')
    
    return dac_packet_data

#metodo per settare livello di livello di corrente a 0.08*10^-6
def send_current_level_csa(gui):    
    """Function to create the slow control packet needed in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.

    Returns
    ----------
    str
        Current level as a string representing a binary.
    """
    ps = gui.rm.open_resource('GPIB1::23::INSTR')
    print(ps.query('*IDN?'))
    print(gui.current_level)

    ps.write(':OUTP:LOW FLO')
    ps.write(':OUTP:OFF:AUTO ON')
    ps.write(':OUTP:PROT ON')
    ps.write(':OUTP:RES:MODE FIX')
    ps.write(':OUTP:RES:SHUN DEF')
    ps.write(':SOUR:FUNC:MODE CURR')
    ps.write(':SOUR:CURR:MODE FIX')
    ps.write(f':SOUR:CURR:LEV {gui.current_level.get()}E-6')
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

    return gui.current_level


def send_current_level(gui):
    """Function to create the slow control packet needed in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.

    Returns
    ----------
    str
        Current level as a string representing a binary.
    """
    ps = gui.rm.open_resource('GPIB1::23::INSTR')
    print(ps.query('*IDN?'))
    print(gui.current_level)

    ps.write(':OUTP:LOW FLO')
    ps.write(':OUTP:OFF:AUTO ON')
    ps.write(':OUTP:PROT ON')
    ps.write(':OUTP:RES:MODE FIX')
    ps.write(':OUTP:RES:SHUN DEF')
    ps.write(':SOUR:FUNC:MODE CURR')
    ps.write(':SOUR:CURR:MODE FIX')
    ps.write(f':SOUR:CURR:LEV {gui.current_level.get()}E-6')
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

    return gui.current_level

def send_slow_ctrl(gui):
    """Function to send clocks in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    if (not gui.slow_ck_sent):
        return 1
    
    full_slow_ctrl_packet = create_slow_ctrl_packet(gui) #str
    print('SLOW_CTRL data to be sent: ',[full_slow_ctrl_packet[i:i+UARTdef.SLOW_CTRL_N_BITS] for i in range(0, len(full_slow_ctrl_packet), UARTdef.SLOW_CTRL_N_BITS)])

    try:
        # set slow packet        
        cmd = create_cmd(UARTdef.SET_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        print('CMD sent: ',cmd)
        for data in create_data_slow(full_slow_ctrl_packet):
            send_UART('', data)
            print('Data sent: ',data)

        time.sleep(1)

        # send slow
        cmd = create_cmd(UARTdef.SEND_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        print('CMD sent: ',cmd)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_UART_DAC(dac_packet):
    """Function to send single DAC packets in UART mode

    Parameters
    ----------
    dac_packet : str
        DAC packet to be sent on UART
    """
    cmd = create_cmd(UARTdef.SET_DAC_CMD, UARTdef.UNUSED_CODE)
    send_UART(cmd)
    print('CMD sent: ',cmd)
    time.sleep(1)

    for i in range(0,math.floor(UARTdef.DAC_PACKET_LENGTH/(UARTdef.DAC_UART_DATA_POS+1))-1): # -1 due to last packet different
        bin_data = dac_packet[i*(UARTdef.DAC_UART_DATA_POS+1):(i+1)*(UARTdef.DAC_UART_DATA_POS+1)]
        bin_data = bin_data[::-1] # as above
        data = create_data_slow(bin_data, UARTdef.NOTLAST_UART_PACKET)
        send_UART('',data)
        print('DATA sent: ',data)
        time.sleep(1)

    bin_data = dac_packet[(i+1)*(UARTdef.DAC_UART_DATA_POS+1):]
    bin_data = bin_data[::-1]
    data = create_data_slow(bin_data, UARTdef.LAST_UART_PACKET)
    send_UART('',data)
    print('DATA sent: ',data)
    time.sleep(1)

    # send DAC
    cmd = create_cmd(UARTdef.SEND_DAC_CMD, UARTdef.UNUSED_CODE)
    send_UART(cmd)
    print('CMD sent: ',cmd)
    time.sleep(1)

def send_DAC(gui):
    """Function to DAC configuration in the FPGA

    Parameters
    ----------
    gui : pFREYA_GUI
        The structure containing all the data related to the tester.
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    if (not gui.dac_sck_sent):
        return 1
    
    dac_config_packet = create_dac_packet(gui,UARTdef.DAC_CMD_CONFIG)
    dac_gain_packet = create_dac_packet(gui,UARTdef.DAC_CMD_GAIN)
    dac_data_packet = create_dac_packet(gui,UARTdef.DAC_CMD_DATA)
    print('DAC configs: ',dac_config_packet,dac_gain_packet,dac_data_packet)

    try:
        send_UART_DAC(dac_config_packet)
        time.sleep(1)
        send_UART_DAC(dac_gain_packet)
        time.sleep(1)
        send_UART_DAC(dac_data_packet)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_sync_time_bases():
    """Function to send the command to sync signals on the FPGA
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.SYNC_TIME_BASE_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        print('CMD sent: ',cmd)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0

def send_reset_FPGA():
    """Function to send the command to reset the FPGA
    
    Returns
    ----------
    int
        0 if everything was ok, 1 otherwise.
    """
    try:
        cmd = create_cmd(UARTdef.RESET_FPGA_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        print('CMD sent: ',cmd)
        time.sleep(1)
    except Exception:
        print(traceback.format_exc())
        return 1
    
    return 0