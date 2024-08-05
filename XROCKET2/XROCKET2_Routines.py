# XROCKET2-Specific Routines

#import sys
#import platform
#import os
import numpy as np
#import serial.tools.list_ports
#import atexit
#import argparse
#from datetime import datetime
#from prettytable.colortable import PrettyTable
#from si_prefix import si_format
#from statistics import mean, NormalDist
#import csv
import time

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors


#Import utilities from py-libs-common
from hal_serial import * #todo: this shouldn't import all symbols but just the ArudinoHAL class
from pattern_runner import *
from fnal_libIO import *
from fnal_libinstrument import *
from fnal_ni_toolbox import * #todo: this should import specific class(es)
import fnal_log_wizard as liblog

from Master_Config import *
#from .XROCKET2_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

XROCKET2_SCAN_CHAIN_BITS = 20480

# Class containing all the data from the XR2 scan chain. 
class XR2_Config_Setting():
    def __init__(self):
        pass

def initialize():

    waves = {}

    waves["count"] = [0]
    waves["testcase"] = ["."]
    waves["testnum"] = [0]

    waves["capClkEN"] = [0]
    waves["scanClk"] = [0]
<<<<<<< Updated upstream
    waves["serialClkEN"] = [0]
=======
    waves["serialClk"] = [0]
>>>>>>> Stashed changes
    waves["configClkEN"] = [0]
    waves["expected_serialOut_AE"] = [0]
    waves["expected_serialOut_PCA"] = [0]

    waves["reset"] = [1]
    waves["scanEn"] = [0]
    waves["clkPCA"] = [0]
    waves["scanClk"] = [0]
<<<<<<< Updated upstream
    waves["serialClkEN"] = [0]
    waves["configClkEN"] = [0]
    waves["reset"] = [0]


=======
    waves["serialClk"] = [0]
    waves["configClkEN"] = [0]
    waves["reset"] = [0]

>>>>>>> Stashed changes
#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_resetDUT():

    waves = {}

    waves["reset"] = [1] * 5
    waves["clkAE"] = [0] * 5
    waves["clkPCA"] = [0] * 5

    waves["reset"] = waves["reset"] + [0,0]
    waves["clkAE"] = waves["clkAE"] + [0,1]
    waves["clkPCA"] = waves["clkPCA"] + [0,1]

    waves["reset"] = waves["reset"] + [1]
    waves["clkAE"] = waves["clkAE"] + [0]
    waves["clkPCA"] = waves["clkPCA"] + [0]

    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
<<<<<<< Updated upstream
def ROUTINE_scanChain():


    SCAN_CHAIN_BITS = 2 * 1024 * 10
=======
def ROUTINE_scanChain(mode):


    SCAN_CHAIN_BITS = 2 * 1024 * 10
    
>>>>>>> Stashed changes
    waves = {
        "scanClk": [],
        "scanEn": [],
        "scanLoad": [],
<<<<<<< Updated upstream
        "scanIn": []
=======
        "scanIn": [],
        "reset": []
>>>>>>> Stashed changes
    }

    with open('spacely-asic-config\\XROCKET2\\testdata\\AE_datain.scrambled.mem', 'r') as AE_memfile:
        f_AE = AE_memfile.read()
        AE_datain = f_AE.split()

    with open('spacely-asic-config\\XROCKET2\\testdata\\PCA_datain.scrambled.mem', 'r') as PCA_memfile:
        f_PCA = PCA_memfile.read()
        PCA_datain = f_PCA.split()

    # Initial setup
<<<<<<< Updated upstream
    waves["scanClk"] = [1]  # scanClk enabled
=======
    waves["scanClk"] = [0,1]  # scanClk enabled,
>>>>>>> Stashed changes
    waves["scanEn"] = [1]      # scanEn enabled
    waves["scanLoad"] = [0]    # scanLoad initial state

    # Loading PCA ScanChain
<<<<<<< Updated upstream
    testcase = "Loading PCA"
    for i in range(1024):
        for j in range(10):
            waves["scanIn"].append(PCA_datain[i][9 - j])
            waves["scanLoad"].append(0)
            waves["scanClk"].append([1, 0])  # Clock cycle

        waves["scanLoad"].append(1)
        waves["scanClk"].append([0, 1])  # Negative edge cycle
        waves["scanEn"].append(1)

    # Loading AE ScanChain
    testcase = "Loading AE"
    for i in range(1024):
        for j in range(10):
            waves["scanIn"].append(AE_datain[i][9 - j])
            waves["scanLoad"].append(0)
            waves["scanClk"].append([1, 0])  # Clock cycle

        waves["scanLoad"].append(1)
        waves["scanClk"].append([0, 1])  # Negative edge cycle
        waves["scanEn"].append(1)

    # Finalizing the scan operation
    for j in range(10):
        waves["scanLoad"].append(0)
        waves["scanClk"].append([1, 0])  # Clock cycle

    waves["scanLoad"].append(1)
    waves["scanClk"].append([0, 1])  # Negative edge cycle

    # Disabling the scan clock and scan enable signals
    waves["scanClk"].append(0)
    waves["scanEn"].append(0)
    waves["scanLoad"].append(0)
=======
    if mode == "PCA":
        for _ in range(2):
            for i in range(1024):
                for j in range(10):
                    waves["scanIn"] = waves["scanIn"] + [PCA_datain[i][9 - j]]*2
                    waves["scanLoad"] = waves["scanLoad"] + [0,0]
                    waves["scanClk"] = waves["scanClk"] + [1,0]  # Clock cycle
                    waves["reset"] = waves["reset"] + [1,1]
        
                waves["scanLoad"] = waves["scanLoad"] + [1,0]
                waves["scanClk"] = waves["scanClk"] + [0,1]  # Negative edge cycle
                waves["scanEn"] = waves["scanEn"] + [1,1]

    # Loading AE ScanChain
    if mode == "AE":
        for _ in range(2):
            for i in range(1024):
                for j in range(10):
                    waves["scanIn"] = waves["scanIn"] + [AE_datain[i][9 - j]]*2
                    waves["scanLoad"] = waves["scanLoad"] + [0,0]
                    waves["scanClk"] = waves["scanClk"] + [1,0]  # Clock cycle
                    waves["reset"] = waves["reset"] + [1,1]

                waves["scanLoad"] = waves["scanLoad"] + [1,0]
                waves["scanClk"] = waves["scanClk"] + [0,1]  # Negative edge cycle
                waves["scanEn"] = waves["scanEn"] + [1,1]

    # Finalizing the scan operation
    for j in range(10):
        waves["scanLoad"] = waves["scanLoad"] + [0,0]
        waves["scanClk"] = waves["scanClk"] + [1,0]  # Clock cycle

    waves["scanLoad"] = waves["scanLoad"] + [1,0]
    waves["scanClk"] = waves["scanClk"] + [0,1]  # Negative edge cycle

    # Disabling the scan clock and scan enable signals
    waves["scanClk"] = waves["scanClk"] + [0]
    waves["scanEn"] = waves["scanEn"] + [1]
    # waves["scanLoad"] = waves["scanLoad"] + [0]
>>>>>>> Stashed changes

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
<<<<<<< Updated upstream
    sg.gc.plot_glue(result_glue)


    # ROUTINE_resetDUT()


=======
    # sg.gc.plot_glue(result_glue)

    # ROUTINE_resetDUT()

>>>>>>> Stashed changes
#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_config_loopback():
    #unstick_VDD_ASIC()
    
    CONFIG_CHAIN_BITS = 4 + (8*2048)
    #Quarter_CONFIG_CHAIN_BITS = CONFIG_CHAIN_BITS/4
    
    waves = {}
    waves["configClk"] = []
    waves["configRst"] = []
    waves["loadShadowReg"] =[]
    waves["configIn"] = []


    for i in range(2*CONFIG_CHAIN_BITS):
        waves["configClk"] = waves["configClk"] + [0,1]
        waves["configRst"] = waves["configRst"] + [1,1]
        waves["loadShadowReg"] = waves["loadShadowReg"] + [0,0]

    for i in range(int(CONFIG_CHAIN_BITS/2)):
        waves["configIn"] = waves["configIn"] + [1,1,1,1,0,0,0,0]
    
    glue_wave = genpattern_from_waves_dict(waves)
    
    result_glue = sg.pr.run_pattern(glue_wave,outfile_tag="result")[0]
    #result_glue = sg.pr.read_glue(glue_wave,outfile_tag="result")
    
    sg.gc.plot_glue(result_glue)

    # ROUTINE_resetDUT()

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_scanChainCheck():
    
    waves = {
        "scanClk": [],
        "scanEn": [],
        "scanLoad": [],
        "scanIn": [],
        "scanOut": [],
<<<<<<< Updated upstream
=======
        "reset": []
>>>>>>> Stashed changes
    }

    with open('spacely-asic-config\\XROCKET2\\testdata\\AE_datain.scrambled.mem', 'r') as AE_memfile:
        f_AE = AE_memfile.read()
        AE_datain = f_AE.split()
        print(len(AE_datain))
<<<<<<< Updated upstream
=======
        #print(f",{AE_datain}")
>>>>>>> Stashed changes

    # with open('spacely-asic-config\\XROCKET2\\testdata\\PCA_datain.scrambled.mem', 'r') as PCA_memfile:
    #     f_PCA = PCA_memfile.read()
    #     PCA_datain = f_PCA.split()

<<<<<<< Updated upstream
    # Initial setup
    # waves["scanClk"] = waves["scanClk"] + [0, 1]
    # waves["scanEn"] = waves["scanEn"] + [0, 1]
    # waves["scanLoad"] = waves["scanLoad"] + ([0, 0])

=======
>>>>>>> Stashed changes
    # Loading Data through ScanChain (2048 * 10)
    for _ in range(4):  # Repeat twice as per the task
        for i in range(1024):
            for j in range(10):
                waves["scanIn"] = waves["scanIn"] + [AE_datain[i][j]]*2
<<<<<<< Updated upstream
                waves["scanLoad"] = waves["scanLoad"] + ([0, 0])
                waves["scanClk"] = waves["scanClk"] + [0, 1]
                waves["scanEn"].append(1)
            waves["scanLoad"] = waves["scanLoad"] + ([1, 1])
            waves["scanClk"] = waves["scanClk"] + [1, 0]
            waves["scanEn"].append(1)

    # Checking Outputs
    # for _ in range(2):  # Repeat twice as per the task
    #     for i in range(1024):
    #         waves["scanIn"].append(0)
    #         for j in range(10):
    #             waves["scanLoad"] = waves["scanLoad"] + ([0, 0])
    #             # waves["scanClk"].append([0, 1])
    #             waves["scanEn"].append(1)
    #             # Note: This is where mismatch checking would occur
    #             # Since we don't have scanOut values, let's just log the wave
    #             # waves["scanOut"].append("check")  # Placeholder for output checking
    #             # In actual usage, compare scanOut to AE_datain[i][j]
    #         waves["scanLoad"].append(1)
    #         waves["scanClk"].append([0, 1])
    #         waves["scanEn"].append(1)

    # Final state
    # waves["scanClk"].append(0)
    # waves["scanEn"].append(0)
    # waves["scanLoad"].append(0)

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_checkAE():
    
    waves = {
        "clkAE": [],
        "dataLatchClkAE": [],
        "serialClk": [],
        # "expected_serialOut_AE": []
    }

    # Initial setup
    # waves["reset"] = waves["reset"] + [0]
    # waves["clkAE"] = waves["clkAE"] + [1]
    # waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1]
    # waves["scanClk"] = waves["scanClk"] + [1]

    # for _ in range(32):
    #     for __ in range (5):
    #         waves["clkAE"] = waves["clkAE"] + [1,0]
    #         waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1,1,0,1]
    #         waves["scanClk"] = waves["scanClk"] + [1,0]
    
    # waves["clkAE"] = waves["clkAE"] + [0,1]
    # waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [0,0]
    # waves["scanClk"] = waves["scanClk"] + [0,1]
            


    # with open('spacely-asic-config\\XROCKET2\\testdata\\AE_data.mem', 'r') as AE_memfile:
    #     f_AE = AE_memfile.read()
    #     AE_dataout = f_AE.split()
    #     print(len(AE_dataout))


    # # with open('spacely-asic-config\\XROCKET2\\testdata\\PCA_datain.scrambled.mem', 'r') as PCA_memfile:
    # #     f_PCA = PCA_memfile.read()
    # #     PCA_datain = f_PCA.split()    

    # Initial setup
    waves["clkAE"] = waves["clkAE"] + [1]
    waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [0]
    waves["serialClk"] = waves["serialClk"] + [0]

    # ROUTINE_scanChain() #- Placeholder for the scan chain function, assume it has been run

    # Clock AE toggling for 30 cycles
    for _ in range(30):
        waves["clkAE"] = waves["clkAE"] + [0, 1]
    
    # # Latching and writing data
    # waves["clkAE"] = waves["clkAE"] + [0]
    # waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [0]
    # # Placeholder for writeArray() and writecompressed() operations



    # # Enable serial clock
    # waves["serialClkEN"] = waves["serialClkEN"] + [1]

    # # Expected serial output AE
    # # waves["expected_serialOut_AE"] = waves["expected_serialOut_AE"] + [AE_dataout[0][0]]*2
    # waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1]

    # # Check Serial Data
    # for i in range(32):
    #     for j in range(5):
    #         if i == 0 and j == 0:
    #             j += 1  # Skip Header
    #         # waves["expected_serialOut_AE"].append(AE_dataout[i][j])
    #         waves["serialClkEN"] = waves["serialClkEN"] + [1]
    
    # # waves["expected_serialOut_AE"] = waves["expected_serialOut_AE"] + [0]
    # waves["serialClkEN"] = waves["serialClkEN"] + [0]

    # # # Ensure vertical alignment of all waveforms
    # # max_len = max(len(waves[key]) for key in waves)
    # # for key in waves:
    # #     waves[key].append([waves[key]] * (max_len - len(waves[key])))

    # ROUTINE_writeArray(AE_dataout)
    # ROUTINE_writecompressed(AE_dataout)

    # # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)


#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_checkPCA(PCA_dataout):

    waves = {
        "clkPCA": [],
        "dataLatchClkPCA": [],
        "serialClkEN": [],
        "expected_serialOut_PCA": []
    }

    # with open('spacely-asic-config\\XROCKET2\\testdata\\AE_datain.scrambled.mem', 'r') as AE_memfile:
    #     f_AE = AE_memfile.read()
    #     AE_datain = f_AE.split()

    with open('spacely-asic-config\\XROCKET2\\testdata\\PCA_dataout.mem', 'r') as PCA_memfile:
        f_PCA = PCA_memfile.read()
        PCA_dataout = f_PCA.split()

    # Initial setup
    waves["clkPCA"].append(0)
    waves["dataLatchClkPCA"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)

    # scanChain() - Placeholder for the scan chain function, assume it has been run
    # Perform scanChain here
    waves["clkPCA"].append(0)
    waves["dataLatchClkPCA"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)

    # Toggling clkPCA for 30 cycles
    for _ in range(30):
        waves["clkPCA"].append(1)
        waves["dataLatchClkPCA"].append(0)
        waves["serialClkEN"].append(0)
        waves["expected_serialOut_PCA"].append(0)
        waves["clkPCA"].append(0)
        waves["dataLatchClkPCA"].append(0)
        waves["serialClkEN"].append(0)
        waves["expected_serialOut_PCA"].append(0)
    
    # Latching and writing data
    waves["clkPCA"].append(0)
    waves["dataLatchClkPCA"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)
    # Placeholder for writeArray_PCA() and writecompressed_PCA() operations

    # Enable serial clock
    waves["serialClkEN"].append(1)

    # Expected serial output PCA
    waves["expected_serialOut_PCA"].append(PCA_dataout[0][2])
    waves["dataLatchClkPCA"].append(1)

    # Check Serial Data
    for i in range(32):
        for j in range(7):
            if i == 0 and j == 0:
                j += 3  # Skip Header
            if j < 7:  # Ensure we don't exceed bounds after skipping header
                waves["expected_serialOut_PCA"].append(PCA_dataout[i][j])
                waves["clkPCA"].append(0)
                waves["dataLatchClkPCA"].append(0)
                waves["serialClkEN"].append(1)

    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)

    # Ensure vertical alignment of all waveforms
    max_len = max(len(waves[key]) for key in waves)
    for key in waves:
        waves[key].append([waves[key][-1]] * (max_len - len(waves[key])))

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

    ROUTINE_resetDUT()

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_writeArray(array_data, filename="ArrayData_AE.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(5120):
            fp.write(f"{array_data[i]:0b}")  # Writing the binary representation
            counter += 1
=======
                waves["scanLoad"] = waves["scanLoad"] + [0,0]
                waves["scanClk"] = waves["scanClk"] + [0,1]
                waves["reset"] = waves["reset"] + [1,1]
                waves["scanEn"].append(1)
            waves["scanLoad"] = waves["scanLoad"] + [0,1]
            waves["scanClk"] = waves["scanClk"] + [1,0]
            waves["scanEn"].append(1)

    # Generate glue wave and send to ASIC, then plot results
    sg.pr._interface["PXI1Slot11/NI6583"].interact('w','lvds_clockout_en',True)
    genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(["genpattern_se_io.glue", "genpattern_lvds.glue"], outfile_tag="result")
    print(result_glue)
    sg.gc.plot_glue(result_glue[0])
    sg.gc.plot_glue(result_glue[1])

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_checkAE():

    # ROUTINE_resetDUT()
    
    waves = {
        "reset":[],
        "clkAE": [],
        "dataLatchClkAE": [],
        "serialClk" : [],
        "scanClk": [],
        "scanLoad":[],
        "scanEn": [],
        "scanIn": []
        # "expected_serialOut_AE": []
    }

    ROUTINE_scanChain("AE")

    # Perform scanChain here
    waves["reset"] = waves["reset"] + [0] #was [1]
    waves["clkAE"] = waves["clkAE"] + [0]
    waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1]
    waves["serialClk"] = waves["serialClk"] + [0]
    # waves["reset"] = waves["reset"] + [0,1]
    waves["scanLoad"] = waves["scanLoad"] + [0]
    waves["scanClk"] = waves["scanClk"] + [0]
    waves["scanEn"] = waves["scanEn"] + [0]
    waves["scanIn"] = waves["scanIn"] + [0]
    # waves["expected_serialOut_PCA"].append(0)
          
    for i in range(10):
        # Toggling clkAE for 30 cycles
        for j in range(30):
            waves["clkAE"] = waves["clkAE"] + [0,1]
            waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1,1]
            waves["serialClk"] = waves["serialClk"] + [0,0]
            waves["reset"] = waves["reset"] + [1,1]

        
        # Latching and writing data
        waves["clkAE"] = waves["clkAE"] + [0]
        waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [0] #was [0,0,0,0]
        waves["serialClk"] = waves["serialClk"] + [0]
        waves["reset"] = waves["reset"] + [1]


        # Enable serial clock
        waves["serialClk"] = waves["serialClk"] + [1,0]

        # Expected serial output AE
        # waves["expected_serialOut_AE"].append(AE_dataout[0][2])
        waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1]

        # Check Serial Data
        for i in range(34):
            for j in range(5):
                if i == 0 and j == 0:
                    j = j + 1  # Skip Header
                # AE_dataout[i][j] = waves["expected_serialOut_AE"]
                waves["clkAE"] = waves["clkAE"] + [0]
                waves["dataLatchClkAE"] = waves["dataLatchClkAE"] + [1]
                waves["serialClk"] = [1]
                waves["reset"] = waves["reset"] + [1]
        
        # waves["expected_serialOut_AE"] = waves["expected_serialOut_AE"] + [0]
        waves["serialClk"] = [0]
        waves["reset"] = waves["reset"] + [0]

    # Generate glue wave and send to ASIC, then plot results
    sg.pr._interface["PXI1Slot11/NI6583"].interact('w','lvds_clockout_en',True)
    genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(["genpattern_se_io.glue", "genpattern_lvds.glue"], outfile_tag="result")
    print(result_glue)
    sg.gc.plot_glue(result_glue[0])
    sg.gc.plot_glue(result_glue[1])

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_checkPCA():

    # ROUTINE_resetDUT()
    waves = {
        "clkPCA": [],
        "dataLatchClkPCA": [],
        "serialClk": [],
        "reset": [],
        "scanClk": [],
        "scanLoad":[],
        "scanEn": [],
        "scanIn": []
        # "expected_serialOut_PCA": []
    }

    # Initial setup
    # waves["clkPCA"] = waves["clkPCA"] + [0]
    # waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [0]
    # waves["serialClk"] = waves["serialClk"] +[0]
    # waves["expected_serialOut_PCA"].append(0)

    ROUTINE_scanChain("PCA") #- Placeholder for the scan chain function, assume it has been run

    # Perform scanChain here
    waves["reset"] = waves["reset"] + [1]
    waves["clkPCA"] = waves["clkPCA"] + [0]
    waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [1]
    waves["serialClk"] = waves["serialClk"] +[0]
    # waves["reset"] = waves["reset"] + [0,1]
    waves["scanLoad"] = waves["scanLoad"] + [0]
    waves["scanClk"] = waves["scanClk"] + [0]
    waves["scanEn"] = waves["scanEn"] + [0]
    waves["scanIn"] = waves["scanIn"] + [0]
    # waves["expected_serialOut_PCA"].append(0)

    for _ in range(1):
        # Toggling clkPCA for 30 cycles
        for _ in range(30):
            waves["clkPCA"] = waves["clkPCA"] + [0,1]
            waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [1,1]
            waves["serialClk"] = waves["serialClk"] +[0,0]
            waves["reset"] = waves["reset"] + [1,1]

        # Latching and writing data
        # waves["reset"] = waves["reset"] + [1]
        waves["clkPCA"] = waves["clkPCA"] + [0]
        waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [0,0,0,0]
        waves["serialClk"] = waves["serialClk"] +[0]
        waves["reset"] = waves["reset"] + [1]

        # Enable serial clock
        waves["serialClk"] = waves["serialClk"] +[1,0]

        # Expected serial output PCA
        # waves["expected_serialOut_PCA"].append(PCA_dataout[0][2])
        waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [1]

        # Check Serial Data
        for i in range(32):
            for j in range(7):
                if i == 0 and j == 0:
                    j = j + 3  # Skip Header
                if j < 7:  # Ensure we don't exceed bounds after skipping header
                    # waves["expected_serialOut_PCA"].append(PCA_dataout[i][j])
                    waves["clkPCA"] = waves["clkPCA"] + [0]
                    waves["dataLatchClkPCA"] = waves["dataLatchClkPCA"] + [1]
                    waves["serialClk"] = waves["serialClk"] +[1]
                    waves["reset"] = waves["reset"] + [1]

        waves["serialClk"] = waves["serialClk"] + [0]
        waves["reset"] = waves["reset"] + [0]
    # waves["expected_serialOut_PCA"].append(0)

    # Generate glue wave and send to ASIC, then plot results
    sg.pr._interface["PXI1Slot11/NI6583"].interact('w','lvds_clockout_en',True)
    genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(["genpattern_se_io.glue", "genpattern_lvds.glue"], outfile_tag="result")
    print(result_glue)
    sg.gc.plot_glue(result_glue[0])
    sg.gc.plot_glue(result_glue[1])

    # ROUTINE_resetDUT()

def writeArray(array_data, filename="ArrayData_AE.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(5120):  # Use the actual length of array_data
            fp.write(f"{array_data[i]:08b}")  # Write 8-bit binary representation
            counter = counter + 1
>>>>>>> Stashed changes
            if counter == 5:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

<<<<<<< Updated upstream
#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_writeArray_PCA(array_data, filename="ArrayData_PCA.txt"):
=======
def writeArray_PCA(array_data, filename="ArrayData_PCA.txt"):
>>>>>>> Stashed changes
    counter = 0
    with open(filename, "w") as fp:
        for i in range(10240):
            fp.write(f"{array_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 10:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

<<<<<<< Updated upstream
#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_writecompressed(compressed_data, filename="compressedData.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(150):
            fp.write(f"{compressed_data[i]:0b}")  # Writing the binary representation
=======
def writecompressed(compressed_data, filename="compressedData.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(150):
            fp.write(f"{compressed_data[i]:5b}")  # Writing the binary representation
>>>>>>> Stashed changes
            counter += 1
            if counter == 5:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

<<<<<<< Updated upstream
#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_writecompressed_PCA(compressed_data, filename="compressedData_PCA.txt"):
=======
def writecompressed_PCA(compressed_data, filename="compressedData_PCA.txt"):
>>>>>>> Stashed changes
    counter = 0
    with open(filename, "w") as fp:
        for i in range(210):
            fp.write(f"{compressed_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 7:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

<<<<<<< Updated upstream
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
=======
#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
>>>>>>> Stashed changes
def ROUTINE_VtestInput(Vin, period):
    waves = {
        "Vtest": [],
        "soc": [],
        "DACclr": [],
        "CLK": []
    }

    # Initialize variables
    Vtest = Vin
    ClkLength = 1
    testcase = "Inputing Vtest Data"

    # Append initial state
    waves["Vtest"].append(Vtest)
    waves["soc"].append(0)
    waves["DACclr"].append(1)
    waves["CLK"].append(0)

    # Initialize Device
    waves["soc"].append(1)
    waves["DACclr"].append(0)

    # One Loop = 1 ADC Acquisition
    for i in range(10):  # 10 Total Runs
        for j in range(ClkLength):  # 1 + 2 + 3 + ... + 9 + 10 = 55 Total Cycles
            waves["CLK"].append(0)  # Clock low on posedge
        waves["CLK"].append(1)  # Clock high

        # Clear CapHi & CapLo for next Run
        for _ in range(period // 10):
            waves["DACclr"].append(1)
        for _ in range(period // 10):
            waves["DACclr"].append(0)

        # Increase Loop Length
        ClkLength += 1

        waves["CLK"].append(0)  # Clock low on negedge

    waves["CLK"].append(0)  # Final clock low on posedge

    # Ensure vertical alignment of all waveforms
    max_len = max(len(waves[key]) for key in waves)
    for key in waves:
        waves[key].append([waves[key][-1]] * (max_len - len(waves[key])))

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

<<<<<<< Updated upstream
#Sub-Routine
#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_unstick_VDD_ASIC():
=======
def unstick_VDD_ASIC():
>>>>>>> Stashed changes
    
    while True:
        VDD_ASIC_Current = V_PORT["VDD_ASIC"].get_current()
        
        if VDD_ASIC_Current < 50e-6:
            break
        
        #rando = np.random.randint(0,350)
        #voltage = 1 + float(rando)/1000
        rando = np.random.randint(100,200)
        voltage = 1.1 + float(rando)/1000

        print(f"Setting VDD_ASIC={voltage}")
        V_PORT["VDD_ASIC"].set_voltage(voltage)
        
    #Restore VDD_ASIC to set voltage.
    V_PORT["VDD_ASIC"].set_voltage(V_LEVEL["VDD_ASIC"])
    print("DONE!")
<<<<<<< Updated upstream



=======
>>>>>>> Stashed changes

# TEST #1: Config Chain Loopback
def XROCKET2_Config_Chain():
    """Verify the XROCKET2 Config Chain by passing data in via configIn and reading it from configOut"""

    tp1_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET2\\Glue_Waves\\Tests_8_23\\Tests\\configchain\\configchain_testoutput_se_io.glue"
    tp1_out_file = "xrocket2_config_output_PXI1Slot5_NI6583_se_io.glue"
    tp1_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET2\\Glue_Waves\\Tests_8_23\\Tests\\configchain\\configchain_golden_se_io.glue"
    
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    
    time.sleep(3)

    print("Checking XROCKET2 Config Chain!")
    
    tp.run_pattern(tp1_in_file, outfile_tag="xrocket2_config_output")
    gc = GlueConverter(DEFAULT_IOSPEC)
    gc.compare(gc.read_glue(tp1_golden), gc.read_glue(tp1_out_file))

# TEST #2: Scan Chain Loopback
def XROCKET2_Scan_Chain():
    """Verify the XROCKET2 Scan Chain by passing data in via scanIn and reading it from scanOut"""
    
    tp1_in_file = "C:\\Users\\aquinn\\Downloads\\scanchain4\\scanchain4\\scanchain_with_reset.glue"
    tp1_out_file = "C:\\Users\\aquinn\Desktop\\SPROCKET Test\\spacely\\PySpacely\\xrocket2_config_output_PXI1Slot5_NI6583_se_io.glue"
    tp1_golden = "C:\\Users\\aquinn\\Downloads\\scanchain4\\scanchain4\\scanchain_golden_se_io.glue"
    
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    
    time.sleep(3)

    print("Checking XROCKET2 Scan Chain!")
    
    tp.run_pattern(tp1_in_file, outfile_tag="xrocket2_scan_output")
    gc = GlueConverter(DEFAULT_IOSPEC)
    gc.compare(gc.read_glue(tp1_golden), gc.read_glue(tp1_out_file))

# TEST #3: Serial Readout
def XROCKET2_Serial_Readout():
    """Verify the XROCKET2 Serial Readout by passing in data via the scan chain and reading it through serialOut"""

    se_io_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\serial readout 3\\serialreadout_testoutput_se_io.glue"
    lvds_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\serial readout 3\\serialreadout_testoutput_lvds.glue"
    out_file = "xrocket2_serial_output_PXI1Slot16_NI6583_lvds.glue"
    lvds_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\serial readout 3\\serialreadout_golden_lvds.glue"
    filepath_lint([se_io_in_file,lvds_in_file, lvds_golden],"XROCKET2_Routines")
    
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    
    time.sleep(3)

    print("Checking XROCKET2 Serial Readout!")
    tp._interface["PXI1Slot16/NI6583"].interact('w','lvds_clockout_en',True)
    time.sleep(1)
    
    res = tp.run_pattern([se_io_in_file, lvds_in_file], outfile_tag="xrocket2_serial_output")
    if res == -1:
        print("run_pattern failed!")
        return
    gc = GlueConverter(DEFAULT_IOSPEC)
    gc.compare(gc.read_glue(lvds_golden), gc.read_glue(out_file))
    
# TEST #4: Vtest Readout
def XROCKET2_Vtest_Readout():
    """Test the complete operation of the array by supplying a Vtest voltage and reading the data out through serialOut"""


    #NOTE changed for debug.
    se_io_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\Vtest 2\\vtest_testoutput_se_io.glue"
    lvds_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\Vtest 2\\vtest_testoutput_lvds.glue"
    lvds_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\Vtest 2\\vtest_golden_lvds.glue"
    se_io_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\XROCKET2\\Glue_Waves\\Vtest 2\\vtest_golden_se_io.glue"
    filepath_lint([se_io_in_file,lvds_in_file, lvds_golden],"XROCKET2_Routines")
    
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)

    config_AWG_as_DC(0) 
    
    time.sleep(3)

    #Turn on LVDS clock. 
    tp._interface["PXI1Slot16/NI6583"].interact('w','lvds_clockout_en',True)
    time.sleep(1)

    #TODO: Program config register to set Vtest=True
    

    for Vtest_mV in [250]: #range(0,1000,100):
        #1) set Vtest to the correct voltage using Spacely.
        set_Vin_mV(Vtest_mV)
        
        #2) Run the appropriate Glue waveform to take an ADC acquisition and read out the data.
        outfile_tag = "xrocket2_Vtest_"+str(Vtest_mV)
        tp.run_pattern([se_io_in_file, lvds_in_file], outfile_tag=outfile_tag)
        se_io_out_file = outfile_tag+"_PXI1Slot5_NI6583_se_io.glue"
        lvds_out_file = outfile_tag+"_PXI1Slot5_NI6583_lvds.glue"
        gc = GlueConverter(DEFAULT_IOSPEC)
        gc.compare(gc.read_glue(se_io_golden), gc.read_glue(se_io_out_file))
        gc.compare(gc.read_glue(lvds_golden), gc.read_glue(lvds_out_file))
    
        #3) Parse the data you read back. 

        pass

# TEST #5: DNL Trim (WIP!!!!)
def XROCKET2_DNL_Trim():
    """Trim the Captrim values of each pixel to optimize DNL."""

    #Set output voltage = 750 mV.
    config_AWG_as_DC(750)

    #Create a glue file from the CDAC CMD "[1]"
    create_glue_wave_from_cdac_cmd([1],"test_cdac_cmd_scan_out")

    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    gc = GlueConverter(DEFAULT_IOSPEC)

    time.sleep(3)

    print("Running Experimental DNL Trim Algorithm!")

    #Run that glue file
    tp.run_pattern("test_cdac_cmd_scan_out_se_io.glue", outfile_tag="xrocket2_dnl_output")

    #Parse the scan chain data
    gc.export_clocked_bitstream(gc.read_glue("xrocket2_dnl_output_PXI1Slot5_NI6583_se_io.glue")
                                , "scanClk","scanOut","scan_chain_data.txt")

    #Plot the scan chain data
    scan_chain_color_map("scan_chain_data.txt",0)

# Another function to verify the scan chain, but this time using ASCII waves.
def XROCKET2_ascii_scan_chain_demo():
    """Test scan chain loopback using an ASCII wave instead of a VCD."""

    # 1) Generate a Glue waveform that pushes all 1's through the scan chain and reads them back. 
    a = AsciiWave()

    a.init_signals([("scanClk",0),("scanEn",0),("scanLoad",0),("scanIn",0)])

    a.set_signal("scanEn",1)
    a.set_signal("scanIn",1)

    for i in range(4096):
        for j in range(10):
            a.pulse_signal("scanClk")
        a.pulse_signal("scanLoad")

    a.write("ascii_scan_chain_demo.txt")

    gc = GlueConverter(DEFAULT_IOSPEC)

    gc.ascii2Glue("ascii_scan_chain_demo.txt",5,"ascii_scan_chain_demo")

    # 2) Run that Glue waveform.
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)
    
    time.sleep(3)

    print("Checking XROCKET2 Scan Chain (ASCII)!")
    
    tp.run_pattern("ascii_scan_chain_demo_se_io.glue", outfile_tag="xrocket2_scan_output_ascii_demo")


    # 3) Parse scan chain data from the Glue waveform that we got back.
    gc.export_clocked_bitstream(gc.read_glue("xrocket2_scan_output_ascii_demo_PXI1Slot5_NI6583_se_io.glue")
                                , "scanClk","scanOut","scan_chain_demo_data.txt")

    scan_chain_color_map("scan_chain_demo_data.txt",0)
    scan_chain_color_map("scan_chain_demo_data.txt",20480)

    #gc.plot_glue("xrocket2_scan_output_ascii_demo_PXI1Slot5_NI6583_se_io.glue")
    
# create_glue_wave_from_cdac_cmd()
#
# This function will create a Glue wave which does the following:
#  1) Toggle DACclr, Rangelock, Qequal, etc. to issue the correct CDAC command.
#  2) Issue 10 pulses on Clk, which will cause w1Reg to walk across its range, clocking all bits into data[]
#  3) Clock Clk2 ONCE, which I hope will cause "eoc" to be asserted and clock data[] --> dataOutput[]
#  4) Scan out all data from dataOutput. 
def create_glue_wave_from_cdac_cmd(cdac_cmd, glue_wave_filename):

    #CDAC command should be entered LSB-first. 
    cdac_cmd.reverse()

    a = AsciiWave()

    a.init_signals([("scanClk",0),("scanEn",0),("scanLoad",0),("scanIn",0),
                    ("DACclr",0),("RangeLock",0),("Qequal",0),("soc",1),
                    ("Clk",0),("Clk2",0)])

    #Start with a negative soc pulse
    a.pulse_signal("soc",posedge=False)

    #Simultaneously fire DACclr and Qequal to completely clear the DAC
    a.custom_wave({"DACclr":"010","Qequal":"010"})

    for i in cdac_cmd:
        if cdac_cmd == 1:
            a.pulse_signal("RangeLock")
        else:
            a.pulse_signal("DACclr")

        a.pulse_signal("Qequal")

    for j in range(10):
        a.pulse_signal("Clk")


    #NOTE: Pulsing scanLoad when scanEn is low should have the same effect
    #      as eoc... that is moving data[] --> dataOutput[]
    a.pulse_signal("scanLoad")

    #Begin scan chain readout.
    a.set_signal("scanEn",1)

    for i in range(2048):
        for j in range(10):
            a.pulse_signal("scanClk")
        a.pulse_signal("scanLoad")
    
    a.write("cdac_cmd.txt")
    
    gc = GlueConverter(DEFAULT_IOSPEC)

    #Use GlueConverter to convert cdac_cmd.txt to a Glue file.
    gc.ascii2Glue("cdac_cmd.txt",5,glue_wave_filename)
 
#Convert binary values from the scan chain into a color map and plot them.      
def scan_chain_color_map(scan_chain_csv, offset):

    with open(scan_chain_csv, 'r') as read_file:
        scan_chain_csv_text = read_file.read()
        scan_chain_bits = [int(x) for x in scan_chain_csv_text.split(",")]

    print("(DBG) Scan chain dump contains",len(scan_chain_bits),"bits, starting from",offset)


    scan_chain_vals = []
    
    

    for i in range(offset, offset+XROCKET2_SCAN_CHAIN_BITS, 10):
        #TODO: CONFIRM THE ENDIANNESS OF SCAN CHAIN VALUES

        #Convert binary list to integer using string comprehension (for every chunk of 10 bits)
        scan_chain_vals.append(int("".join(str(i) for i in scan_chain_bits[i:i+10]),2))


    sc_array = np.array(scan_chain_vals)

    #TODO: MAKE SURE THAT SCAN CHAIN PIXELS ARE IN THE CORRECT PHYSICAL ORDER. (reshape(32,64) is just the most naive way to arrange them)
    sc_array = sc_array.reshape(32,64)

    cmap = colors.ListedColormap(['red','blue'])

    fig, ax = plt.subplots()
    grid=ax.imshow(sc_array, cmap=matplotlib.colormaps["coolwarm"], vmin=0, vmax=1023)
    
    plt.colorbar(grid)
    plt.show()

#CAPTRIM CODE BELOW ###########################################################################################################################################################################

#I paste the ideal trims here because I'm lazy
TRIM_ARRAY = [0, 36, 16, 32, 0, 0, 24, 0, 32, 16, 12, 0, 8, 24, 48, 0, 24, 36, 0, 32, 0, 0, 48, 0, 32, 8, 8, 16, 8, 24, 12, 56, 8, 48, 8, 0, 56, 0, 40, 4, 40, 0, 24, 48, 8, 32, 60, 48, 16, 32, 0, 20, 32, 48, 36, 48, 56, 8, 48, 8, 8, 10, 0, 0, 4, 32, 32, 16, 0, 32, 0, 0, 0, 36, 8, 0, 48, 8, 48, 8, 48, 0, 24, 0, 40, 0, 20, 48, 16, 32, 16, 24, 32, 0, 8, 16, 8, 16, 32, 16, 12, 20, 4, 52, 40, 16, 0, 4, 2, 52, 0, 0, 16, 16, 48, 32, 4, 40, 4, 0, 0, 40, 8, 0, 24, 20, 48, 0, 0, 40, 48, 4, 24, 0, 0, 0, 16, 32, 4, 40, 0, 16, 8, 16, 0, 8, 40, 16, 8, 56, 48, 8, 0, 48, 36, 0, 0, 0, 32, 32, 4, 8, 12, 48, 32, 8, 0, 8, 0, 48, 24, 0, 40, 0, 32, 16, 8, 4, 0, 4, 0, 32, 0, 32, 0, 16, 8, 28, 36, 8, 32, 0, 16, 40, 12, 48, 32, 8, 0, 0, 4, 32, 8, 0, 8, 0, 0, 48, 48, 52, 40, 32, 36, 16, 32, 0, 0, 0, 4, 32, 0, 0, 0, 0, 0, 12, 24, 0, 4, 48, 4, 0, 24, 24, 4, 16, 0, 0, 0, 0, 16, 12, 32, 0, 0, 32, 24, 0, 32, 24, 32, 48, 0, 32, 0, 48, 56, 44, 40, 48, 32, 0, 32, 0, 32, 8, 0, 0, 0, 32, 32, 4, 12, 60, 48, 40, 24, 0, 4, 32, 48, 4, 0, 32, 0, 2, 20, 48, 24, 20, 40, 8, 0, 32, 32, 32, 32, 52, 32, 0, 8, 20, 0, 32, 20, 32, 18, 4, 40, 16, 0, 0, 48, 16, 32, 8, 4, 0, 0, 0, 2, 4, 0, 52, 0, 0, 0, 2, 40, 8, 32, 0, 0, 0, 0, 0, 40, 16, 40, 16, 4, 16, 48, 20, 48, 0, 0, 8, 4, 0, 32, 56, 28, 52, 4, 34, 40, 24, 48, 48, 36, 32, 8, 48, 24, 8, 8, 0, 24, 0, 52, 56, 52, 0, 8, 8, 32, 16, 56, 0, 4, 40, 16, 16, 32, 0, 16, 0, 0, 0, 0, 8, 4, 0, 40, 36, 48, 32, 0, 52, 0, 0, 32, 36, 0, 36, 16, 0, 0, 0, 0, 0, 0, 36, 40, 0, 20, 52, 0, 20, 8, 32, 0, 8, 32, 0, 0, 16, 4, 8, 32, 52, 40, 16, 24, 8, 32, 0, 0, 4, 16, 0, 0, 8, 52, 0, 0, 32, 0, 24, 16, 0, 0, 0, 8, 8, 48, 0, 24, 32, 0, 0, 48, 0, 16, 24, 0, 28, 16, 0, 8, 32, 56, 32, 16, 40, 0, 36, 0, 0, 0, 8, 16, 0, 8, 40, 40, 0, 40, 4, 0, 32, 16, 48, 0, 32, 40, 8, 12, 0, 0, 16, 4, 4, 52, 16, 0, 0, 32, 32, 0, 16, 0, 8, 16, 32, 12, 0, 40, 0, 0, 56, 8, 0, 0, 0, 32, 0, 32, 24, 16, 0, 0, 8, 56, 0, 0, 20, 32, 0, 32, 0, 0, 16, 16, 16, 12, 0, 16, 40, 32, 32, 0, 48, 0, 20, 0, 0, 32, 32, 0, 0, 4, 20, 24, 48, 32, 8, 24, 48, 0, 16, 0, 8, 0, 0, 32, 0, 8, 0, 48, 8, 0, 0, 8, 8, 16, 48, 0, 16, 0, 20, 56, 48, 0, 8, 32, 0, 8, 0, 0, 0, 56, 48, 24, 4, 0, 24, 52, 0, 0, 8, 8, 32, 4, 56, 0, 0, 0, 0, 8, 0, 20, 40, 0, 4, 44, 4, 16, 24, 24, 16, 32, 40, 0, 56, 0, 0, 0, 0, 32, 0, 0, 48, 16, 48, 0, 8, 0, 40, 40, 0, 0, 0, 24, 48, 24, 0, 0, 32, 0, 0, 32, 24, 0, 48, 0, 32, 0, 0, 0, 48, 4, 0, 32, 48, 16, 8, 0, 0, 0, 4, 24, 32, 48, 16, 0, 0, 16, 32, 4, 32, 16, 32, 0, 0, 16, 0, 8, 8, 48, 48, 0, 4, 0, 8, 4, 32, 0, 8, 0, 48, 20, 48, 16, 16, 32, 20, 16, 0, 24, 48, 40, 32, 48, 16, 40, 4, 0, 0, 40, 0, 16, 12, 0, 32, 36, 0, 32, 8, 16, 32, 32, 0, 32, 0, 40, 16, 12, 0, 8, 4, 44, 8, 32, 32, 48, 0, 24, 0, 0, 40, 8, 16, 16, 0, 36, 0, 40, 0, 36, 0, 0, 48, 36, 0, 32, 12, 0, 0, 0, 16, 32, 48, 32, 32, 32, 0, 8, 8, 0, 0, 4, 8, 0, 0, 16, 0, 0, 16, 16, 0, 40, 4, 0, 0, 24, 48, 0, 24, 0, 44, 0, 32, 32, 0, 32, 32, 0, 24, 40, 56, 0, 0, 56, 32, 4, 0, 32, 16, 0, 32, 32, 40, 0, 12, 48, 48, 32, 8, 24, 8, 48, 16, 0, 0, 8, 8, 4, 32, 28, 24, 16, 0, 16, 24, 0, 24, 20, 16, 24, 16, 32, 16, 0, 8, 8, 48, 0, 8, 8, 0, 4, 0, 16, 0, 0, 0, 0, 32, 24, 8, 0, 0, 0, 0, 0, 32, 8, 0, 36, 40, 16, 16, 0, 48, 16, 0, 0, 24, 40, 0, 32, 16, 12, 0, 16, 32, 20, 8, 36, 40, 32, 48, 0, 20, 40, 32, 8, 40, 0, 24, 0, 0, 0, 40, 0, 24, 24, 0, 40, 32, 40, 4, 32, 36, 24, 0, 0, 24, 32, 16, 0, 32, 48, 16, 20, 0, 0, 32, 48, 8, 48, 16, 8, 12, 52, 0, 20, 56, 52, 0, 32, 16, 4, 8, 24, 0, 16, 4, 20, 16, 16, 32, 4, 32, 56, 16, 20, 0, 0, 8, 52, 0, 0, 40, 56, 16, 32, 56, 4, 24, 8, 16, 0, 0, 0, 32, 40, 0, 32, 32, 12, 0, 32, 0, 0, 40, 32, 40, 52, 40, 0, 16, 0, 28, 32, 8, 0, 16, 32, 32, 36, 0, 8, 8, 4, 48, 0, 20, 16, 0, 0, 4, 0, 36, 16, 0, 4, 16, 0, 8, 0, 24, 16, 0, 8, 4, 16, 32, 8, 0, 48, 32, 40, 4, 48, 36, 24, 0, 32, 0, 40, 4, 40, 4, 0, 4, 56, 56, 20, 48, 0, 32, 32, 0, 8, 32, 0, 16, 56, 32, 8, 24, 0, 32, 4, 0, 16, 32, 40, 16, 48, 56, 40, 0, 8, 32, 0, 32, 0, 16, 36, 0, 32, 8, 4, 32, 16, 0, 32, 32, 32, 40, 8, 0, 48, 0, 0, 56, 0, 48, 0, 40, 16, 16, 56, 8, 48, 36, 48, 32, 48, 0, 0, 36, 0, 16, 0, 8, 24, 52, 8, 36, 8, 24, 24, 24, 16, 0, 48, 0, 56, 8, 36, 32, 4, 4, 0, 0, 16, 16, 8, 16, 0, 48, 16, 48, 32, 40, 36, 0, 24, 4, 40, 16, 48, 4, 48, 16, 32, 0, 16, 0, 4, 16, 36, 24, 36, 24, 40, 36, 20, 16, 0, 0, 0, 16, 40, 0, 32, 16, 8, 52, 34, 40, 20, 0, 0, 48, 32, 36, 40, 0, 0, 16, 4, 40, 2, 16, 0, 36, 0, 24, 0, 8, 40, 32, 0, 32, 0, 0, 40, 0, 36, 44, 16, 0, 24, 4, 12, 40, 8, 32, 24, 20, 0, 8, 40, 20, 16, 24, 0, 16, 32, 0, 32, 48, 32, 16, 32, 0, 0, 0, 48, 16, 48, 0, 8, 16, 40, 56, 0, 32, 4, 0, 48, 0, 16, 0, 16, 32, 28, 8, 24, 0, 0, 48, 20, 12, 24, 0, 44, 0, 32, 0, 44, 32, 8, 52, 48, 0, 52, 32, 16, 48, 36, 48, 16, 0, 40, 48, 4, 24, 16, 48, 48, 32, 40, 40, 40, 40, 0, 24, 24, 32, 4, 48, 2, 36, 0, 20, 36, 36, 8, 44, 20, 40, 16, 48, 32, 36, 36, 0, 24, 8, 4, 48, 0, 16, 8, 20, 8, 32, 4, 0, 8, 32, 52, 0, 20, 4, 16, 60, 32, 8, 16, 8, 16, 32, 4, 16, 32, 8, 0, 16, 28, 32, 4, 24, 48, 0, 16, 56, 16, 56, 16, 16, 48, 48, 0, 32, 60, 24, 0, 20, 16, 16, 40, 48, 8, 4, 8, 8, 8, 0, 4, 48, 56, 4, 36, 48, 0, 32, 24, 0, 0, 0, 4, 48, 24, 0, 16, 16, 12, 32, 16, 32, 8, 0, 48, 40, 8, 32, 48, 32, 36, 56, 0, 24, 32, 0, 4, 4, 8, 0, 0, 0, 0, 0, 24, 48, 16, 8, 0, 48, 24, 8, 20, 16, 32, 40, 50, 8, 0, 0, 8, 48, 8, 48, 28, 32, 0, 4, 56, 8, 16, 36, 16, 0, 32, 24, 44, 16, 8, 32, 0, 0, 36, 0, 48, 0, 32, 0, 32, 20, 16, 0, 36, 0, 20, 0, 40, 0, 56, 32, 32, 40, 8, 0, 44, 16, 16, 32, 4, 32, 32, 44, 16, 16, 8, 4, 4, 16, 16, 0, 8, 0, 4, 16, 0, 24, 16, 48, 0, 8, 4, 36, 0, 4, 0, 32, 48, 40, 16, 32, 20, 32, 0, 32, 8, 48, 0, 48, 8, 48, 24, 32, 16, 8, 28, 48, 12, 32, 24, 0, 16, 0, 32, 4, 16, 8, 56, 16, 0, 8, 8, 8, 48, 44, 36, 8, 48, 8, 32, 24, 0, 16, 8, 8, 32, 20, 16, 20, 4, 8, 24, 32, 32, 0, 56, 16, 0, 28, 32, 48, 40, 0, 48, 52, 24, 16, 16, 8, 32, 24, 48, 0, 4, 0, 32, 0, 0, 32, 8, 4, 0, 48, 24, 8, 8, 24, 4, 48, 4, 16, 16, 32, 20, 0, 8, 28, 20, 16, 0, 8, 32, 0, 8, 24, 16, 44, 8, 36, 40, 32, 16, 0, 8, 8, 32, 4, 32, 32, 24, 32, 0, 8, 0, 4, 16, 32, 8, 40, 32, 32, 16, 52, 36, 8, 0, 16, 40, 8, 0, 8, 48, 40, 56, 0, 0, 20, 0, 0, 56, 8, 52, 40, 16, 20, 32, 16, 16, 60, 16, 36, 32, 48, 24, 32, 24, 4, 40, 16, 20, 0, 16, 32, 48, 48, 24, 32, 16, 18, 56, 0, 52, 48, 16, 4, 24, 8, 8, 16, 16, 4, 4, 0, 40, 16, 20, 8, 0, 16, 32, 48, 0, 0, 8, 0, 16, 0, 24, 0, 20, 8, 16, 32, 24, 16, 16, 8, 12, 16, 0, 0, 48, 16, 36, 16, 0, 60, 40, 16, 4, 8, 0, 8, 0, 16, 4, 20, 32, 0, 8, 16, 48, 16, 4, 8, 34, 16, 0, 0, 36, 0, 0, 32, 16, 0, 0, 28, 32, 40, 16, 48, 0, 0, 40, 48, 16, 48, 16, 32, 16, 24, 4, 0, 0, 24, 0, 36, 8, 16, 12, 0, 48, 0, 8, 16, 36, 2, 8, 0, 8, 40, 52, 0, 4, 0, 0, 4, 36, 32, 48, 0, 0, 48, 0, 16, 48, 56, 32, 0, 56, 32, 20, 2, 24, 36, 28, 48, 0, 16, 16, 0, 0, 36, 32, 0, 16, 0, 4, 0, 4, 48, 60, 0, 0, 0, 8, 16, 20, 24, 0, 0, 36, 0, 0, 0, 4, 4, 0, 0, 16, 52, 0, 0, 16, 0, 0, 8, 0, 0, 36, 0, 44, 8, 24, 4, 36, 0, 40, 16, 16, 16, 16, 0, 24, 16, 24, 0, 0, 0, 12, 32, 24, 0, 16, 44, 24, 36, 8, 32, 32, 0, 8, 12, 24, 4, 36, 32, 8, 20, 2, 48, 32, 36, 48, 32, 8, 0, 56, 48, 40, 8, 16, 32, 0, 48, 16, 0, 8, 8, 8, 8, 0, 20, 4, 16, 8, 56, 40, 16, 8, 56, 0, 48, 16, 0, 40, 24, 32, 24, 0, 40, 36, 16, 8, 0, 32, 52, 4, 56, 0, 24, 8, 16, 20, 24, 48, 36, 12, 24, 36, 0, 4, 0, 4, 56, 16, 36, 8, 0, 36, 0, 0, 40, 32, 0, 12, 0, 32, 0, 40, 32, 32, 32, 48, 32, 16, 32, 56, 0, 0, 0, 0, 28, 40, 56, 12, 0, 0, 24, 24, 0, 16, 12]
#This is just for enabling specifice pixels to identify their position in the scan chain
ENABLE_ARRAY = [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

#This function adjusts bytes for use with the config chain. For 'mode' parameter, input "flip", "invert", or nothing.
def bit_manip(inbits, mode=None):
    outbits = []

    if type(inbits) != str:
        raise TypeError("bit_manip() requires binary string input.")

    if mode == "invert":
        for bit in inbits:
            if bit == '0':
                outbits.append('1')
            if bit == '1':
                outbits.append('0')
        return outbits
    
<<<<<<< Updated upstream
=======
    if mode == "flip":
        for i in range(len(inbits)):
            outbits.append(inbits[-i-1])
        return outbits
    
    if mode == None:
        return list(inbits)

#This function generates and loads the binary chain to set the trim levels for each ADC
#You can either give this function an integer or a list for the parameters 'captrim' and 'TestEn'
#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_run_config_chain(TestEn=1, InjEn=0, captrim=0, N_PIX=2048, Display=True):
    print("Generating Config Chain...")
    config_chain = []

    # Convert InjEn and TestEn to characters so they can be appended to a list of bits
    inj_en_bit = '1' if InjEn else '0'
    if type(TestEn) != list:
        test_en_bit = '1' if TestEn else '0'
    
    else:
        #If TestEn is a list, check that the list is the right size
        if len(TestEn) != N_PIX:
            raise ValueError("List of enable bits must have same number of entries as the number of pixels!")
        
        #Convert TestEn list to a list of strings
        for i in range(len(TestEn)):
            TestEn[i] = str(TestEn[i])

    #If the captrim input is a list, check that the list is the right size
    if type(captrim) == list:
        if len(captrim) != N_PIX:
            raise ValueError("List of cap trims must have same number of entries as the number of pixels!")

    #If the captrim input is an integer, ensure it is within the correct range, and convert it to a list 
    if type(captrim) == int:
        if (captrim < 0 or captrim > 63):
            raise ValueError("captrim must be between 0 and 63 (inclusive).")
        captrim = [captrim] * N_PIX
        
    #Construct config chain
    for i in range(int(N_PIX / 2)):
        for j in range(2):
            #Convert captrim to a 6-bit binary representation, flip it due to the way the captrim bits are fed
            captrim_bin = ''.join(bit_manip(format(captrim[(i*2)+j], '06b'), "flip"))

            #Decide whether this pixel is enabled (You can ignore this unless you only want to enable specific pixels)
            if type(TestEn) == list:
                test_en_bit = TestEn[(i*2)+j]

            #Create the 8-bit binary number as a list of characters
            config_byte = test_en_bit + inj_en_bit + captrim_bin

            #Check if the pixel is odd or not and flip the byte if it is
            if j == 0:
                config_double_byte = bit_manip(config_byte, "flip")
            else:
                config_double_byte = config_double_byte + list(config_byte)

        #Append the double-byte to the config chain
        config_chain = config_chain + config_double_byte

    #Convert the config chain to a list of integers
    config_chain = [int(bit) for bit in config_chain]

    #Show config chain for verification
    if Display:
        print("Config chain: ODD = (CT0-CT5, InjEn, TestEn) EVEN = (TestEn, InjEn, CT5-CT0)")
        for i in range(N_PIX):
            print(f"Pixel: {i+1}\tTrim:{captrim[i]}:{format(captrim[i],'06b')}\tByte:{config_chain[(i*8):(i*8)+8]}")

    #Initialize waves
    waves = {
    "configClk"     :    [0],   #Data is clocked in on positive edge
    "configIn"      :    [0],
    "configRst"     :    [0],   #Triggered by negative assertion, start with a reset
    "loadShadowReg" :    [1]    #Triggered by negative assertion
    }

    #Construct wave forms from config chain
    for i in range(N_PIX):
        for j in range(8):
            waves["configIn"] = waves["configIn"] + [config_chain[(i*8)+j]] * 2
            waves["configClk"] = waves["configClk"] + [0,1]
            waves["configRst"] = waves["configRst"] + [1,1]
            waves["loadShadowReg"] = waves["loadShadowReg"] + [1,1]
        waves["configClk"] = waves["configClk"] + [1,0]
        waves["configIn"] = waves["configIn"] + [0,0]
        waves["configRst"] = waves["configRst"] + [1,1]
        waves["loadShadowReg"] = waves["loadShadowReg"] + [1,1]

    #Add 2 extra clock cycles for the 2 additional config bits at the top of the config chain
    for i in range(2):
        waves["configIn"] = waves["configIn"] + [0,0]
        waves["configClk"] = waves["configClk"] + [0,1]
        waves["configRst"] = waves["configRst"] + [1,1]
        waves["loadShadowReg"] = waves["loadShadowReg"] + [1,1]

    #Load config chain into shadow register
    waves["configIn"] = waves["configIn"] + [0,0]
    waves["configClk"] = waves["configClk"] + [0,0]
    waves["configRst"] = waves["configRst"] + [1,1]
    waves["loadShadowReg"] = waves["loadShadowReg"] + [0,1]

    #Run the pattern
    sg.pr.run_pattern(genpattern_from_waves_dict(waves), outfile_tag="Result")
    print("Config Chain Loaded")

    #Display the waveforms
    if Display:
        result_glue = sg.gc.read_glue("result_PXI1Slot11_NI6583_se_io.glue")
        sg.gc.plot_glue(result_glue)
    
    return

#This function plots a given pixel's transfer function with parameters input by the user
#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_array_xf_check():
    #Filepaths for loading data or saving plots
    rawdata_filepath = "spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF"
    XFPlots_filepath = "spacely-asic-config\\XROCKET2\\PixelXF\\XF_Plots"

    #Choose whether to use existing data or create new data
    print("1: Create plots from raw data file")
    print("2: Create plots from new ADC acquisition")
    Mode = int(input("Please choose an operation: "))

    #Create plots using the data saved by array_trim_sweep
    if Mode == 1:
        print(f"Loading raw transfer functions from '{rawdata_filepath}'...")

        #Choose whether to view one XF or save all of them
        print("1: Save all trim plots to a folder")
        print("2: View a specific transfer function")
        Option = int(input("Please choose an operation: "))

        #Grab the list of test voltages from the raw data file, and convert them from strings to floats
        f = open(f"{rawdata_filepath}\\Vtest_range.csv", "r")
        Vtest_range = f.read().split(", ")
        f.close()
        for i in range(len(Vtest_range)):
            Vtest_range[i] = float(Vtest_range[i])

        Pixelnum = int(input("Which pixel do you want to see?: "))

        if Option == 1:
            input(f"Ensure folder '{XFPlots_filepath}\\TRIM_PLOTS\\PIXEL{str(Pixelnum) if Pixelnum > 9 else ('0' + str(Pixelnum))}_TRIMPLOTS' exists. Press [ENTER] to continue.")
            for trim in range(64):
                #Get the transfer function
                pixel_xf = extractXF(Pixelnum, trim)

                #Plot the data
                plt.scatter(np.array(Vtest_range), np.array(pixel_xf))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"XF of pixel #{Pixelnum} w/ Trim: {trim} CC: {correlation_coeff(Vtest_range, pixel_xf)} NL: {midpoint_DNL(Vtest_range, pixel_xf, (False if Pixelnum > 1024 else True))}")
                plt.savefig(f"{XFPlots_filepath}\\TRIM_PLOTS\\PIXEL{str(Pixelnum) if Pixelnum > 9 else ('0' + str(Pixelnum))}_TRIMPLOTS\\TRIM_{str(trim) if trim > 9 else ('0' + str(trim))}")
                plt.clf()

        #Repeat to let the user see multiple trim plots
        if Option == 2:
            while True:
                trim = input("Which trim value do you want to plot? (Press [ENTER] to end): ")
                if trim == "":
                    break
                else:
                    trim = int(trim)

                #Get the transfer function
                pixel_xf = extractXF(Pixelnum, trim)

                #Plot the data
                plt.scatter(np.array(Vtest_range), np.array(pixel_xf))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"XF of pixel #{Pixelnum} w/ Trim: {trim} CC: {correlation_coeff(Vtest_range, pixel_xf)} NL: {midpoint_DNL(Vtest_range, pixel_xf, (False if Pixelnum > 1024 else True))}")
                plt.show()
                plt.clf()

    #Create plots using newly acquired data
    if Mode == 2:
        print("1: Save all pixel's transfer function plots to file")
        print("2: See transfer function scatter-plot")
        print("3: See a specific pixel's transfer function")
        Option = int(input("Please choose an operation: "))

        #Create list of voltages to test
        increment = int(input("Please specify a voltage increment (mV): "))
        Vtest_range = [x for x in range(440, 541, increment)]
        print(f"Testing voltages: {Vtest_range}")

        #Set trim
        trim = input("Please specify a trim value, or press [ENTER] to use saved trims: ")
        trimstr = ('0' + trim) if len(trim) == 1 else trim
        if trim == "":
            trim = TRIM_ARRAY
        else:
            trim = int(trim)

        #Set time-scale factor
        TSF = input("Please specify a time-scale factor: ")
        if TSF == "":
            TSF = 1
        else:
            TSF = int(TSF)

        if Option == 1:
            input(f"Ensure folder '{XFPlots_filepath}\\ALL_PIXELS\\TRIM_{trimstr if type(trim) == int else 'IDEAL'}' exists. Press [ENTER] to continue.")

        #Get transfer functions at specified trim and voltages
        all_pixels_xf = get_array_transfer_functions(trim, Vtest_range, True, TSF)
        Pixelnum = 0

        #Save all transfer functions to file
        if Option == 1:
            for pixel_xf in all_pixels_xf:
                Pixelnum += 1
                R_coeff = correlation_coeff(Vtest_range, pixel_xf)

                #Create a graph of ADC response vs Vtest_range, and save it.
                plt.scatter(np.array(Vtest_range), np.array(pixel_xf))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"XF of pixel #{Pixelnum} w/ Trim: {trim if type(trim)==int else TRIM_ARRAY[Pixelnum - 1]} TSF: {TSF} R: {R_coeff}")
                plt.savefig(f"{XFPlots_filepath}\\ALL_PIXELS\\TRIM_{trimstr if type(trim) == int else 'IDEAL'}\\XF_ScatterPlot_Check_{Pixelnum}")
                plt.clf()

        #See transfer function scatter plot
        if Option == 2:
            for pixel_xf in all_pixels_xf[0:1023]:
                Pixelnum += 1

                #Show scatter plot for first half of pixels
                plt.scatter(np.array(Vtest_range), np.array(pixel_xf))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"Pixels 1-1024 XF scatter-plot w/ Trim: {trim if type(trim)==int else 'ARRAY'} TSF: {TSF}")
            plt.show()
            plt.clf()

            for pixel_xf in all_pixels_xf[1024:2047]:
                Pixelnum += 1
            
                #Show scatter plot for second half of pixels
                plt.scatter(np.array(Vtest_range), np.array(pixel_xf))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"Pixels 1025-2048 XF scatter-plot w/ Trim: {trim if type(trim)==int else 'ARRAY'} TSF: {TSF}")
            plt.show()
            plt.clf()

        #See a specific pixel's transfer function
        if Option == 3:
            while True:
                Pixelnum = input("Which pixel do you want to see? (Press [ENTER] to end): ")
                if Pixelnum == "":
                    break
                else:
                    Pixelnum = int(Pixelnum) - 1
                R_coeff = correlation_coeff(Vtest_range, all_pixels_xf[Pixelnum])

                #Report plateaus
                print("Plateaus:")
                for i in range(1024):
                    count = all_pixels_xf[Pixelnum].count(i)
                    if count > 1:
                        print(f"Value: {i}\t{format(i,'010b')}\tLength: {count}")

                #Create a scatter-plot for the specified pixel
                plt.scatter(np.array(Vtest_range), np.array(all_pixels_xf[Pixelnum]))
                plt.xlabel("Voltage Applied")
                plt.ylabel("ADC Response")
                plt.title(f"XF of pixel #{Pixelnum + 1} w/ Trim: {trim if type(trim)==int else TRIM_ARRAY[Pixelnum]} TSF: {TSF} R: {R_coeff}")
                plt.show()
                plt.clf()

#This function sweeps through each of the trim values, and saves transfer functions for all of the pixels
#When the function finishes, it returns the trim values that yield either the highest correlation coefficient or lowest DNL
#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_array_trim_sweep():
    N_PIX = 2048
    max_trim = 64
    VStart = 470 #mV
    VEnd = 505   #mV
    increment = 0.1
    num_samples = 10
    pixel_nl_vs_captrim = [[] for i in range(N_PIX)]

    #Create the list of voltages to be tested and save them to the raw data file, incremented at 0.1 mV
    Vtest_range = [(VStart + (x * increment)) for x in range(0, ((VEnd - VStart) / increment) + 1)]
    f = open("spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF\\Vtest_range.csv", "w")
    f.write(", ".join(str(voltage) for voltage in Vtest_range))
    f.close()

    #COLLECT XF DATA FOR EVERY PIXEL FOR EVERY CAPTRIM
    for captrim in range(max_trim):
        print(f"COLLECTION PHASE: {captrim+1}/{max_trim}")
        all_pixels_xf = get_array_transfer_functions(captrim, Vtest_range, False, 2, 0, num_samples)

        #Save transfer functions to raw data file
        f = open(f"spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF\\All_XF_Trim{('0' + str(captrim)) if captrim < 10 else str(captrim)}.csv", "w")
        for pixel in range(N_PIX):
            f.write(", ".join(str(value) for value in all_pixels_xf[pixel]))
            f.write("\n")
        f.close()

        for i in range(N_PIX):
            pixel_xf = all_pixels_xf[i]

            #Use this line for CC
            nonlinearity = correlation_coeff(Vtest_range, pixel_xf)
            pixel_nl_vs_captrim[i].append(nonlinearity)

            #Use the below lines for DNL
            # firsthalf = True if i < 1024 else False
            # if i != 0: #Skip first ADC
            #     nonlinearity = midpoint_DNL(Vtest_range, pixel_xf, firsthalf)
            # else:
            #     nonlinearity = 0
            # pixel_nl_vs_captrim[i].append(nonlinearity)

    #ANALYZE TO DETERMINE BEST CAPTRIM FOR EACH PIXEL
    correct_trim = [0] * N_PIX

    for i in range(N_PIX):
        correct_trim[i] = pixel_nl_vs_captrim[i].index(max(pixel_nl_vs_captrim[i]))
    
    print("Cap trim values:")
    print(correct_trim)

    return

#This function minimizes the voltage sweep necessary to cross the midpoint of each ADC's transfer function
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_sweep_minimizer():
    rawdata_filepath = "spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF"
    f = open(f"{rawdata_filepath}\\Vtest_range.csv", "r")
    Vtest_range = f.read().split(", ")
    f.close()
    for i in range(len(Vtest_range)):
        Vtest_range[i] = float(Vtest_range[i])

    highest_starting_index = 0
    lowest_ending_index = 0
    for trim in range(64):
        f = open(f"{rawdata_filepath}\\All_XF_Trim{str(trim) if trim > 9 else ('0' + str(trim))}.csv", "r")

        starting_index = 0
        ending_index = 0
        for pixel in range(2047):
            midpoint_code = 511 if pixel < 1025 else 751

            pixel_xf = f.readline().split(", ")
            for i in range(len(pixel_xf)):
                pixel_xf[i] = int(pixel_xf[i])

            try:
                starting_index = pixel_xf.index(midpoint_code) - 1
                ending_index = pixel_xf.index(midpoint_code + 2)

            except:
                continue

            else:
                if starting_index < 0:
                    starting_index = 0

                if (starting_index < highest_starting_index) or ((pixel == 0) and (trim == 0)):
                    highest_starting_index = starting_index

                if ending_index > lowest_ending_index:
                    lowest_ending_index = ending_index
        
        phase = round((100 / 64) * (trim + 1))
        print(f"Completion:\t%{phase}\tStart:\t{highest_starting_index}\tEnd:\t{lowest_ending_index}", end='\r')
        
        f.close()

    increment = Vtest_range[1] - Vtest_range[0]
    print(f"\nSmallest voltage sweep: {Vtest_range[0] + (highest_starting_index * increment)} - {Vtest_range[lowest_ending_index]} mV")
    print(f"This range is {round(((lowest_ending_index - highest_starting_index) / len(Vtest_range)), 5)} times the size.")
    return

#This function uses the data saved by array_trim_sweep and plots NL vs Trim for a desired pixel
#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_plot_NL():
    N_PIX = 2048
    max_trim = 64

    #***"CC" for correlation coefficient, "NL" for nonlinearity, "ENL" for efficient NL
    mode = "ENL"

    #Grab the list of test voltages from the raw data file, and convert them from strings to floats
    f = open("spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF\\Vtest_range.csv", "r")
    Vtest_range = f.read().split(", ")
    f.close()
    for i in range(len(Vtest_range)):
        Vtest_range[i] = float(Vtest_range[i])

    #Prompt the user for a pixel to view
    while True:
        Pixelnum = input("Which pixel do you want to see? (Press [ENTER] to end): ")
        if Pixelnum == "":
            break
        else:
            Pixelnum = int(Pixelnum)

        #Sweep through trim values, and get the NL of the XF at each trim value
        NL_vs_Trim = []
        for Trim in range(64):
            pixel_XF = extractXF(Pixelnum, Trim)

            #***Decide how to calculate NL based on mode
            if mode == "NL":
                NL_vs_Trim.append(midpoint_DNL(Vtest_range, pixel_XF, False if Pixelnum > 1024 else True))
            if mode == "CC":
                NL_vs_Trim.append(correlation_coeff(Vtest_range, pixel_XF))
            if mode == "ENL":
                NL_vs_Trim.append(efficient_NL(Vtest_range, pixel_XF, False if Pixelnum > 1024 else True))

        #Plot that data, playa
        plt.plot(np.array(range(max_trim)), np.array(NL_vs_Trim), marker='o')
        plt.xlabel("ADC Trim Value")
        plt.ylabel(f"ADC XF {mode}.")
        plt.title(f"ADC Trim vs. {mode} of pixel #{Pixelnum}")
        plt.grid(axis='y')
        plt.show()
        plt.clf()

#This function takes inputs for a given pixel (1-2048) and trim (0-63) and extracts the corresponding transfer function from the raw data file if it exists
def extractXF(Pixel, Trim):
    #Convert trim value to a formatted string
    Trim = str(Trim) if Trim > 9 else ('0' + str(Trim))

    #Open the file and go to the line corresponding to the desired pixel
    f = open(f"spacely-asic-config\\XROCKET2\\PixelXF\\Raw_XF\\All_XF_Trim{Trim}.csv", "r")
    for i in range(Pixel - 1):
        f.readline()

    #Split the line into a list of strings and close the file
    PixelXF = f.readline().split(", ")
    f.close()

    #Convert string list to an int list
    for i in range(len(PixelXF)):
        PixelXF[i] = int(PixelXF[i])

    return PixelXF

#This function calculates the mean absolute deviation for each transfer function compared to an example transfer function
#If display=True, then the function generates and displays a plot of the distribution
#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_deviation_distribution(display=True):
    #Set the example functions to compare each other function to (starting at #1)
    example_pixel1 = 2 #using #2 because #1 doesn't display correctly
    example_pixel2 = 1025

    output = []

    #Create voltage range to test ADC's at
    Vtest_range = [x for x in range(0,1001,10)]

    #Get the transfer functions and split the first half from the second half
    all_pixel_functions = get_array_transfer_functions(0, Vtest_range, False, 100)
    pixel_functions1 = all_pixel_functions[:1024]
    pixel_functions2 = all_pixel_functions[1024:]

    #Get the deviation for the first half
    array_deviation = []
    ignore = True   #Ignore deviation of pixel #1 so that it doesn't skew the scale of our output graphs
    for pixelxf in pixel_functions1:
        deviation = 0
        for i in range(len(pixelxf)):
            deviation += abs(pixelxf[i] - all_pixel_functions[example_pixel1-1][i])
        deviation = deviation / len(pixelxf)
        if ignore:
            deviation = 0
            ignore = False
        array_deviation.append(deviation)

    #Display a scatter plot if the function hasn't been called to return an array
    if display:
        print("Building plot #1")
        plt.scatter(np.array([x for x in range(1,1025)]), np.array(array_deviation))
        plt.xlabel("Pixel Number")
        plt.ylabel("Mean Absolute Deviation")
        plt.title("Pixels #1-1024 Deviation")
        plt.show()
        plt.clf()

    output.append(array_deviation)
    
    #Get the deviation for the second half
    array_deviation = []
    for pixelxf in pixel_functions2:
        deviation = 0
        for i in range(len(pixelxf)):
            deviation += abs(pixelxf[i] - all_pixel_functions[example_pixel2-1][i])
        deviation = deviation / len(pixelxf)
        array_deviation.append(deviation)

    #Display a scatter plot if the function hasn't been called to return an array
    if display:
        print("Building plot #2")
        plt.scatter(np.array([x for x in range(1025,2049)]), np.array(array_deviation))
        plt.xlabel("Pixel Number")
        plt.ylabel("Mean Absolute Deviation")
        plt.title("Pixels #1025-2048 Deviation")
        plt.show()
        plt.clf()
    
    output.append(array_deviation)
    return output

#This function returns the correlation coefficient for set of x and y ranges
def correlation_coeff(xrange, yrange):
    if len(xrange) != len(yrange):
        raise ValueError("X-range and Y-range lists must be the same length")
    
    xmean = mean(xrange)
    ymean = mean(yrange)

    numerator = 0.0
    for i in range(len(xrange)):
        numerator += ((xrange[i] - xmean) * (yrange[i] - ymean))

    denominator_x = 0.0
    denominator_y = 0.0
    for i in range(len(xrange)):
        denominator_x += (xrange[i] - xmean)**2
        denominator_y += (yrange[i] - ymean)**2

    denominator = np.sqrt(denominator_x * denominator_y)
     
    return round((numerator / denominator), 6)

#This function finds the nonlinearity at the midpoint by comparing the central step to the next higher step of the ADC transfer function
#If you're calling this function for pixels 1-1024, firsthalf = True
def midpoint_DNL(Vtest_range, pixel_xf, firsthalf=True):
    #The code output by the ADC at the middle of the voltage range (0-1000 mV)
    midpoint_code = 511 if firsthalf else 751

    #Attempt to run the function
    try:
        #Find the width of the first full step in the transfer function
        start_code = pixel_xf[0]
        voltage1 = Vtest_range[pixel_xf.index(start_code + 1)]
        voltage2 = Vtest_range[pixel_xf.index(start_code + 2)]

        #Find the width of the middle step of the transfer function
        voltage3 = Vtest_range[pixel_xf.index(midpoint_code)]
        voltage4 = Vtest_range[pixel_xf.index(midpoint_code + 1)]

        #Compare the two
        DNL = (voltage4 - voltage3) - (voltage2 - voltage1)

        return round(DNL, 3)

    #If the midpoint doesn't exist, return '-1' which indicates a missing code
    except:
        return -1

def efficient_NL(Vtest_range, pixel_xf, firsthalf=True):
    midpoint_code = 511 if firsthalf else 751
    ideal_LSB = 1000 / 1024
    step = 1

    while (midpoint_code not in pixel_xf) or ((midpoint_code + 1) not in pixel_xf):
        midpoint_code -= 1
        step += 1

    lower_code_voltages = []
    higher_code_voltages = []
    for i in range(len(pixel_xf)):
        if pixel_xf[i] == midpoint_code:
            lower_code_voltages.append(Vtest_range[i])
        if pixel_xf[i] == midpoint_code + step:
            higher_code_voltages.append(Vtest_range[i])
    
    lower_voltage = mean(lower_code_voltages)
    higher_voltage = mean(higher_code_voltages)
    voltage_step = higher_voltage - lower_voltage

    DNL = (voltage_step / (ideal_LSB * step)) - 1
    return DNL

#This function captures the transfer function of every pixel in the array, for a single value of CapTrim.
#  captrim = fixed value of CapTrim to use for ALL pixels
#  Vtest_range = list of Vtest values we want to sweep over
def get_array_transfer_functions(captrim, Vtest_range, Display=False, TSF=2, pixel_select=0, num_samples=1):
    
    N_PIX = 2048
    
    #Make a list to hold data from pixels
    Test_data = []
    
    #SETUP CHIP 
        # Biases are already set up by XROCKET2_Config.py
    
    #Program Config Chain
    ROUTINE_run_config_chain(1, 0, captrim, N_PIX, Display)

    #Configure AWG & purge scan chain
    sg.INSTR["AWG"].config_AWG_as_DC(Vtest_range[0])
    ROUTINE_adc_aquisition(time_scale_factor=TSF)
    get_scan_chain()
    
    #SWEEP OVER VTEST_RANGE AND RECORD RESULTS
    for Vtest in Vtest_range:
        
        #Set Vtest port voltage to Vtest
        sg.INSTR["AWG"].set_offset(Vtest)

        #Take the specified number of samples
        super_sample = [0 for x in range(2048)]
        for i in range(num_samples):
            #Run one ADC acquisition and read values from scan chain
            ROUTINE_adc_aquisition(time_scale_factor=TSF)
            sample = get_scan_chain()

            #Add the sample to the super sample
            for j in range(len(sample)):
                super_sample[j] = super_sample[j] + sample[j]

        #Find the mean value for each pixel
        mean_sample = [int(round(super_sample[i] / num_samples)) for i in range(len(super_sample))]
            
        #Read pixel data and add it to data array
        Test_data.append(mean_sample)

        #^THIS^
        #Creates a matrix like this:
        #[V1:[P1, P2, P3...],
        # V2:[P1, P2, P3...],
        # V3:[P1, P2, P3...]...] 
                          
    #Convert data array into a per-pixel transfer function array
    all_pixels_xf = []
    pixel_xf = []
    for Pixel in range(N_PIX):
        for Vtest in range(len(Vtest_range)):
            pixel_xf.append(Test_data[Vtest][Pixel])
        all_pixels_xf.append(pixel_xf)
        pixel_xf = []

        #^THIS^
        #Converts previous matrix to a matrix like this:
        #[P1:[V1, V2, V3...],
        # P2:[V1, V2, V3...],
        # P3:[V1, V2, V3...]...]

    #Return either full xf array, or a particular xf
    if pixel_select == 0:
        return all_pixels_xf
    else:
        return all_pixels_xf[pixel_select-1]

#This function clocks the scan chain to read the ADC outputs, then it parses and converts the data to a list of integers.
def get_scan_chain():
    #Check to see if the glue wave file already exists to save time
    if sg.gc.read_glue("spacely-asic-config\\XROCKET2\\Gluewaves\\Scan_Chain_read.glue") != None:
        wave = sg.gc.read_glue("spacely-asic-config\\XROCKET2\\Gluewaves\\Scan_Chain_read.glue")
        sg.pr.run_pattern(wave, outfile_tag="result")[0]

    #If the glue wave doesn't exist, create one and save it
    else:
        print("Generating new glue wave: spacely-asic-config\\XROCKET2\\Gluewaves\\Scan_Chain_read.glue")
        waves = {
            "scanClk": [],
            "scanEn": [],
            "scanLoad": [],
            "scanIn": [],
            "scanOut": []
        }

        #Create glue wave to cycle scanClk (# of pixels)*(10 bits) times
        for i in range(2048):
            for k in range(10):
                waves["scanIn"] = waves["scanIn"] + [0,0]
                waves["scanLoad"] = waves["scanLoad"] + [0,0]
                waves["scanClk"] = waves["scanClk"] + [0,1]
                waves["scanEn"] = waves["scanEn"] + [1,1]
            waves["scanIn"] = waves["scanIn"] + [0,0]
            waves["scanLoad"] = waves["scanLoad"] + [0,1]
            waves["scanClk"] = waves["scanClk"] + [0,0]
            waves["scanEn"] = waves["scanEn"] + [1,1]

        #Generate and save the pattern, then run it
        wave = genpattern_from_waves_dict(waves)
        sg.gc.write_glue(sg.gc.read_glue(wave), "spacely-asic-config\\XROCKET2\\Gluewaves\\Scan_Chain_read.glue")
        sg.pr.run_pattern(wave, outfile_tag="result")[0]

    #Extract the scanOut bitstream when scanClk is high
    result_glue = sg.gc.read_glue("result_PXI1Slot11_NI6583_se_io.glue")
    Output = sg.gc.get_clocked_bitstream(result_glue,"scanClk","scanOut")
    #sg.gc.plot_glue(result_glue)
    
    #Convert bitstream into a list of 10-bit pixel values
    pixel_data = []
    pixel_str = ""
    for i in range(2048):
        for j in range(10):
            #Converting bits to strings to easily string them together
            pixel_str = pixel_str + str(Output[(i*10)+j]) 
        pixel_data.append(pixel_str)
        pixel_str = ""
    
    #Convert binary values into decimals and return output
    for i in range(len(pixel_data)):
        pixel_data[i] = int(pixel_data[i],2)
         
    return pixel_data

#This function runs all of the ADC's through their aquisition sequence and outputs their data onto the scan chain
#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_adc_aquisition(time_scale_factor=2, apply_pulse_1_fix=False, tsf_qequal=1, tsf_pause=1, tsf_finalpause=0):

    #Location where the glue wave will be saved to reduce time spent regenerating glue wave during consecutive aquisitions
    filePath = "spacely-asic-config\\XROCKET2\\Gluewaves\\"
    fileName = f"ADC_Aquisition_TSF{time_scale_factor}.glue"

    #Check if the glue wave file already exists to save time
    if sg.gc.read_glue(filePath + fileName) != None:
        wave = sg.gc.read_glue(filePath + fileName)
        sg.pr.run_pattern(wave, outfile_tag="result")[0]

    #If the glue wave doesn't exist, create one and save it
    else:
        print(f"Generating new glue wave: {filePath + fileName}")

        Clk_d_trigger = False       #This is flipped to 'True' each time Clk fires, and is flipped back once Clk_d fires

        waves = {}
        
        #Start off w/ some zeros to avoid extra pulse bug.
        waves["Soc"]    = [1]*10    #Should be asserted at the beginning of the conversion (with the first DACclr).
        waves["DACclr"] = [0]*10    #Should be asserted on first capClk of each approximation cycle (1,2,4,7,11...)
        waves["Qequal"] = [0]*10    #Should be non-overlapping with capClk
        waves["capClk"] = [0]*9     #Should be asserted with Clk2 (Set to 9 to avoid race-condition. Without this, several ADC's have fragmented transfer functions)
        waves["Clk"]    = [0]*10    #Should be asserted with every DACclr except the first one
        waves["Clk2"]   = [0]*10    #Should be asserted with capClk
        waves["Clk_d"]  = [0]*10    #Should be asserted on the capClk cycle after Clk fires
        waves["scanEn"] = [0]*10    #Must be low to acquire ADC data
        waves["scanClk"]= [0]*10    #Must be low to acquire ADC data
        
        #Start of conversion pulse
        waves["Soc"]    = waves["Soc"] + [0]
        waves["Soc"]    = waves["Soc"] + [1]

        #Whether or not to extend first phase
        extend = 10 if apply_pulse_1_fix else 1
        
        #Loop through acquisition phases
        for adc_bit in range(1,12):
            #Loop through clock cycles in each phase
            for clk_cycle in range(adc_bit):
                #Check if it's the first clock cycle of a phase
                if clk_cycle == 0:
                    #Each phase starts off w/ a DACclr pulse.
                    waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor*extend
                    waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor*extend
                    waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor*extend
                    waves["Clk_d"]  = waves["Clk_d"]  + [0,0,0]*time_scale_factor*extend
                    
                    #Clk is synced with DACclr except for the first pulse.
                    if adc_bit != 1:
                        waves["Clk"] = waves["Clk"] + [1,1,1]*time_scale_factor*extend
                        Clk_d_trigger = True
                    else:
                        waves["Clk"] = waves["Clk"] + [0,0,0]*time_scale_factor*extend

                else:
                    #capClk pulse
                    waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor
                    waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
                    waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor
                    waves["Clk"]    = waves["Clk"]    + [0,0,0]*time_scale_factor
                    
                    #check if Clk fired last capClk cycle
                    if Clk_d_trigger:
                        waves["Clk_d"] = waves["Clk_d"] + [1,1,1]*time_scale_factor
                        Clk_d_trigger = False
                    else:
                        waves["Clk_d"] = waves["Clk_d"] + [0,0,0]*time_scale_factor

                #Add a 0 for non-overlapping.    
                waves["DACclr"] = waves["DACclr"] + [0]*tsf_pause
                waves["capClk"] = waves["capClk"] + [0]*tsf_pause
                waves["Qequal"] = waves["Qequal"] + [0]*tsf_pause
                waves["Clk"]    = waves["Clk"]    + [0]*tsf_pause
                waves["Clk_d"]  = waves["Clk_d"]  + [0]*tsf_pause
                
                #Qequal pulse
                waves["DACclr"] = waves["DACclr"] + [0,0,0]*time_scale_factor*tsf_qequal
                waves["capClk"] = waves["capClk"] + [0,0,0]*time_scale_factor*tsf_qequal
                waves["Qequal"] = waves["Qequal"] + [1,1,1]*time_scale_factor*tsf_qequal
                waves["Clk"]    = waves["Clk"]    + [0,0,0]*time_scale_factor*tsf_qequal
                waves["Clk_d"]  = waves["Clk_d"]  + [0,0,0]*time_scale_factor*tsf_qequal
                
                #Add a 0 for non-overlapping.    
                waves["DACclr"] = waves["DACclr"] + [0]*tsf_pause
                waves["capClk"] = waves["capClk"] + [0]*tsf_pause
                waves["Qequal"] = waves["Qequal"] + [0]*tsf_pause
                waves["Clk"]    = waves["Clk"]    + [0]*tsf_pause
                waves["Clk_d"]  = waves["Clk_d"]  + [0]*tsf_pause
                
            waves["DACclr"] = waves["DACclr"] + [0]*tsf_finalpause
            waves["capClk"] = waves["capClk"] + [0]*tsf_finalpause
            waves["Qequal"] = waves["Qequal"] + [0]*tsf_finalpause
            waves["Clk"]    = waves["Clk"]    + [0]*tsf_finalpause
            waves["Clk_d"]  = waves["Clk_d"]  + [0]*tsf_finalpause
            
        #Final DACclr pulse.
        waves["DACclr"] = waves["DACclr"] + [1,1,1]*time_scale_factor
        waves["capClk"] = waves["capClk"] + [1,1,1]*time_scale_factor
        waves["Qequal"] = waves["Qequal"] + [0,0,0]*time_scale_factor
        waves["Clk"]    = waves["Clk"]    + [1,1,1]*time_scale_factor
        waves["Clk_d"]  = waves["Clk_d"]  + [0,0,0]*time_scale_factor

        #Have clk2's waveform mirror capClk's waveform
        waves["Clk2"] = waves["capClk"]

        #Generate glue wave, save it, then send to ASIC
        wave = genpattern_from_waves_dict(waves)
        sg.gc.write_glue(sg.gc.read_glue(wave), filePath + fileName)
        sg.pr.run_pattern(wave, outfile_tag="result")[0]

    return
        
#<<Registered w/ Spacely as ROUTINE 14, call as ~r14>>
def ROUTINE_FC_Avg_XF(experiment=None, data_file=None):
    """Capture the Average FullConv Transfer function"""

    if experiment is None: #Interactive mode
    
        custom_name = input("Custom Exp name?")
    
        e = Experiment(custom_name)    
    
        e.set("VIN_STEP_uV",1000)
        e.set("VIN_STEP_MAX_mV",1000)
        e.set("VIN_STEP_MIN_mV",5)
        
        e.set("NUM_AVERAGES",20)
    
        #NOTES:
        # - Trigger must be supplied from NI, pre-level-shifters. 

        input("""NOTE: PLEASE CONFIRM THAT
        1) AWG TRIG IS CONNECTED to phi1_ext (silk as 'P1.0') on the NI side.
        2) Scope Ch1 is also connected to P1.0
        3) Scope Ch2 is also connected to halt_sample (silk as 'Charge')""")
    
        #Set default values for the whole experiment.    
        e.set("time_scale_factor",10)
        e.set("tsf_sample_phase",2)
        
        e.set("Range2",0)       
        
        e.set("CapTrim",25)
        
        e.set("n_skip",1)
        e.set("SINGLE_PULSE_MODE",True)
        
    else:
        e = experiment
        
    if data_file is None:    
        df_name = f'FullConv_Noise_Histogram_{e.get("VIN_mV")}mV_on_'+time.strftime("%Y_%m_%d")
        
        df = e.new_data_file(df_name)
    else:
        df = data_file
        
           
    #############################################################################
    
    if not df.check(["tsf_sample_phase","Range2","CapTrim","n_skip","VIN_STEP_uV","VIN_STEP_MAX_mV","VIN_STEP_MIN_mV"]):
        return -1
    
    df.set("check_halt_sample",False)

    VIN_STEP_uV = df.get("VIN_STEP_uV")

    NUM_AVERAGES = df.get("NUM_AVERAGES")
    
    VIN_MIN_mV = df.get("VIN_STEP_MIN_mV")
    
    VIN_MAX_mV = df.get("VIN_STEP_MAX_mV")
    
    VIN_RANGE = [i/1000 for i in range(int(1000*VIN_MIN_mV),int(1000*VIN_MAX_mV),VIN_STEP_uV)]

    fc_glue = setup_full_conversion(df)
    
    if df.get("check_halt_sample"):
        df.write("Vin,Avg Result,Std Dev,Avg Halt_Sample\n")
    else:
        df.write("Vin,Avg Result, Std Dev\n")

    for vin in VIN_RANGE:
                
        #Set the input voltage:
        sg.INSTR["AWG"].set_pulse_mag(vin)

        results_this_vin = []
        hs_this_vin = []

        for i in range(NUM_AVERAGES):  
            
            #Pass 'None' for pulse_mag because we DON'T want to set it each time, only once at the beginning.
            result = get_full_conversion_result(fc_glue, None, df)

            if df.get("check_halt_sample"):
                hs_this_vin.append(halt_sample)

            results_this_vin.append(result)
                
        if df.get("check_halt_sample"):
            df.write(f"{vin},{np.mean(results_this_vin)},{np.std(results_this_vin)},{np.mean(hs_this_vin)}\n")
        else:
            df.write(f"{vin},{np.mean(results_this_vin)},{np.std(results_this_vin)}\n")
     
    df.close()

#PIXEL MAPPING FUNCTIONS BELOW####################################################################################################################

## XR2 Pixel Location Tool
# For each pixel in order on the scan chain, this tool gives its physical location.
# (0,0) is the top left of the chip. X is horizontal left to right, Y is vertical top to bottom.
# For example, the four pixels in the upper-left corner of the array have the coordinates:
# (0,0) (1,0)
# (0,1) (1,1)
#
# phys_coords = (x,y) coords in physical space
# superpix_coord = 4-index coords in the logical space that follows the organization in source RTL
# scan_chain_coords = index on the scan chain, from 0 to 1023

def superpix_coord_to_phys_coord(super_row, super_col, pix_row, pix_col):
    y = super_row*4 + pix_row
    x = super_col*4 + pix_col
    return (x,y)

def phys_coord_to_superpix_coord(x,y):
    super_col = int(x/4)
    pix_col = x % 4
    super_row = int(y/4)
    pix_row = y % 4
    return (super_row, super_col, pix_row, pix_col)

def superpix_coord_to_scan_chain_coord(super_row, super_col, pix_row, pix_col):
    sc_idx = pix_col + pix_row*4 + super_col*16 + super_row*128
    return sc_idx

def gen_pixel_coords():
    #Generate phys_coords for all pixels in a 32x32 grid
    superpix_coords = []
    phys_coords = []

    for super_row in range(8):
        for super_col in range(8):
            for pix_row in range(4):
                for pix_col in range(4):
                    superpix_coords.append((super_row, super_col, pix_row, pix_col))
                    phys_coords.append(superpix_coord_to_phys_coord(super_row, super_col, pix_row, pix_col))

    # print("PHYS COORDS PER PIXEL")
    # print(phys_coords)

    #Display pixel map
    # print("SCAN CHAIN INDICES OF EACH PHYSICAL PIXEL IN THE ARRAY")
    # print("(0 is the first and 1023 is the last pixel in the scan chain)")

    # for y in range(32):
    #     row_string = ""
    #     for x in range(32):
    #         sr, sc, r, c = phys_coord_to_superpix_coord(x,y)
    #         sc_idx = superpix_coord_to_scan_chain_coord(sr, sc, r, c)
    #         row_string = row_string + f"{sc_idx:4}|"
    #     print(row_string)
    #     print("-----"*32)

    return phys_coords

#This function creates a heatmap with the pixels in their correct positions respective to one another and a color gradient dependent on a list of data values for each pixel
def construct_pixel_grid(pixel_vals, pixel_coords):
    xvals = []
    yvals = []
    for i in range(len(pixel_vals)):
        xvals.append(pixel_coords[i][0])
        yvals.append(pixel_coords[i][1])
    
    cvals = np.array(pixel_vals)
    xvals = np.array(xvals)
    yvals = np.array(yvals)

    plt.scatter(xvals, yvals, c=cvals, cmap='viridis')
    plt.colorbar()
    pix = "1-1024" if pixel_vals[1] == 0 else "1025-2048"
    plt.title(f"ADC Mean-Absolute-Deviation Heatmap for ADC's {pix}")
    plt.xlabel("ADC X Position")
    plt.ylabel("ADC Y Position")
    plt.show()

#This function creates a map of each ADC's mean absolute deviation with respect to its position on the ASIC
#<<Registered w/ Spacely as ROUTINE 15, call as ~r15>>
def ROUTINE_pixel_deviation_grid():
    #Get mean absolute deviation array and pixel coordinate array
    MAD_array = ROUTINE_deviation_distribution(False)
    pixel_coords = gen_pixel_coords()

    #Feed each half of the deviation array to the heatmap function
    for i in range(2):
        pixel_vals = MAD_array[i]
        construct_pixel_grid(pixel_vals, pixel_coords)
>>>>>>> Stashed changes
