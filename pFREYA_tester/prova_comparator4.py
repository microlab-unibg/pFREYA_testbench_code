import matplotlib.pyplot as plt
import numpy as np
# import pandas as pd
import pyvisa
# import matplotlib.colors as mcolors
# from datetime import datetime
import time
# import glob
import config
from TeledyneLeCroyPy import TeledyneLeCroyPy
# import pFREYA_tester_processing as pYtp
# import pFREYA_tester as freya 
import sys
import json
import grafici

def list_active_measures1(lecroy):
    print("=== Misure attive sull'oscilloscopio ===")

    pid = "P5"
    try:
        src = lecroy.query(f"VBS? 'app.Measure.{pid}.Source1'").strip().replace('"', '')
        meas_type = lecroy.query(f"VBS? 'app.Measure.{pid}.Param'").strip().replace('"', '')

        # avg = config.lecroy.query("VBS? 'app.Measure.P5.Mean'")  # la versione con config non dovrebbe funzionare perchè lecroy non viene toccato in quel contesto
        avg = lecroy.query("VBS? 'app.Measure.P5.Mean'")

        if src:  # misura attiva
            print(f"{pid}: tipo='{meas_type}', canale='{src}'")
            print(f"{pid}: media={avg}")
    except Exception as e:
        print(f"{pid}: Errore -> {e}")

def list_active_measures2(lecroy):
    print("=== Misure attive sull'oscilloscopio ===")
    pid = "P1"

    try:
        avg = lecroy.query("VBS? 'app.Measure.P1.Out.Result.Value'")
        print(f"{pid}: media={avg}")
    except Exception as e:
        print(f"{pid}: Errore -> {e}")

def list_active_measures3(lecroy):
    print("=== Misure attive sull'oscilloscopio ===")
    pid = "P1"

    try:
        avg = lecroy.query("VBS? 'app.Measure.P1.Out.Result.Value'")
        print(f"{pid}: media={avg}")
    except Exception as e:
        print(f"{pid}: Errore -> {e}")


def list_active_measures4(lecroy):
    lecroy.write("VBS 'app.Measure.MeasureMode = \"MyMeasure\"'")

    # valore corrente (colonna “value” sullo schermo)
    value = float( lecroy.query("VBS? 'app.Measure.P1.Out.Result.Value'") )

    # media
    mean  = float( lecroy.query("VBS? 'app.Measure.P1.Mean.Result.Value'") )
    mean2 = float( lecroy.query("VBS? 'app.Measure.P1.Statistics(\"mean\").Result.Value'") )
    print(value)
    print(mean)
    print(mean2)

def list_active_measures5(lecroy):
    lecroy.write("VBS 'app.Measure.MeasureMode = \"MyMeasure\"'")

    # valore corrente (colonna “value” sullo schermo)
    value = lecroy.query("VBS? 'app.Measure.P1.Out.Result.Value'").strip()

    # media
    mean  = lecroy.query("VBS? 'app.Measure.P1.Mean.Result.Value'").strip()
    mean2 = lecroy.query("VBS? 'app.Measure.P1.Statistics(\"mean\").Result.Value'").strip()
    print(value)
    print(mean)
    print(mean2)

def list_active_measures6(lecroy):
    vmax  = lecroy.query(":MEASure:VMAX? CHAN2").strip()
    vmin  = lecroy.query(":MEASure:VMIN? CHAN2").strip()
    vmean = lecroy.query(":MEASure:VAVerage? CHAN2").strip()

    print(vmax)
    print(vmin)
    print(vmean)




lecroy = None
if lecroy is None:
    lecroy = TeledyneLeCroyPy.LeCroyWaveRunner('TCPIP0::169.254.1.214::inst0::INSTR')
    print(lecroy.idn)
list_active_measures4(lecroy)



#MAIN
# json_file = sys.argv[1] #sys.argv[1] serve a prendere il parametro (json) col il subprocess.run

# with open(json_file, "r") as f:
#     gui_data = json.load(f)


# config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)


# dict = {
#     'Current level' : [],
#     'AVG SOT': [],
#     '% SOT' : [],
#     'Max #SOT': [],
#     'Min #SOT': []
# }

# data = []
# # data.append(float(config.lecroy.query('C1:CRVA? HREL').split(',')[2])) #C1 è il canale 1, CRVA? interroga per il cursor value, HREL è la modalità di come vengono interpretate le posizioni dei cursori (Horizontal relative)

# # considerando che in un altra parte del codice per leggere dall'oscilloscopio ho questa funzione config.lecroy.query('C1:CRVA? HREL'), quindi questa istruzione config.lecroy.query("VBS? 'app.Measure.P5.value'") dovrebbe essere giusta?

# while(True):
#     time.sleep(0.7)
#     val = config.lecroy.query("VBS? 'app.Measure.P5.Mean'")
#     time.sleep(0.3)
#     print(str(val))








# x = [dict['Current level']]
# y = [dict['% SOT']]
# label = 'null'
# xlabel = 'Current [μA]'
# ylabel = 'Scatti [%]'
# title = 'Curva ad S (Thrgen_ref=280, Vthrp = 601, Vthrp = 599)'

# grafici.creaGrafico(x, y, label, xlabel, ylabel, title)


