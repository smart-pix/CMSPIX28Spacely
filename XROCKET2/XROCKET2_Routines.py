# XROCKET2-Specific Routines

import sys
import platform
import os
import numpy as np
import serial.tools.list_ports
import atexit
import argparse
from datetime import datetime
from prettytable.colortable import PrettyTable
from si_prefix import si_format
from statistics import mean, NormalDist
import csv

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import colors


#Import utilities from py-libs-common
from hal_serial import * #todo: this shouldn't import all symbols but just the ArudinoHAL class
from pattern_runner import *
from fnal_libawg import AgilentAWG
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
    


ROUTINES = [XROCKET2_Config_Chain, XROCKET2_Scan_Chain, XROCKET2_Serial_Readout, XROCKET2_Vtest_Readout, XROCKET2_DNL_Trim, XROCKET2_ascii_scan_chain_demo, ]
