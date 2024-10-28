import tkinter as tk
import subprocess
#import pFREYA_tester.pFREYA_tester_processing.pFREYA_tester_processing as pYtp
def run_script():
    subprocess.run(["python", "prova_transcharacteristics_auto.py"])

#finestra
gui = tk.Tk()
gui.title("test 1")
gui.geometry("200x100")
gui.resizable(False,False)
#etichetta+pulsante
frame = tk.Frame(gui)
frame.pack(pady=10)
label = tk.Label(frame, text="Transcharacteristics")
label.pack(side=tk.LEFT, padx=10)
#button = tk.Button(gui, text="Test", command = pYtp.send_clocks(gui))
button = tk.Button(gui, text="run", command = run_script)
#button = tk.Button(gui, text="Test", command = pYtp.send_CSA_RESET_N(gui))
button.pack(pady=20)

#run
gui.mainloop()