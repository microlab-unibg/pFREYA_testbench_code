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

def list_active_measures7(lecroy):
    pid = "P5"

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
    print(mean)
    print(mean2)


config.config(channel='csa',lemo='none',n_steps=20,cfg_bits=[0,1,1,1,0,1,0],cfg_inst=True, active_probes=False)


#QUESTA PARTE (tranne lecroy.timeout e lecroy.clear()) VIENE GIA' FATTA IN config.config()
# lecroy = None
# if lecroy is None:
#     lecroy = TeledyneLeCroyPy.LeCroyWaveRunner('TCPIP0::169.254.1.214::inst0::INSTR')
# print(lecroy.idn)
list_active_measures7(config.lecroy)