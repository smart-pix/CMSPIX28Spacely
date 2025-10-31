'''
Author: Anthony Badea, Benjamin Parpillon
Date: June, 2024
'''

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

def onstartup():

    # GLOBAL CONFIG VARIABLES
    assume_defaults = False
    
    print("====================================")
    print("=== Starting CMSPIX28 Default Setup ===")

    if not assume_defaults:
        do_setup = input("Press enter to begin or 'n' to skip >")
        if 'n' in do_setup:
            print("Skipping all setup!")
            return

    init_car =  input("Step 2: Initializing CaR Board ('n' to skip)>>>")

    if 'n' in init_car:
        print("Skipped!")
    else:

        #Basic initialization of CaR board
        sg.INSTR["car"].init_car()

        #Init CMOS I/O voltages
        print(">  Setting CMOS In/Out Voltage = 0.9 V",end='')
        if not assume_defaults: 
            set_cmos_voltage = input("('n' to skip)")
        if assume_defaults or not 'n' in set_cmos_voltage:
            sg.INSTR["car"].set_input_cmos_level(0.9)
            sg.INSTR["car"].set_output_cmos_level(0.9)
        print("finished setting CMOS")
       

    init_asic = input("Step 3: Initializing ASIC ('n' to skip)>>>")

    if 'n' in init_asic:
        print("Skipped!")
    else:
        iDVDD = V_PORT["vddd"].get_current()
        iAVDD = V_PORT["vdda"].get_current()
        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")
        print("Programming of the ASIC shift register")
        # ROUTINE_IP1_test1() -> converted to ROUTINE_ProgPixelsOnly()
        print("shift register Programmed")
        iDVDD = V_PORT["vddd"].get_current()
        iAVDD = V_PORT["vdda"].get_current()
        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_ProgShiftRegRaw(
        configclk_period=ROUTINE_SETTINGS["configclk_period"], cfg_test_delay=ROUTINE_SETTINGS["cfg_test_delay"], 
        cfg_test_sample=ROUTINE_SETTINGS["cfg_test_sample"],cfg_test_gate_config_clk=ROUTINE_SETTINGS["cfg_test_gate_config_clk"]):
    return ProgShiftRegRaw(configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk)

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_ProgPixelsOnly(
        configclk_period=ROUTINE_SETTINGS["configclk_period"], cfg_test_delay=ROUTINE_SETTINGS["cfg_test_delay"], 
        cfg_test_sample=ROUTINE_SETTINGS["cfg_test_sample"],cfg_test_gate_config_clk=ROUTINE_SETTINGS["cfg_test_gate_config_clk"],
        pixelList = [0], pixelValue=[1]):
    return ProgPixelsOnly(configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk,pixelList, pixelValue) 

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_ProgShiftRegs(
        progDebug=False, verbose=False, 
        configclk_period=ROUTINE_SETTINGS["configclk_period"], cfg_test_delay=ROUTINE_SETTINGS["cfg_test_delay"], 
        cfg_test_sample=ROUTINE_SETTINGS["cfg_test_sample"],cfg_test_gate_config_clk=ROUTINE_SETTINGS["cfg_test_gate_config_clk"], 
        iP=0, timeSleep=0.011):
    return ProgShiftRegs(progDebug, verbose, configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk, iP, timeSleep)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_ScanChainOneShot(
        scan_load_delay=ROUTINE_SETTINGS["scan_load_delay"], startBxclkState=ROUTINE_SETTINGS["startBxclkState"], 
        bxclk_delay=ROUTINE_SETTINGS["bxclk_delay"], bxclk_period=ROUTINE_SETTINGS["bxclk_period"],
        injection_delay=ROUTINE_SETTINGS["injection_delay"], scanLoopBackBit=ROUTINE_SETTINGS["scanLoopBackBit"], 
        test_sample=ROUTINE_SETTINGS["test_sample"], test_delay=ROUTINE_SETTINGS["test_delay"], 
        scanLoadPhase =ROUTINE_SETTINGS["scanLoadPhase"]):
    return ScanChainOneShot(scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, scanLoadPhase )

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_PreProgSCurve(
        scanLoadPhase =ROUTINE_SETTINGS["scanLoadPhase"], 
        scan_load_delay=ROUTINE_SETTINGS["scan_load_delay"], startBxclkState=ROUTINE_SETTINGS["startBxclkState"], 
        bxclk_delay=ROUTINE_SETTINGS["bxclk_delay"], bxclk_period=ROUTINE_SETTINGS["bxclk_period"],
        injection_delay=ROUTINE_SETTINGS["injection_delay"], scanLoopBackBit=ROUTINE_SETTINGS["scanLoopBackBit"], 
        test_sample=ROUTINE_SETTINGS["test_sample"], test_delay=ROUTINE_SETTINGS["test_delay"], 
        v_min = 0.001, v_max=0.4, v_step=0.001, nsample=1000, nPix=0):
    return PreProgSCurve(scanLoadPhase, scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, v_min, v_max, v_step, nsample, nPix)

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_SCurveMatrix():
    return SCurveMatrix()

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_DNN(
        progDebug=False, loopbackBit=ROUTINE_SETTINGS["loopbackBit"], patternIndexes = [0], verbose=False, 
        injection_delay=ROUTINE_SETTINGS["injection_delay"], bxclk_period=ROUTINE_SETTINGS["bxclk_period"],
        startBxclkState=ROUTINE_SETTINGS["startBxclkState"],scan_load_delay=ROUTINE_SETTINGS["scan_load_delay"], 
        cfg_test_delay=ROUTINE_SETTINGS["cfg_test_delay"], cfg_test_sample=ROUTINE_SETTINGS["cfg_test_sample"], 
        progResetMask=ROUTINE_SETTINGS["progResetMask"], configclk_period=ROUTINE_SETTINGS["configclk_period"], 
        test_delay=ROUTINE_SETTINGS["test_delay"], test_sample=ROUTINE_SETTINGS["test_sample"], 
        bxclk_delay=ROUTINE_SETTINGS["bxclk_delay"],configClkGate=ROUTINE_SETTINGS["configClkGate"],
        scanLoadPhase =ROUTINE_SETTINGS["scanLoadPhase"],
        vth0 = 0.08, vth1=0.16, vth2=0.32, readYproj=True, 
        pixel_compout_csv=FNAL_SETTINGS["pixel_compout_csv"], dnn_csv=FNAL_SETTINGS["dnn_csv"]
):
        
        return DNN(progDebug,loopbackBit, patternIndexes, verbose, injection_delay, bxclk_period, startBxclkState, scan_load_delay, cfg_test_delay, cfg_test_sample, progResetMask, configclk_period, test_delay, test_sample, bxclk_delay,configClkGate, scanLoadPhase, vth0=vth0, vth1=vth1, vth2=vth2, readYproj=readYproj, pixel_compout_csv=pixel_compout_csv, dnn_csv=dnn_csv)

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_DiscrimTuneScanChain(
        nEvents=1000, time_sleep = 1, dnn_Pattern=0,  
        scan_load_delay=ROUTINE_SETTINGS["scan_load_delay"], startBxclkState=ROUTINE_SETTINGS["startBxclkState"], 
        bxclk_delay=ROUTINE_SETTINGS["bxclk_delay"], bxclk_period=ROUTINE_SETTINGS["bxclk_period"],
        injection_delay=ROUTINE_SETTINGS["injection_delay"], scanLoopBackBit=ROUTINE_SETTINGS["scanLoopBackBit"], 
        test_sample=ROUTINE_SETTINGS["test_sample"], test_delay=ROUTINE_SETTINGS["test_delay"], 
        scanLoadPhase =ROUTINE_SETTINGS["scanLoadPhase"]):
    ROUTINE_DNN(patternIndexes=[dnn_Pattern])
    print("Routine_DNN completed, starting ScanChainOneShot loop.")
    for evt_iter in range(nEvents):
        ScanChainOneShot(scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, scanLoadPhase )
        print(f'ScanChainOneShot number {evt_iter+1} executed, sleeping 1s.')
        time.sleep(1)

#
#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_SettingsScan(
        loopbackBit=ROUTINE_SETTINGS["loopbackBit"], patternIndexes = [2], verbose=False, vin_test='1D', freq='3f', 
        start_bxclk_state=ROUTINE_SETTINGS["startBxclkState"],
        # cfg_test_delay='08', #original setting is '08' instead of the '05' used in other routines
        cfg_test_delay=ROUTINE_SETTINGS["cfg_test_delay"], 
        # cfg_test_sample='08', #original setting is '08' instead of the '20' used in other routines
        cfg_test_sample=ROUTINE_SETTINGS["cfg_test_sample"], 
        # bxclk_delay='0B', #original setting is '0B' instead of the the '12' used in other routines
        bxclk_delay=ROUTINE_SETTINGS["bxclk_delay"], 
        scan_load_delay=ROUTINE_SETTINGS["scan_load_delay"]
):
    return SettingsScan(loopbackBit, patternIndexes, verbose, vin_test, freq, start_bxclk_state, cfg_test_delay, cfg_test_sample, bxclk_delay, scan_load_delay)

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_DNNTraining(asic_training=False):
    return DNNTraining(asic_training = asic_training)
