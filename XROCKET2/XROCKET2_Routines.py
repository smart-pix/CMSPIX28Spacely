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
    waves["scanClkEN"] = [0]
    waves["serialClkEN"] = [0]
    waves["configClkEN"] = [0]
    waves["expected_serialOut_AE"] = [0]
    waves["expected_serialOut_PCA"] = [0]

    waves["reset"] = [1]
    waves["scanEn"] = [0]
    waves["ClkPCA"] = [0]
    waves["scanClkEN"] = [0]
    waves["serialClkEN"] = [0]
    waves["configClkEN"] = [0]
    waves["reset"] = [0]


def resetDUT():

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

    return genpattern_from_waves_dict(waves)

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_scanChain(PCA_datain, AE_datain):
    SCAN_CHAIN_BITS = 2 * 1024 * 10
    waves = {
        "scanClkEN": [],
        "scanEn": [],
        "scanLoad": [],
        "scanIn": []
    }

    # Initial setup
    waves["scanClkEN"] = [1]  # scanClkEN enabled
    waves["scanEn"] = [1]      # scanEn enabled
    waves["scanLoad"] = [0]    # scanLoad initial state

    # Loading PCA ScanChain
    testcase = "Loading PCA"
    for i in range(1024):
        for j in range(10):
            waves["scanIn"].append(PCA_datain[i][9 - j])
            waves["scanLoad"].append(0)
            waves["scanClkEN"].append([1, 0])  # Clock cycle

        waves["scanLoad"].append(1)
        waves["scanClkEN"].append([0, 1])  # Negative edge cycle
        waves["scanEn"].append(1)

    # Loading AE ScanChain
    testcase = "Loading AE"
    for i in range(1024):
        for j in range(10):
            waves["scanIn"].append(AE_datain[i][9 - j])
            waves["scanLoad"].append(0)
            waves["scanClkEN"].append([1, 0])  # Clock cycle

        waves["scanLoad"].append(1)
        waves["scanClkEN"].append([0, 1])  # Negative edge cycle
        waves["scanEn"].append(1)

    # Finalizing the scan operation
    for j in range(10):
        waves["scanLoad"].append(0)
        waves["scanClkEN"].append([1, 0])  # Clock cycle

    waves["scanLoad"].append(1)
    waves["scanClkEN"].append([0, 1])  # Negative edge cycle

    # Disabling the scan clock and scan enable signals
    waves["scanClkEN"].append(0)
    waves["scanEn"].append(0)
    waves["scanLoad"].append(0)

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
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

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_scanChainCheck(AE_datain):
    waves = {
        "scanClkEN": [],
        "scanEn": [],
        "scanLoad": [],
        "scanIn": [],
        "scanOut": [],
    }

    # Initial setup
    waves["scanClkEN"].append([0, 1])
    waves["scanEn"].append([0, 1])
    waves["scanLoad"].append([0, 0])

    # Loading Data through ScanChain (2048 * 10)
    for _ in range(2):  # Repeat twice as per the task
        for i in range(1024):
            for j in range(10):
                waves["scanIn"].append(AE_datain[i][j])
                waves["scanLoad"].append(0)
                waves["scanClkEN"].append([1, 0])
                waves["scanEn"].append(1)
            waves["scanLoad"].append(1)
            waves["scanClkEN"].append([0, 1])
            waves["scanEn"].append(1)

    # Checking Outputs
    for _ in range(2):  # Repeat twice as per the task
        for i in range(1024):
            waves["scanIn"].append(0)
            for j in range(10):
                waves["scanLoad"].append(0)
                waves["scanClkEN"].append([1, 0])
                waves["scanEn"].append(1)
                # Note: This is where mismatch checking would occur
                # Since we don't have scanOut values, let's just log the wave
                waves["scanOut"].append("check")  # Placeholder for output checking
                # In actual usage, compare scanOut to AE_datain[i][j]
            waves["scanLoad"].append(1)
            waves["scanClkEN"].append([0, 1])
            waves["scanEn"].append(1)

    # Final state
    waves["scanClkEN"].append(0)
    waves["scanEn"].append(0)
    waves["scanLoad"].append(0)

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_checkAE(AE_dataout):
    waves = {
        "ClkAE": [],
        "dataLatchClkAE": [],
        "serialClkEN": [],
        "expected_serialOut_AE": []
    }

    # Initial setup
    waves["ClkAE"].append(0)
    waves["dataLatchClkAE"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_AE"].append(0)

    # scanChain() - Placeholder for the scan chain function, assume it has been run

    # Clock AE toggling for 30 cycles
    for _ in range(30):
        waves["ClkAE"].append(0)
        waves["ClkAE"].append(1)
    
    # Latching and writing data
    waves["ClkAE"].append(0)
    waves["dataLatchClkAE"].append(0)
    # Placeholder for writeArray() and writecompressed() operations

    # Enable serial clock
    waves["serialClkEN"].append(1)

    # Expected serial output AE
    waves["expected_serialOut_AE"].append(AE_dataout[0][0])
    waves["dataLatchClkAE"].append(1)

    # Check Serial Data
    for i in range(32):
        for j in range(5):
            if i == 0 and j == 0:
                j += 1  # Skip Header
            waves["expected_serialOut_AE"].append(AE_dataout[i][j])
            waves["serialClkEN"].append(1)
    
    waves["expected_serialOut_AE"].append(0)
    waves["serialClkEN"].append(0)

    # Ensure vertical alignment of all waveforms
    max_len = max(len(waves[key]) for key in waves)
    for key in waves:
        waves[key].append([waves[key][-1]] * (max_len - len(waves[key])))

    # Generate glue wave and send to ASIC, then plot results
    glue_wave = genpattern_from_waves_dict(waves)
    result_glue = sg.pr.run_pattern(glue_wave, outfile_tag="result")[0]
    sg.gc.plot_glue(result_glue)

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_checkPCA(PCA_dataout):

    waves = {
        "ClkPCA": [],
        "dataLatchClkPCA": [],
        "serialClkEN": [],
        "expected_serialOut_PCA": []
    }

    # Initial setup
    waves["ClkPCA"].append(0)
    waves["dataLatchClkPCA"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)

    # scanChain() - Placeholder for the scan chain function, assume it has been run
    # Perform scanChain here
    waves["ClkPCA"].append(0)
    waves["dataLatchClkPCA"].append(0)
    waves["serialClkEN"].append(0)
    waves["expected_serialOut_PCA"].append(0)

    # Toggling ClkPCA for 30 cycles
    for _ in range(30):
        waves["ClkPCA"].append(1)
        waves["dataLatchClkPCA"].append(0)
        waves["serialClkEN"].append(0)
        waves["expected_serialOut_PCA"].append(0)
        waves["ClkPCA"].append(0)
        waves["dataLatchClkPCA"].append(0)
        waves["serialClkEN"].append(0)
        waves["expected_serialOut_PCA"].append(0)
    
    # Latching and writing data
    waves["ClkPCA"].append(0)
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
                waves["ClkPCA"].append(0)
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

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_writeArray(array_data, filename="ArrayData_AE.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(5120):
            fp.write(f"{array_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 5:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_writeArray_PCA(array_data, filename="ArrayData_PCA.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(10240):
            fp.write(f"{array_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 10:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_writecompressed(compressed_data, filename="compressedData.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(150):
            fp.write(f"{compressed_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 5:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_writecompressed_PCA(compressed_data, filename="compressedData_PCA.txt"):
    counter = 0
    with open(filename, "w") as fp:
        for i in range(210):
            fp.write(f"{compressed_data[i]:0b}")  # Writing the binary representation
            counter += 1
            if counter == 7:
                fp.write(" ")
                counter = 0
    # No need to explicitly close the file, as the context manager handles it

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
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

#Sub-Routine
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_unstick_VDD_ASIC():
    
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
    

#######################################################################################################
# HELPER FUNCTIONS
#######################################################################################################

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
    
