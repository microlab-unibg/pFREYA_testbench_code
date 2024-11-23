'''
import tkinter as tk
import subprocess
import time
import sys
import os
from tkinter import Toplevel, Label, Button



def run_script_csa():
  print("Reset FPGA")
  g1.reset_iniziale()
  time.sleep(2)

  print("json")
  g1.to_json_CSA()
  time.sleep(2)

  print("clk")
  g1.auto_clock()
  time.sleep(2)
  
  print("slw")
  g1.auto_slwctrl()
  time.sleep(2)

  print("current")
  g1.auto_currentlvl()
  time.sleep(2)

  
  print("csa_reset_n")
  g1.auto_csa_reset()
  time.sleep(3)
  
  #metodo transient csa
  subprocess.run(["python", "transient_auto_csa.py"]) #metodo transient csa
  subprocess.run(["python", "transcharacteristics_auto_csa.py"]) #metodo transcharacteristics csa

def run_script_shap():
  #g1. richiama funzioni da pFREYA_tester.py 
  import pFREYA_tester as g1
  print("Reset FPGA")
  g1.reset_iniziale()
  time.sleep(2)

  print("json")
  g1.to_json_CSA()
  time.sleep(2)

  print("clk")
  g1.auto_clock()
  time.sleep(2)
  
  print("slw")
  g1.auto_slwctrl()
  time.sleep(2)

  print("current")
  g1.auto_currentlvl()
  time.sleep(2)

  
  print("csa_reset_n")
  g1.auto_csa_reset()
  time.sleep(3)
  
  #metodo transient csa
  subprocess.run(["python", "transient_auto_shap.py"]) #metodo transient csa
  subprocess.run(["python", "transcharacteristics_auto_shap.py"]) #metodo transcharacteristics csa

#metodo per shap(stessa cosa per per csa)
#transcharacteristics shap
#transient shap

#finestra gui 2
class gui2(tk.Toplevel):
  def __init__(self,parent):
    super().__init__(parent)
    self.title("pFREYA tester v0 - Automatic testing")
    self.geometry("400x120")
    self.resizable(False, False)
    
    frame = tk.Frame(self)
    frame.pack(pady=10)

    label1 = tk.Label(frame, text="csa")
    label1.grid(row=0, column=0, padx=10, pady=10)
    button1 = tk.Button(frame, text="run", command=run_script_csa)
    button1.grid(row=0, column=1, padx=10, pady=10)

    label2 = tk.Label(frame, text="shap")
    label2.grid(row=1, column=0, padx=10, pady=10)

    button2 = tk.Button(frame, text="run", command=run_script_shap)
    button2.grid(row=1, column=1, padx=10, pady=10)
    self.mainloop()
    '''