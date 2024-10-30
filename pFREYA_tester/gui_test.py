import tkinter as tk
import subprocess
import sys
import os


import pFREYA_tester_processing as pYtp

gui = tk.Tk()

def run_script():
  pYtp.send_clocks(gui)
  subprocess.run(["python", "prova_transcharacteristics_auto.py"])
  pYtp.send_CSA_RESET_N(gui)

#metodo per shap

#finestra

gui.title("test 1")
gui.geometry("400x120")
gui.resizable(False,False)
#etichetta+pulsante
frame = tk.Frame(gui)
frame.pack(pady=10)


label1 = tk.Label(frame, text="Transcharacteristics csa")
label1.grid(row=0, column=0, padx=10, pady=10)
button1 = tk.Button(frame, text="Test CSA", command=run_script)
button1.grid(row=0, column=1, padx=10, pady=10)

label2 = tk.Label(frame, text="Transcharacteristics shap")
label2.grid(row=1, column=0, padx=10, pady=10)
button2 = tk.Button(frame, text="Test shap", command=lambda: print("Pulsante 2 premuto"))
button2.grid(row=1, column=1, padx=10, pady=10)

#run
gui.mainloop()



