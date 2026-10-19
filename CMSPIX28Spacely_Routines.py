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
        # I_PORT["OUTsink"].set_current(0.000003) # just to initialize the current readout for the chip
        # I_LEVEL["OUTsink"] = 0.000003
        I_PORT["Isource10uA"].set_current(0.000003) # just to initialize the current readout for the chip
        I_LEVEL["Isource10uA"] = 0.000003

        I_PORT["ThresholdOut"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdOut"] = 0.000001
        I_PORT["ThresholdDown"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdDown"] = 0.000001
        I_PORT["ThresholdUp"].set_current(0.000001) # just to initialize the current readout for the chip
        I_LEVEL["ThresholdUp"] = 0.000001

        print(f"DVDD current is {iDVDD}")
        print(f"AVDD current is {iAVDD}")
        # print(f"Ibias current is {I_LEVEL['OUTsink']*1000000}uA")
        print(f"Ibias current is {I_LEVEL['Isource10uA']*1000000}uA")
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
def ROUTINE_ProgShiftRegs(progDebug=False, verbose=False, configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk='1', iP=0, timeSleep=0.011,     send_fw_reset_opcode=True,   reset_asic_before_test= True, expect_previous_same_model=False):
    return ProgShiftRegs(progDebug, verbose, configclk_period, cfg_test_delay, cfg_test_sample,cfg_test_gate_config_clk, iP, timeSleep, send_fw_reset_opcode, reset_asic_before_test, expect_previous_same_model)

#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_ScanChainOneShot(scan_load_delay='13', startBxclkState='0', bxclk_delay='12', bxclk_period='28', injection_delay='1E', scanLoopBackBit='0', test_sample='F', test_delay='14', scanLoadPhase ='26'):
    return ScanChainOneShot(scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, scanLoadPhase )

#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_PreProgSCurve(scanLoadPhase = '26', scan_load_delay='13', startBxclkState='0', bxclk_delay='12', bxclk_period='28', injection_delay='1D', scanLoopBackBit='0', test_sample='0F', test_delay='14', v_min = 0.001, v_max=0.4, v_step=0.001, nsample=1000, nPix=0):
    return PreProgSCurve(scanLoadPhase, scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, v_min, v_max, v_step, nsample, nPix)

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_SCurveMatrix():
    return SCurveMatrix()

# def ROUTINE_DNN(
#         progDebug=False, loopbackBit=0, patternIndexes = [0], verbose=False, 
#         injection_delay='1E', bxclk_period='28', startBxclkState='0',scan_load_delay='13', 
#         cfg_test_delay='5', cfg_test_sample='20', progResetMask='0', configclk_period='64', 
#         test_delay='14', test_sample='0F', bxclk_delay='12',configClkGate='0',scanLoadPhase ='26',
#         vth0 = 0.08, vth1=0.16, vth2=0.32, readYproj=True, pixel_compout_csv=None, dnn_csv=None
# ):
#         return DNN(progDebug,loopbackBit, patternIndexes, verbose, injection_delay, bxclk_period, startBxclkState, scan_load_delay, cfg_test_delay, cfg_test_sample, progResetMask, configclk_period, test_delay, test_sample, bxclk_delay,configClkGate, scanLoadPhase, vth0=vth0, vth1=vth1, vth2=vth2, readYproj=readYproj, pixel_compout_csv=pixel_compout_csv, dnn_csv=dnn_csv)

# ---------------------------------------------------------------------------
# Current ASIC-in-the-loop campaign.
#
# Spacely invokes ~r9/~r10 with DEFAULT ARGUMENTS ONLY -- there is no
# ~r9(arg=...) -- so these two lines are the one place to edit when the
# operating point changes, and the routine signatures below are the one place
# to edit for the training knobs.
#
# ~r9 (training) and ~r10 (fidelity check) deliberately read the SAME vth and
# pg_hlev: a fidelity check taken at a different chip bias than the training run
# measures a different chip and cannot be compared against it.
#
# To vary anything without editing this file, call the underlying functions
# directly at the Spacely prompt:
#   asicFidelityCheck(model_file="./checkpoints_700_1400_2100/model_epoch12.h5")
#   DNNTraining(asic_training=True, vth=(550,1100,1650), pg_hlev=0.2)
# ---------------------------------------------------------------------------
RUN_VTH = (700, 1400, 2100)   # discriminator thresholds, electrons
RUN_PG_HLEV = 0.2             # injection pulse high level, V
RUN_TIMESTAMP = TIMESTAMP_DEFAULT   # readout slice scored as the answer (of 40)

# Where the dnn0/dnn1 DAC lines sit right now, volts. ~r11 scans around these
# and reports where to move them; update them here once a scan has a winner so
# the next scan starts from the setting actually on the bench.
#
# The discriminator flips between 0.079 and 0.080 V on dnn0, and between 0.070
# and 0.071 V on dnn1 -- and those pairs are ADJACENT DAC CODES, not the ends of
# a range with room in between. The CaR DAC7678 runs on a 4.096 V reference, so
# one code is exactly 1 mV and the observed transition is as narrow as this
# hardware can resolve. Write these as whole millivolts; a value like 0.0795
# does not exist on the line (see dnnDacCode in the B5 subroutines).
#
# Note the scale -- the new discriminator operates near 0.08 V, not the ~1.59 V
# of the old one, so any scan list written for the old part is nonsense here,
# not merely mistuned.
RUN_DNN0 = 0.079
RUN_DNN1 = 0.070

# Discriminator hysteresis, volts -- the width of the loop, NOT a tolerance.
# ~r11 overshoots every setting by 3x this and comes back, so all its points sit
# on the same branch, and it refuses to refine below it.
#
# 1 mV is the width of the flip region quoted above (0.079-0.080 and
# 0.070-0.071), i.e. an observation rather than the old 3 mV placeholder -- but
# it is an upper bound read off the bench, not a measurement of the loop itself.
# It is also exactly one DAC code, so it is the smallest number that can mean
# anything here: the overshoot is 3 codes and refinement cannot go below 1.
# Run ~r11 once with hyst_check=True to get the real number in the same units as
# every other figure it prints.
RUN_DNN_HYSTERESIS = 0.001

# The CaR DAC drives dnn0/dnn1 (BIAS_7/BIAS_6), so ~r11 programs the lines
# directly and talks in absolute volts. Set True only if these lines ever go
# back to bare potentiometers with no meter, where the only executable
# instruction is a counted turn of a dial ("turn 1 step CCW") and the whole
# voltage-approach protocol -- hysteresis, approach, hyst_check -- has to switch
# off because every part of it needs a voltage you cannot read.
RUN_POT_STEPS = False


#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_DNN(
        progDebug=False, loopbackBit=0, patternIndexes = [0], verbose=False, 
        injection_delay='1E', bxclk_period='28', startBxclkState='0',scan_load_delay='13', 
        cfg_test_delay='5', cfg_test_sample='20', progResetMask='0', configclk_period='64', 
        test_delay='14', test_sample='0F', bxclk_delay='12',configClkGate='0',scanLoadPhase ='26',
        vth0 = 400, vth1=800, vth2=1200, pg_hlev=0.22, dnn0=RUN_DNN0, dnn1=RUN_DNN1,readYproj=True, pixel_compout_csv=None, dnn_csv=None):
        #dnn0 =  1.573, dnn1 = 1.588/ 1.589
        # vth0 = 0.08, vth1=0.16, vth2=0.32, pg_hlev=0.22, dnn0=1.586, dnn1=1.588,readYproj=True, pixel_compout_csv=None, dnn_csv=None
        vth_0_mv = round((vth0 - 196.84)/16960.09, 3)
        vth_1_mv = round((vth1 - 223.96)/16853.41, 3)
        vth_2_mv = round((vth2 - 224.42)/16922.43, 3)
        print(f"vth_0 [e-] = {vth0}, vth_1 [e-] = {vth1}, vth_2 [e-] = {vth2}")
        print(f"vth_0 [mV] = {vth_0_mv}, vth_1 [mV] = {vth_1_mv}, vth_2 [mV] = {vth_2_mv}")
        # V_PORT["dnn0_vt"].set_voltage(dnn0)
        # V_PORT["dnn1_vt"].set_voltage(dnn1)
        return DNN(progDebug,loopbackBit, patternIndexes, verbose, injection_delay, bxclk_period, startBxclkState, scan_load_delay, cfg_test_delay, cfg_test_sample, progResetMask, configclk_period, test_delay, test_sample, bxclk_delay,configClkGate, scanLoadPhase, vth0=vth_0_mv, vth1=vth_1_mv, vth2=vth_2_mv, pg_hlev=pg_hlev, dnn0=dnn0, dnn1=dnn1 ,readYproj=readYproj, pixel_compout_csv=pixel_compout_csv, dnn_csv=dnn_csv)

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_DiscrimTuneScanChain(nEvents=1000, time_sleep = 1, dnn_Pattern=0,  scan_load_delay='13', startBxclkState='0', bxclk_delay='12', bxclk_period='28', injection_delay='1E', scanLoopBackBit='0', test_sample='F', test_delay='14', scanLoadPhase ='26'):
    ROUTINE_DNN(patternIndexes=[dnn_Pattern])
    print("Routine_DNN completed, starting ScanChainOneShot loop.")
    for evt_iter in range(nEvents):
        ScanChainOneShot(scan_load_delay, startBxclkState, bxclk_delay, bxclk_period, injection_delay, scanLoopBackBit, test_sample, test_delay, scanLoadPhase )
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
def ROUTINE_DNNTraining(asic_training=False,
                        vth=RUN_VTH, pg_hlev=RUN_PG_HLEV, data_dir=None,
                        init_model=INIT_MODEL_DEFAULT, out_model="model.h5",
                        checkpoint_dir=None,
                        alpha=1.0, asic_every=1, asic_warmup_epochs=0,
                        epochs=12, patience=None,
                        batch_size=1024, learning_rate=1e-4,
                        timestamp=RUN_TIMESTAMP):
    """Fine-tune the QKeras model, optionally with the chip in the loop.

    data_dir=None      -> the dataset generated at `vth` (datasetDir()), so the
                          data and the chip bias cannot drift apart.
    checkpoint_dir=None -> ./checkpoints_<vth0>_<vth1>_<vth2>, so two runs at
                          different thresholds cannot append to each other's
                          history.csv.
    patience=None      -> epochs, i.e. early stopping disabled.
    """
    return DNNTraining(asic_training=asic_training,
                       vth=vth, pg_hlev=pg_hlev, data_dir=data_dir,
                       init_model=init_model, out_model=out_model,
                       checkpoint_dir=checkpoint_dir,
                       alpha=alpha, asic_every=asic_every,
                       asic_warmup_epochs=asic_warmup_epochs,
                       epochs=epochs, patience=patience,
                       batch_size=batch_size, learning_rate=learning_rate,
                       timestamp=timestamp)

#<<Register     ROUTINE 10, call as ~r10>>
#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_ASICFidelityCheck(model_file="model.h5", n_samples=1024, repeats=2,
                              use_val=True, batch_stride=None,
                              vth=RUN_VTH, pg_hlev=RUN_PG_HLEV, data_dir=None,
                              timestamp=RUN_TIMESTAMP):
    """Chip-vs-software fidelity at the same operating point ~r9 trains at.

    Defaults score ./model.h5, the model ~r9 just wrote. To score a specific
    epoch instead, call asicFidelityCheck(model_file=...) directly.

    Also prints bitErrorBreakdown() -- which readout line (dnn1/dnn0) carries
    the errors and in which direction -- and scanTimeSlices(), which scores
    every one of the chip's 40 readout slices, not just `timestamp`.
    """
    return asicFidelityCheck(model_file=model_file, n_samples=n_samples,
                             repeats=repeats, use_val=use_val,
                             batch_stride=batch_stride,
                             vth=vth, pg_hlev=pg_hlev, data_dir=data_dir,
                             timestamp=timestamp)


#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_TuneDnnThresholds(model_file="model.h5",
                              dnn0=RUN_DNN0, dnn1=RUN_DNN1,
                              dnn1_scan=((-2, -1, 1, 2) if RUN_POT_STEPS
                                         else (0.076, 0.073, 0.070,
                                               0.067, 0.064)),
                              dnn0_scan=None,
                              n_samples=2048, repeats=2,
                              vth=RUN_VTH, pg_hlev=RUN_PG_HLEV,
                              timestamp=RUN_TIMESTAMP, objective="err",
                              hysteresis=RUN_DNN_HYSTERESIS,
                              approach="above", hyst_check=False,
                              pot_steps=RUN_POT_STEPS):
    """Scan the dnn1 discriminator threshold and report where to set the DAC.

    VOLTAGE MODE is on (RUN_POT_STEPS=False): the CaR DAC drives dnn0/dnn1
    (BIAS_7/BIAS_6), so every setting is programmed directly and the scan is
    unattended -- no prompts, no dial. Scan lists are absolute volts.

    The defaults BRACKET the current setting (two points either side of
    RUN_DNN1) rather than only stepping in the direction the bit-error asymmetry
    suggests. The asymmetry gives a direction but not a reliable sign, so let
    the measured curve establish which way is which, once. After that, scan one
    side only.

    SCALE. The new discriminator flips near 0.08 V, not the ~1.59 V of the old
    part. A scan list carried over from the old one is off by a factor of 20 and
    will measure nothing -- check the numbers are in the 0.06-0.09 range.

    HYSTERESIS matters here in a way it did not on the dial: a voltage reached
    on the way down and the same voltage reached on the way up are different
    operating points. Every setting is therefore overshot by 3x
    RUN_DNN_HYSTERESIS and approached from `approach`, so all points sit on the
    same branch. RUN_DNN_HYSTERESIS is currently 1 mV, read off the width of the
    observed flip region rather than measured -- run once with hyst_check=True
    to get the real loop width, since it sets the floor on how finely these
    lines can be trimmed at all.

    Set RUN_POT_STEPS = True only if these lines go back to bare pots with no
    meter: the scan then talks in counted turns of a dial ("turn 1 step CCW")
    and hysteresis/approach/hyst_check are all ignored, because every part of
    that protocol needs a voltage you cannot read.

    repeats=2 on purpose: the second run at the FIRST setting is what measures
    the chip's disagreement with itself, which is the floor every threshold
    improvement has to clear.

    dnn0_scan is None by default -- do one line at a time. Take dnn1's winner,
    put it in RUN_DNN1 above, then run again with dnn0_scan set (bracketing
    RUN_DNN0, i.e. around 0.079 V).

    hyst_check is OFF: it costs an extra setting and it is not needed to run a
    valid scan. Turn it on (hyst_check=True) to find out how much of the
    variation is the discriminator's loop rather than the chip -- it re-measures
    the voltage you started at, approached from the other side. Worth doing once
    now, since RUN_DNN_HYSTERESIS is still an estimate.

    Unattended on the DAC: ~14 minutes of chip time for the default 6
    measurements at n_samples=2048.
    """
    return tuneDnnThresholds(model_file=model_file, dnn0=dnn0, dnn1=dnn1,
                             dnn1_scan=list(dnn1_scan) if dnn1_scan else None,
                             dnn0_scan=list(dnn0_scan) if dnn0_scan else None,
                             n_samples=n_samples, repeats=repeats,
                             vth=vth, pg_hlev=pg_hlev,
                             timestamp=timestamp, objective=objective,
                             hysteresis=hysteresis, approach=approach,
                             hyst_check=hyst_check, pot_steps=pot_steps)
