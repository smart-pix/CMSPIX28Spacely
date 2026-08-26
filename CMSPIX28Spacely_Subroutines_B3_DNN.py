# spacely
from Master_Config import *

# python modules
import sys
import time
import pandas as pd
try:
    import os
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately

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
    readYproj=True,
    dnnPowerBool = False
):

    #set threshold to higher values

    V_PORT["vth0"].set_voltage(vth0)
    V_LEVEL["vth0"] = vth0
    V_PORT["vth1"].set_voltage(vth1)
    V_LEVEL["vth1"] = vth1
    V_PORT["vth2"].set_voltage(vth2)
    V_LEVEL["vth2"] = vth2

    if dnnPowerBool==False:
        SDG7102A_SWEEP(HLEV=pg_hlev) # Set the pulse generator to 0.3V
    
    testType = "DNN"

    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}"
    # output directory
    outDir = os.path.join(dataDir, chipInfo, testInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # Set the firmware to the default state
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)

    # First set up the pulse generator
    if dnnPowerBool==False:
        SDG7102A_SWEEP(HLEV=pg_hlev)
        print("Setting the pulse generator HLEV to “, pg_hlev, “V for ROUTINE_DNN.")
    
    # Program shift register
    hex_lists = [
        # ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 1M
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{configclk_period}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]
    sw_write32_0(hex_lists)


    # load all of the configs
    filename = pixel_compout_csv if pixel_compout_csv else "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)

    # loop over test cases
    patternIndexes = range(len(pixelLists)) if patternIndexes == None else patternIndexes
    
    # list to save to
    yprofiles = []
    readouts = []
    iN = 0

    # [TIMING] per-stage cumulative totals across the whole run, printed
    # periodically below so the per-test-vector breakdown doesn't get lost
    # in thousands of lines of output.
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
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

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
            return None

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
            if readYproj:
                # save to csv file
                yprofileOutputFile = os.path.join(outDir,"yprofiles.csv")
                with open(yprofileOutputFile, 'w', newline="") as file:
                    writer = csv.writer(file)
                    writer.writerows(yprofiles)
                print("Saving to: ", yprofileOutputFile)

            # save readouts to csv

            readoutOutputFile = os.path.join(outDir,"readout.csv")
            with open(readoutOutputFile, "w", newline="") as file:
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

    return None


def DNN_power(n_tb=100, waitTime=1.4, dnnwaitTime=1, pNoiseBool=False, vth0=0.014, vth1=0.083, vth2=0.128):

    startTime = time.time()
    SDG7102A_INJ_CONT()
    time.sleep(waitTime)
    suffix="OnHit"
    if pNoiseBool:
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
        dnnPowerBool = True
        )
        time.sleep(3*dnnwaitTime) # wait for some time just in case

    testType = "DNN"
    dataDir=FNAL_SETTINGS["storageDirectory"]
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}"
    # create temp directory to delete dirs between ABC_temp and ABC_dnnPower
    outDirTemp = os.path.join(dataDir, chipInfo, testInfo)
    outDirTemp = outDirTemp + str("_temp")
    print(f"Saving results to {outDirTemp}")
    os.makedirs(outDirTemp, exist_ok=True)
    os.chmod(outDirTemp, mode=0o777)
    Ivddd_post = []

    for i in range(n_tb):
        if i%1000==0:
            print(f"Running DNN power test for test vector {i+1}/{n_tb}")
        if pNoiseBool:
            time.sleep(0.1) # no injection happening, only triggering on noise, so wait time has been reduced.
            # print("Ivdd_post=",Ivddd_post)
            Ivddd_post.append(V_PORT["vddd"].get_current())
        else:
            #set pulse generator in normal condition
            DNN(
            progDebug=False,
            loopbackBit=0, 
            patternIndexes = [i], 
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
            vth0=0.014,#0.08,
            vth1=0.083,#0.16,
            vth2=0.128,#0.32,
            readYproj=True,
            dnnPowerBool = True
            )
            #set pulse generator in continuous injection
            time.sleep(dnnwaitTime)
            Ivddd_post.append(V_PORT["vddd"].get_current())
            print("Ivdd_post=",Ivddd_post)

    print("post current measurement done")
    time.sleep(60)

    SDG7102A_INJ_BURST()
    time.sleep(waitTime)
    if pNoiseBool:
        SDG7102A_SWEEP(HLEV=0)
        time.sleep(dnnwaitTime)

    print("pre current measurement done")
    Ivddd_pre=V_PORT["vddd"].get_current()
    print("Ivdd_pre=", Ivddd_pre)
    time.sleep(60)
    print("time elapsed = ", time.time()-startTime)

    testType = "DNN"
    dataDir=FNAL_SETTINGS["storageDirectory"]
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    testInfo = (datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    testInfo += f"_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}"
    # output directory that saves the current values
    outDirPower = os.path.join(dataDir, chipInfo, testInfo)
    outDirPower = outDirPower + str("_dnnPower") + str(suffix)
    print(f"Saving results to {outDirPower}")
    os.makedirs(outDirPower, exist_ok=True)
    os.chmod(outDirPower, mode=0o777)
    Ivddd_pre = [Ivddd_pre]*n_tb
    df = pd.DataFrame()
    df["Ivddd_pre"] = Ivddd_pre
    df["Ivddd_post"] = Ivddd_post
    df.to_csv(outDirPower+"/Ivddd.csv", index=False)



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
