import tkinter as tk
import subprocess
import sys

sys.path.append('..')
from pFREYA_tester.pFREYA_tester_processing import UART_definitions

 
#import pFREYA_tester.pFREYA_tester_processing.pFREYA_tester_processing as pYtp
def run_script():
# send_clocks(gui)
    subprocess.run(["python", "prova_transcharacteristics_auto.py"])
  #  send_CSA_RESET_N(gui)

#finestra
gui = tk.Tk()
gui.title("test 1")
gui.geometry("300x100")
gui.resizable(False,False)
#etichetta+pulsante
frame = tk.Frame(gui)
frame.pack(pady=10)
label = tk.Label(frame, text="Transcharacteristics")
label.pack(side=tk.LEFT, padx=10)

button = tk.Button(gui, text="run", command = run_script)
button.pack(pady=10)

#run
gui.mainloop()




