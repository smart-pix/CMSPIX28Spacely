# spacely
from Master_Config import *

# python modules
import sys
try:
    import tqdm
    import random
    import numpy as np
    import math
    import csv
    import time
    from datetime import datetime
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately

# This function uses IP2 test 1:  serial readout of the schanChain : scanIn -> scanOut
# This first test needs to be run to evaluate the Sample Delay Settings
# Sample Delay is internal to the FW and needs to be tuned ONCE for the entire chip
# Sample Delay varies with the setup delay such as cable length, LVDS driver, level shifter
# it encompasses ASIC to FPGA delay (how long BxCLK takes to arrive to ASIC) and FPGA to ASIC delay (how long data takes to come back)
# Once the setting range has be found for a single BxCKL frequency and BxCLK_DELAY, select the middle value for the Scurve test 
# If BxCLK_DELAY shifts, the Sample Delay will need to shift by the same amount
# If BxCLK frequency shifts, the Sample Delay will need to be retuned 

def settingsScanSampleFW(
        bxclkFreq='28', 
        start_bxclk_state='0', 
        cfg_test_sample='08', 
        bxclkDelay= '0B', #'11', 
        scanInjDly='1D', #'04', 
        loopbackBit='0', 
        cfg_test_delay='03', 
        scanload_delay='13', 
        scanIndata='0001', 
        nrepeat=1, 
        debug=False,
        dateTime = None,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        testType = "firmWareCalibration",
        ):
    
    # configure output directory
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    print(chipInfo)
    # configure test info
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    scanFreq_inMhz = 400/int(bxclkFreq, 16) # 400MHz is the FPGA clock
    print(testInfo)
    # configure based on test type
    if testType == "firmWareCalibration":
        testInfo += f"_BXCLK{scanFreq_inMhz:.2f}_bxclkFreq{scanFreq_inMhz}_bxclkDelay{bxclkDelay}_scanInjDly{scanInjDly}_scanload_delay{scanload_delay}_debugMode{debug}_nrepeat{nrepeat}"
    outDir = os.path.join(dataDir, chipInfo, testInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)


    # Step 1: Program Static Array 0 for IP2 and BxCLK frequencies and BxCLK delay
    # the other settings like scanLoad are not important for this test because we are not injecting charges

    hex_lists = [
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanload_delay}", "1'h0", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{bxclkFreq}"], #BSDG7102A and CARBOARD
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
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()

    # Step 2
    # Program CFG ARRAY 0 with a data stream of 256 words of 16 bits data = 4096 bits
    # The data stream is going to be sent to the ASIC through the scanIn input

    # first empty the CFG_ARRAY 0 - optional but safer
    hex_list = [["4'h2", "4'h6", "8'h" + hex(i)[2:], f"16'h0000"] for i in range(256)]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()

    # now fill the CFG_ARRAY 0 with the data stream - in this case we are going to use a random number generator
    for i in range(48*2):   #48 words of 16 - bit words; 2 frames; 
        scanInRandom = random.getrandbits(16)
        if debug==False:
            scanIndata = format(scanInRandom, '04x')
        hex_list.append(["4'h2", "4'h6", "8'h" + hex(i)[2:], f"16'h{scanIndata}"])
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()
    
    nWord = 24
    words = ["0"*32] * nWord
    words_A0 = []      

    # Step 3
    # Let's read back CFG_ARRAY 0 from the FW first before starting 
    # We read back in 128 addresses of 32-bit words  

    for iW in range(0, nWord, 1):                                 
        address = hex(iW*2)[2:]
        hex_list0 = [
        [
            "4'h2", "4'h7", f"8'h{address}", "16'h0"]         #ReadBack from READ_CFG_ARRAY 0            
        ]
        sw_write32_0(hex_list0)
        sw_read32_0, sw_read32_1, _, _ = sw_read32() 
        words[iW] = int_to_32bit(sw_read32_0)[::-1]


    words_A0 = [int(i) for i in "".join(words)] 
    words_A0 = np.stack(words_A0, 0)   #should be 0hAAAAAAAA repeated 128 times
    words_A0 = np.reshape(words_A0, (nWord, 32))  

    if debug:
        hex_list_6b = [f'{i:X}' for i in range(1, int(cfg_test_sample,16)+1)]                    # smaller list set for debug
    else:
        hex_list_6b = [f'{i:X}' for i in range(1, int(bxclkFreq,16)+1)]  # create the list of setting space to range from 0 to 63
    
    # Step 4
    # Execute the test for different cfg_test_sample delay values
    settingList = []
    settingList1 = []
    settingList2 = []
    settingPass = []
   
    for cfg_test_delay in hex_list_6b:
        for cfg_test_sample in hex_list_6b:

            testRepeat = []

            for i in range(nrepeat):
                hex_lists = [
                    [
                        "4'h2",  # firmware id
                        "4'hF",  # op code for execute
                        "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                        #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                        f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                        f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                        "4'h1",   # Test 1 we run scanchain like a shift register  
                        f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                        f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                    ]
                ]       
                sw_write32_0(hex_lists)

                sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()
                PASS = True

                # IMPORTANT
                # If loop delay is more than clock period, we need to shift the second frame by 1 bit !
                # the wordlist will probably need to change for 40Mhz

                wordList =   list(range(nWord,nWord*2)) # We read the second Frame Only 

                words = []

                # Step 5
                # Readback the data from DATA_ARRAY_0

                for iW in wordList: #range(nwords):

                    # send read
                    address = "8'h" + hex(iW)[2:]
                    hex_lists = [
                        ["4'h2", "4'hC", address, "16'h0"] 
                    ]
                    sw_write32_0(hex_lists)
                    
                    # read back data
                    sw_read32_0, sw_read32_1, _, _ = sw_read32()
                    
                    # update
                    PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

                    # store data
                    words.append(int_to_32bit(sw_read32_0)[::-1])
                # print(words)
                s = [int(i) for i in "".join(words)]     
                s = np.array(s)
                s = np.reshape(s, (nWord, 32))

                # compare cfg_array_0 with data_array_0 - returns 0 is fail - returns 1 if pass
                testRepeat.append(int(np.all(words_A0 == s)))
            
            
            # Step 6      
            # Compare the data read back from DATA_ARRAY_0 with the data written to CFG_ARRAY_0 
            # are_equal = np.array_equal(s, words_A0) # PUT BACK WHEN READY    
            # print(testRepeat)
            testRepeat = np.array(testRepeat)

            # search through all the repeated run if any of them is failed - the setting is considered failed
            PassCondition = int(np.all(testRepeat == 1))

            # print(PassSetting)
            settingList1.append(cfg_test_delay)
            settingList2.append(cfg_test_sample)
            settingPass.append(PassCondition)

            #settingPass.append(int(np.all(words_A0 == s)))  # To test
            if debug:
                print(s)
                print(words_A0)
                print(int(np.all(words_A0 == s)))
            # print(s)
            # print(words_A0)
    # Step 7 - Compare arrays, extract working range and find the middle setting for the sample delay
    settingPass = np.array(settingPass)        
    settingList = np.array([settingList1,settingList2])


    outFileNameSetting = os.path.join(outDir, f"settingList.npy")
    np.save(outFileNameSetting, settingList)
    outFileNameSettingPass = os.path.join(outDir, f"settingPass.npy")
    np.save(outFileNameSettingPass, settingPass)

    print(settingList.shape)
    print(settingPass.shape)
    print(settingList)
    print(settingPass)
    outFileNameSetting = os.path.join(outDir, f"settingList.npy")
    np.save(outFileNameSetting, settingList)
    outFileNameSettingPass = os.path.join(outDir, f"settingPass.npy")
    np.save(outFileNameSettingPass, settingPass)
    # settingPassIdx = np.where(settingPass ==1)[0]              # np where create a list of list because it can take more than one array
    # print(settingPass)
    # if len(settingPass)>0:
    #     idx = settingPassIdx[math.ceil((len(settingPassIdx) -1)/2)]   #return the sample delay for middle setting
    #     sampleDelayOut = settingList[idx]
    # else:
    #     sampleDelayOut = -999
    #     print("No setting pass")
    # cnt_True = np.sum(settingPass)                   #count how many pass
    # firstTrue = np.argmax(settingPass != 0)          #return the index of the first pass
    # sampleDelayOut = settingList[int((cnt_True+firstTrue)/2+firstTrue)]       #return the sample delay for middle setting

    # cnt_True = np.sum(np.char.find(settingPass, 'True') !=-1)                   #count how many pass
    # firstTrue = np.argmax(np.char.find(settingPass[:,1], 'True') !=-1)          #return the index of the first pass
    # sampleDelayOut = settingPass[int((cnt_True+firstTrue)/2+firstTrue),0]       #return the sample delay for middle setting

    return #sampleDelayOut



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
            for bxclkDelay in ['11']: #hex_list_5b: #hex_list_5b:
                for scanInjDly in ['16', '17']: #hex_list_6b:  #hex_list_6b:
                    for cfg_test_sample in hex_list_6b: #['08']:
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
        tsleep = 100e-6,
        tsleep2 = 0.5,
        loopbackBit=0, 
        pixMin=0,
        pixMax=255,
        scanFreq='28', 
        nsample=32,
        v_min = 0.001, 
        v_max = 0.4, 
        v_step = 0.034/2, 
        dateTime = None,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        testType = "MatrixCalibration",
):
    
    # break if this happens
    if nsample>1365:
        print("You asked for more samples per iteration that the firmware can achieve. Max allowed is nsample = 1365. Please increase nIter instead and rerun.")
        return
    
    # configure output directory
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    print(chipInfo)
    # configure test info
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    scanFreq_inMhz = 400/int(scanFreq, 16) # 400MHz is the FPGA clock
    print(testInfo)
    # configure based on test type
    if testType == "MatrixCalibration":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}"
    outDir = os.path.join(dataDir, chipInfo, testInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # configure vasic steps
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)
    print(vasic_steps)
    np.save(os.path.join(outDir, "vasic_steps.npy"), vasic_steps) # save vasic_steps to a file

    # write op code E (status clear)
    hex_lists = [
        ["4'h2", "4'hE", "11'h7ff", "1'h1", "1'h1", "5'h1f", "6'h3f"] 
    ]
    sw_write32_0(hex_lists)
    sw_read32_0 = sw_read32()


    # program shift register
    hex_lists = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h6F"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_lists)
    # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

    hex_lists = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
   ]
    sw_write32_0(hex_lists)
    # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")
    

    # settings
    pixList = list(range(pixMin, pixMax+1))
    nsampleHex = int_to_32bit_hex(nsample)
    print(nsampleHex, nsample)
    
    # settings for the scan
    # start_bxclk_state = '0'
    # start_bxclk_stateList = ['0'] #['0', '1']
    # scanloadDlyList = ['13'] # ['12', '13', '14']
    # bxclkDelayList =  ['0B']
    # scanInjDlyList =  ['1D']
    # cfg_test_sampleList = ['08']
    # cfg_test_delayList = ['08']

    start_bxclk_stateList = ['0']                                                   #['0', '1']
    scanloadDlyList = ['13']                                                        #['12', '13', '14']
    bxclkDelayList =  ['0B']                                                        #['13','12','10','0B']
    scanInjDlyList =  ['1D']                                                        #[f'{i:X}' for i in range(1, int(scanFreq,16)+1)]  #['14', '15', '16','17', '18', '19', '1A', '1B']
    cfg_test_sampleList = [f'{i:X}' for i in range(1, int(scanFreq,16)+1)]          #['1B', '1B', '10', '18']
    cfg_test_delayList = [f'{i:X}' for i in range(1, int(scanFreq,16)+1)]           #['4', 'C', '1A', '26']
    
    # loop over pulse generator voltage step first since this is the most time consuming
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    for iV, vasic_step in tqdm.tqdm(enumerate(vasic_steps), desc="Voltage Step"):
        
        # set the pulse gen to 2x v_asic step because of an extra resistor
        v_asic = round(vasic_step, 3)
        if v_asic > 0.9:
            v_asic = 0 
            return 
        SDG7102A_SWEEP(v_asic*2)
        time.sleep(tsleep2)  # necessary to prevent issue in the pulse generator settling time

        # list to store data and settings to scan over
        save_data = []
        settingList = []
        
        # loop over the pixels
        for iN, nPix in enumerate(pixList):
                    
            # program shift register
            ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [nPix], pixelValue=[1])

            # pix value in hex
            nPixHex = int_to_32bit_hex(nPix)

            # BxCK_Delay for BxCLK_DELAY_SIGN = 0
            # Delay between rising edge of BxCLK_ANA and rising edge of BxCLK.  
            # BxCLK_ANA is the reference and doesn't move. 
            # If delay is larger that half clock cycle.
            # The delay is still functionally but duty cycle of BxCLK IS affected and get smaller than 50%
            # (since period and delay have to be maintained).
            # Must scan from 0 to scanFreq/2

            # BxclkDelay for bxCLK_DELAY_SIGN = 1
            # THE DELAY IS defined between the rising edge of BxCLK_ANA and the falling edge of BxCLK
            # if delay is larger tha half clock cycle, the duty cycle is also impacted and get larger than 50%

            # append one list per v_asic step
            save_data.append([])
            
            # loop over the settings
            for start_bxclk_state in start_bxclk_stateList:
                for scanloadDly in scanloadDlyList: #  in increment BxCLK periods - value is defined in respect to the pulse generator delay and should NOT be changed 
                    for bxclkDelay in  bxclkDelayList:   # ['13','12','11','10'] Constrain it to the following list ---> [scanFreq/2-1, scanFreq/2-2, scanFreq/2-3, scanFreq/2-4] 
                        for scanInjDly in scanInjDlyList: # [Min Value = 0x01 ; Max Value = scanFreq, INCR = 1] increment delay of 400MHz period: ie - 2.5ns : align injection time
                            for cfg_test_delay in cfg_test_delayList: #cfg_test_delay, cfg_test_sample in zip(cfg_test_delayList,cfg_test_sampleList): # [Min Value = 0x03 ; Max Value = scanFreq, INCR = 2 ] increment delay of 400MHz period, can be used to fine tune scanLoad, reset_not, scanIn. Counter starts at 1, so 0 is not allowed. Then we need 2 more counts to have BxCLK_ANA defined.
                                for cfg_test_sample in cfg_test_sampleList:
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

                                    sw_write32_0(hex_lists)
                                    # sw_read32_0 = sw_read32() 
                                    
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
                                    sw_write32_0(hex_lists)

                                    # read the words back
                                    maxWordFWArray = 128
                                    nword = math.ceil(nsample*3/32)
                                    wordList =  list(range(maxWordFWArray-nword,maxWordFWArray))  # VERIFY THIS : we list from 128-nword to 127
                                    words = ["0"*32] * nword
                                    time.sleep(tsleep*nsample) # added time for burst to complete

                                    for iW in wordList:

                                        # send read
                                        address = "8'h" + hex(iW)[2:]
                                        hex_lists = [
                                            ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                                        ]
                                        sw_write32_0(hex_lists,doPrint=False)
                                        sw_read32_0, _, _, _ = sw_read32()
                                        # store data
                                        words[(maxWordFWArray-1)-iW] = int_to_32bit(sw_read32_0) #[::-1]
                                    
                                    s = [int(i) for i in "".join(words)]
                                    # Cutting last bit because 3x1365 = 4095
                                    s = s[:nsample*3]
                                    save_data[-1].append(s)

                                    # save the settings
                                    if iN == 0 and iV == 0:
                                        settingList.append([start_bxclk_state, scanloadDly, bxclkDelay, scanInjDly, cfg_test_sample, cfg_test_delay])
            
            # for the first loop save all settings
            if iN == 0 and iV == 0:
                settingList = np.stack(settingList, 0)
                np.save(os.path.join(outDir, "settings.npy"), settingList)

        # after full loop of vasic step save                      
        save_data = np.stack(save_data, 0)
        # reshape to reasonable format
        # save_data = save_data.reshape(len(vasic_steps), len(scanloadDlyList)*len(bxclkDelayList)*len(scanInjDlyList)*len(cfg_test_sampleList), nsample, 3)
        save_data = save_data.reshape(len(pixList), len(scanloadDlyList)*len(bxclkDelayList)*len(scanInjDlyList)*len(cfg_test_delayList)*len(cfg_test_sampleList)*len(start_bxclk_stateList), nsample, 3)
        save_data = save_data[:,:,:,::-1]
        # save to file
        outfileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outfileName, save_data)
        
    return None