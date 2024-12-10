# spacely
from Master_Config import *

def DNN(progDebug=False,loopbackBit=0, patternIndexes = [0], verbose=False, vinTest='1D', freq='28', startBxclkState='0',scanloadDly='13', progDly='5', progSample='20', progResetMask='0', progFreq='64', testDelaySC='08', sampleDelaySC='08', bxclkDelay='0B',configClkGate='0'):
    # hex_lists = [
    #     ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    # ]

    # sw_write32_0(hex_lists)
    # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    #PROGRAM SHIFT REGISTER
    hex_lists = [
        # ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{progFreq}"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 1M
        ["4'h1", "4'h2", "16'h0", "1'h1", f"7'h{progFreq}"],
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

#     hex_lists = [
#         ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
#    ]
#     sw_write32_0(hex_lists)
#     sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    #Manual programming for debugging
    # pixels = [
    #     [list(range(0,256)), [3]*256],
    #     #[[74, 75, 72, 73, 77, 76, 81, 138, 139, 142, 143, 146, 137, 136, 141], [3, 2] + [3] * 12 + [1]],
    #     [[16, 12, 21, 17, 13, 9, 5, 83, 79, 75, 71, 67,82, 78, 74], [3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]],
    #     [[82, 78, 74,80, 76,72], [3,3,2,3,3,2]],                                                                                        # RTL should see low momentum 1
    #     [[206, 202, 211, 207, 203, 199, 195, 145, 141, 137, 133, 129, 144, 140, 136], [3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]],  # RTL should see low momentum 2
    #     [[86,82,78,74,70, 83,67, 80,76,72], [3,3,3,3,3,  3,2, 3,3,3]],                                                                     # RTL should see low momentum 1
    #     [[148,144,140,136,132, 149,145, 150,146,142], [3,3,3,3,3,  3,2, 3,3,3]],    # RTL should see low momentum 0
    # ]  
    #pixelLists = [i[0] for i in pixels]
    #pixelValues = [i[1] for i in pixels]

    # load all of the configs
    filename = "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_D/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)

    # loop over test cases
    patternIndexes = range(len(pixelLists)) if patternIndexes == None else patternIndexes
    
    # list to save to
    yprofiles = []
    readouts = []
    iN = 0

    for iP in tqdm.tqdm(patternIndexes):

        # increment counter of number of patterns
        iN += 1
        hiddenBit="/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/hidden_debug.csv"
        # pick up pixel config for the given pattern
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

        # Programming the NN weights and biases
        if(progDebug==True):
            hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin_debug2.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        else:
            hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig, hiddenBitCSV = hiddenBit)
        sw_write32_0(hex_lists, doPrint=False)
        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

        hex_lists = [
            [
                "4'h1",  # firmware id
                "4'hf",  # op code d for execute
                f"1'h{progResetMask}",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
                "3'h0", # 3 bits for spare_index_max
                f"1'h{configClkGate}", # 1 bit for gating configClk
                "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                "4'h1",  # 4 bits for test number
                f"7'h{progSample}", # 6 bits test sample
                f"7'h{progDly}"  # 6 bits for test delay
            ]
        
        ]
        sw_write32_0(hex_lists)
        time.sleep(0.5)
        # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

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

        # # hex lists                                                                                                                    
        hex_lists = [
            ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclkDelay}", f"6'h{freq}"], #BSDG7102A and CARBOARD 
            #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
            
            # BxCLK is set to 10MHz : "6'h28"
            # BxCLK starts with a delay: "5'hB"
            # BxCLK starts LOW: "1'h0"
            # Superpixel 1 is selected: "1'h1"
            # scan load delay is set : "6'h0A"                 
            # scan_load delay  disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"

            # SPARE bits:  "4'h0"
            # Register Static 0 is programmed : "4'h2"
            # IP 2 is selected: "4'h2"

        ]

        sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
        
        # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
        
        # # DODO SETTINGS
        hex_lists = [
            [
                "4'h2",  # firmware id
                "4'hF",  # op code for execute
                "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                f"6'h{vinTest}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                f"6'h{sampleDelaySC}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                f"6'h{testDelaySC}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
            ]
        ]       

        sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 
        
        # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
        # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
        nwords = 24 # 24 words * 32 bits/word = 768 bits - I added one in case
        words = []
        
        for iW in range(nwords):

            # send read
            address = "8'h" + hex(iW)[2:]
            hex_lists = [
                ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
            ]
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
        yprofiles.append(row_sums)
        readouts.append(dnn_s)

        # save every 25 and on the last one
        if iN % 25 == 0 or iN == len(patternIndexes):
            
            # save to csv file
            yprofileOutputFile = "yprofiles.csv"
            with open(yprofileOutputFile, 'w', newline="") as file:
                writer = csv.writer(file)
                writer.writerows(yprofiles)
        
            # save readouts to csv
            readoutOutputFile = "readout.csv"
            with open(readoutOutputFile, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(readouts)

            print("Saving to: ", yprofileOutputFile, readoutOutputFile, iN)

    return None
