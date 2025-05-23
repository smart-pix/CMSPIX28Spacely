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
def ROUTINE_ProgShiftRegRaw(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1'):
    return ProgShiftRegRaw(configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk)

#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_ProgPixelsOnly( configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1',pixelList = [0], pixelValue=[3]):
    return ProgPixelsOnly(configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk,pixelList, pixelValue) 

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_ProgShiftRegs(progDebug=False, verbose=False, configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1', iP=0, timeSleep=0.011):
    return ProgShiftRegs(progDebug, verbose, configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk, iP, timeSleep)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_ScanChainOneShot(scan_load_delay='13', startBxclkState='0', bxclk_delay='12', bxclk_period='28', injection_delay='1E', scanLoopBackBit='0', test_sample='F', test_delay='14', scanLoadPhase ='26'):
    return ScanChainOneShot(scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, scanLoadPhase )

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_PreProgSCurve(scanLoadPhase = '26', scan_load_delay='13', startBxclkState='0', bxclk_delay='12', bxclk_period='28', injection_delay='1D', scanLoopBackBit='0', test_sample='0F', test_delay='14', v_min = 0.001, v_max=0.4, v_step=0.001, nsample=1000, nPix=0):
    return PreProgSCurve(scanLoadPhase, scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, v_min, v_max, v_step, nsample, nPix)

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_SCurveMatrix():
    return SCurveMatrix()

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_DNN(
        progDebug=False, loopbackBit=0, patternIndexes = [0], verbose=False, 
        injection_delay='1E', bxclk_period='28', startBxclkState='0',scan_load_delay='13', 
        cfg_test_delay='5', cfg_test_sample='20', progResetMask='0', configclk_period='64', 
        test_delay='14', test_sample='0F', bxclk_delay='12',configClkGate='0',scanLoadPhase ='26',
        readYproj=True,
):
        return DNN(progDebug,loopbackBit, patternIndexes, verbose, injection_delay, bxclk_period, startBxclkState, scan_load_delay, cfg_test_delay, cfg_test_sample, progResetMask, configclk_period, test_delay, test_sample, bxclk_delay,configClkGate, scanLoadPhase, readYproj=readYproj)

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_SettingsScan(
        loopbackBit=0, patternIndexes = [2], verbose=False, vin_test='1D', 
        freq='3f', start_bxclk_state='0', cfg_test_delay='08', cfg_test_sample='08', 
        bxclk_delay='0B', scanload_delay='13'
):
    return SettingsScan(loopbackBit, patternIndexes, verbose, vin_test, freq, start_bxclk_state, cfg_test_delay, cfg_test_sample, bxclk_delay, scanload_delay)

#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_DNNTraining(asic_training=False):
    return DNNTraining(asic_training = asic_training)
