# SQUIDDAC Routines


import numpy as np
import time

#Import utilities from py-libs-common
from hal_serial import * #todo: this shouldn't import all symbols but just the ArudinoHAL class
from pattern_runner import *
from fnal_libawg import AgilentAWG
from fnal_ni_toolbox import * #todo: this should import specific class(es)
import fnal_log_wizard as liblog

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *



def test1():
    """Simple Test"""

    pr = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)
    time.sleep(3)

    report = ""

    #For a quick demo, just do DACs 1 and 2, codes 0~8.
    for test in [1,2]: #loop over dacs
        for v in range(8): #loop over codes

            #Create Glue Pattern
            pattern_filename = generate_test_pattern(test,v)

            #Run Glue Pattern
            pr.run_pattern(pattern_filename,outfile_tag="temp")
            
            #Measure SMU
            report = report+"Test DAC = "+str(test)+"; Code = "+str(v)+"; SMU Current is:"+str(V_PORT["Vout"].get_current())+"\n"

    with open("report.txt","w") as write_file:
        write_file.write(report)


# generate_test_pattern()
# Generate the pattern needed to run a single DAC test
# dac_under_test = integer from 0 to 7
# code = integer from 0 to 63
def generate_test_pattern(dac_under_test, code):

    gc = GlueConverter(DEFAULT_IOSPEC)
    
    # (1) GENERATE THE DATA
    send_bits = []
    for dac in range(8): #loop over dacs
        #Send codes to only the DAC under test, zeros to all others.
        if dac==dac_under_test:
            bit_array = np.unpackbits(np.uint8(code))
        else:
            bit_array = [0,0,0,0,0,0,0,0]

        # "send_bits" is created by concatenating all the bit_arrays
        # together.
        if len(send_bits)==0:
            send_bits=bit_array[2:8]
        else:
            send_bits=np.concatenate((send_bits,bit_array[2:8]))


    # (2) WRITE AN ASCII WAVEFORM
    waveform = "scanIn:"
    for bit in send_bits:
        waveform = waveform + str(bit)

    waveform = waveform+"\nenable:"+"1"*48

    wave_filename = "pattern_"+str(dac_under_test)+"_"+str(code)
    with open(wave_filename+".txt",'w') as write_file:
        write_file.write(waveform)
        

    # (3) CONVERT ASCII WAVEFORM to GLUE
    gc.ascii2Glue(wave_filename+".txt", 1, wave_filename)


    return wave_filename+"_se_io.glue"
    
ROUTINES = [test1]
