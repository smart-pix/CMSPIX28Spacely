# spacely
from Master_Config import *

# python modules
import sys
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
    outDir = "./", 
    readYproj=True):

    # Set the firmware to the default state
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)

    # First set up the pulse generator
    SDG7102A_SWEEP(HLEV=0.4)
    
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

    # loop over all patterns
    for iP in tqdm.tqdm(patternIndexes):
        
        # increment counter of number of patterns
        iN += 1
        hiddenBit="/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/hidden_debug.csv"
        # pick up pixel config for the given pattern
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

        # Programming the NN weights and biases
        # THIS TAKES SIGNIFICANT AMOUNT OF TIME (~0.3sec) --> COULD IMPROVE --<
        if(progDebug==True):
            hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin_debug2.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        else:
            filename = dnn_csv if dnn_csv else '/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv'
            # hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
            hex_lists = dnnConfig(filename, pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        sw_write32_0(hex_lists)
        
        # write execute command
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

        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
        # # We ran ROUTINE_ProgShiftRegs with debug mode ON and found the breaking point of the delay value to get the correct data in DATA_ARRAY 0 and DATA_ARRAY_1
        # We went 10% above breaking point
        time.sleep(0.02)

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
        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
        
        # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
        
        # input("Press Enter to continue...") # wait for user input to continue

        # # DODO SETTINGS
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
        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 
        
        # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
        # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
        
        if readYproj:
            nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
            words = []
            
            for iW in range(nwords):

                # send read
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                # sw_write32_0(hex_lists)

                sw_write32_0(hex_lists)

                sw_read32_0, sw_read32_1, _, _ = sw_read32() 

                # store data
                words.append(int_to_32bit(sw_read32_0)[::-1])
            
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
                 

        dnn_nwords = 8
        dnn_words = []
        for iW in range(dnn_nwords):
            # send read
            address = "8'h" + hex(iW)[2:]
            hex_lists = [
                ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_1
            ]
            sw_write32_0(hex_lists)
            sw_read32_0, sw_read32_1, _, _ = sw_read32() 

            # store data
            dnn_words.insert(0, int_to_32bit(sw_read32_0))

        dnn_s = ''.join(dnn_words)

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
        if iN % 25 == 0 or iN == len(patternIndexes):
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

    return None

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
