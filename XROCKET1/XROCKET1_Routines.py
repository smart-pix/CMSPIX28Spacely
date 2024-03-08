# XROCKET1-specific Test Routines #

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
import Spacely_Globals as sg
from Spacely_Utils import *



def ROUTINE4_XROCKET1_Config():
    """r4: Flash the config chain for XROCKET1 and read the result back."""


    print("""REQUIREMENTS:
        > NI FPGA should be connected to XROCKET1.
        > XROCKET1 should be powered up.
        """)
    input("Press Enter to continue...")
    
    
    #Data files

    tp1_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\xrocket1_config_input_se_io.glue"
    tp1_out_file = "C:\\Users\\aquinn\Desktop\\SPROCKET Test\\spacely\\PySpacely\\xrocket1_config_output_PXI1Slot5_NI6583_se_io.glue"
    tp1_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\xrocket1_config_golden_se_io.glue"
    #glue_bitfile = "C:\\Users\\Public\\Documents\\LABVIEWTEST\\GlueDirectBitfile_6_27_b.lvbitx"

   
    #Set up classes
    tp = PatternRunner(sg.log, DEFAULT_IOSPEC)

    #hardware_dict = {input_wave.fpga_name:NiFpga(log,input_wave.hardware[0])}
    #hardware_dict["PXI1Slot5/NI6583"].start(glue_bitfile)

    #dbg = NiFpgaDebugger(log, hardware_dict["PXI1Slot5/NI6583"])
    #dbg.configure(GLUEFPGA_DEFAULT_CFG)

    #NOTE: FPGA Needs > 2 seconds of delay in between setup and running the first test pattern!
    time.sleep(3)

    print("Running XROCKET1 Config!")
    
    tp.run_pattern(tp1_in_file, outfile_tag="xrocket1_config_output")
    gc = GlueConverter(DEFAULT_IOSPEC)
    gc.compare(gc.read_glue(tp1_golden), gc.read_glue(tp1_out_file))


def ROUTINE5_XROCKET1_Readout():
    """Test Serial Readout"""

    print("""REQUIREMENTS:
        > NI FPGA should be connected to XROCKET1.
        > XROCKET1 should be powered up.
        """)
    input("Press Enter to continue...")


    #Data files

    #tp1_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\xrocket1_config_input_se_io.glue"
    tp1_in_file = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\XR1_force_config_low.glue"  #configIn_force_high.glue"
    tp1_out_file = "C:\\Users\\aquinn\Desktop\\SPROCKET Test\\spacely\\PySpacely\\xrocket1_out_PXI1Slot16_NI6583_se_io.glue"
    tp1_golden = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\xrocket1_config_golden_se_io.glue"
    readback_se_io = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\XR1_readback_se_io_reset_active_low.glue" #xrocket1_readback_input_with_reset_se_io.glue"
    readback_lvds  = "C:\\Users\\Public\\Documents\\XROCKET Test and Analysis\\XROCKET1\\xrocket1_readback_input_lvds.glue"

    tp = PatternRunner(sg.log, DEFAULT_IOSPEC, DEFAULT_FPGA_BITFILE_MAP)

    config_AWG_as_DC(0)

    time.sleep(3)

    print("Running XROCKET1 Readback!")
    tp.run_pattern(tp1_in_file, outfile_tag="xrocket1_config_output")
    tp._interface["PXI1Slot16/NI6583"].interact('w','lvds_clockout_en',True)
    time.sleep(1)
    tp.run_pattern([readback_se_io,readback_lvds], outfile_tag="xrocket1_readback_output")



ROUTINES = [ROUTINE4_XROCKET1_Config, ROUTINE5_XROCKET1_Readout]
