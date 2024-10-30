import tkinter as tk
import subprocess
import sys
import os


import pFREYA_tester_processing as pYtp
import pFREYA_tester as g1

def run_script():
  pYtp.send_clocks(g1)
  pYtp.send_slow_ctrl(g1)
  subprocess.run(["python", "prova_transcharacteristics_auto.py"])
  pYtp.send_CSA_RESET_N(g1)
  
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





