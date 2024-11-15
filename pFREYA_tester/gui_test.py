import tkinter as tk
import subprocess
import time
import sys
import os
#from ..pFREYA_analysis import config
sys.path.append('..')
#from pFREYA_analysis import config
#from pFREYA_analysis import comms
import pFREYA_tester as g1

def run_script():
  #g1. richiama funzioni da pFREYA_tester.py 
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
  subprocess.run(["python", "prova_transient_auto.py"]) #metodo transient csa
  #subprocess.run(["python", "prova_transcharacteristics_auto.py"]) #metodo transcharacteristics csa
  

#metodo per shap(stessa cosa per per csa)
#transcharacteristics shap
#transient shap

#finestra gui 2
def open_gui2():
  gui2 = tk.Tk()
  gui2.title("pFREYA tester v0 - Automatic testing")
  gui2.geometry("400x120")
  gui2.resizable(False, False)

  frame = tk.Frame(gui2)
  frame.pack(pady=10)

  label1 = tk.Label(frame, text="csa")
  label1.grid(row=0, column=0, padx=10, pady=10)
  button1 = tk.Button(frame, text="run", command=run_script)
  button1.grid(row=0, column=1, padx=10, pady=10)

  label2 = tk.Label(frame, text="shap")
  label2.grid(row=1, column=0, padx=10, pady=10)

  button2 = tk.Button(frame, text="run", command=lambda: print("Pulsante 2 premuto"))
  button2.grid(row=1, column=1, padx=10, pady=10)
  gui2.mainloop()

