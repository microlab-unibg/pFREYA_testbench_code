import pFREYA_tester_processing.UART_definitions as UARTdef
from utilities.bitstring_to_bytes import bitstring_to_bytes

import serial
import math
import time

def send_UART(cmd='', data=''):
    """Function to send UART words to FPGA

    Parameters
    ----------
    cmd : bytes
        Command to be sent on UART
    data : bytes, opt
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
    """Function to create a command byte starting from the command name and the signal name in binary format

    Parameters
    ----------
    cmd_name : bytes
        command name
    signal_name : bytes
        signal name

    Returns
    -------
    bytes
        command packet
    """
    #return (UARTdef.CMD_PACKET << UARTdef.UART_PACKET_SIZE-1) + (cmd_name << UARTdef.CMD_END_POS) + (signal_name << UARTdef.SIGNAL_END_POS)
    return str(UARTdef.CMD_PACKET) + str(cmd_name) + str(signal_name)

def create_data(data):
    """Function to create a data byte starting from the data in binary format

    Parameters
    ----------
    data : bytes
        data

    Returns
    -------
    bytes
        data packet
    """
    return str(UARTdef.DATA_PACKET) + str(data)

def create_data_slow(data,type):
    """Function to create a data byte starting from the data in binary format

    Parameters
    ----------
    data : bytes
        data

    Returns
    -------
    bytes
        data packet
    """
    if (type == UARTdef.LAST_UART_PACKET):
        return UARTdef.CMD_PACKET + UARTdef.LAST_UART_PACKET + data
    else:
        # the 8'd0 at the beginning is to set bits that are not useful
        return 0b00000000 + UARTdef.CMD_PACKET + UARTdef.NOTLAST_UART_PACKET + data

def convert_strvar_bin(strvar):
    """Convert StrVar to binary representation

    Parameters
    ----------
    strvar : StrVar
        strvar

    Returns
    -------
    bytes
        Binary representation of strvar
    """
    return '{0:07b}'.format(int(strvar.get())) # get rid of 0b

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
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.csa_reset_n['delay']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.CSA_RESET_N_CODE)
        data = create_data(convert_strvar_bin(gui.csa_reset_n['high']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.CSA_RESET_N_CODE)
        data = create_data(convert_strvar_bin(gui.csa_reset_n['low']))
        send_UART(cmd, data)
        print(cmd,'\n',data)
    except:
        return 1
    
    return 0

def send_SH_PHI1D_INF(gui):
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.sh_phi1d_inf['delay']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.SH_INF_CODE)
        data = create_data(convert_strvar_bin(gui.sh_phi1d_inf['high']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.SH_INF_CODE)
        data = create_data(convert_strvar_bin(gui.sh_phi1d_inf['low']))
        send_UART(cmd, data)
        print(cmd,'\n',data)
    except:
        return 1
    
    return 0

def send_SH_PHI1D_SUP(gui):
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.sh_phi1d_sup['delay']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.SH_SUP_CODE)
        data = create_data(convert_strvar_bin(gui.sh_phi1d_sup['high']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.SH_SUP_CODE)
        data = create_data(convert_strvar_bin(gui.sh_phi1d_sup['low']))
        send_UART(cmd, data)
        print(cmd,'\n',data)
    except:
        return 1
    
    return 0

def send_ADC_START(gui):
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.adc_start['delay']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_HIGH_CMD, UARTdef.ADC_START_CODE)
        data = create_data(convert_strvar_bin(gui.adc_start['high']))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_LOW_CMD, UARTdef.ADC_START_CODE)
        data = create_data(convert_strvar_bin(gui.adc_start['low']))
        send_UART(cmd, data)
        print(cmd,'\n',data)
    except:
        return 1
    
    return 0

def send_clocks(gui):
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.slow_ck))
        send_UART(cmd, data)
        print(cmd,'\n',data)
        gui.slow_ck_sent = True

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.SEL_CK_CODE)
        data = create_data(convert_strvar_bin(gui.sel_ck))
        send_UART(cmd, data)
        print(cmd,'\n',data)
        gui.sel_ck_sent = True

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.ADC_CK_CODE)
        data = create_data(convert_strvar_bin(gui.adc_ck))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.INJ_STB_CODE)
        data = create_data(convert_strvar_bin(gui.inj_stb))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.DAC_SCK_CODE)
        data = create_data(convert_strvar_bin(gui.dac_sck))
        send_UART(cmd, data)
        print(cmd,'\n',data)
        gui.dac_sck_sent = True

        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.SER_CK_CODE)
        data = create_data(convert_strvar_bin(gui.ser_ck))
        send_UART(cmd, data)
        print(cmd,'\n',data)
    except:
        return 1
    
    return 0

def send_asic_ctrl(gui):
    """Function to send clocks to the FPGA

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
    send_SH_PHI1D_INF(gui)
    send_SH_PHI1D_SUP(gui)
    send_ADC_START(gui)

def send_pixel(gui):
    """Function to send clocks to the FPGA

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
        data = create_data(convert_strvar_bin(gui.pixel_row))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        time.sleep(1)

        cmd = create_cmd(UARTdef.SET_PIXEL_CMD, UARTdef.PIXEL_COL_CODE)
        data = create_data(convert_strvar_bin(gui.pixel_col))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        time.sleep(1)

        # send pixel sel
        cmd = create_cmd(UARTdef.SEND_PIXEL_SEL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
    except:
        return 1
    
    return 0

def create_slow_ctrl_packet(gui):
    """_summary_

    Parameters
    ----------
    gui : _type_
        _description_
    """
    # for each pixel is the same
    slow_ctrl_packet = gui.csa_mode_n.get() + gui.inj_en_n.get() + gui.shap_mode.get() + gui.ch_en.get() + gui.inj_mode_n.get()
    full_slow_ctrl_packet = ''
    for i in range(0, UARTdef.PIXEL_N):
        full_slow_ctrl_packet = full_slow_ctrl_packet + slow_ctrl_packet
    return full_slow_ctrl_packet

def create_dac_packet(gui):
    """_summary_

    Parameters
    ----------
    gui : _type_
        _description_
    """
    # for each pixel is the same
    # implement dac_gain and ref
    dac_packet_data = convert_strvar_bin(gui.dac["level"]) + UARTdef.DAC_DATA_REGISTER_PADDING
    return dac_packet_data

def send_slow_ctrl(gui):
    """Function to send clocks to the FPGA

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

    try:
        # set slow packet
        cmd = create_cmd(UARTdef.SET_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        for i in range(0,math.floor(UARTdef.SLOW_CTRL_PACKET_LENGTH/(UARTdef.SLOW_CTRL_UART_DATA_POS+1))):
            bin_data = convert_str_bin(full_slow_ctrl_packet[i*(UARTdef.SLOW_CTRL_UART_DATA_POS+1):(i+1)*(UARTdef.SLOW_CTRL_UART_DATA_POS+1)-1])
            data = create_data_slow(bin_data, UARTdef.NOTLAST_UART_PACKET)
            send_UART('',data)
            print(data)
        
        cmd = create_cmd(UARTdef.SET_CK_CMD, UARTdef.ADC_CK_CODE)
        data = create_data(convert_strvar_bin(gui.adc_ck))
        send_UART(cmd, data)
        print(cmd,'\n',data)

        bin_data = convert_str_bin(full_slow_ctrl_packet[i*(UARTdef.SLOW_CTRL_UART_DATA_POS+1):])
        data = create_data_slow(bin_data, UARTdef.LAST_UART_PACKET)
        send_UART('',data)
        print(data)

        # send slow
        cmd = create_cmd(UARTdef.SEND_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        data = create_data(convert_strvar_bin(gui.pixel_col))
        send_UART(cmd)
        print(cmd)
    except:
        return 1
    
    return 0

def send_DAC(gui):
    """Function to send clocks to the FPGA

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
    
    full_dac_packet = create_dac_packet(gui) #str

    try:
        # set slow packet
        cmd = create_cmd(UARTdef.SET_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        send_UART(cmd)
        for i in range(0,math.floor(UARTdef.DAC_PACKET_LENGTH/(UARTdef.DAC_UART_DATA_POS+1))-1): # -1 due to last packet different
            bin_data = convert_str_bin(full_dac_packet[i*(UARTdef.DAC_UART_DATA_POS+1):(i+1)*(UARTdef.DAC_UART_DATA_POS+1)-1])
            data = create_data_slow(bin_data, UARTdef.NOTLAST_UART_PACKET)
            send_UART('',data)
            print(data)

        bin_data = convert_str_bin(full_dac_packet[i*(UARTdef.DAC_UART_DATA_POS+1):])
        data = create_data_slow(bin_data, UARTdef.LAST_UART_PACKET)
        send_UART('',data)
        print(data)

        # send slow
        cmd = create_cmd(UARTdef.SEND_SLOW_CTRL_CMD, UARTdef.UNUSED_CODE)
        data = create_data(convert_strvar_bin(gui.pixel_col))
        send_UART(cmd)
        print(cmd)
    except:
        return 1
    
    return 0