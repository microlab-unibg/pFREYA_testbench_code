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
  g1.reset_iniziale()
  print("Reset FPGA")
  time.sleep(2)

  g1.to_json_CSA()
  print("json ok")
  time.sleep(2)

  g1.auto_clock()
  print("clk ok")
  time.sleep(2)

  g1.auto_slwctrl()
  print("slw ok")
  time.sleep(2)

  g1.auto_currentlvl()
  print("current ok")
  time.sleep(2)

  g1.auto_send_pixel()
  print("pixel ok")
  time.sleep(2)
  
  g1.auto_csa_reset()
  
  #devo fare metodo per inviare corrente
  #subprocess.run(["python", "prova_transcharacteristics_auto.py"])
#metodo per shap

#finestra
def auto_slow_control():
    gui2 = tk.Tk()
    gui2.title("Test 1")
    gui2.geometry("400x120")
    gui2.resizable(False, False)

    frame = tk.Frame(gui2)
    frame.pack(pady=10)

    label1 = tk.Label(frame, text="Transcharacteristics csa")
    label1.grid(row=0, column=0, padx=10, pady=10)

    button1 = tk.Button(frame, text="Test CSA", command=run_script)
    button1.grid(row=0, column=1, padx=10, pady=10)

    label2 = tk.Label(frame, text="Transcharacteristics shap")
    label2.grid(row=1, column=0, padx=10, pady=10)

    button2 = tk.Button(frame, text="Test shap", command=lambda: print("Pulsante 2 premuto"))
    button2.grid(row=1, column=1, padx=10, pady=10)

    gui2.mainloop()





