'''
Author: Anthony Badea, Benjamin Parpillon
Date: June, 2024
'''

# spacely
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *
import getpass

def tb(args):
    """Fill every delay argument left as None from the active test bench profile
    (CMSPIX28Spacely_Config: TESTBENCH, TB_DELAYS, USER_DELAY_OVERRIDES).
    Pass locals() of a ROUTINE_*; returns the dict with the delays resolved."""
    if TESTBENCH not in TB_DELAYS:
        raise ValueError(f"Unknown TESTBENCH '{TESTBENCH}', valid: {list(TB_DELAYS)}")
    prof = dict(TB_DELAYS[TESTBENCH])
    prof.update(USER_DELAY_OVERRIDES.get(getpass.getuser(), {}).get(TESTBENCH, {}))
    out = {k: (prof[k] if v is None and k in prof else v) for k, v in args.items()}
    print(f"[{TESTBENCH}] delays: " + ", ".join(f"{k}={out[k]}" for k in prof if k in out))
    return out


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
        I_PORT["ISource10uA"].set_current(0.000003) # just to initialize the current readout for the chip
        I_LEVEL["ISource10uA"] = 0.000003

        I_PORT["ThresholdOut"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdOut"] = 0.000001
        I_PORT["ThresholdDown"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdDown"] = 0.000001
        I_PORT["ThresholdUp"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdUp"] = 0.000001

        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")
        print(f"Ibias current is {I_LEVEL['OUTsink']*1000000}uA")
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
def ROUTINE_ProgPixelsOnly( configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1',pixelList = [0], pixelValue=[1]):
    return ProgPixelsOnly(configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk,pixelList, pixelValue) 

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_ProgShiftRegs(progDebug=False, verbose=False, configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1', iP=0, timeSleep=0.011):
    return ProgShiftRegs(progDebug, verbose, configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk, iP, timeSleep)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_ScanChainOneShot(scan_load_delay=None, startBxclkState=None, bxclk_delay=None, bxclk_period=None, injection_delay=None, scanLoopBackBit=None, test_sample='F', test_delay=None, scanLoadPhase=None):
    a = tb(locals())
    return ScanChainOneShot(a['scan_load_delay'], a['startBxclkState'], a['bxclk_delay'], a['bxclk_period'], a['injection_delay'], a['scanLoopBackBit'], test_sample, a['test_delay'], a['scanLoadPhase'] )

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_PreProgSCurve(scanLoadPhase=None, scan_load_delay=None, startBxclkState=None, bxclk_delay=None, bxclk_period=None, injection_delay=None, scanLoopBackBit=None, test_sample='0F', test_delay=None, v_min = 0.1, v_max=0.4, v_step=0.1, nsample=1000, nPix=1):
    a = tb(locals())
    return PreProgSCurve(a['scanLoadPhase'], a['scan_load_delay'], a['startBxclkState'], a['bxclk_delay'], a['bxclk_period'], a['injection_delay'], a['scanLoopBackBit'], test_sample, a['test_delay'], v_min, v_max, v_step, nsample, nPix)

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_SCurveMatrix():
    return SCurveMatrix()

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_DNN(
        progDebug=False, loopbackBit=0, patternIndexes = [0], verbose=False, 
        injection_delay=None, bxclk_period=None, startBxclkState=None,scan_load_delay=None, 
        cfg_test_delay='5', cfg_test_sample='20', progResetMask='0', configclk_period='64', 
        test_delay=None, test_sample='0F', bxclk_delay=None,configClkGate='0',scanLoadPhase=None,
        vth0 = 0.08, vth1=0.16, vth2=0.32, readYproj=True, pixel_compout_csv=None, dnn_csv=None, model=None
):
        # model: key of DNN_MODELS (e.g. "Model1_400_800_1200"); overrides vth0/1/2 and dnn_csv, and sets the pulse generator high level (pg_hlev)
        if model is not None:
            if model not in DNN_MODELS:
                raise ValueError(f"Unknown DNN model '{model}', valid: {list(DNN_MODELS)}")
            m = DNN_MODELS[model]
            vth0, vth1, vth2, dnn_csv = m["vth0"], m["vth1"], m["vth2"], m["dnn_csv"]
            SDG7102A_SWEEP(HLEV=m["pg_hlev"])
        a = tb(locals())
        return DNN(progDebug,loopbackBit, patternIndexes, verbose, a['injection_delay'], a['bxclk_period'], a['startBxclkState'], a['scan_load_delay'], cfg_test_delay, cfg_test_sample, progResetMask, configclk_period, a['test_delay'], test_sample, a['bxclk_delay'],configClkGate, a['scanLoadPhase'], vth0=vth0, vth1=vth1, vth2=vth2, readYproj=readYproj, pixel_compout_csv=pixel_compout_csv, dnn_csv=dnn_csv)

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_DiscrimTuneScanChain(nEvents=1000, time_sleep = 1, dnn_Pattern=0,  scan_load_delay=None, startBxclkState=None, bxclk_delay=None, bxclk_period=None, injection_delay=None, scanLoopBackBit=None, test_sample='F', test_delay=None, scanLoadPhase=None):
    a = tb(locals())
    ROUTINE_DNN(patternIndexes=[dnn_Pattern])
    print("Routine_DNN completed, starting ScanChainOneShot loop.")
    for evt_iter in range(nEvents):
        ScanChainOneShot(a['scan_load_delay'], a['startBxclkState'], a['bxclk_delay'], a['bxclk_period'], a['injection_delay'], a['scanLoopBackBit'], test_sample, a['test_delay'], a['scanLoadPhase'] )
        print(f'ScanChainOneShot number {evt_iter+1} executed, sleeping 1s.')
        time.sleep(1)


#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_SettingsScan(
        loopbackBit=0, patternIndexes = [2], verbose=False, vin_test='1D', 
        freq='3f', start_bxclk_state='0', cfg_test_delay='08', cfg_test_sample='08', 
        bxclk_delay='0B', scanload_delay='13'
):
    return SettingsScan(loopbackBit, patternIndexes, verbose, vin_test, freq, start_bxclk_state, cfg_test_delay, cfg_test_sample, bxclk_delay, scanload_delay)

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_DNNTraining(asic_training=False):
    return DNNTraining(asic_training = asic_training)

# r10 to r14 and r16 take scan_load_delay, bxclk_delay, bxclk_period, injection_delay, scanLoadPhase, startBxclkState, scanLoopBackBit,
# test_delay, pulseGen and delayMode from the test bench profile (Config: TESTBENCH, TB_DELAYS) when they are not given on the call.
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_PulseDelayScan(nPix=1, progPixel=True, v_asic=0.1, delay_min_ns=-50, delay_max_ns=50, delay_step_ns=2, pulseGen=None, base_delay=None, injection_delay=None, bxclk_delay=None, scan_load_delay=None, scanLoadPhase=None, bxclk_period=None, startBxclkState=None, scanLoopBackBit=None, test_delay=None, nsample=1365, nIter=1, verify=False, tsleep_delay=0.1, delayMode=None):
    a = tb(locals())
    return PulseDelayScan(nPix=nPix, progPixel=progPixel, v_asic=v_asic, delay_min_ns=delay_min_ns, delay_max_ns=delay_max_ns, delay_step_ns=delay_step_ns, pulseGen=a['pulseGen'], base_delay=a['base_delay'], injection_delay=a['injection_delay'], bxclk_delay=a['bxclk_delay'], scan_load_delay=a['scan_load_delay'], scanLoadPhase=a['scanLoadPhase'], bxclk_period=a['bxclk_period'], startBxclkState=a['startBxclkState'], scanLoopBackBit=a['scanLoopBackBit'], test_delay=a['test_delay'], nsample=nsample, nIter=nIter, verify=verify, tsleep_delay=tsleep_delay, delayMode=a['delayMode'])

#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_PulseDelayScanSweepVTH(nPix=1, vth_min=0.001, vth_max=0.120, vth_step=0.002, vthNames=["vth0", "vth1", "vth2"], v_asic=0.100, delay_min_ns=-50, delay_max_ns=50, delay_step_ns=1, pulseGen=None, base_delay=None, injection_delay=None, bxclk_delay=None, scan_load_delay=None, scanLoadPhase=None, bxclk_period=None, startBxclkState=None, scanLoopBackBit=None, test_delay=None, nsample=1365, nIter=1, verify=False, tsleep_delay=0.010, delayMode=None):
    a = tb(locals())
    return PulseDelayScanSweepVTH(nPix=nPix, vth_min=vth_min, vth_max=vth_max, vth_step=vth_step, vthNames=vthNames, v_asic=v_asic, delay_min_ns=delay_min_ns, delay_max_ns=delay_max_ns, delay_step_ns=delay_step_ns, pulseGen=a['pulseGen'], base_delay=a['base_delay'], injection_delay=a['injection_delay'], bxclk_delay=a['bxclk_delay'], scan_load_delay=a['scan_load_delay'], scanLoadPhase=a['scanLoadPhase'], bxclk_period=a['bxclk_period'], startBxclkState=a['startBxclkState'], scanLoopBackBit=a['scanLoopBackBit'], test_delay=a['test_delay'], nsample=nsample, nIter=nIter, verify=verify, tsleep_delay=tsleep_delay, delayMode=a['delayMode'])

#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_PulseDelayScanMatrix(pixelList=None, vth_min=0.000, vth_max=0.300, vth_step=0.010, vthNames=["vth0", "vth1", "vth2"], v_asic=0.100, delay_min_ns=-50, delay_max_ns=30, delay_step_ns=2.5, pulseGen=None, base_delay=None, injection_delay=None, bxclk_delay=None, scan_load_delay=None, scanLoadPhase=None, bxclk_period=None, startBxclkState=None, scanLoopBackBit=None, test_delay=None, nsample=1365, nIter=1, tsleep_delay=0.010, delayMode=None):
    a = tb(locals())
    return PulseDelayScanMatrix(pixelList=pixelList, vth_min=vth_min, vth_max=vth_max, vth_step=vth_step, vthNames=vthNames, v_asic=v_asic, delay_min_ns=delay_min_ns, delay_max_ns=delay_max_ns, delay_step_ns=delay_step_ns, pulseGen=a['pulseGen'], base_delay=a['base_delay'], injection_delay=a['injection_delay'], bxclk_delay=a['bxclk_delay'], scan_load_delay=a['scan_load_delay'], scanLoadPhase=a['scanLoadPhase'], bxclk_period=a['bxclk_period'], startBxclkState=a['startBxclkState'], scanLoopBackBit=a['scanLoopBackBit'], test_delay=a['test_delay'], nsample=nsample, nIter=nIter, tsleep_delay=tsleep_delay, delayMode=a['delayMode'])

# readout="burst" (IP2 test 5, single pixel, fast) or "scan" (scan chain readout of PreProgSCurve, nPix=None/list reads all the pixels at once)
#<<Registered w/ Spacely as ROUTINE 13, call as ~r13>>
def ROUTINE_ScurveDelaySweep(nPix=1, v_asic=0.100, vth_min=0.001, vth_max=0.080, vth_step=0.002, vthNames=["vth0", "vth1", "vth2"], delay_min_ns=-62.5, delay_max_ns=30, delay_step_ns=2.5, pulseGen=None, base_delay=None, injection_delay=None, bxclk_delay=None, scan_load_delay=None, scanLoadPhase=None, bxclk_period=None, startBxclkState=None, scanLoopBackBit=None, test_delay=None, nsample=1365, nIter=1, verify=False, tsleep_vth=0.010, tsleep_delay=0.200, delayMode=None, readout="burst"):
    a = tb(locals())
    return ScurveDelaySweep(nPix=nPix, v_asic=v_asic, vth_min=vth_min, vth_max=vth_max, vth_step=vth_step, vthNames=vthNames, delay_min_ns=delay_min_ns, delay_max_ns=delay_max_ns, delay_step_ns=delay_step_ns, pulseGen=a['pulseGen'], base_delay=a['base_delay'], injection_delay=a['injection_delay'], bxclk_delay=a['bxclk_delay'], scan_load_delay=a['scan_load_delay'], scanLoadPhase=a['scanLoadPhase'], bxclk_period=a['bxclk_period'], startBxclkState=a['startBxclkState'], scanLoopBackBit=a['scanLoopBackBit'], test_delay=a['test_delay'], nsample=nsample, nIter=nIter, verify=verify, tsleep_vth=tsleep_vth, tsleep_delay=tsleep_delay, delayMode=a['delayMode'], readout=readout)

# readout="scan": the pixels of pixelList (None = all) are programmed together and read in one pass with the scan chain readout of PreProgSCurve
#<<Registered w/ Spacely as ROUTINE 14, call as ~r14>>
def ROUTINE_ScurveDelaySweepMatrix(pixelList=0, v_asic=0.100, vth_min=0.000, vth_max=0.072, vth_step=0.003, vthNames=["vth0", "vth1", "vth2"], delay_min_ns=-62.5, delay_max_ns=30, delay_step_ns=2.5, pulseGen=None, base_delay=None, injection_delay=None, bxclk_delay=None, scan_load_delay=None, scanLoadPhase=None, bxclk_period=None, startBxclkState=None, scanLoopBackBit=None, test_delay=None, nsample=1000, nIter=1, tsleep_vth=0.010, tsleep_delay=0.200, delayMode=None, readout="scan"):
    a = tb(locals())
    return ScurveDelaySweepMatrix(pixelList=pixelList, v_asic=v_asic, vth_min=vth_min, vth_max=vth_max, vth_step=vth_step, vthNames=vthNames, delay_min_ns=delay_min_ns, delay_max_ns=delay_max_ns, delay_step_ns=delay_step_ns, pulseGen=a['pulseGen'], base_delay=a['base_delay'], injection_delay=a['injection_delay'], bxclk_delay=a['bxclk_delay'], scan_load_delay=a['scan_load_delay'], scanLoadPhase=a['scanLoadPhase'], bxclk_period=a['bxclk_period'], startBxclkState=a['startBxclkState'], scanLoopBackBit=a['scanLoopBackBit'], test_delay=a['test_delay'], nsample=nsample, nIter=nIter, tsleep_vth=tsleep_vth, tsleep_delay=tsleep_delay, delayMode=a['delayMode'], readout=readout)

#<<Registered w/ Spacely as ROUTINE 15, call as ~r15>>
def ROUTINE_PreProgSCurveBurst_StaticPulse(scan_load_delay='5', startBxclkState='0', bxclk_delay='10', bxclk_period='28', injection_delay='7', scanLoopBackBit='0', test_sample='0F', scanLoadPhase='26', test_delay='14', tsleep=10e-3, v_min=0.001, v_max=0.2, v_step=0.001, nsample=1365, nIter=1, nPix=1, v_asic=0.05):
    return PreProgSCurveBurst_StaticPulse(scan_load_delay=scan_load_delay, startBxclkState=startBxclkState, bxclk_delay=bxclk_delay, bxclk_period=bxclk_period, injection_delay=injection_delay, scanLoopBackBit=scanLoopBackBit, test_sample=test_sample, scanLoadPhase=scanLoadPhase, test_delay=test_delay, tsleep=tsleep, v_min=v_min, v_max=v_max, v_step=v_step, nsample=nsample, nIter=nIter, nPix=nPix, v_asic=v_asic)

#<<Registered w/ Spacely as ROUTINE 16, call as ~r16>>
def ROUTINE_PreProgSCurveSweepVTH(nPix=None, v_asic=0.100, delay_ns=12, delayMode=None, vth_min=0.000, vth_max=0.100, vth_step=0.002, vthNames=["vth0", "vth1", "vth2"], pulseGen=None, base_delay=None, scan_load_delay=None, startBxclkState=None, bxclk_delay=None, bxclk_period=None, injection_delay=None, scanLoopBackBit=None, test_sample='0F', test_delay=None, scanLoadPhase=None, nsample=1000, verify=False, tsleep_vth=0.1, tsleep_delay=0.2):
    a = tb(locals())
    return PreProgSCurveSweepVTH(nPix=nPix, v_asic=v_asic, delay_ns=delay_ns, delayMode=a['delayMode'], vth_min=vth_min, vth_max=vth_max, vth_step=vth_step, vthNames=vthNames, pulseGen=a['pulseGen'], base_delay=a['base_delay'], scan_load_delay=a['scan_load_delay'], startBxclkState=a['startBxclkState'], bxclk_delay=a['bxclk_delay'], bxclk_period=a['bxclk_period'], injection_delay=a['injection_delay'], scanLoopBackBit=a['scanLoopBackBit'], test_sample=test_sample, test_delay=a['test_delay'], scanLoadPhase=a['scanLoadPhase'], nsample=nsample, verify=verify, tsleep_vth=tsleep_vth, tsleep_delay=tsleep_delay)
