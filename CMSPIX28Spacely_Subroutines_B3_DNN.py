# spacely
from Master_Config import *

# python modules
import sys
import time
import pandas as pd
import numpy as np
try:
    import os
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately

# Only needed for DNN_power(..., plotBool=True); not otherwise used in this
# file, so a missing install shouldn't block hardware runs that don't plot.
try:
    import matplotlib.pyplot as plt
    from scipy.stats import norm, linregress
except ImportError:
    plt = None
    norm = None
    linregress = None

def DNN(
    progDebug=False,
    loopbackBit=0, 
    patternIndexes = [0], 
    verbose=False, 
    injection_delay='1E', 
    bxclk_period='28', 
    startBxclkState='0',
    scan_load_delay='13', 
    cfg_test_delay='5', 
    cfg_test_sample='20', 
    progResetMask='0', 
    configclk_period='64', 
    test_delay='14', 
    test_sample='0F', 
    bxclk_delay='12',
    configClkGate='0',
    scanLoadPhase ='26', 
    dnn_csv=None, 
    pixel_compout_csv=None, 
    dataDir = FNAL_SETTINGS["storageDirectory"],
    dateTime = None,
    vth0=0.08,
    vth1=0.16,
    vth2=0.32,
    pg_hlev = 0.22,
    dnn0=0.079,
    dnn1=0.070,
    readYproj=True,
    dnnPowerBool = False,
    appendMode = False
):

    # [TIMING] per-call stage timings for the dnnPowerBool=True path (DNN_power
    # calls DNN() once per test vector with a single-element patternIndexes,
    # so this function returns right after the status-done poll below -
    # everything from here down to that return is the entire per-vector cost).
    t0 = time.time()

    #set threshold to higher values

    V_PORT["vth0"].set_voltage(vth0)
    V_LEVEL["vth0"] = vth0
    V_PORT["vth1"].set_voltage(vth1)
    V_LEVEL["vth1"] = vth1
    V_PORT["vth2"].set_voltage(vth2)
    V_LEVEL["vth2"] = vth2
    V_PORT["dnn0"].set_voltage(dnn0)
    V_LEVEL["dnn0"] = dnn0
    V_PORT["dnn1"].set_voltage(dnn1)
    V_LEVEL["dnn1"] = dnn1

    if dnnPowerBool==False:
        SDG7102A_SWEEP(HLEV=pg_hlev) # Set the pulse generator to 0.3V
    t_vth_set = time.time() - t0

    testType = "DNN"

    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}"
    # output directory
    outDir = os.path.join(dataDir, chipInfo, testInfo)
    t0 = time.time()
    # appendMode callers (DNN_power) pass a fixed `dateTime` so outDir is the
    # same path on every call - os.makedirs(exist_ok=True) is then a cheap
    # no-op after the first call instead of a fresh directory per test
    # vector. Only the log print is suppressed to avoid n_tb lines of spam.
    if not appendMode:
        print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)
    t_outdir_setup = time.time() - t0

    # Set the firmware to the default state
    t0 = time.time()
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)
    t_fw_reset = time.time() - t0

    # First set up the pulse generator
    if dnnPowerBool==False:
        SDG7102A_SWEEP(HLEV=pg_hlev)
        print("Setting the pulse generator HLEV to “, pg_hlev, “V for ROUTINE_DNN.")

    # Program shift register
    t0 = time.time()
    hex_lists = [
        # ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 1M
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]
    sw_write32_0(hex_lists)
    t_write_static = time.time() - t0


    # load all of the configs
    t0 = time.time()
    filename = pixel_compout_csv if pixel_compout_csv else "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)
    t_csv_parse = time.time() - t0

    # loop over test cases
    patternIndexes = range(len(pixelLists)) if patternIndexes == None else patternIndexes

    # list to save to
    yprofiles = []
    readouts = []
    iN = 0

    # [TIMING] per-stage cumulative totals across the whole run, printed
    # periodically below so the per-test-vector breakdown doesn't get lost
    # in thousands of lines of output.
    t_pixelconfig_total = 0.0
    t_dnnconfig_total = 0.0
    t_write_cfg_total = 0.0
    t_write_exec1_total = 0.0
    t_sleep_total = 0.0
    t_write_scanload_total = 0.0
    t_write_exec2_total = 0.0
    t_read_yproj_total = 0.0
    t_read_dnn_total = 0.0
    t_save_total = 0.0
    t_loop_start = time.time()
    TIMING_PRINT_EVERY = 50

    # loop over all patterns
    for iP in tqdm.tqdm(patternIndexes):

        # increment counter of number of patterns
        iN += 1
        hiddenBit= "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/hidden_debug.csv"

        # pick up pixel config for the given pattern
        t0 = time.time()
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])
        t_pixelconfig_total += time.time() - t0

        # Programming the NN weights and biases
        # THIS TAKES SIGNIFICANT AMOUNT OF TIME (~0.3sec) --> COULD IMPROVE --<
        t0 = time.time()
        if(progDebug==True):
            hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin_debug2.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        else:
            filename = dnn_csv if dnn_csv else '/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv'

            # hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
            hex_lists = dnnConfig(filename, pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        t_dnnconfig_total += time.time() - t0

        t0 = time.time()
        sw_write32_0(hex_lists)
        t_write_cfg_total += time.time() - t0

        # write execute command
        t0 = time.time()
        hex_lists = [
            [
                "4'h1",  # firmware id
                "4'hf",  # op code d for execute
                f"1'h{progResetMask}",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
                "3'h0", # 3 bits for spare_index_max
                f"1'h{configClkGate}", # 1 bit for gating configClk
                "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                "4'h1",  # 4 bits for test number
                f"7'h{cfg_test_sample}", # 6 bits test sample
                f"7'h{cfg_test_delay}"  # 6 bits for test delay
            ]
        ]
        sw_write32_0(hex_lists)
        t_write_exec1_total += time.time() - t0

        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
        # Wait for the CONFIG-SHIFT-REG load triggered above to actually finish,
        # by polling the real hardware status_done bit (sm_test1_o_status_done,
        # bit 14 of sw_read32_1) instead of a fixed sleep. 20ms timeout kept as
        # a safety fallback (the previously-tuned empirical worst case).
        t0 = time.time()
        cfgDone, cfgDoneElapsedUs = sw_pollStatusDone(bit_index=14, timeout_us=20000)
        if not cfgDone:
            print(f"WARNING: DNN CONFIG-SHIFT-REG status_done poll timed out after {cfgDoneElapsedUs}us")
        t_sleep_total += time.time() - t0
        if dnnPowerBool:
            return {
                "vth_set": t_vth_set,
                "outdir_setup": t_outdir_setup,
                "fw_reset": t_fw_reset,
                "write_static": t_write_static,
                "csv_parse": t_csv_parse,
                "pixelconfig": t_pixelconfig_total,
                "dnnconfig": t_dnnconfig_total,
                "write_cfg": t_write_cfg_total,
                "write_exec1": t_write_exec1_total,
                "status_poll": t_sleep_total,
            }

        # verbose and debug mode
        if(verbose==True and progDebug==True):
            #ReadBack from READ_ARRAY 1
            words_A0 = []      
            words_A1 = []
            words_A2 = []    
            words_DA0 = []
            words_DA1 = []              
            for i in range(0, 256,2):
                address = hex(i)[2:]
                hex_list0 = [
                [
                    "4'h1", "4'h7", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 0            
                ]
                sw_write32_0(hex_list0)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A0.append([address,int_to_32bit(sw_read32_0)])

                hex_list1 = [
                [
                    "4'h1", "4'h9", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 1            
                ]
                sw_write32_0(hex_list1)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A1.append([address,int_to_32bit(sw_read32_0)])

                hex_list2 = [
                [
                    "4'h1", "4'hB", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 2            
                ]
                sw_write32_0(hex_list2)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_A2.append([address,int_to_32bit(sw_read32_0)])
            
            for i in range(256):
                address = hex(i)[2:]
                hex_list_rdata0 = [
                [
                    "4'h1", "4'hC", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 0            
                ]
                sw_write32_0(hex_list_rdata0)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_DA0.append([address,int_to_32bit(sw_read32_0)])

                hex_list_rdata1 = [
                [
                    "4'h1", "4'hD", f"8'h{address}", "16'h0"]         #ReadBack from READ DATA ARRAY 1            
                ]
                sw_write32_0(hex_list_rdata1)
                sw_read32_0, sw_read32_1, _, _ = sw_read32() 
                words_DA1.append([address,int_to_32bit(sw_read32_0)])

            print("CFG ARRAY 0")
            for i in words_A0:
                print(i)
            print("CFG ARRAY 1")
            for i in words_A1:
                print(i)
            print("CFG ARRAY 2")  
            for i in words_A2:
                print(i)           
            print("READ DATA 0")   
            for i in words_DA0:
                print(i)    
            print("READ DATA 1")  
            for i in words_DA1:
                print(i)
            cfgArray0File = "cfgArray0.csv"
            with open(cfgArray0File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_A0)
            array0File = "array0.csv"                  
            with open(array0File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_DA0)
            array1File = "array1.csv"                  
            with open(array1File, 'a+', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(words_DA1)

        # NEED SLEEP TIME BECAUSE FW TAKES 53ms (5162 shift register at 100KHz speed) which is slower than python in this case
        t0 = time.time()
        x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
        scanLoadPhase1= hex(int(x[:2], 2))[2:]
        scanLoadPhase0= hex(int(x[2:], 2))[2:]
        # # hex lists                                     
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

        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", "19'h0"],           
         # 8 - bits to identify pixel number
         # 11 - bit to program number of samples
         # SPARE bits:  "4'h0"
         # Register Static 1 is programmed : "4'h4"
         # IP 2 is selected: "4'h2"
        ]
            

        sw_write32_0(hex_lists)
        t_write_scanload_total += time.time() - t0

        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")

        # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.

        # input("Press Enter to continue...") # wait for user input to continue

        # # DODO SETTINGS
        t0 = time.time()
        hex_lists = [
            [
                "4'h2",  # firmware id
                "4'hF",  # op code for execute
                "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                f"6'h{injection_delay}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                f"6'h{test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                f"6'h{test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
            ]
        ]       


        sw_write32_0(hex_lists)
        t_write_exec2_total += time.time() - t0

        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()

        # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits).
        # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0

        t0 = time.time()
        if readYproj:
            nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case

            # burst-read all 24 DATA_ARRAY_0 words in one round trip instead of
            # 24 individual write(address)+read requests
            sw_read32_0_stream, _, _, _ = sw_readStream(
                N=nwords, opcode=0xC, base_addr=0, do_sw_read32_1=False
            )
            words = [int_to_32bit(word)[::-1] for word in sw_read32_0_stream]

            s = ''.join(words)
            row_sums = [0]*16
            if s.find("1") != -1:
                #Y-projection
                temp = np.array([int(i) for i in s]).reshape(256,3)
                superpixel_array = np.zeros((8,32))
                for iP, val in enumerate(temp):
                    if 1 in val:
                        result_string = ''.join(val.astype(str))
                        row = 7-find_grid_cell_superpix(iP)[0]
                        col = find_grid_cell_superpix(iP)[1]
                        superpixel_array[row][col]=int(thermometric_to_integer(result_string[::-1]))
                        even_columns = superpixel_array[:,::2].sum(axis=1)
                        odd_columns = superpixel_array[:,1::2].sum(axis=1)
                        row_sums = []
                        for i, j in zip(even_columns, odd_columns):
                            row_sums.append(int(i))
                            row_sums.append(int(j))
                        # row_sums = np.array(row_sums) 
                row_sums = row_sums[::-1]
        t_read_yproj_total += time.time() - t0

        t0 = time.time()
        dnn_nwords = 8

        # burst-read all 8 DATA_ARRAY_1 words in one round trip instead of 8
        # individual write(address)+read requests
        sw_read32_0_stream, _, _, _ = sw_readStream(
            N=dnn_nwords, opcode=0xD, base_addr=0, do_sw_read32_1=False
        )
        # old loop built dnn_words via insert(0, ...) each iteration, so the
        # final order is address-descending (word7 first); reverse to match
        dnn_words = [int_to_32bit(word) for word in reversed(sw_read32_0_stream)]

        dnn_s = ''.join(dnn_words)
        t_read_dnn_total += time.time() - t0

        if verbose:
            print(f"the input vector to the DNN is {row_sums}")
            # Printout of data seen in FW
            # dnn_0=dnn_s[-48:] 
            # dnn_1=dnn_s[-96:-48] 
            # bxclk_ana=dnn_s[-144:-96] 
            # bxclk=dnn_s[-192:-144] 
            dnn_0=dnn_s[-64:] 
            dnn_1=dnn_s[-128:-64] 
            bxclk_ana=dnn_s[-192:-128] 
            bxclk=dnn_s[-256:-192]            
            print(f"reversed dnn_0     = {dnn_0}", len(dnn_0), hex(int(dnn_0, 2)))
            print(f"reversed dnn_1     = {dnn_1}", len(dnn_1), hex(int(dnn_1, 2))) 
            print(f"reversed bxclk_ana = {bxclk_ana}", len(bxclk_ana), hex(int(bxclk_ana, 2)))
            print(f"reversed bxclk     = {bxclk}", len(bxclk), hex(int(bxclk, 2)))   
            get_power()

        # append to y profile list and dnn output list
        if readYproj:
            yprofiles.append(row_sums)
        readouts.append(dnn_s)

        # save every 25 and on the last one
        t0 = time.time()
        if iN % 100 == 0 or iN == len(patternIndexes):
            # appendMode callers (DNN_power) call DNN() once per test vector
            # with a single-element patternIndexes, so each call's
            # yprofiles/readouts is just that one row - append instead of
            # overwrite so repeated calls build up one growing file rather
            # than each call replacing the last one's row.
            file_mode = 'a' if appendMode else 'w'
            if readYproj:
                # save to csv file
                yprofileOutputFile = os.path.join(outDir,"yprofiles.csv")
                with open(yprofileOutputFile, file_mode, newline="") as file:
                    writer = csv.writer(file)
                    writer.writerows(yprofiles)
                print("Saving to: ", yprofileOutputFile)

            # save readouts to csv

            readoutOutputFile = os.path.join(outDir,"readout.csv")
            with open(readoutOutputFile, file_mode, newline="") as file:
                writer = csv.writer(file)
                writer.writerows(readouts)

            print("Saving to: ", readoutOutputFile, iN)
        t_save_total += time.time() - t0

        # [TIMING] periodic per-stage breakdown so this doesn't get lost in
        # thousands of lines of tqdm output. Uses tqdm.write() rather than
        # print() so it doesn't corrupt the progress bar rendering.
        if iN % TIMING_PRINT_EVERY == 0 or iN == len(patternIndexes):
            elapsed = time.time() - t_loop_start
            tqdm.tqdm.write(
                f"[TIMING] n={iN} total_elapsed={elapsed:.2f}s avg/vec={elapsed/iN:.4f}s | "
                f"dnnConfig={t_dnnconfig_total/iN:.4f} "
                f"write_cfg={t_write_cfg_total/iN:.4f} "
                f"write_exec1={t_write_exec1_total/iN:.4f} "
                f"sleep={t_sleep_total/iN:.4f} "
                f"write_scanload={t_write_scanload_total/iN:.4f} "
                f"write_exec2={t_write_exec2_total/iN:.4f} "
                f"read_yproj={t_read_yproj_total/iN:.4f} "
                f"read_dnn={t_read_dnn_total/iN:.4f} "
                f"save={t_save_total/iN:.4f} (s/vec)"
            )

    # the output path is built here from a timestamp, so callers that need to
    # read readout.csv back (e.g. ASIC-in-the-loop training) cannot reconstruct
    # it; hand it back rather than making them guess.
    return outDir


def DNN_power(n_tb=100, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=0.014, vth1=0.083, vth2=0.128, pg_hlev=0.6, pixel_compout_csv=None, dnn_csv=None, plotBool=False, LHC_RATE=1):

    startTime = time.time()

    # --- time probe: accumulates {bucket_name: [total_seconds, call_count]} ---
    timing = {}
    def _tic():
        return time.time()
    def _toc(bucket, t0):
        entry = timing.setdefault(bucket, [0.0, 0])
        entry[0] += time.time() - t0
        entry[1] += 1

    t0 = _tic()
    SDG7102A_INJ_CONT(LHC_RATE=LHC_RATE)
    time.sleep(waitTime)
    _toc("initial_inj_cont+waitTime", t0)

    suffix="OnHit"
    if pNoiseBool:
        t0 = _tic()
        suffix="OnNoise"
        SDG7102A_INJ_BURST()
        SDG7102A_SWEEP(HLEV=0)
        V_PORT["vth0"].set_voltage(vth0)
        V_LEVEL["vth0"] = vth0
        V_PORT["vth1"].set_voltage(vth1)
        V_LEVEL["vth1"] = vth1
        V_PORT["vth2"].set_voltage(vth2)
        V_LEVEL["vth2"] = vth2
        #set pulse generator in normal condition
        DNN(
        progDebug=False,
        loopbackBit=0,
        patternIndexes = [0],
        verbose=False,
        injection_delay='1E',
        bxclk_period='28',
        startBxclkState='0',
        scan_load_delay='13',
        cfg_test_delay='5',
        cfg_test_sample='20',
        progResetMask='0',
        configclk_period='64',
        test_delay='14',
        test_sample='0F',
        bxclk_delay='12',
        configClkGate='0',
        scanLoadPhase ='26',
        dnn_csv=None,
        pixel_compout_csv=None,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        vth0=vth0,
        vth1=vth1,
        vth2=vth2,
        readYproj=True,
        dnnPowerBool = True,
        appendMode = True
        )
        time.sleep(3*dnnwaitTime) # wait for some time just in case
        _toc("noise_setup_block", t0)

    t0 = _tic()
    pixelLists, pixelValues = genPixelConfigFromInputCSV(pixel_compout_csv)
    _toc("initial_csv_parse", t0)
    num_clusters = len(pixelLists)
    testType = "DNN"
    dataDir=FNAL_SETTINGS["storageDirectory"]
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    if vth0 < 1:
        print("WARNING: vth0, vth1, vth2 are in volts, not in electrons. Please convert them to electrons or update the routine.")
        sys.exit(1)
    vth_0_mv = round((vth0 - 196.84)/16960.09, 3)
    vth_1_mv = round((vth1 - 223.96)/16853.41, 3)
    vth_2_mv = round((vth2 - 224.42)/16922.43, 3)
    print(f"vth_0 [e-] = {vth0}, vth_1 [e-] = {vth1}, vth_2 [e-] = {vth2}")
    print(f"vth_0 [mV] = {vth_0_mv}, vth_1 [mV] = {vth_1_mv}, vth_2 [mV] = {vth_2_mv}")
    V_PORT["vth0"].set_voltage(vth_0_mv)
    V_LEVEL["vth0"] = vth_0_mv
    V_PORT["vth1"].set_voltage(vth_1_mv)
    V_LEVEL["vth1"] = vth_1_mv
    V_PORT["vth2"].set_voltage(vth_2_mv)
    V_LEVEL["vth2"] = vth_2_mv

    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pg_hlev-{pg_hlev:.3f}_LHC_RATE-{LHC_RATE}"
    # create temp directory to delete dirs between ABC_temp and ABC_dnnPower
    outDirTemp = os.path.join(dataDir, chipInfo, testInfo)
    outDirTemp = outDirTemp + str("_temp")
    # print(f"Saving results to {outDirTemp}")
    os.makedirs(outDirTemp, exist_ok=True)
    os.chmod(outDirTemp, mode=0o777)

    # output directory that saves the current values - computed up front (not
    # after the loop) so Ivddd.csv can be checkpointed periodically below,
    # rather than only written once after all n_tb vectors have run.
    testInfo = (datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pg_hlev-{pg_hlev:.3f}_LHC_RATE-{LHC_RATE}"
    outDirPower = os.path.join(dataDir, chipInfo, testInfo)
    outDirPower = outDirPower + str("_dnnPower") + str(suffix)
    print(f"Saving results to {outDirPower}")
    os.makedirs(outDirPower, exist_ok=True)
    os.chmod(outDirPower, mode=0o777)
    ivdddFile = os.path.join(outDirPower, "Ivddd.csv")

    # Fixed timestamp so every DNN() call below (dateTime=dnnCallDateTime)
    # resolves to the same outDir instead of a fresh one per test vector -
    # yprofiles.csv/readout.csv then accumulate across the whole loop.
    dnnCallDateTime = datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + "_dnnPowerLoop"

    Ivddd_post = []
    Ivddd_pre = []
    Event_number = []
    Vvddd = []
    current_pre_val = -1

    def _save_ivddd_csv():
        partial_df = pd.DataFrame()
        partial_df["Event_number"] = Event_number
        partial_df["Ivddd_pre"] = Ivddd_pre
        partial_df["Ivddd_post"] = Ivddd_post
        partial_df["Vvddd"] = Vvddd
        partial_df["i_dnn"] = partial_df["Ivddd_post"] - partial_df["Ivddd_pre"]
        partial_df.to_csv(ivdddFile, index=False)
        return partial_df

    for i in range(n_tb):
        evt_index = num_clusters - n_tb + i
        if i%1000==0:
            print(f"Running DNN power test for test vector {i+1}/{n_tb}")
        if pNoiseBool:
            t0 = _tic()
            time.sleep(0.1) # no injection happening, only triggering on noise, so wait time has been reduced.
            # print("Ivdd_post=",Ivddd_post)
            Ivddd_post.append(V_PORT["vddd"].get_current())
            _toc("noise_measure_post", t0)
        else:
            #set pulse generator in normal condition
            t0 = _tic()
            DNN(
            progDebug=False,
            loopbackBit=0,
            patternIndexes = [evt_index],  # inject the last n_tb clusters
            verbose=False,
            injection_delay='1E',
            bxclk_period='28',
            startBxclkState='0',
            scan_load_delay='13',
            cfg_test_delay='5',
            cfg_test_sample='20',
            progResetMask='0',
            configclk_period='64',
            test_delay='14',
            test_sample='0F',
            bxclk_delay='12',
            configClkGate='0',
            scanLoadPhase ='26',
            dnn_csv=dnn_csv,
            pixel_compout_csv=pixel_compout_csv,
            dataDir = FNAL_SETTINGS["storageDirectory"],
            dateTime = dnnCallDateTime,
            vth0=vth_0_mv,#0.08,
            vth1=vth_1_mv,#0.16,
            vth2=vth_2_mv,#0.32,
            pg_hlev=pg_hlev,
            readYproj=True,
            appendMode = True
            )
            _toc("dnn_call_total", t0)
            #set pulse generator in continuous injection
            t0 = _tic()
            time.sleep(dnnwaitTime)
            _toc("dnnwaitTime_sleep", t0)
            t0 = _tic()
            Event_number.append(evt_index)
            Vvddd.append(V_PORT["vddd"].get_voltage()) 
            Ivddd_post.append(V_PORT["vddd"].get_current()*100) #convert in mA, the carboard has an x10 resistor already
            _toc("measure_post", t0)
            # print("Ivdd_post=",Ivddd_post)
        if i % 10 == 0:
            t0 = _tic()
            SDG7102A_SWEEP(HLEV=0)
            time.sleep(1)
            current_pre_val = V_PORT["vddd"].get_current()*100  # Capture single value in mA
            SDG7102A_SWEEP(HLEV=pg_hlev)
            time.sleep(1)
            _toc("measure_pre_block", t0)
        # Append exactly 1 item every loop to guarantee matching list lengths
        Ivddd_pre.append(current_pre_val)

        # Checkpoint Ivddd.csv every 100 test vectors (and on the last one) so
        # a long n_tb run doesn't lose everything if it's interrupted partway.
        if (i + 1) % 100 == 0 or i == n_tb - 1:
            t0 = _tic()
            _save_ivddd_csv()
            _toc("ivddd_csv_checkpoint", t0)

    print("post current measurement done")
    # time.sleep(60)

    # SDG7102A_INJ_BURST()
    # time.sleep(waitTime)
    # if pNoiseBool:
    #     SDG7102A_SWEEP(HLEV=0)
    #     time.sleep(dnnwaitTime)

    # print("pre current measurement done")
    # Ivddd_pre=V_PORT["vddd"].get_current()
    # print("Ivdd_pre=", Ivddd_pre)
    # time.sleep(60)
    # Ivddd_pre = [Ivddd_pre]*n_tb
    totalElapsed = time.time() - startTime
    print("time elapsed = ", totalElapsed)

    print("--- time probe breakdown ---")
    for bucket, (total, count) in sorted(timing.items(), key=lambda kv: kv[1][0], reverse=True):
        pct = 100.0 * total / totalElapsed if totalElapsed else 0.0
        avg = total / count if count else 0.0
        print(f"  {bucket:28s} total={total:8.2f}s ({pct:5.1f}%)  count={count:5d}  avg={avg*1000:7.1f}ms")
    print("----------------------------")

    # Already checkpointed every 100 vectors (and on the last one) above -
    # this just gets the final in-memory df back for plotting below.
    df = _save_ivddd_csv()

    if plotBool:
        DNN_power_plot(df, pixel_compout_csv, outDirPower)


def DNN_power_plot(df, pixel_compout_csv, outDirPower):
    # Same math as analysis/power_measurement.py's parse_data()/histogram/
    # cluster-size blocks, just generated inline so a DNN_power() run doesn't
    # need a separate offline analysis pass to see the power spread.
    if plt is None or norm is None or linregress is None:
        print("WARNING: matplotlib/scipy not available - skipping DNN_power plots.")
        return

    Power_uW = df["i_dnn"] * 0.9 * 1000  # (Ivddd_post - Ivddd_pre) scaled to uW

    # --- Plot A: histogram of Power with a Gaussian fit ---
    mean = np.mean(Power_uW)
    rms = np.sqrt(np.mean(np.square(Power_uW - mean)))
    fit_min, fit_max = mean - 3 * rms, mean + 3 * rms
    Power_filtered = Power_uW[(Power_uW >= fit_min) & (Power_uW <= fit_max)]
    mu, std = norm.fit(Power_filtered)

    fig, ax = plt.subplots(figsize=(8, 6))
    counts, bins, _ = ax.hist(Power_uW, bins=50, facecolor='none', edgecolor='black', linewidth=1.5, label="Data")
    bin_width = bins[1] - bins[0]
    scaling_factor = len(Power_uW) * bin_width
    x = np.linspace(bins[0], bins[-1], 200)
    p = norm.pdf(x, mu, std) * scaling_factor
    ax.plot(x, p, color='red', linewidth=2, label=f"Gaussian fit\n$\\mu={mu:.2f}, \\sigma={std:.2f}$ $\\mu$W")
    ax.set_xlabel("Power [$\\mu$W]")
    ax.set_ylabel("Events")
    ax.grid()
    ax.legend(loc='upper right')
    fig.tight_layout()
    histFile = os.path.join(outDirPower, "power_hist.pdf")
    fig.savefig(histFile)
    plt.close(fig)
    print(f"Saved power histogram to {histFile}")

    # --- Plot B: Power vs. cluster size (cluster size read from the compout CSV) ---
    event_numbers = df["Event_number"]
    if len(event_numbers) == 0 or pixel_compout_csv is None:
        print("WARNING: no Event_number/compout data available - skipping power_vs_clusterSize.pdf")
        return

    with open(pixel_compout_csv, 'r') as f:
        lines = f.readlines()

    cluster_sizes = []
    for idx in event_numbers:
        line = lines[idx].strip()
        pixels = [int(val) for val in line.split(',')]
        matrix = np.array(pixels).reshape(16, 16)
        # cluster size = number of rows (y-direction) with at least one hit pixel
        cluster_sizes.append(np.count_nonzero(matrix.sum(axis=1)))
    cluster_sizes = np.array(cluster_sizes)

    unique_cluster_sizes = np.arange(0, 14)
    average_powers = []
    valid_cluster_sizes = []
    for size in unique_cluster_sizes:
        power_values = Power_uW[cluster_sizes == size]
        if len(power_values):
            valid_cluster_sizes.append(size)
            average_powers.append(np.mean(power_values))

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(cluster_sizes, Power_uW, color='purple', marker='o', s=15, label='Power vs cluster size')
    if len(valid_cluster_sizes) >= 2:
        slope, intercept, r_value, p_value, std_err = linregress(valid_cluster_sizes, average_powers)
        fitted_line = slope * np.array(valid_cluster_sizes) + intercept
        ax.scatter(valid_cluster_sizes, average_powers, color='darkorange', marker='d', s=15, label='Average power')
        ax.plot(valid_cluster_sizes, fitted_line, color='blue', label=f"Fit: y = {slope:.2f}x + {intercept:.2f}")
    ax.set_xlabel("Cluster size (y-direction) [pixels]")
    ax.set_ylabel("Power [$\\mu$W]")
    ax.grid()
    ax.legend(loc='best')
    fig.tight_layout()
    scatterFile = os.path.join(outDirPower, "power_vs_clusterSize.pdf")
    fig.savefig(scatterFile)
    plt.close(fig)
    print(f"Saved power vs. cluster size plot to {scatterFile}")


def DNN_analyse(debug=False, latency_bit=37, bxclkFreq='28', readout_CSV="readout.csv", debug_tv=0):
    #divider used in the test for bxclk frequency
    fdivider= int(bxclkFreq, 16) # Convert the frequency divider for BxCLK into decimal to recover latency #63       
    print(fdivider)
    dnn_words = []
    dnn_0 =[]
    dnn_1 =[]
    dnn_s = []
    dnn_out =[]
    reshaped_dnn_out =[]

    with open(readout_CSV, mode='r', newline='') as file:
        reader = csv.reader(file)

        for row in reader:
            dnn_words.append(row)
            # data.append([int(value) for value in row])

    # print(dnn_words[0])
    # print(len(dnn_words))

    # Reformatting the DNN list - removing extract bits
    for tv in range(len(dnn_words)):
        dnn_s.append(''.join(dnn_words[tv]))
    
    dnn_0= [item[-fdivider:] for item in dnn_s]
    dnn_1= [item[-(64+fdivider):-64]  for item in dnn_s]
    bxclk_ana= [item[-(128+fdivider):-128] for item in dnn_s]
    bxclk= [item[-(192+fdivider):-192]  for item in dnn_s]

    if debug==True:
        debug_tv = debug_tv  #print test vector #1
        print("signal before latency correction")
        print(dnn_0[debug_tv])
        print(dnn_1[debug_tv])
        print(bxclk_ana[debug_tv])
        print(bxclk[debug_tv])

        # Shifting the DNN lists to compensate for system latencies
        dnn_0 = [shift_right(item,latency_bit) for item in dnn_0]
        dnn_1 = [shift_right(item,latency_bit) for item in dnn_1]
        print("signal after latency correction")
        print(dnn_0[debug_tv])
        print(dnn_1[debug_tv])
        print(bxclk_ana[debug_tv])
        print(bxclk[debug_tv])


    # for tv in [debug_tv]: #range(len(dnn_words)):
    for tv in range(len(dnn_words)):   
        cnt_dnn0_zeros = 0  
        cnt_dnn0_ones = 0     
        cnt_dnn1_zeros = 0       
        cnt_dnn1_ones = 0    
        cnt_bxclkana = 0
        for index, element in enumerate(str(bxclk_ana[tv])):
            # if element == '1':
            #     cnt_bxclkana += 1
            #     if dnn_0[tv][index] =='0':
            #         cnt_dnn0_zeros += 1
            #     else:
            #         cnt_dnn0_ones += 1
            #     if dnn_1[tv][index] =='0':
            #         cnt_dnn1_zeros += 1
            #     else:
            #         cnt_dnn1_ones +=1

            if dnn_0[tv][index] =='0':
                cnt_dnn0_zeros += 1
            else:
                cnt_dnn0_ones += 1
            if dnn_1[tv][index] =='0':
                cnt_dnn1_zeros += 1
            else:
                cnt_dnn1_ones +=1
        if debug==True and tv==debug_tv:
            print("voting")
            print(cnt_dnn0_zeros)
            print(cnt_dnn0_ones)
            print(cnt_dnn1_zeros)
            print(cnt_dnn1_ones)    
            print(cnt_bxclkana)   
        # Voting system
        # if cnt_dnn0_zeros>cnt_dnn0_ones and cnt_dnn0_ones>0:
        if cnt_dnn0_ones > 4: 
            dnn_0[tv] = '1'
        else:
            dnn_0[tv] = '0'
        # if cnt_dnn1_zeros>cnt_dnn1_ones and cnt_dnn0_ones>0:
        if cnt_dnn1_zeros > 4:
            dnn_1[tv] = '0'
        else:
            dnn_1[tv] = '1'         
        dnn_out.append(int(dnn_1[tv]+(dnn_0[tv]),2))

    #Reshaping the list into 13000 rows of column 1
    for tv in range(len(dnn_words)):
        reshaped_dnn_out.append(dnn_out[tv:tv+1])
    # reshaped_dnn_out = np.array(reshaped_dnn_out).flatten()
    
    dnnAsicOutFile = 'dnn_ASIC_out.csv'
    with open(dnnAsicOutFile, 'w', newline="") as file:
        writer = csv.writer(file)
        writer.writerows(reshaped_dnn_out)

    # interpret data from chip to just give NN prediction
    # return reshaped_dnn_out


def DNN_analyse_2(readout_CSV, timestamp = 19):
    dnn0 = [0,0]
    dnn1 = [0,1]
    dnn2 = [1,0]
    possible_dnn_outputs = [dnn0, dnn1, dnn2]
    shape_per_event_results = 4,64
    len_dnn_data = 40
    len_empty_bits = 24
    results_file = np.genfromtxt(readout_CSV, delimiter=',', dtype=int)
    final_results = []
    for evt_iter in range(len(results_file)):
        event_output = results_file[evt_iter]
        reshaped_output = event_output.reshape(shape_per_event_results)
        dnn0_clipped = reshaped_output[-1][len_empty_bits:]
        dnn1_clipped = reshaped_output[-2][len_empty_bits:]
        lsb = dnn0_clipped[timestamp]
        msb = dnn1_clipped[timestamp]
        event_result = [msb, lsb]
        if event_result not in possible_dnn_outputs:
            print(f"Event result {event_result} does not match with possible values {possible_dnn_outputs}")
            final_results.append(3) # Append a default value (e.g., 3) for unmatched results
        else:
            matching_index = possible_dnn_outputs.index(event_result)
            final_results.append(matching_index)

    final_results = np.array(final_results)
    return final_results

def DNN_power_routine():
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=1600, vth2=2400, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/compouts_power_vs_cluster_size.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_centeredIncidence/trainedModels/model4/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=1600, vth2=2400, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_centeredIncidence/trainedModels/model4/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=1600, vth2=2400, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_mirror_rtl.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_centeredIncidence/trainedModels/model4/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=1600, vth2=2400, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_ltr_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_centeredIncidence/trainedModels/model4/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=1600, vth2=2400, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_rtl_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_centeredIncidence/trainedModels/model4/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/compouts_power_vs_cluster_size.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_mirror_rtl.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_ltr_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.6, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_rtl_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)


    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/compouts_power_vs_cluster_size.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True,  LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_mirror_rtl.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True,  LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_ltr_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_rtl_uniform_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)

    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.15, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=550, vth1=1100, vth2=1650, pg_hlev=0.145, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_550_1100_1650/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=700, vth1=1400, vth2=2100, pg_hlev=0.2, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=850, vth1=1700, vth2=2550, pg_hlev=0.225, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_850_1700_2550/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=767, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/filter/compouts_power_vs_cluster_size_center_spread.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    

    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.15, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/400_800_1200/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=3)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=550, vth1=1100, vth2=1650, pg_hlev=0.145, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/550_1100_1650/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_550_1100_1650/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=3)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=700, vth1=1400, vth2=2100, pg_hlev=0.2, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/700_1400_2100/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=1)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=850, vth1=1700, vth2=2550, pg_hlev=0.225, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/850_1700_2550/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_850_1700_2550/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=3)
    DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/1000_2000_3000/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=3)
    
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.15, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/400_800_1200/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=550, vth1=1100, vth2=1650, pg_hlev=0.145, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/550_1100_1650/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_550_1100_1650/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=700, vth1=1400, vth2=2100, pg_hlev=0.2, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/700_1400_2100/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=850, vth1=1700, vth2=2550, pg_hlev=0.225, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/850_1700_2550/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_850_1700_2550/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=5)
    DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/1000_2000_3000/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=5)

    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.15, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/400_800_1200/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=550, vth1=1100, vth2=1650, pg_hlev=0.145, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/550_1100_1650/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_550_1100_1650/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=700, vth1=1400, vth2=2100, pg_hlev=0.2, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/700_1400_2100/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.5)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=850, vth1=1700, vth2=2550, pg_hlev=0.225, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/850_1700_2550/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_850_1700_2550/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.5)
    DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/1000_2000_3000/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.5)

    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=400, vth1=800, vth2=1200, pg_hlev=0.15, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/400_800_1200/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_400_800_1200/model1/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.25)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=550, vth1=1100, vth2=1650, pg_hlev=0.145, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/550_1100_1650/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_550_1100_1650/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.25)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=700, vth1=1400, vth2=2100, pg_hlev=0.2, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/700_1400_2100/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_700_1400_2100/model3/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.25)
    # DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=850, vth1=1700, vth2=2550, pg_hlev=0.225, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/850_1700_2550/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_850_1700_2550/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.25)
    DNN_power(n_tb=10000, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=1000, vth1=2000, vth2=3000, pg_hlev=0.345, pixel_compout_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/1000_2000_3000/compouts_ylocal_0.00_1.35.csv", dnn_csv="/asic/projects/C/CMS_PIX_28/dshekar/filter/model_pipeline/tmp_16x16_hlevOptimized/trainedModel_1000_2000_3000/model0/qmodel_0_catapult_prj/firmware/weights/b5_w5_b2_w2_pixel_bin.csv", plotBool=True, LHC_RATE=0.25)