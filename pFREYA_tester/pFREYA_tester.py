from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from serial import *

import json

import serial

from utilities.clock_structure import ClockStructure

# === CONSTANTS ===
# The other constants have been moved to the config file
FPGA_COM_DEF = "XILINX"

# === GUI FUNCTIONS ===
def load_config():
    with open("pFREYA_tester_config.json", "r") as f:
        try:
            json_obj = json.load(f)
        except json.JSONDecodeError:
            json_obj = {}
    return json_obj

def save_config(gui):
    with open("pFREYA_tester_config.json", "w") as f:
        json_obj = gui.to_json()
        f.write(json.dumps(json_obj, indent=4))

def connect_fpga():
    ports = serial.tools.list_ports.comports()
    # search port
    fpga_com = ""
    for port, desc, hwid in sorted(ports):
        if (FPGA_COM_DEF in desc):
            fpga_com = port
            return True
    
    # if no port was available
    messagebox.showinfo(message = "No FPGA was detected...")
    return False

def show_about():
    about_root = Tk()
    about_root.geometry("200x150")
    about_frame = ttk.Frame(about_root, padding = 10)
    
    about_root = Label(about_frame, text="Copyright (C)\nPaolo Lazzaroni\n2023\n\nHelp...", font=18)
    about_frame.pack()
    about_root.pack()

# === GUI CLASS ===
class pFREYA_GUI():
    """Class representing the GUI
    """
    def __init__(self):
        """Init that sets defaults and load GUI StringVars
        """
        # Retrieve config
        json_config = load_config()

        # clocks
        self.slow_ck = StringVar(value=json_config.get("clocks","").get("slow_ck",""))
        self.sel_row_ck = StringVar(value=json_config.get("clocks","").get("sel_row_ck",""))
        self.sel_col_ck = StringVar(value=json_config.get("clocks","").get("sel_col_ck",""))
        self.adc_ck = StringVar(value=json_config.get("clocks","").get("adc_ck",""))
        self.dac_ck = StringVar(value=json_config.get("clocks","").get("dac_ck",""))
        self.ser_ck = StringVar(value=json_config.get("clocks","").get("ser_ck",""))

        # test config
        self.dac_inj_level = StringVar(value=json_config.get("test","").get("dac_inj_level",""))
        self.delay_events = StringVar(value=json_config.get("test","").get("delay_events",""))

        # slow control
        self.csa_mode_n = StringVar(value=json_config.get("slow_ctrl","").get("csa_mode_n",""))
        self.inj_en_n = StringVar(value=json_config.get("slow_ctrl","").get("inj_en_n",""))
        self.shap_mode = StringVar(value=json_config.get("slow_ctrl","").get("shap_mode",""))
        self.ch_en = StringVar(value=json_config.get("slow_ctrl","").get("ch_en",""))
        self.inj_mode_n = StringVar(value=json_config.get("slow_ctrl","").get("inj_mode_n",""))

        # pixel selection
        self.pixel_row = StringVar(value=json_config.get("pixel_sel","").get("pixel_row",""))
        self.pixel_col = StringVar(value=json_config.get("pixel_sel","").get("pixel_col",""))

        # ASIC power up control
        self.slow_ctrl_reset_n = {}
        self.slow_ctrl_reset_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("slow_ctrl_reset_n","").get("delay",""))
        self.slow_ctrl_reset_n["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("slow_ctrl_reset_n","").get("period",""))
        self.slow_ctrl_reset_n["width"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("slow_ctrl_reset_n","").get("width",""))
        
        self.sel_init_n = {}
        self.sel_init_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sel_init_n","").get("delay",""))
        self.sel_init_n["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sel_init_n","").get("period",""))
        self.sel_init_n["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("sel_init_n","").get("width",""))

        # ASIC transient control
        self.csa_reset_n = {}
        self.csa_reset_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("delay",""))
        self.csa_reset_n["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("period",""))
        self.csa_reset_n["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("width",""))
        
        self.sh_phi1d_inf = {}
        self.sh_phi1d_inf["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("delay",""))
        self.sh_phi1d_inf["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("period",""))
        self.sh_phi1d_inf["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("width",""))
        
        self.sh_phi1d_sup = {}
        self.sh_phi1d_sup["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("delay",""))
        self.sh_phi1d_sup["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("period",""))
        self.sh_phi1d_sup["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("width",""))
        
        self.adc_start = {}
        self.adc_start["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("delay",""))
        self.adc_start["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("period",""))
        self.adc_start["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("width",""))

        # ASIC serialiser control
        self.ser_reset_n = {}
        self.ser_reset_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("delay",""))
        self.ser_reset_n["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("period",""))
        self.ser_reset_n["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("width",""))

        self.ser_read = {}
        self.ser_read["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("delay",""))
        self.ser_read["period"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("period",""))
        self.ser_read["width"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("width",""))
    
    def to_json(self):
        # === START JSON DEFINITION ===
        return {
                    "__pFREYA_GUI__": True,
                    "clocks": {
                        "slow_ck":    self.slow_ck.get(),
                        "sel_row_ck": self.sel_row_ck.get(),
                        "sel_col_ck": self.sel_col_ck.get(),
                        "adc_ck":     self.adc_ck.get(),
                        "dac_ck":     self.dac_ck.get(),
                        "ser_ck":     self.ser_ck.get()
                    },
                    "test": {
                        "dac_inj_level": self.dac_inj_level.get(),
                        "delay_events":  self.delay_events.get()
                    },
                    "slow_ctrl": {
                        "csa_mode_n": self.csa_mode_n.get(),
                        "inj_en_n":   self.inj_en_n.get(),
                        "shap_mode":  self.shap_mode.get(),
                        "ch_en":      self.ch_en.get(),
                        "inj_mode_n": self.inj_mode_n.get()
                    },
                    "pixel_sel": {
                        "pixel_row": self.pixel_row.get(),
                        "pixel_col": self.pixel_col.get()
                    },
                    "asic_ctrl": {
                        "slow_ctrl_reset_n": {
                            "delay":  self.slow_ctrl_reset_n["delay"].get(),
                            "period": self.slow_ctrl_reset_n["period"].get(),
                            "width":  self.slow_ctrl_reset_n["width"].get()
                        },
                        "sel_init_n": {
                            "delay":  self.sel_init_n["delay"].get(),
                            "period": self.sel_init_n["period"].get(),
                            "width":  self.sel_init_n["width"].get()
                        },
                        "csa_reset_n": {
                            "delay":  self.csa_reset_n["delay"].get(),
                            "period": self.csa_reset_n["period"].get(),
                            "width":  self.csa_reset_n["width"].get()
                        },
                        "sh_phi1d_inf": {
                            "delay":  self.sh_phi1d_inf["delay"].get(),
                            "period": self.sh_phi1d_inf["period"].get(),
                            "width":  self.sh_phi1d_inf["width"].get()
                        },
                        "sh_phi1d_sup": {
                            "delay":  self.sh_phi1d_sup["delay"].get(),
                            "period": self.sh_phi1d_sup["period"].get(),
                            "width":  self.sh_phi1d_sup["width"].get()
                        },
                        "adc_start": {
                            "delay":  self.adc_start["delay"].get(),
                            "period": self.adc_start["period"].get(),
                            "width":  self.adc_start["width"].get()
                        },
                        "ser_reset_n": {
                            "delay":  self.ser_reset_n["delay"].get(),
                            "period": self.ser_reset_n["period"].get(),
                            "width":  self.ser_reset_n["width"].get()
                        },
                        "ser_read": {
                            "delay":  self.ser_read["delay"].get(),
                            "period": self.ser_read["period"].get(),
                            "width":  self.ser_read["width"].get()
                        }
                    }
                }
        # === END JSON DEFINITION ===

# === MAIN LOOP ===
# Start GUI window
root = Tk()
root.title("pFREYA tester v0 - Manual testing")
gui = pFREYA_GUI()

# Build the GUI
main_frame = ttk.Frame(root, padding=10)
main_frame.pack()

# Menu
menubar = Menu(root)
root['menu'] = menubar
menu_config = Menu(menubar, tearoff=0)
menu_config.add_command(label='Load configuration file', command=lambda: load_config)
menu_config.add_command(label='Save configuration file', command=lambda: save_config(gui))
menubar.add_cascade(menu=menu_config, label='Config')
menubar.add_command(label='About', command=lambda: show_about)

# Clock configuration
ck_lframe = ttk.Labelframe(main_frame, text="Clocks configuration", padding=10, width=200, height=100)
ck_lframe.grid(column=0, row=0, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(ck_lframe, text="Slow control clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.slow_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ck_lframe, text="Selection row clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.sel_row_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ck_lframe, text="Selection col clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.sel_col_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ck_lframe, text="ADC clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.adc_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ck_lframe, text="INJ DAC clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.dac_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ck_lframe, text="Serialiser clock:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ck_lframe, textvariable=gui.ser_ck, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="kHz").grid(column=2, row=row_idx)
row_idx += 1
ttk.Button(ck_lframe, text="Set clocks").grid(column=1, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# Slow ctrl configuration
sc_lframe = ttk.Labelframe(main_frame, text="Slow control configuration", padding=10, width=200, height=100)
sc_lframe.grid(column=1, row=0, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(sc_lframe, text="CSA_MODE_N:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(sc_lframe, textvariable=gui.csa_mode_n, width=2).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="INJ_EN_N:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(sc_lframe, textvariable=gui.inj_en_n, width=1).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="SHAP_MODE:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(sc_lframe, textvariable=gui.shap_mode, width=2).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="CH_EN:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(sc_lframe, textvariable=gui.ch_en, width=1).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="INJ_MODE_N:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(sc_lframe, textvariable=gui.inj_mode_n, width=1).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Button(sc_lframe, text="Set slow ctrl").grid(column=1, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)
row_idx += 1
ttk.Button(sc_lframe, text="Send slow ctrl").grid(column=1, columnspan=2, row=row_idx, pady=[0,0], sticky=SE)

# Test setup configuration
ts_lframe = ttk.Labelframe(main_frame, text="Test setup configuration", padding=10, width=200, height=100)
ts_lframe.grid(column=2, row=0, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(ts_lframe, text="DAC injection level:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ts_lframe, textvariable=gui.dac_inj_level, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ts_lframe, text="BOH").grid(column=2, row=row_idx)
row_idx += 1
ttk.Label(ts_lframe, text="Delay between events:").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ts_lframe, textvariable=gui.delay_events, width=6).grid(column=1, row=row_idx, padx=5)
ttk.Label(ts_lframe, text="kHz").grid(column=2, row=row_idx)

# Pixel selection
ps_lframe = ttk.Labelframe(main_frame, text="Pixel selection", padding=10, width=200, height=100)
ps_lframe.grid(column=4, row=0, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(ps_lframe, text="Row (from bottom):").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ps_lframe, textvariable=gui.pixel_row, width=1).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(ps_lframe, text="Column (from right):").grid(column=0, row=row_idx, sticky=E)
ttk.Entry(ps_lframe, textvariable=gui.pixel_col, width=1).grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Button(ps_lframe, text="Set pixel sel").grid(column=1, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# ASIC power up control
asic_lframe = ttk.Labelframe(main_frame, text="ASIC power up control", padding=10, width=200, height=100)
asic_lframe.grid(column=0, row=2, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(asic_lframe, text="Slow control reset (_N in the ASIC)", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
ttk.Label(asic_lframe, text="Set by FPGA based on slow ctrl packet").grid(column=1, columnspan=5, row=row_idx, sticky=W)

row_idx += 1
ttk.Label(asic_lframe, text="Select init (_N in the ASIC)", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
ttk.Label(asic_lframe, text="Set by FPGA based on number of row and col packet").grid(column=1, columnspan=5, row=row_idx, sticky=W)

# row_idx += 1
# ttk.Button(asic_lframe, text="Send ASIC power up config").grid(column=6, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# ASIC transient control
asic_lframe = ttk.Labelframe(main_frame, text="ASIC transient control", padding=10, width=200, height=100)
asic_lframe.grid(column=0, row=3, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(asic_lframe, text="CSA reset (_N in the ASIC)", width=33).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["delay"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Label(asic_lframe, text="S/H phases", width=33).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="INF:").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx+1, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["delay"], width=6).grid(column=col_idx+2, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+3, row=row_idx, padx=[0,20])
col_idx += 4
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="SUP:").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx+1, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["delay"], width=6).grid(column=col_idx+2, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+3, row=row_idx, padx=[0,20])
col_idx += 4
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Label(asic_lframe, text="ADC start", width=33).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.adc_start["delay"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.adc_start["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.adc_start["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

# ASIC serialiser control
asic_lframe = ttk.Labelframe(main_frame, text="ASIC serialiser control", padding=10, width=200, height=100)
asic_lframe.grid(column=0, row=4, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(asic_lframe, text="Serialiser reset (_N in the ASIC)", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_reset_n["delay"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_reset_n["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_reset_n["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Label(asic_lframe, text="Serialiser read", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_read["delay"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Period").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_read["period"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Width").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.ser_read["width"], width=6).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="ns").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Button(asic_lframe, text="Start test").grid(column=6, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

root.mainloop()