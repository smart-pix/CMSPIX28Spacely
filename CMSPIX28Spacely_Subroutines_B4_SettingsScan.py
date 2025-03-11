# spacely
from Master_Config import *

# python
import tqdm
import numpy as np
import math
import csv

def SettingsScan(loopbackBit=0, patternIndexes = [197], verbose=False, vin_test='1D', freq='3f', start_bxclk_state='0', cfg_test_delay='08',cfg_test_sample='08', bxclk_delay='0B',scanload_delay='13' ):
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    

    # load all of the configs
    filename = "/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/compouts.csv"
    pixelLists, pixelValues = genPixelConfigFromInputCSV(filename)

    # loop over test cases
    patternIndexes = range(len(pixelLists)) if patternIndexes == None else patternIndexes
    
    # list to save to
    yprofiles = []
    readouts = []
    iN = 0
    # programming pulse generator
    SDG7102A_SWEEP(0.2)
    time.sleep(0.2)

    for iP in tqdm.tqdm(patternIndexes):

        # increment counter of number of patterns
        iN += 1

        # pick up pixel config for the given pattern
        pixelConfig = genPixelProgramList(pixelLists[iP], pixelValues[iP])

        # Programming the NN weights and biases
        hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig)
        sw_write32_0(hex_lists, doPrint=False)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

        hex_lists = [
            [
                "4'h1",  # firmware id
                "4'hf",  # op code d for execute
                "1'h1",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
                "4'h0", # 3 bits for spare_index_max
                "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                "4'h1",  # 4 bits for test number
                "7'h4", # 6 bits test sample
                "7'h3F"  # 6 bits for test delay
            ]
        
        ]
        sw_write32_0(hex_lists)
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

        # NEED SLEEP TIME BECAUSE FW TAKES 53ms (5162 shift register at 100KHz speed) which is slower than python in this case
        time.sleep(0.5)
        settingList=[]
        hex_list_6b = [f'{i:X}' for i in range(0, 64)]
        hex_list_5b = 1 #[f'{i:X}' for i in range(0, 32)]
        hex_list_1b =1
        for scanload_delay in hex_list_6b:
            for bxclk_delay in ['14']: #hex_list_5b:
                for vin_test in hex_list_6b:
                    for cfg_test_sample in ['08']:
                        for cfg_test_delay in ['08']:
                          

                            # 
                            # setting.append((scanload_delay,bxclk_delay,vin_test,cfg_test_sample,cfg_test_delay))
                            
                            # # DODO SETTINGS
                            # # hex lists                                                                                                                    
                            hex_lists = [
                                ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanload_delay}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclk_delay}", f"6'h{freq}"], #BSDG7102A and CARBOARD
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
                            print(hex_lists)

                            sw_write32_0(hex_lists)
                            sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
                            
                            # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.

                            hex_lists = [
                                [
                                    "4'h2",  # firmware id
                                    "4'hF",  # op code for execute
                                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                                    #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"6'h{vin_test}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                                    "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min     
                                    f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                                    f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                                ]
                            ]       
                            print(hex_lists)
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
                                dnn_0=dnn_s[-48:] 
                                dnn_1=dnn_s[-96:-48] 
                                bxclk_ana=dnn_s[-144:-96] 
                                bxclk=dnn_s[-192:-144] 
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
                            setting = [scanload_delay,bxclk_delay,vin_test,cfg_test_sample,cfg_test_delay]
                            settingList.append(setting)
                            yprofiles.append(row_sums)
                            readouts.append(dnn_s)

                            # save every 25 and on the last one

                            # save to csv file


                            # save to csv file
                            yprofileOutputFile = "yprofiles_scan.csv"
                            with open(yprofileOutputFile, 'w', newline="") as file:
                                writer = csv.writer(file)
                                writer.writerows(yprofiles)
                        
                            # save readouts to csv
                            readoutOutputFile = "readout_scan.csv"
                            with open(readoutOutputFile, "w", newline="") as file:
                                writer = csv.writer(file)
                                writer.writerows(readouts)

                            print("Saving to: ", yprofileOutputFile, readoutOutputFile, iN)
        settingOutputFile = "setting.csv"
        with open(settingOutputFile, 'w', newline="") as file:
            writer = csv.writer(file)
            writer.writerows(settingList)

    return None


def SettingsScanSinglePix(loopbackBit=0, nPix=0, scanFreq='28'):
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    

    # programming pulse generator to low value
    SDG7102A_SWEEP(0.2)
    time.sleep(0.2)
    
    ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [nPix], pixelValue=[1])
    pixSetting = []
    save_data = []
    start_bxclk_state = '0'

    time.sleep(0.5)
    settingList=[]
    hex_list_6b = [f'{i:X}' for i in range(0, 64)]
    hex_list_5b = [f'{i:X}' for i in range(0, 32)]
    hex_list_2b = [f'{i:X}' for i in range(0, 2)]
    hex_list_1b =1
    for scanloadDly in ['13']: #hex_list_6b:
        for bxclkDelay in hex_list_5b: #hex_list_5b:
            for scanInjDly in hex_list_6b:  #hex_list_6b:
                for cfg_test_sample in ['08']:
                    for cfg_test_delay in ['08']:
                        

                        # 
                        # setting.append((scanload_delay,bxclk_delay,vin_test,cfg_test_sample,cfg_test_delay))
                        
                        # # DODO SETTINGS
                        # # hex lists                                                                                                                    
                        hex_lists = [
                            ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"], #BSDG7102A and CARBOARD
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
                        print(hex_lists)

                        sw_write32_0(hex_lists)
                        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
                        
                        # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.

                        hex_lists = [
                            [
                                "4'h2",  # firmware id
                                "4'hF",  # op code for execute
                                "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                                #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                                "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min     
                                f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                                f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                            ]
                        ]       
                        print(hex_lists)
                        sw_write32_0(hex_lists)
                        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

                        # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
                        # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
                        

                        # if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                        #     wordList = [int(((nPix-1)*3+1)/32)]
                        # else:
                        #     wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

                        # list(range(24))
                        nWord = 24
                        words = ["0"*32] * nWord
                        
                        for iW in range(nWord):

                            # send read
                            address = "8'h" + hex(iW)[2:]
                            hex_lists = [
                                ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                            ]
                            sw_write32_0(hex_lists)
                            
                            sw_read32_0, sw_read32_1, _, _ = sw_read32() 

                            # store data
                            words[iW] = int_to_32bit(sw_read32_0)[::-1]
                        s = [int(i) for i in "".join(words)]
                        pixSetting.append(s)
                        setting = [scanloadDly,bxclkDelay,scanInjDly,cfg_test_sample,cfg_test_delay]
                        pixSettingNP = np.stack(pixSetting, 0)
                        pixSettingNP = pixSettingNP.reshape(-1, 256, 3)
                        pixSettingNP = pixSettingNP[:,nPix]
                        x = pixSettingNP.tolist()
                        settingNP = np.stack(setting, 0)
                        # 
                        # pixSetting = np.hstack((np.array([setting]), pixSetting))
                        # setting = [scanloadDly,bxclkDelay,scanInjDly,cfg_test_sample,cfg_test_delay] 
                        
                        data = setting + x[-1]
                        save_data.append(data)
    outFileName = "nPix.npy"
    np.save(outFileName, pixSettingNP)
    np.save("setting.npy", settingNP)
                    # save_data.append(pixSetting)
    # 
    # 
    
    # save_data = save_data.tolist()

    settingOutputFile = "setting.csv"
    with open(settingOutputFile, 'w', newline="") as file:
        writer = csv.writer(file)
        writer.writerows(save_data)

    return None


def calibrationMatrix(loopbackBit=0, scanFreq='28'):
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")
    
    # programming pulse generator to low value
    SDG7102A_SWEEP(0.2)
    time.sleep(0.2)
    
    for nPix in range(256):
        ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [nPix], pixelValue=[1])
        pixSetting = []
        save_data = []
        start_bxclk_state = '0'

        time.sleep(0.5)
        settingList=[]
        hex_list_6b = [f'{i:X}' for i in range(0, 64)]
        hex_list_5b = [f'{i:X}' for i in range(0, 32)]
        hex_list_2b = [f'{i:X}' for i in range(0, 2)]
        hex_list_1b =1
        for scanloadDly in ['13']: #hex_list_6b:
            for bxclkDelay in hex_list_5b: #hex_list_5b:
                for scanInjDly in hex_list_6b:  #hex_list_6b:
                    for cfg_test_sample in ['08']:
                        for cfg_test_delay in ['08']:
                            

                            # 
                            # setting.append((s     canload_delay,bxclk_delay,vin_test,cfg_test_sample,cfg_test_delay))
                            
                            # # DODO SETTINGS
                            # # hex lists                                                                                                                    
                            hex_lists = [
                                ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"], #BSDG7102A and CARBOARD
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
                            print(hex_lists)

                            sw_write32_0(hex_lists)
                            sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
                            
                            # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.

                            hex_lists = [
                                [
                                    "4'h2",  # firmware id
                                    "4'hF",  # op code for execute
                                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                                    #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                                    "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min     
                                    f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                                    f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                                ]
                            ]       
                            print(hex_lists)
                            sw_write32_0(hex_lists)
                            sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

                            # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
                            # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
                            

                            # if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                            #     wordList = [int(((nPix-1)*3+1)/32)]
                            # else:
                            #     wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

                            # list(range(24))
                            nWord = 24
                            words = ["0"*32] * nWord
                            
                            for iW in range(nWord):

                                # send read
                                address = "8'h" + hex(iW)[2:]
                                hex_lists = [
                                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                                ]
                                sw_write32_0(hex_lists)
                                
                                sw_read32_0, sw_read32_1, _, _ = sw_read32() 

                                # store data
                                words[iW] = int_to_32bit(sw_read32_0)[::-1]
                            s = [int(i) for i in "".join(words)]
                            pixSetting.append(s)
                            setting = [scanloadDly,bxclkDelay,scanInjDly,cfg_test_sample,cfg_test_delay]
                            settingList.append(setting)
                            pixSettingNP = np.stack(pixSetting, 0)
                            pixSettingNP = pixSettingNP.reshape(-1, 256, 3)
                            pixSettingNP = pixSettingNP[:,nPix]
                            x = pixSettingNP.tolist()
                            settingNP = np.stack(settingList, 0)
                            # 
                            # pixSetting = np.hstack((np.array([setting]), pixSetting))
                            # setting = [scanloadDly,bxclkDelay,scanInjDly,cfg_test_sample,cfg_test_delay] 
                            
                            data = setting + x[-1]
                            save_data.append(data)
        outFileName = f"calibrationNPix{nPix}.npy"
        np.save(outFileName, pixSettingNP)
        np.save("setting.npy", settingNP)
                        # save_data.append(pixSetting)
        # 
        # 
        
        # save_data = save_data.tolist()

        settingOutputFile = "setting.csv"
        with open(settingOutputFile, 'w', newline="") as file:
            writer = csv.writer(file)
            writer.writerows(save_data)

    return None


def calibrationMatrixHighStat(
        loopbackBit=0, 
        scanFreq='28', 
        nsample=1365,
        dateTime = None,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        testType = "matrixCalibration",
):
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    print(chipInfo)
    # configure test info
    # testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    scanFreq_inMhz = 400/int(scanFreq, 16) # 400MHz is the FPGA clock
    print(testInfo)
    # configure based on test type
    if testType == "matrixCalibration":
        testInfo += f"_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}"
    outDir = os.path.join(dataDir, chipInfo, testInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)


    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] # write op code E (status clear)
    ]

    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")


    #PROGRAM SHIFT REGISTER
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")
    
    # programming pulse generator to low value
    SDG7102A_SWEEP(0.2)
    time.sleep(0.2)


    for nPix in range(2):
        ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [nPix], pixelValue=[1])
        pixSetting = []
        save_data = []
        start_bxclk_state = '0'
        nPixHex = int_to_32bit_hex(nPix)
        nsampleHex = int_to_32bit_hex(nsample)
        print(nsampleHex, nsample)

        if nsample>1365:
            print("You asked for more samples per iteration that the firmware can achieve. Max allowed is nsample = 1365. Please increase nIter instead and rerun.")
            return
        time.sleep(0.5)
        settingList=[]
        hex_list_6b = [f'{i:X}' for i in range(0, 64)]
        hex_list_5b = [f'{i:X}' for i in range(0, 32)]
        hex_list_2b = [f'{i:X}' for i in range(0, 2)]
        hex_list_1b =1
        for scanloadDly in ['13']: #hex_list_6b:
            for bxclkDelay in hex_list_5b: #hex_list_5b:
                for scanInjDly in hex_list_6b:  #hex_list_6b:
                    for cfg_test_sample in ['08']:
                        for cfg_test_delay in ['08']:
                            

                            # 
                            # setting.append((s     canload_delay,bxclk_delay,vin_test,cfg_test_sample,cfg_test_delay))
                            
                            # # DODO SETTINGS
                            # # hex lists                                                                                                                    
                            hex_lists = [
                                ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"], #BSDG7102A and CARBOARD
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
                                ["4'h2", "4'h4", "5'h3", f"11'h{nsampleHex}", f"8'h{nPixHex}"],          
                                # 8 - bits to identify pixel number
                                # 11 - bit to program number of samples
                                # SPARE bits:  "4'h0"
                                # Register Static 1 is programmed : "4'h4"
                                # IP 2 is selected: "4'h2"
                            ]
                            print(hex_lists)

                            sw_write32_0(hex_lists)
                            sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ibh")
                            
                            # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.

                            hex_lists = [
                                [
                                    "4'h2",  # firmware id
                                    "4'hF",  # op code for execute
                                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                                    #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                    f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                                    "4'h3",   # Test 5 is the only test none thermometrically encoded because of lack of code space  
                                    f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                                    f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                                ]
                            ]       
                            print(hex_lists)
                            sw_write32_0(hex_lists)
                            sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() 

                            # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
                            # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
                            

                            # if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                            #     wordList = [int(((nPix-1)*3+1)/32)]
                            # else:
                            #     wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

                            # list(range(24))
                            maxWordFWArray = 128
                            nword = math.ceil(nsample*3/32)
                            wordList =  list(range(maxWordFWArray-nword,maxWordFWArray))  # VERIFY THIS : we list from 128-nword to 127
                            words = ["0"*32] * nword
                            time.sleep(80e-6*nsample) #added time for burst to complete
                            time.sleep(0.2) #added time for pulse generator to settle

                            for iW in wordList:

                                # send read
                                address = "8'h" + hex(iW)[2:]
                                hex_lists = [
                                    ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                                ]
                                sw_write32_0(hex_lists,doPrint=False)
                                sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 
                                # store data
                                words[(maxWordFWArray-1)-iW] = int_to_32bit(sw_read32_0) #[::-1]
                            s = [int(i) for i in "".join(words)]
                            # Cutting last bit because 3x1365 = 4095
                            s = s[:nsample*3]
                            save_data.append(s)
                            pixSetting.append(s)
        pixSettingNP = np.stack(pixSetting, 0)

        pixSettingNP = pixSettingNP.reshape(nsample*32*64, 3)
        pixSettingNP = pixSettingNP[:,::-1]

        settingList = [scanloadDly,bxclkDelay,scanInjDly,cfg_test_sample,cfg_test_delay]
        settingNP = np.stack(settingList, 0)
        outFileName1 = os.path.join(outDir, f"calibrationNPix{nPix}.npy")
        outFileName2 = os.path.join(outDir, "setting.npy")
        np.save(outFileName1, pixSettingNP)
        np.save(outFileName2, settingNP)

    return None