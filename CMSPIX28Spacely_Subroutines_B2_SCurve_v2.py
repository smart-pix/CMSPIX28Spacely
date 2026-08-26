# spacely
from Master_Config import *

# python modules
import sys
try:
    import tqdm
    import numpy as np
    import math
    import h5py
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately


#-----------------------------------------------------------------------
# PreProgSCurve_v2 function - OPTIMIZED VERSION using sw_readStream
#-----------------------------------------------------------------------
# This function is identical to PreProgSCurve but uses sw_readStream() for
# bulk read operations instead of individual per-word reads.
# Data format is identical - no changes to output.
#
# Key improvement: Replace nested read loop (lines 176-197) with streaming
# Expected speedup: 2-3× for the readback phase
#-----------------------------------------------------------------------

def PreProgSCurve_v2(
        scanLoadPhase = '26',
        scan_load_delay = '13',
        startBxclkState = '0',
        bxclk_delay = '12', #'0B',
        bxclk_period = '28',
        injection_delay = '1E', # vin_test_trig_out in the FW
        scanLoopBackBit = '0',
        test_sample = '0F',
        test_delay = '14',
        v_min = 0.01,
        v_max = 0.4,
        v_step = 0.01,
        nsample = 1000,
        nPix = 0,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        testType = "Single",
        parameter = None
):

    # Note we do not yet have a smoke test. verify this on scope as desired.
    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]
    # hex lists
    hex_lists = [
        # Setting up STATIC_ARRAY_0 for IP 2 test 5 - nothing change from other test
        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scan_load_delay}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclk_delay}", f"6'h{bxclk_period}"],
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # w_cfg_static_0_reg_pack_data_array_0_IP2
         # SPARE bits:  "3'h0"
         # Register Static 0 is programmed : "4'h3"
         # IP 2 is selected: "4'h2"

        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"19'h0"],
         # 8 - bits to identify pixel number
         # 11 - bit to program number of samples
         # SPARE bits:  "4'h0"
         # Register Static 1 is programmed : "4'h4"
         # IP 2 is selected: "4'h2"
    ]
    sw_write32_0(hex_lists)
    # sw_read32_0, _, _, _ = sw_read32()

    # define range of asic voltages
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of 32bit word to read the scanChain
    nWord = 24
    ipixel = (V_PORT["vdda"].get_current())*1000000/(512*10)    # extract roughtly Ibias for a pixel. NEED TO KNOW I_testStructure!!!

    # 400MHz is the FPGA clock
    bxclk_period_inMhz = 400/int(bxclk_period, 16)
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    # create output directory

    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_Ibias{V_LEVEL['Ibias']:.3f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixIbias":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_nPix{nPix}"
        # pixelInfo = f"Ibias{V_LEVEL['Ibias']:.3f}"
        pixelInfo = f"Ibias{I_LEVEL['OUTsink']:.6f}"
    elif testType == "MatrixVTH":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}_nPix{nPix}"
        pixelInfo = f"vth{V_LEVEL['vth0']:.3f}"
    elif testType == "MatrixInjDly":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_nPix{nPix}"
        pixelInfo = f"injDly{injection_delay_in_ns:.2f}"
    elif testType == "MatrixBxCLKDly":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_injDly{injection_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_nPix{nPix}"
        pixelInfo = f"MatrixBxCLKDly{bxclk_delay_in_ns:.2f}"
    elif testType == "MatrixPulseGenFall":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_Ibias{V_LEVEL['Ibias']:.3f}__vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_nPix{nPix}"
        pixelInfo = f"FallTime{parameter:.3e}"

    elif testType == "Single":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pixPower{ipixel*0.9:.3f}_nPix{nPix}_streamRead"
        pixelInfo = ""

    # output directory
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # loop over the voltage steps
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0
            return

        # The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
        # each voltage step is then set with 2.vstep
        # 1mV equals 25e- (TBD!!!!!)
        SDG7102A_SWEEP(v_asic*2) # we used 50 ohm output load settings in the pulse generator
        # BK4600HLEV_SWEEP(v_asic*2)

        save_data = []
        for j in tqdm.tqdm(range(nsample), desc="Number of Samples", leave=False):

            # write configuration
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    #"6'h1D", # 6 bits for w_execute_cfg_test_injection_delay_index_max
                    f"6'h{injection_delay}", # 6 bits for w_execute_cfg_test_injection_delay_index_max
                    f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST
                    f"6'h{test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    f"6'h{test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ]
            sw_write32_0(hex_lists)

            if nPix == None:
                wordList = list(range(24))
            # prepare the word list to read
            else:
                if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                    wordList = [int(((nPix-1)*3+1)/32)]
                else:
                    wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

            # allocate array for the words
            words = ["0"*32] * nWord

            # ============================================================
            # OPTIMIZED READBACK: Use sw_readStream() for bulk reads
            # ============================================================
            # Instead of per-word reads, set up all addresses first,
            # then use streaming read to get all data in one bulk operation.
            # Data format is identical to original version.

            # Send all read address commands
            for iW in wordList:
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                sw_write32_0(hex_lists)

            # Now use streaming read to get all data at once
            # This single bulk read replaces len(wordList) individual reads
            try:
                # Use sw_readStream to bulk read from the FPGA
                sw_read32_0_stream = sg.INSTR["car"].stream_memory("sw_read32_0", len(wordList))

                # Convert streamed data to same format as original
                for idx, iW in enumerate(wordList):
                    words[iW] = int_to_32bit(sw_read32_0_stream[idx])[::-1]

            except Exception as e:
                # Fallback to original per-word reads if streaming not available
                sg.log.warning(f"Stream read failed: {e}. Falling back to per-word reads.")
                for iW in wordList:
                    address = "8'h" + hex(iW)[2:]
                    hex_lists = [
                        ["4'h2", "4'hC", address, "16'h0"]
                    ]
                    sw_write32_0(hex_lists)
                    sw_read32_0, sw_read32_1_old, _, _ = sw_read32()
                    words[iW] = int_to_32bit(sw_read32_0)[::-1]

            # save words (identical data format to original)
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        save_data = save_data[:, 0:-3]
        save_data = save_data.reshape(-1, 255, 3)
        save_data = save_data[:,nPix]
        # save the output file
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)

    return None
