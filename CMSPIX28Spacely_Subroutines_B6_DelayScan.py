# spacely
from Master_Config import *

# python modules
import sys
try:
    import os
    import time
    import tqdm
    import numpy as np
    import math
    import json
    from datetime import datetime
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately


#-----------------------------------------------------------------------
# PulseDelayScan function
#-----------------------------------------------------------------------
# This test measures the hit rate of a single pixel as a function of the
# pulse generator delay (ie: when the injected charge arrives w.r.t. BxCLK / scanLoad)
# This function programs a single pixel (optional) and uses IP2 test 5 (burst) for statistics
# 1. Set static array 0 and static array 1 to configure the correct frequency and scanLoad arrival time and phases.
# 2. Static array 1 needs to be configured also with the number of samples (nSample) and the pixel number to stack (nPix)
# 3. Set the pulse generator amplitude to a fixed v_asic
# 4. loop over the pulse generator burst delay: base_delay + [delay_min_ns, delay_max_ns] in steps of delay_step_ns
# 5. Execute IP2 test 5, read DATA_ARRAY_1 and save the samples to delay_<ns>.npy
# delayMode = "PG": every delay step is a pulse generator delay change (resolution limited by the pulse generator, ~8 ns for the BK4065)
# delayMode = "FW": 2.5 ns steps with the firmware injection_delay (the 400 MHz FPGA clock, trigger position within one BxCLK period),
#                   only injection_delay = 1..period/2 injects (21..40 gave no hits at bxclk_period '28'), so the pulse generator
#                   delay changes by half BxCLK periods when the scan range needs more than one half period
# The pulse generator must already be initialized (BK4600_INIT() or SDG7102A_INIT())
# Analysis and plots: CMSPIX28_DAQ/lab_analysis/PulseDelayScan.py (run through launchAnalysis.py)
#-----------------------------------------------------------------------

def PulseDelayScan(
        nPix = 0,
        progPixel = True,
        v_asic = 0.1,
        delay_min_ns = 0,
        delay_max_ns = 100,
        delay_step_ns = 1,
        pulseGen = "BK4600", # key of PULSEGEN in A0
        base_delay = None, # None uses the delay from the pulse generator INIT. The scan is an offset from this. Set to 0 for absolute delays
        scan_load_delay = '5',
        startBxclkState = '0',
        bxclk_delay = '10',
        bxclk_period = '28',
        injection_delay = '7',
        scanLoopBackBit = '0',
        test_sample = '0F',
        scanLoadPhase = '26',
        test_delay = '14',
        tsleep = 250e-3, # wait after setting the pulse amplitude
        tsleep_delay = 100e-3, # wait after each pulse generator delay change
        nsample = 1365,
        nIter = 1,
        verify = False,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        testType = "PulseDelayScan",
        vthLabel = "vth0", # threshold used to name the sub folder for PulseDelayScanVTH
        delayMode = "PG", # "PG": pulse generator delay steps, "FW": 2.5 ns firmware injection_delay steps (see above)
):

    if nsample>1365:
        print("You asked for more samples per iteration that the firmware can achieve. Max allowed is nsample = 1365. Please increase nIter instead and rerun.")
        return

    if base_delay is None:
        base_delay = PULSEGEN[pulseGen]["base_delay"]

    # program single pixel
    if progPixel:
        ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk ='1', pixelList = [nPix], pixelValue=[1])

    nPixHex = int_to_32bit_hex(nPix)
    nsampleHex = int_to_32bit_hex(nsample)

    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]
    # hex lists - same static configuration as PreProgSCurveBurst
    hex_lists = [
        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scan_load_delay}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclk_delay}", f"6'h{bxclk_period}"],
        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"11'h{nsampleHex}", f"8'h{nPixHex}"],
    ]
    sw_write32_0(hex_lists)
    sw_read32_0= sw_read32()

    # define range of delays (in ns, offset from base_delay)
    # exact steps of delay_step_ns from delay_min_ns, last point is the largest one <= delay_max_ns
    n_step = int(np.floor((delay_max_ns - delay_min_ns)/delay_step_ns + 1e-6))+1
    delay_steps_ns = delay_min_ns + delay_step_ns*np.arange(n_step)

    # plan for every delay point: (total delay offset [ns], pulse generator delay offset [ns], injection_delay in hex)
    if delayMode == "FW":
        period = int(bxclk_period, 16)
        inj0 = int(injection_delay, 16)
        half = period//2
        if not 1 <= inj0 <= half:
            print(f"injection_delay = {injection_delay} must be between 1 and bxclk_period/2 = {half:X} (hex) for delayMode='FW'.")
            return
        # 2.5 ns grid; only injection_delay in the first half of the BxCLK period (1..period/2) injects a pulse
        # points on the grid inside [delay_min_ns, delay_max_ns], step rounded to a multiple of 2.5 ns (at least 2.5 ns)
        k = max(1, int(round(delay_step_ns/2.5)))
        n = np.arange(int(np.ceil(delay_min_ns/2.5 - 1e-6)), int(np.floor(delay_max_ns/2.5 + 1e-6)) + 1, k)
        if abs(k*2.5 - delay_step_ns) > 1e-6 or abs(n[0]*2.5 - delay_min_ns) > 1e-6:
            print(f"delayMode='FW': using the 2.5 ns firmware grid, {n[0]*2.5:.1f} to {n[-1]*2.5:.1f} ns in steps of {k*2.5:.1f} ns")
        seg = np.floor((n + inj0 - 1)/half).astype(int)      # half BxCLK periods the pulse generator has to move
        inj = inj0 + n - seg*half                             # injection_delay for this point, always in 1..period/2
        plan = [(round(2.5*ni, 3), round(2.5*half*si, 3), f"{ii:X}") for ni, si, ii in zip(n, seg, inj)]
        if len(set(seg)) > 1:
            print(f"delayMode='FW': the range spans {len(set(seg))} half BxCLK periods, the pulse generator delay changes by {2.5*half:.1f} ns between them. "
                  "Its delay resolution can offset the segments from each other by up to one of its steps: check the continuity at the segment boundaries.")
    else:
        plan = [(round(d, 3), round(d, 3), injection_delay) for d in delay_steps_ns]

    # negative offsets are fine as long as the absolute pulse generator delay stays positive
    if base_delay + min(p[1] for p in plan)*1e-9 < 0:
        print(f"delay_min_ns = {delay_min_ns} ns would give a negative pulse generator delay (base delay is {base_delay*1e9:.1f} ns). Increase delay_min_ns or base_delay and rerun.")
        return

    # 400MHz is the FPGA clock
    bxclk_period_inMhz = 400/int(bxclk_period, 16)
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "PulseDelayScanVTH":
        testInfo += f"_vasic{v_asic:.3f}_baseDly{base_delay*1e9:.1f}_dlyMin{delay_min_ns:.1f}_dlyMax{delay_max_ns:.1f}_dlyStep{delay_step_ns:.2f}_nSample{nsample*nIter}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}_nPix{nPix}"
        pixelInfo = f"vth{V_LEVEL[vthLabel]:.3f}"
    elif testType == "PulseDelayScanMatrix":
        testInfo += f"_vasic{v_asic:.3f}_baseDly{base_delay*1e9:.1f}_dlyMin{delay_min_ns:.1f}_dlyMax{delay_max_ns:.1f}_dlyStep{delay_step_ns:.2f}_nSample{nsample*nIter}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}"
        pixelInfo = os.path.join(f"nPix{nPix}", f"vth{V_LEVEL[vthLabel]:.3f}")
    else:
        testInfo += f"_vasic{v_asic:.3f}_baseDly{base_delay*1e9:.1f}_dlyMin{delay_min_ns:.1f}_dlyMax{delay_max_ns:.1f}_dlyStep{delay_step_ns:.2f}_nSample{nsample*nIter}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_Ibias{V_LEVEL['Ibias']:.3f}_nPix{nPix}"
        pixelInfo = ""

    if delayMode == "FW":
        testInfo += "_dlyModeFW"

    # output directory
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # set the injected amplitude once
    # The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
    PULSEGEN[pulseGen]["set_hlev"](v_asic*2)
    time.sleep(tsleep)

    try:
        # save the timing settings of this run, so scope measurements of the timing (for the 2D map overlay) can be matched to the settings
        with open(os.path.join(outDir, "scan_settings.json"), "w") as fs:
            json.dump({"bxclk_period": bxclk_period, "bxclk_delay": bxclk_delay, "scanLoadPhase": scanLoadPhase, "scan_load_delay": scan_load_delay,
                       "injection_delay": injection_delay, "test_delay": test_delay, "test_sample": test_sample, "base_delay_ns": base_delay*1e9,
                       "pulseGen": pulseGen, "delayMode": delayMode, "v_asic": v_asic, "nPix": nPix}, fs, indent=1)

        # save the plan for FW mode: which pulse generator delay and injection_delay gave each point
        if delayMode == "FW":
            np.savez(os.path.join(outDir, "delay_plan.npz"), delay_ns=[p[0] for p in plan], pg_delay_ns=[p[1] for p in plan], injection_delay=[int(p[2], 16) for p in plan])

        # loop over the delay steps
        pg_set, readback = None, None
        for dly_ns, pg_ns, inj_hex in tqdm.tqdm(plan, desc="Delay Step"):

            # only touch the pulse generator when its delay changes
            if pg_ns != pg_set:
                readback = PULSEGEN_DLAY_SWEEP(base_delay + pg_ns*1e-9, pulseGen=pulseGen, verify=verify)
                time.sleep(tsleep_delay) # added time for pulse generator to settle after the delay change
                pg_set = pg_ns

            # save data
            save_data = []
            for j in tqdm.tqdm(range(nIter), desc="Number of Samples", leave=False):

                # write configuration
                hex_lists = [
                    [
                        "4'h2",  # firmware id
                        "4'hF",  # op code for execute
                        "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                        f"6'h{inj_hex}", # 6 bits for w_execute_cfg_test_injection_delay_index_max
                        f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
                        "4'h3",  # Test 5 is the only test none thermometrically encoded because of lack of code space
                        f"6'h{test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                        f"6'h{test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                    ]
                ]
                sw_write32_0(hex_lists)

                # prepare the word list to read
                maxWordFWArray = 128
                nword = math.ceil(nsample*3/32)
                base_addr = maxWordFWArray - nword  # first word address to read: from 128-nword to 127
                words = ["0"*32] * nword
                # added time for burst to complete
                time.sleep(100e-6*nsample)

                # read all nword words from DATA_ARRAY_1 (opcode 0xD) in a single round trip
                raw_words, _, _, _ = sw_readStream(do_sw_read32_1 = False, N = nword, opcode = 0xD, base_addr = base_addr)
                for i, iW in enumerate(range(base_addr, maxWordFWArray)):
                    words[(maxWordFWArray-1)-iW] = int_to_32bit(raw_words[i])

                # save words
                s = [int(i) for i in "".join(words)]
                # Cutting last bit because 3x1365 = 4095
                s = s[:nsample*3]
                save_data.append(s)

            # same bit ordering as PreProgSCurveBurst
            save_data = np.stack(save_data, 0)
            save_data = save_data.reshape(nsample*nIter, 3)
            save_data = save_data[:,::-1]

            # save data
            outFileName = os.path.join(outDir, f"delay_{dly_ns:.3f}.npy")
            np.save(outFileName, save_data)

            # quick look at the bench, full analysis is in lab_analysis/PulseDelayScan.py
            readbackInfo = f" (PG reports {(readback - base_delay)*1e9:.3f} ns)" if readback is not None else ""
            if delayMode == "FW":
                readbackInfo += f" [PG offset {pg_ns:.1f} ns, injection_delay {inj_hex}]"
            tqdm.tqdm.write(f"delay {dly_ns:.3f} ns{readbackInfo}: hit rate any bit = {100*np.any(save_data, axis=1).mean():.1f}%")

    finally:
        # always put the pulse generator delay back to where it was
        PULSEGEN_DLAY_SWEEP(base_delay, pulseGen=pulseGen)

    return outDir


#-----------------------------------------------------------------------
# PulseDelayScanSweepVTH function
#-----------------------------------------------------------------------
# This function programs a single pixel and runs PulseDelayScan while sweeping the threshold voltages
# By default vth0, vth1 and vth2 are set to the same value (like SCurveSweepVTH); use vthNames to sweep only some of them
# All thresholds are stored in the same test folder, one vth<value> sub folder per threshold (like MatrixVTH)
# The thresholds are restored to their starting values at the end
# Analysis, 1D plots and the 2D hit map (delay vs threshold): CMSPIX28_DAQ/lab_analysis/PulseDelayScan.py
#-----------------------------------------------------------------------

def PulseDelayScanSweepVTH(
        nPix = 0,
        vth_min = 0.01,
        vth_max = 0.2,
        vth_step = 0.01,
        vthNames = ["vth0", "vth1", "vth2"],
        v_asic = 0.1,
        delay_min_ns = 0,
        delay_max_ns = 100,
        delay_step_ns = 1,
        pulseGen = "BK4600",
        base_delay = None,
        nsample = 1365,
        nIter = 1,
        verify = False,
        tsleep_vth = 0.1,
        tsleep_delay = 100e-3, # wait after each pulse generator delay change
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None, # set by PulseDelayScanMatrix so all pixels share one test folder
        testType = "PulseDelayScanVTH",
        **kwargs, # any other PulseDelayScan setting (injection_delay, bxclk_delay, ...)
):

    # program single pixel once, PulseDelayScan does not need to reprogram it
    ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk ='1', pixelList = [nPix], pixelValue=[1])

    # same timestamp for every threshold so they end up in the same folder
    now = dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    # Sweep range
    # exact steps of vth_step from vth_min, last point is the largest one <= vth_max
    n_step = int(np.floor((vth_max - vth_min)/vth_step + 1e-6))+1
    vthList = vth_min + vth_step*np.arange(n_step)

    # remember starting thresholds to restore at the end
    vthStart = {name : V_LEVEL[name] for name in vthNames}

    outDir = None
    try:
        for vth in vthList:
            vth = round(vth, 4)
            print(f"Setting {vthNames} = {vth:.3f} V")
            for name in vthNames:
                V_PORT[name].set_voltage(vth)
                V_LEVEL[name] = vth
            time.sleep(tsleep_vth) # let the bias settle
            V_PORT["vdda"].get_current()

            # read back what the board actually set
            for name in vthNames:
                v_rd = V_PORT[name].get_voltage()
                print(f"  {name}: set {vth:.4f} V, read back {v_rd:.4f} V")
                if abs(v_rd - vth) > vth_step/2:
                    print(f"  WARNING: {name} read back differs from the set value by more than half a step ({vth_step/2*1e3:.1f} mV)")

            vthDir = PulseDelayScan(
                nPix = nPix,
                progPixel = False,
                v_asic = v_asic,
                delay_min_ns = delay_min_ns,
                delay_max_ns = delay_max_ns,
                delay_step_ns = delay_step_ns,
                pulseGen = pulseGen,
                base_delay = base_delay,
                nsample = nsample,
                nIter = nIter,
                verify = verify,
                dataDir = dataDir,
                dateTime = now,
                testType = testType,
                vthLabel = vthNames[0],
                tsleep_delay = tsleep_delay,
                **kwargs
            )
            outDir = os.path.dirname(os.path.normpath(vthDir))

    finally:
        # put the thresholds back
        for name, v in vthStart.items():
            V_PORT[name].set_voltage(v)
            V_LEVEL[name] = v

    return outDir


#-----------------------------------------------------------------------
# PulseDelayScanMatrix function
#-----------------------------------------------------------------------
# Runs PulseDelayScanSweepVTH (delay vs threshold hit map) for every pixel in pixelList, like SCurveMatrix
# Each pixel is programmed alone, then swept over thresholds and pulse generator delays
# All pixels are stored in the same test folder: <test>/nPix<n>/vth<V>/delay_<ns>.npy
# A full sweep is long: the time per pixel is printed before starting; use pixelList to run a subset
# Analysis (2D maps per bit, cumulative hit rate vs threshold, width at half maximum threshold per pixel):
# CMSPIX28_DAQ/lab_analysis/PulseDelayScan.py (run through launchAnalysis.py)
#-----------------------------------------------------------------------

def PulseDelayScanMatrix(
        pixelList = None, # None = all 256 pixels
        vth_min = 0.002,
        vth_max = 0.120,
        vth_step = 0.004,
        vthNames = ["vth0", "vth1", "vth2"],
        v_asic = 0.1,
        delay_min_ns = -50,
        delay_max_ns = 50,
        delay_step_ns = 2,
        tsleep_delay = 100e-3,
        tsleep_vth = 0.1,
        nsample = 1365,
        nIter = 1,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        **kwargs, # any other PulseDelayScan setting (injection_delay, bxclk_delay, scan_load_delay, pulseGen, base_delay, ...)
):

    if pixelList is None:
        pixelList = list(range(256))

    # rough time estimate: delay wait + burst (100us per sample) + ~50 ms readout per point
    nVth = int(np.floor((vth_max - vth_min)/vth_step + 1e-6))+1
    nDelay = int(np.floor((delay_max_ns - delay_min_ns)/delay_step_ns + 1e-6))+1
    if kwargs.get("delayMode", "PG") == "FW":
        nSeg = int(np.ceil((delay_max_ns - delay_min_ns)/(2.5*(int(kwargs.get("bxclk_period", '28'), 16)//2)))) + 1
        tPixel = nVth*(nDelay*(100e-6*nsample*nIter + 0.05) + nSeg*tsleep_delay + tsleep_vth)
    else:
        tPoint = tsleep_delay + 100e-6*nsample*nIter + 0.05
        tPixel = nVth*(nDelay*tPoint + tsleep_vth)
    print(f"PulseDelayScanMatrix: {len(pixelList)} pixels x {nVth} thresholds x {nDelay} delays")
    print(f"Estimated time: ~{tPixel/60:.1f} min per pixel, ~{len(pixelList)*tPixel/3600:.1f} h in total")

    # same timestamp for every pixel so they end up in the same folder
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    outDir = None
    for iP, nPix in enumerate(pixelList):
        print(f"Pixel {nPix} ({iP+1}/{len(pixelList)})")
        pixDir = PulseDelayScanSweepVTH(
            nPix = nPix,
            vth_min = vth_min,
            vth_max = vth_max,
            vth_step = vth_step,
            vthNames = vthNames,
            v_asic = v_asic,
            delay_min_ns = delay_min_ns,
            delay_max_ns = delay_max_ns,
            delay_step_ns = delay_step_ns,
            tsleep_delay = tsleep_delay,
            tsleep_vth = tsleep_vth,
            nsample = nsample,
            nIter = nIter,
            dataDir = dataDir,
            dateTime = now,
            testType = "PulseDelayScanMatrix",
            **kwargs
        )
        if pixDir is not None:
            outDir = os.path.dirname(os.path.normpath(pixDir))

    return outDir
