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
        avg = lecroy.query(f"VBS? 'app.Measure.{pid}.Mean'")

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
        avg = lecroy.query(f"VBS? 'app.Measure.{pid}.Out.Result.Value'")
        print(f"{pid}: media={avg}")
    except Exception as e:
        print(f"{pid}: Errore -> {e}")


def list_active_measures5(lecroy):
    pid = "P1"
    lecroy.write("VBS 'app.Measure.MeasureMode = \"MyMeasure\"'")

    # valore corrente (colonna “value” sullo schermo)
    value = lecroy.query(f"VBS? 'app.Measure.{pid}.Out.Result.Value'").strip()

    # media
    mean  = lecroy.query(f"VBS? 'app.Measure.{pid}.Mean.Result.Value'").strip()
    mean2 = lecroy.query(f"VBS? 'app.Measure.{pid}.Statistics(\"mean\").Result.Value'").strip()
    print(value)
    print(mean)
    print(mean2)

def list_active_measures6(lecroy):
    try:
        vmax  = lecroy.query(":MEASure:VMAX? CHAN2").strip()
        vmin  = lecroy.query(":MEASure:VMIN? CHAN2").strip()
        vmean = lecroy.query(":MEASure:VAVerage? CHAN2").strip()
<<<<<<< HEAD

        print(vmax)
        print(vmin)
        print(vmean)
    except Exception as e:
        print(e)

def list_active_measures7(lecroy):
    pid = "P1"

    #   PROVARE LE ISTRUZIONI SIA IN MINUSCOLO CHE CON LE INIZIALI MAIUSCOLE

    # lecroy.write(r"""vbs 'app.measure.showmeasure = true ' """)
    # lecroy.write(r"""vbs 'app.measure.statson = true ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.view = true ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.paramengine = "<value>" ' """)
    # lecroy.write(r"""vbs 'app.measure.p1.source1 = "C1" ' """)

    # lecroy.write("VBS 'app.Measure.ShowMeasure = true'")
    # lecroy.write("VBS 'app.Measure.StatsOn = true'")
    # lecroy.write("VBS 'app.Measure.P1.View = true'")

    mean  = lecroy.query(f"VBS? 'return=app.Measure.{pid}.Mean.Result.Value'")
    mean2 = lecroy.query(f"VBS? 'return=app.Measure.{pid}.Statistics(\"mean\").Result.Value'")


# config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)


#QUESTA PARTE (tranne lecroy.timeout e lecroy.clear()) VIENE GIA' FATTA IN config.config()
lecroy = None
if lecroy is None:
    lecroy = TeledyneLeCroyPy.LeCroyWaveRunner('TCPIP0::169.254.1.214::inst0::INSTR')
    lecroy.timeout = 5000
    lecroy.clear()