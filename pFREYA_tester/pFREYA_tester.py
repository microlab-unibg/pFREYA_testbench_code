from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from serial import *
import subprocess
import json
import serial
import pFREYA_tester_processing as pYtp
import UART_definitions as UARTdef

import pyvisa
import time

# === CONSTANTS ===
# The other constants have been moved to the config file
FPGA_COM_DEF = "XILINX"

# === GUI FUNCTIONS ===
def to_json_CSA(): #parametri fissi per caso 1
    use_autocsa = False
    return{
        "pFREYA_GUI__": True,
        "clocks":{
            "slow_ck": '40',
            "sel_ck": '262143',
            "adc_ck": '262143',
            "inj_stb": '1', 
            "ser_ck": '262143', 
            "dac_sck": '262143' 
        }, 
        "INJ": { 
            "current_level": '-0.8'
        },
        "slow_ctrl": { 
            "csa_mode_n": '10', 
            "inj_en_n": '1', 
            "shap_mode": '10', 
            "ch_en": '1', 
            "inj_mode_n": '1' 
        }, 
        "pixel_sel": { 
            "pixel_row": '3', 
            "pixel_col": '1' 
        }, 
        "asic_ctrl": {
            "csa_reset_n": {
                "delay":  '1',
                "high": '60',
                "low": '4000' 
            }
        }

    }
def reset_iniziale():
    pYtp.send_reset_FPGA()
def auto_clock():
    pYtp.send_clocks(gui)
def auto_csa_reset():
    pYtp.send_CSA_RESET_N(gui)
def auto_slwctrl():
    pYtp.send_slow_ctrl(gui)

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

def on_canvas_configure(event):
    # Update the scroll region to match the content in the frame
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_mouse_scroll(event):
    # Enable scrolling using the mouse wheel
    canvas.yview_scroll(-1 * (event.delta // 120), "units")

def check_fpga_clocks(strvar):
    value = strvar.get()
    if (not value.isnumeric()):
        messagebox.showerror('FPGA Period Error', f'FPGA Period must be a number between 1 and {2**UARTdef.DATA_PACKET_LENGTH-1}.')
    elif (int(value) < 1 or int(value) > 2**UARTdef.DATA_PACKET_LENGTH-1):
        messagebox.showerror('FPGA Period Error', f'FPGA Period must be between 1 and {2**UARTdef.DATA_PACKET_LENGTH-1}.')

def check_dac_level(strvar):
    value = strvar.get()
    if (not value.isnumeric()):
        messagebox.showerror('DAC Level Error', f'DAC must be a number between 0 and {2**UARTdef.DAC_BITS-1}.')
    elif (int(value) < 0 or int(value) > 2**UARTdef.DAC_BITS-1):
        messagebox.showerror('DAC Level Error', f'DAC must be between 0 and {2**UARTdef.DAC_BITS-1}.')

def check_current_level(strvar):
    value = strvar.get()
    try:
        float(value)
    except:
        messagebox.showerror('Current Level Error', f'Current level must be a number between {UARTdef.CURRENT_LEVEL_MIN} and {UARTdef.CURRENT_LEVEL_MAX}.')
    
    if (float(value) < UARTdef.CURRENT_LEVEL_MIN or float(value) > UARTdef.CURRENT_LEVEL_MAX):
        messagebox.showerror('Current Level Error', f'Current level must be between {UARTdef.CURRENT_LEVEL_MIN} and {UARTdef.CURRENT_LEVEL_MAX}.')

def check_pixel(strvar,type):
    value = strvar.get()
    if (not value.isnumeric()):
        messagebox.showerror('FPGA Pixel Error', f'Pixel row or col must be a number (0-7, 0-1).')
    if (type == "row"):
        if (int(value) < 0 or int(value) > 7):
            messagebox.showerror('FPGA Pixel Error', f'Pixel row must be a number (0-7).')
    else:
        if (int(value) < 0 or int(value) > 1):
            messagebox.showerror('FPGA Pixel Error', f'Pixel col must be a number (0-1).')

def check_pixel_to_inj(strvar):
    value = strvar.get()
    if "," not in value:
        values = list(value)
    else:
        values = value.split(",")
    for v in values:
        if (not v.isnumeric()):
            messagebox.showerror('FPGA Pixel to Inj Error', f'Pixel to inject must be a number (0-{UARTdef.PIXEL_N-1}).')
        elif (int(v) < 0 or int(v) > UARTdef.PIXEL_N-1):
            messagebox.showerror('FPGA Pixel to Inj Error', f'Pixel to inject must be a number (0-{UARTdef.PIXEL_N-1}).')

def check_slow_ctrl(strvar,n_bit_expected):
    value = strvar.get()
    if (n_bit_expected != len(value)):
        messagebox.showerror('FPGA Slow Ctrl Error', f'Slow control bits have a specific length to be respected. In this case {n_bit_expected}.')
    elif (value not in ('0','1','00','01','10','11')):
        messagebox.showerror('FPGA Slow Ctrl Error', f'Slow control bits are binary (0 or 1).')
# === GUI CLASS ===
class pFREYA_GUI():
    """Class representing the GUI
    """
    def __init__(self, root):
        """Init that sets defaults and load GUI StringVars
        """
        self.root=root
        # Retrieve config
        json_config = load_config()
        # clocks
        self.slow_ck = StringVar(value=json_config.get("clocks","").get("slow_ck",""))
        self.sel_ck = StringVar(value=json_config.get("clocks","").get("sel_ck",""))
        self.adc_ck = StringVar(value=json_config.get("clocks","").get("adc_ck",""))
        self.inj_stb = StringVar(value=json_config.get("clocks","").get("inj_stb",""))
        self.ser_ck = StringVar(value=json_config.get("clocks","").get("ser_ck",""))
        self.dac_sck = StringVar(value=json_config.get("clocks","").get("dac_sck",""))

        self.clock_map = {
            UARTdef.SLOW_CTRL_CK_CODE : self.slow_ck,
            UARTdef.SEL_CK_CODE       : self.sel_ck,
            UARTdef.ADC_CK_CODE       : self.adc_ck,
            UARTdef.INJ_STB_CODE      : self.inj_stb,
            UARTdef.SER_CK_CODE       : self.ser_ck,
            UARTdef.DAC_SCK_CODE      : self.dac_sck
        }

        # DAC config
        self.dac = {}
        self.dac["source"] = StringVar(value=json_config.get("DAC","").get("source",""))
        self.dac["divider"] = StringVar(value=json_config.get("DAC","").get("divider",""))
        self.dac["gain"] = StringVar(value=json_config.get("DAC","").get("gain",""))
        self.dac["level"] = StringVar(value=json_config.get("DAC","").get("level",""))

        # INJ config
        self.current_level = StringVar(value=json_config.get("INJ","").get("current_level",""))

        # slow control
        self.csa_mode_n = StringVar(value=json_config.get("slow_ctrl","").get("csa_mode_n",""))
        self.inj_en_n = StringVar(value=json_config.get("slow_ctrl","").get("inj_en_n",""))
        self.shap_mode = StringVar(value=json_config.get("slow_ctrl","").get("shap_mode",""))
        self.ch_en = StringVar(value=json_config.get("slow_ctrl","").get("ch_en",""))
        self.inj_mode_n = StringVar(value=json_config.get("slow_ctrl","").get("inj_mode_n",""))
        self.pixel_to_inj = StringVar(value=json_config.get("slow_ctrl","").get("pixel_to_inj",""))

        # pixel selection
        self.pixel_row = StringVar(value=json_config.get("pixel_sel","").get("pixel_row",""))
        self.pixel_col = StringVar(value=json_config.get("pixel_sel","").get("pixel_col",""))

        # ASIC transient control
        self.csa_reset_n = {}
        self.csa_reset_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("delay",""))
        self.csa_reset_n["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("high",""))
        self.csa_reset_n["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("csa_reset_n","").get("low",""))
        
        self.sh_phi1d_inf = {}
        self.sh_phi1d_inf["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("delay",""))
        self.sh_phi1d_inf["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("high",""))
        self.sh_phi1d_inf["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_inf","").get("low",""))
        
        self.sh_phi1d_sup = {}
        self.sh_phi1d_sup["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("delay",""))
        self.sh_phi1d_sup["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("high",""))
        self.sh_phi1d_sup["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("sh_phi1d_sup","").get("low",""))
        
        self.adc_start = {}
        self.adc_start["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("delay",""))
        self.adc_start["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("high",""))
        self.adc_start["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("adc_start","").get("low",""))

        # ASIC serialiser control
        self.ser_reset_n = {}
        self.ser_reset_n["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("delay",""))
        self.ser_reset_n["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("high",""))
        self.ser_reset_n["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_reset_n","").get("low",""))

        self.ser_read = {}
        self.ser_read["delay"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("delay",""))
        self.ser_read["high"] = \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("high",""))
        self.ser_read["low"]= \
            StringVar(value=json_config.get("asic_ctrl","").get("ser_read","").get("low",""))
        
        # GUI control
        self.slow_ck_sent = False
        self.sel_ck_sent = False
        self.dac_sck_sent = False

        # power source
        self.rm = pyvisa.ResourceManager()
        print(self.rm.list_resources())

    def to_json(self):
        use_autocsa = False
        # === START JSON DEFINITION ===
        return {
                    "__pFREYA_GUI__": True,
                    "clocks": {
                        "slow_ck":    self.slow_ck.get(),
                        "sel_ck":     self.sel_ck.get(),
                        "adc_ck":     self.adc_ck.get(),
                        "inj_stb":    self.inj_stb.get(),
                        "ser_ck":     self.ser_ck.get(),
                        "dac_sck":     self.dac_sck.get()
                    },
                    "DAC": {
                        "source": self.dac["source"].get(),
                        "divider": self.dac["divider"].get(),
                        "gain": self.dac["gain"].get(),
                        "level": self.dac["level"].get()
                    },
                    "INJ": {
                        "current_level": self.current_level.get()
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
                        "csa_reset_n": {
                            "delay":  self.csa_reset_n["delay"].get(),
                            "high": self.csa_reset_n["high"].get(),
                            "low":  self.csa_reset_n["low"].get()
                        },
                        "sh_phi1d_inf": {
                            "delay":  self.sh_phi1d_inf["delay"].get(),
                            "high": self.sh_phi1d_inf["high"].get(),
                            "low":  self.sh_phi1d_inf["low"].get()
                        },
                        "sh_phi1d_sup": {
                            "delay":  self.sh_phi1d_sup["delay"].get(),
                            "high": self.sh_phi1d_sup["high"].get(),
                            "low":  self.sh_phi1d_sup["low"].get()
                        },
                        "adc_start": {
                            "delay":  self.adc_start["delay"].get(),
                            "high": self.adc_start["high"].get(),
                            "low":  self.adc_start["low"].get()
                        },
                        "ser_reset_n": {
                            "delay":  self.ser_reset_n["delay"].get(),
                            "high": self.ser_reset_n["high"].get(),
                            "low":  self.ser_reset_n["low"].get()
                        },
                        "ser_read": {
                            "delay":  self.ser_read["delay"].get(),
                            "high": self.ser_read["high"].get(),
                            "low":  self.ser_read["low"].get()
                        }
                    }
                }
        # === END JSON DEFINITION ===

# === MAIN LOOP ===
#Metodo per decidere quale JSON utilizzare 
def get_json(self, use_csa=False): 
    if use_csa: 
        return self.to_json_CSA() 
    else: 
        return self.to_json()

#seconda gui
def run_script_csa():
    print("\n--- RUNNING SCRIPT CSA---")  
    
    print("\n--Reset FPGA--")
    reset_iniziale()
    time.sleep(2)

    print("\n--start clk--")
    auto_clock()
    time.sleep(2)
    print("--end clk\n")

    print("--start csa_reset_n--")
    auto_csa_reset()
    print("--end csa_reset_n\n")
    time.sleep(3)

    print("--TRANSIENT CSA START\n")
    subprocess.run(["python", "transient_auto_csa.py"]) #metodo transient csa
    print("--TRANSIENT CSA END--")
    time.sleep(0.5)
    
    print("\n--Reset FPGA--")
    reset_iniziale()
    time.sleep(2)

    print("\n--start clk--")
    auto_clock()
    time.sleep(2)
    print("--end clk--")

    print("--start csa_reset_n--")
    auto_csa_reset()
    print("--end csa_reset_n\n")
    time.sleep(3)

    print("--TRANCHARACTERISTICS CSA START--")
    subprocess.run(["python", "transcharacteristics_auto_csa.py"]) #metodo transcharacteristics csa
    print("--TRANCHARACTERISTICS CSA END--")
    print("\n---SCRIPT CSA ENDED---\n")  

def run_script_shap():
    print("\n--- RUNNING SCRIPT SHAPER---")

    print("\n--Reset FPGA--")
    reset_iniziale()
    time.sleep(2)

    print("\n--start clk--")
    auto_clock()
    time.sleep(2)
    print("--end clk--")

    print("--start csa_reset_n--")
    auto_csa_reset()
    print("--end csa_reset_n\n")
    time.sleep(3)

    #metodo transient shap
    print("--TRANSIENT SHAP START--\n")
    subprocess.run(["python", "transient_auto_shap.py"]) #metodo transient csa
    print("\nTRANSIENT SHAP END")
  
    print("\n--Reset FPGA--")
    reset_iniziale()
    time.sleep(2)

    print("\n--start clk--")
    auto_clock()
    time.sleep(2)
    print("--end clk--")

    print("--start csa_reset_n--")
    auto_csa_reset()
    print("--end csa_reset_n\n")
    time.sleep(3)

    print("TRANCHARACTERISTICS SHAP START--\n")
    subprocess.run(["python", "transcharacteristics_auto_shap.py"]) #metodo transcharacteristics csa
    print("\n--TRANCHARACTERISTICS SHAP END--")
    print("\n---SCRIPT SHAP ENDED---\n") 

def run_script_enc():
    print("\n---RUNNING SCRIPT ENC---") 
        
    print("\n--Reset FPGA--")
    reset_iniziale()
    time.sleep(2)

    print("\n--start clk--")
    auto_clock()
    time.sleep(2)
    print("--end clk--")

    print("--start csa_reset_n--")
    auto_csa_reset()
    print("--end csa_reset_n\n")
    time.sleep(3)

    #metodo enc
    print("--ENC START--\n")
    subprocess.run(["python", "auto_enc.py"])
    print("\n--ENC END--")

class gui2(Toplevel):
  def __init__(self,parent):
    super().__init__(parent)
    self.title("pFREYA tester v0 - Automatic testing")
    self.geometry("420x175")
    self.resizable(False, False)
    
    frame = Frame(self)
    frame.pack(pady=10)

    label1 =Label(frame, text="csa")
    label1.grid(row=0, column=0, padx=10, pady=10)
    button1 = Button(frame, text="run", command=run_script_csa)
    button1.grid(row=0, column=1, padx=10, pady=10)

    label2 = Label(frame, text="shap")
    label2.grid(row=1, column=0, padx=10, pady=10)
    button2 = Button(frame, text="run", command=run_script_shap)
    button2.grid(row=1, column=1, padx=10, pady=10)

    label3 = Label(frame, text="enc")
    label3.grid(row=2, column=0, padx=10, pady=10)
    button3 = Button(frame, text="run", command=run_script_enc)
    button3.grid(row=2, column=1, padx=10, pady=10)

    self.mainloop()

def open_child():
    print("opening gui2")
    child=gui2(root)

# Start GUI window
root = Tk()
root.title("pFREYA tester v1 - Manual/Auto testing")
root.geometry("1200x800+0+0")
gui = pFREYA_GUI(root)

# Scrollbar
canvas = Canvas(root, highlightthickness=0)
canvas.pack(side=LEFT, fill=BOTH, expand=True)

# Create a vertical scrollbar linked to the canvas
scrollbar = ttk.Scrollbar(root, orient=VERTICAL, command=canvas.yview)
scrollbar.pack(side=RIGHT, fill=Y)
canvas.configure(yscrollcommand=scrollbar.set)

# Build the GUI
main_frame = ttk.Frame(canvas, padding=10)
canvas.create_window((0, 0), window=main_frame, anchor="nw")

# Menu
menubar = Menu(root)
root['menu'] = menubar
menu_config = Menu(menubar, tearoff=0)
menu_config.add_command(label='Load configuration file', command= load_config)
menu_config.add_command(label='Save configuration file', command= lambda: save_config(gui))
menubar.add_cascade(menu=menu_config, label='Config')
menubar.add_command(label='About', command= show_about)

# Clock configuration
row_idx = 0
ttk.Label(main_frame, text="FPGA Clock period = 5 ns (200 MHz). Only rising edge is available so unit of time FP = 10 ns (100 MHz).", width=90).grid(column=0, columnspan=3, row=row_idx, sticky=NW)

ck_lframe = ttk.Labelframe(main_frame, text="Clocks configuration", padding=10, width=200, height=100)
ck_lframe.grid(column=0, row=0, padx=5, pady=30, sticky=NSEW)
row_idx += 1
ttk.Label(ck_lframe, text="Slow control clock:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.slow_ck, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.slow_ck))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.SLOW_CTRL_CK_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Label(ck_lframe, text="Selection clock:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.sel_ck, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks (gui.sel_ck))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.SEL_CK_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Label(ck_lframe, text="ADC clock:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.adc_ck, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks (gui.adc_ck))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.ADC_CK_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Label(ck_lframe, text="INJ strobe:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.inj_stb, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks (gui.inj_stb))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.INJ_STB_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Label(ck_lframe, text="Serialiser clock:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.ser_ck, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks (gui.ser_ck))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.SER_CK_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Label(ck_lframe, text="DAC SPI clock:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ck_lframe, textvariable=gui.dac_sck, width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks (gui.dac_sck))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ck_lframe, text="FP").grid(column=2, row=row_idx)
ttk.Button(ck_lframe, text="Send", command=lambda: pYtp.send_clock_single(gui,UARTdef.DAC_SCK_CODE)).grid(column=3, columnspan=1, row=row_idx, pady=[0,0], sticky=EW)
row_idx += 1
ttk.Button(ck_lframe, text="Send clocks", command=lambda: pYtp.send_clocks(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# Slow ctrl configuration
sc_lframe = ttk.Labelframe(main_frame, text="Slow control configuration", padding=10, width=200, height=100)
sc_lframe.grid(column=1, row=0, padx=5, pady=30, sticky=NSEW)
row_idx = 0
ttk.Label(sc_lframe, text="CSA_MODE_N:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(sc_lframe, textvariable=gui.csa_mode_n, width=2)
current_entry.bind("<FocusOut>", lambda x: check_slow_ctrl(gui.csa_mode_n,2))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
current_label = ttk.Label(sc_lframe, text="INJ_EN_N:")
current_label.grid(column=0, row=row_idx, sticky=E)
current_label.configure(state='disable')
current_entry = ttk.Entry(sc_lframe, textvariable=gui.inj_en_n, width=1)
current_entry.bind("<FocusOut>", lambda x: check_slow_ctrl(gui.inj_en_n,1))
current_entry.grid(column=1, row=row_idx, padx=5)
current_entry.configure(state='disable')
row_idx += 1
ttk.Label(sc_lframe, text="SHAP_MODE:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(sc_lframe, textvariable=gui.shap_mode, width=2)
current_entry.bind("<FocusOut>", lambda x: check_slow_ctrl(gui.shap_mode,2))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="CH_EN:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(sc_lframe, textvariable=gui.ch_en, width=1)
current_entry.bind("<FocusOut>", lambda x: check_slow_ctrl(gui.ch_en,1))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="INJ_MODE_N:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(sc_lframe, textvariable=gui.inj_mode_n, width=1)
current_entry.bind("<FocusOut>", lambda x: check_slow_ctrl(gui.inj_mode_n,1))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(sc_lframe, text="Pixel to inject:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(sc_lframe, textvariable=gui.pixel_to_inj, width=4)
current_entry.bind("<FocusOut>", lambda x: check_pixel_to_inj(gui.pixel_to_inj))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Button(sc_lframe, text="Send slow ctrl", command=lambda: pYtp.send_slow_ctrl(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)
ttk.Button(sc_lframe, text="Auto", command=open_child).grid(column=0, columnspan=1, row=row_idx, pady=[10,0], sticky=SE)
# # DAC configuration
# ts_lframe = ttk.Labelframe(main_frame, text="DAC configuration", padding=10, width=200, height=100)
# ts_lframe.grid(column=2, row=0, padx=5, pady=30, sticky=NSEW)
# row_idx = 0
# col_idx = 0
# ttk.Label(ts_lframe, text="VREF source:").grid(column=col_idx, row=row_idx, sticky=W)
# ttk.Radiobutton(ts_lframe, text="EXT", variable=gui.dac["source"], value=UARTdef.DAC_DATA_CONFIG_REF_EXT).grid(column=col_idx+1, row=row_idx, pady=5, padx=5)
# ttk.Radiobutton(ts_lframe, text="INT", variable=gui.dac["source"], value=UARTdef.DAC_DATA_CONFIG_REF_INT).grid(column=col_idx+2, row=row_idx, pady=5, padx=5)
# row_idx += 1
# ttk.Label(ts_lframe, text="VREF divider:").grid(column=col_idx, row=row_idx, sticky=W)
# ttk.Radiobutton(ts_lframe, text="1", variable=gui.dac["divider"], value=UARTdef.DAC_DATA_GAIN_DIV1).grid(column=col_idx+1, row=row_idx, pady=5, padx=5)
# ttk.Radiobutton(ts_lframe, text="2", variable=gui.dac["divider"], value=UARTdef.DAC_DATA_GAIN_DIV2).grid(column=col_idx+2, row=row_idx, pady=5, padx=5)
# row_idx += 1
# ttk.Label(ts_lframe, text="VREF gain:").grid(column=col_idx, row=row_idx, sticky=W)
# ttk.Radiobutton(ts_lframe, text="1", variable=gui.dac["gain"], value=UARTdef.DAC_DATA_GAIN_BUF1).grid(column=col_idx+1, row=row_idx, pady=5, padx=5)
# ttk.Radiobutton(ts_lframe, text="2", variable=gui.dac["gain"], value=UARTdef.DAC_DATA_GAIN_BUF2).grid(column=col_idx+2, row=row_idx, pady=5, padx=5)
# row_idx += 1
# ttk.Label(ts_lframe, text="DAC level:").grid(column=col_idx, row=row_idx, sticky=W)
# current_entry = ttk.Entry(ts_lframe, textvariable=gui.dac["level"], width=4)
# current_entry.bind("<FocusOut>", lambda x: check_dac_level(gui.dac["level"]))
# current_entry.grid(column=1, row=row_idx, padx=5)
# row_idx += 1
# ttk.Button(ts_lframe, text="Send DAC", command=lambda: pYtp.send_DAC(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[20,0], sticky=SE)

# Current level config power source
ts_lframe = ttk.Labelframe(main_frame, text="INJ configuration", padding=10, width=200, height=100)
ts_lframe.grid(column=2, row=0, padx=5, pady=30, sticky=NSEW)
row_idx = 0
ttk.Label(ts_lframe, text="Current level:").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ts_lframe, textvariable=gui.current_level, width=8)
current_entry.bind("<FocusOut>", lambda x: check_current_level(gui.current_level))
current_entry.grid(column=1, row=row_idx, padx=5)
ttk.Label(ts_lframe, text="uA").grid(column=2, row=row_idx, sticky=E)
row_idx += 1
ttk.Button(ts_lframe, text="Send INJ", command=lambda: pYtp.send_current_level(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[115,0], sticky=SE)



# Pixel selection
ps_lframe = ttk.Labelframe(main_frame, text="Pixel selection", padding=10, width=200, height=100)
ps_lframe.grid(column=4, row=0, padx=5, pady=30, sticky=NSEW)
row_idx = 0
ttk.Label(ps_lframe, text="Row (from bottom):").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ps_lframe, textvariable=gui.pixel_row, width=1)
current_entry.bind("<FocusOut>", lambda x: check_pixel(gui.pixel_row,'row'))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Label(ps_lframe, text="Column (from right):").grid(column=0, row=row_idx, sticky=E)
current_entry = ttk.Entry(ps_lframe, textvariable=gui.pixel_col, width=1)
current_entry.bind("<FocusOut>", lambda x: check_pixel(gui.pixel_col,'col'))
current_entry.grid(column=1, row=row_idx, padx=5)
row_idx += 1
ttk.Button(ps_lframe, text="Send pixel sel", command=lambda: pYtp.send_pixel(gui)).grid(column=1, columnspan=2, row=row_idx, pady=[95,0], sticky=SE)

# ASIC power up control
asic_lframe = ttk.Labelframe(main_frame, text="ASIC power up control", padding=10, width=200, height=100)
asic_lframe.grid(column=0, row=2, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(asic_lframe, text="SLOW_CTRL_RESET_N", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
ttk.Label(asic_lframe, text="Set by FPGA based on slow ctrl packet").grid(column=1, columnspan=5, row=row_idx, sticky=W)

row_idx += 1
ttk.Label(asic_lframe, text="SEL_INIT_N", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
ttk.Label(asic_lframe, text="Set by FPGA based on number of row and col packet").grid(column=1, columnspan=5, row=row_idx, sticky=W)

# row_idx += 1
# ttk.Button(asic_lframe, text="Send ASIC power up config").grid(column=6, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# ASIC transient control
asic_lframe = ttk.Labelframe(main_frame, text="ASIC transient control", padding=10, width=200, height=100)
asic_lframe.grid(column=0, row=3, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(asic_lframe, text="CSA_RESET_N", width=15).grid(column=0, row=row_idx, sticky=W)
row_idx += 0
col_idx = 1
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["delay"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.csa_reset_n["delay"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["high"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.csa_reset_n["high"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.csa_reset_n["low"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.csa_reset_n["low"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Button(asic_lframe, text="Send CSA_RESET_N", command=lambda: pYtp.send_CSA_RESET_N(gui)).grid(column=col_idx, columnspan=3, row=row_idx, pady=[0,0], sticky=EW)

row_idx += 1
ttk.Label(asic_lframe, text="S/H phases", width=15).grid(column=0, row=row_idx, sticky=W)
row_idx += 1
col_idx = 1
ttk.Label(asic_lframe, text="INF: Delay").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["delay"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_inf["delay"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=(1.3,0))
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["high"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_inf["high"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_inf["low"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_inf["low"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Button(asic_lframe, text="Send SH_PHI1D_INF", command=lambda: pYtp.send_SH_PHI1D_INF(gui)).grid(column=col_idx, columnspan=3, row=row_idx, pady=[0,0], sticky=EW)

row_idx += 1
col_idx = 1
ttk.Label(asic_lframe, text="SUP: Delay").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["delay"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_sup["delay"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=(1.3,0))
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["high"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_sup["high"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.sh_phi1d_sup["low"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.sh_phi1d_sup["low"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Button(asic_lframe, text="Send SH_PHI1D_SUP", command=lambda: pYtp.send_SH_PHI1D_SUP(gui)).grid(column=col_idx, columnspan=3, row=row_idx, pady=[0,0], sticky=EW)

row_idx += 1
ttk.Label(asic_lframe, text="ADC_START", width=15).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 0
col_idx = 1
ttk.Label(asic_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.adc_start["delay"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.adc_start["delay"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=(1.3,0))
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(asic_lframe, textvariable=gui.adc_start["high"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.adc_start["high"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.adc_start["high"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(asic_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
current_entry = ttk.Entry(asic_lframe, textvariable=gui.adc_start["low"], width=UARTdef.WIDTH_ENTRY)
current_entry.bind("<FocusOut>", lambda x: check_fpga_clocks(gui.adc_start["low"]))
current_entry.grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(asic_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Button(asic_lframe, text="Send ADC_START", command=lambda: pYtp.send_ADC_START(gui)).grid(column=col_idx, columnspan=3, row=row_idx, pady=[0,0], sticky=EW)

row_idx += 1
ttk.Button(asic_lframe, text="Send ASIC control", command=lambda: pYtp.send_asic_ctrl(gui)).grid(column=4, columnspan=5, row=row_idx, pady=[10,0], sticky=SE)

# ASIC serialiser control
ser_lframe = ttk.Labelframe(main_frame, text="ASIC serialiser control", padding=10, width=200, height=100)
ser_lframe.grid(column=0, row=4, columnspan=5, padx=5, sticky=NSEW)
row_idx = 0
ttk.Label(ser_lframe, text="SER_RESET_N", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(ser_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_reset_n["delay"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(ser_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_reset_n["high"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(ser_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_reset_n["low"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Label(ser_lframe, text="SER_READ", width=30).grid(column=0, columnspan=3, row=row_idx, sticky=W)
row_idx += 1
col_idx = 0
ttk.Label(ser_lframe, text="Delay").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_read["delay"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(ser_lframe, text="High").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_read["high"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3
ttk.Label(ser_lframe, text="Low").grid(column=col_idx, row=row_idx, sticky=E)
ttk.Entry(ser_lframe, textvariable=gui.ser_read["low"], width=UARTdef.WIDTH_ENTRY).grid(column=col_idx+1, row=row_idx, padx=5)
ttk.Label(ser_lframe, text="FP").grid(column=col_idx+2, row=row_idx, padx=[0,20])
col_idx += 3

row_idx += 1
ttk.Button(ser_lframe, text="Send serial").grid(column=6, columnspan=2, row=row_idx, pady=[10,0], sticky=SE)

# disable last frame
for child in ser_lframe.winfo_children():
   child.configure(state='disable')

ser_lframe = ttk.Labelframe(main_frame, text="Special FPGA controls", padding=10, width=200, height=10)
ser_lframe.grid(column=0, row=5, columnspan=5, padx=5, sticky=NSEW)
ttk.Button(ser_lframe, text="Sync signals", command=lambda: pYtp.send_sync_time_bases()).grid(column=0, row=0, sticky=SE)
ttk.Button(ser_lframe, text="Reset FPGA", command=lambda: pYtp.send_reset_FPGA()).grid(column=1, row=0, sticky=SE)
ttk.Button(ser_lframe, text="Upload bitstream", command=lambda: pYtp.upload_bitstream()).grid(column=2, row=0, sticky=SE)

# Bind events to update the canvas scroll region and enable mouse scrolling
main_frame.bind("<Configure>", on_canvas_configure)
canvas.bind_all("<MouseWheel>", on_mouse_scroll)

root.mainloop()



