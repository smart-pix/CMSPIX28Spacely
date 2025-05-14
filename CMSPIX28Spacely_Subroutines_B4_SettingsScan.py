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

# **********************************************************************************
# This function uses IP2 test 1:  serial readout of the schanChain : scanIn -> scanOut
# This first test needs to be run to evaluate the Sample Delay Settings
# Sample Delay is internal to the FW and needs to be tuned ONCE for the entire chip
# Sample Delay varies with the setup delay such as cable length, LVDS driver, level shifter
# it encompasses ASIC to FPGA delay (how long BxCLK takes to arrive to ASIC) and FPGA to ASIC delay (how long data takes to come back)
# Once the setting range has be found for a single BxCKL frequency and BxCLK_DELAY, select the middle value for the Scurve test 
# If BxCLK_DELAY shifts, the Sample Delay will need to shift by the same amount
# If BxCLK frequency shifts, the Sample Delay will need to be retuned 
# **********************************************************************************
    
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
    error = []
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
        hex_list_6b = [cfg_test_delay] # [f'{i:X}' for i in range(1, int(cfg_test_delay,16)+1)]                    # smaller list set for debug
    else:
        hex_list_6b = [f'{i:X}' for i in range(1, int(bxclkFreq,16)+1)]  # create the list of setting space to range from 0 to 63
        # hex_list_6b = [f'{i:X}' for i in range(1, int('4',16)+1)]  # create the list of setting space to range from 0 to 63
    
    # Step 4
    # Execute the test for different cfg_test_sample delay values
    settingList = []
    settingList1 = []
    settingList2 = []
    settingPass = []
    testRepeatSave = []
    error = []
    for cfg_test_delay in hex_list_6b:
        for cfg_test_sample in hex_list_6b:
            print(f"cfg_test_delay = {cfg_test_delay}, cfg_test_sample = {cfg_test_sample}")

            testRepeat = []
            fw_status_clear() # this is a test to make sure we read back all zeros on status register?
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

                _, sw_read32_1, _, _ = sw_read32(print_code = "ihb")
                if any(x=='1' for x in int_to_32bit(sw_read32_1)[0:5]):
                    error.append(int(True))
                else:
                    error.append(int(False))

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
                    sw_read32_0, _, _, _ = sw_read32(do_sw_read32_1=False)
                    
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
            testRepeatSave.append(testRepeat)
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
    testRepeatSave = np.array(testRepeatSave)
    error = np.array(error)

    outFileNameSetting = os.path.join(outDir, f"settingList.npy")
    np.save(outFileNameSetting, settingList)
    outFileNameSetting = os.path.join(outDir, f"testRepeatSave.npy")
    np.save(outFileNameSetting, testRepeatSave)
    outFileNameSettingPass = os.path.join(outDir, f"settingPass.npy")
    np.save(outFileNameSettingPass, settingPass)
    outFileNameSettingPass = os.path.join(outDir, f"error.npy")
    np.save(outFileNameSettingPass, error)
    # print(settingList.shape)
    # print(settingPass.shape)
    # print(testRepeatSave.shape)
    # print(settingList)
    # print(settingPass)
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

# **********************************************************************************
# This function uses IP2 test 5:  parallel Load and serial readout of the schanChain with burst to get higher statistics
# This second test needs to be run to evaluate the Test sample Delay and test delay Settings
# Test Sample Delay is internal to the FW and needs to be tuned ONCE for the entire chip
# Test Sample Delay varies with the setup delay such as cable length, LVDS driver, level shifter
# it encompasses ASIC to FPGA delay (how long BxCLK takes to arrive to ASIC) and FPGA to ASIC delay (how long data takes to come back)
# Once the setting range has be found for a single BxCKL frequency and BxCLK_DELAY, select the middle value for the Scurve test 
# If BxCLK_DELAY shifts, the Sample Delay will need to shift by the same amount
# If BxCLK frequency shifts, the Sample Delay will need to be retuned 
# **********************************************************************************
def calibrationMatrixHighStat(
        scanLoadPhase = '27', # DEAULT VALUE '25',
        tsleep = 200e-6,
        tsleep2 = 0.5,
        loopbackBit=0, 
        pixMin=0,
        pixMax=255,
        scanFreq='28', 
        nsample=32,
        v_min = 0.001, 
        v_max = 0.4, 
        v_step = 0.034, 
        bxclkDelay = '13', # DEFAULT VALUE '11',
        scanInjDly = '1F', # DEFAULT VALUE '1D',
        scanloadDly = '13',
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
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}_BxCLK_DELAY_0x{bxclkDelay}_SCAN_INJ_DLY_0x{scanInjDly}_SCAN_LOAD_DLY_0x{scanloadDly}_scanLoadPhase_0x{scanLoadPhase}"
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
    pixList = list(range(256))
    nsampleHex = int_to_32bit_hex(nsample)
    
    # settings for the scan
    # start_bxclk_state = '0'
    # start_bxclk_stateList = ['0'] #['0', '1']
    # scanloadDlyList = ['13'] # ['12', '13', '14']
    # bxclkDelayList =  ['0B']
    # scanInjDlyList =  ['1D']
    # cfg_test_sampleList = ['08']
    # cfg_test_delayList = ['08']

    start_bxclk_stateList = ['0']                                                   #['0', '1']
    scanloadDlyList = [scanloadDly]                                                        #['12', '13', '14']
    bxclkDelayList =  [bxclkDelay]                                                        #['13','12','10','0B']
    scanInjDlyList =  [scanInjDly]                                                        #[f'{i:X}' for i in range(1, int(scanFreq,16)+1)]  #['14', '15', '16','17', '18', '19', '1A', '1B']
    # cfg_test_sampleList = [f'{i:X}' for i in range(1, int(scanFreq,16)+1)]          #['1B', '1B', '10', '18']
    # cfg_test_delayList = [f'{i:X}' for i in range(3, int(scanFreq,16)+1)]           #['4', 'C', '1A', '26']
    # cfg_test_sampleList = [f'{i:X}' for i in range(6, 30)]          #['1B', '1B', '10', '18']
    cfg_test_delayList = [f'{i:X}' for i in range(6, 30)]           #['4', 'C', '1A', '26']
    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]

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
            cfg_test_sampleList_max=len([f'{i:X}' for i in range(6, 7+int('1D', 16))])
            cnt = 0
            # loop over the settings
            for start_bxclk_state in start_bxclk_stateList:
                for scanloadDly in scanloadDlyList: #  in increment BxCLK periods - value is defined in respect to the pulse generator delay and should NOT be changed 
                    for bxclkDelay in  bxclkDelayList:   # ['13','12','11','10'] Constrain it to the following list ---> [scanFreq/2-1, scanFreq/2-2, scanFreq/2-3, scanFreq/2-4] 
                        for scanInjDly in scanInjDlyList: # [Min Value = 0x01 ; Max Value = scanFreq, INCR = 1] increment delay of 400MHz period: ie - 2.5ns : align injection time
                            for cfg_test_delay in cfg_test_delayList: #cfg_test_delay, cfg_test_sample in zip(cfg_test_delayList,cfg_test_sampleList): # [Min Value = 0x03 ; Max Value = scanFreq, INCR = 2 ] increment delay of 400MHz period, can be used to fine tune scanLoad, reset_not, scanIn. Counter starts at 1, so 0 is not allowed. Then we need 2 more counts to have BxCLK_ANA defined.
                                cfg_test_sampleList = [f'{i:X}' for i in range(6, 7+int(cfg_test_delay, 16))]  #define a modular list
                                for cfg_test_sample in cfg_test_sampleList:

                                # for cfg_test_sample in cfg_test_sampleList:
                                    
                                    cnt += 1  #calculate the number of settings

                                    # # DODO SETTINGS
                                    # # hex lists                                                                                                                    
                                    hex_lists = [
                                        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"], #BSDG7102A and CARBOARD
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
                                        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"11'h{nsampleHex}", f"8'h{nPixHex}"],           
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
                                            #  "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
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
                                        sw_read32_0, _, _, _ = sw_read32(do_sw_read32_1 = False) #test
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
        print(cnt)
        # after full loop of vasic step save                      
        save_data = np.stack(save_data, 0)
        # reshape to reasonable format
        # save_data = save_data.reshape(len(vasic_steps), len(scanloadDlyList)*len(bxclkDelayList)*len(scanInjDlyList)*len(cfg_test_sampleList), nsample, 3)
        save_data = save_data.reshape(len(pixList), cnt, nsample, 3)
        save_data = save_data[:,:,:,::-1]
        # save to file
        outfileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outfileName, save_data)
        
    return None

# **********************************************************************************
# This function uses IP2 test 3:  parallel Load and serial readout of the schanChain with no burst
# This second test needs to be run to evaluate the Test sample Delay and test delay Settings
# Test Sample Delay is internal to the FW and needs to be tuned ONCE for the entire chip
# Test Sample Delay varies with the setup delay such as cable length, LVDS driver, level shifter
# it encompasses ASIC to FPGA delay (how long BxCLK takes to arrive to ASIC) and FPGA to ASIC delay (how long data takes to come back)
# Once the setting range has be found for a single BxCKL frequency and BxCLK_DELAY, select the middle value for the Scurve test 
# If BxCLK_DELAY shifts, the Sample Delay will need to shift by the same amount
# If BxCLK frequency shifts, the Sample Delay will need to be retuned 
# **********************************************************************************

def calibrationMatrixLowStat(
        scanLoadPhase = '27',
        tsleep2 = 0.5,
        loopbackBit=0, 
        nPix=0,
        scanFreq='28', 
        nsample=32,
        v_min = 0.001, 
        v_max = 0.4, 
        v_step = 0.034,
        bxclkDelay = '13', #DEFAULT VALUE: '12',
        scanInjDly = '1F', # DEFAULT VALUE: '1D',
        scanloadDly = '13',
        dateTime = None,
        dataDir = FNAL_SETTINGS["storageDirectory"],
        testType = "MatrixCalibration",
):
    nIter=nsample
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
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}_BxCLK_DELAY_0x{bxclkDelay}_SCAN_INJ_DLY_0x{scanInjDly}_SCAN_LOAD_DLY_0x{scanloadDly}_scanLoadPhase_0x{scanLoadPhase}_nPix{nPix}"
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
    sw_/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea_112024/CMSPIX28_DAQ/spacely/PySpacely/spacely-asic-config/CMSPIX28Spacely/oldwrite32_0(hex_lists)
    # sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")
    

    # settings
    pixList = [nPix] #list(range(pixMin, pixMax+1))
    nsampleHex = int_to_32bit_hex(nsample)
    print(nsampleHex, nsample)
    start_bxclk_stateList = ['0']                                                   #['0', '1']
    scanloadDlyList = [scanloadDly]                                                        #['12', '13', '14']
    bxclkDelayList =  [bxclkDelay]                                                        #['13','12','10','0B']
    scanInjDlyList =  [scanInjDly]                                                        #[f'{i:X}' for i in range(1, int(scanFreq,16)+1)]  #['14', '15', '16','17', '18', '19', '1A', '1B']
    cfg_test_sampleList = [f'{i:X}' for i in range(1, int(scanFreq,16)+1)]          #['1B', '1B', '10', '18']
    cfg_test_delayList = [f'{i:X}' for i in range(3, int(scanFreq,16)+1)]           #['4', 'C', '1A', '26']
    

    
    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]

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
            cnt = 0
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
                                        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{start_bxclk_state}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"], #BSDG7102A and CARBOARD
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
                                        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"11'h{nsampleHex}", f"8'h{nPixHex}"],          
                                        # 8 - bits to identify pixel number
                                        # 11 - bit to program number of samples
                                        # SPARE bits:  "4'h0"
                                        # Register Static 1 is programmed : "4'h4"
                                        # IP 2 is selected: "4'h2"
                                    ]

                                    sw_write32_0(hex_lists)
                                    # sw_read32_0 = sw_read32() 
                                    for j in tqdm.tqdm(range(nIter), desc="Number of Samples", leave=False):

                                        hex_lists = [
                                            [
                                                "4'h2",  # firmware id
                                                "4'hF",  # op code for execute
                                                "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                                                #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                                f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                                                f"1'h{loopbackBit}",  # 1 bit for w_execute_cfg_test_loopback
                                                # "4'h3",   # Test 5 is the only test none thermometrically encoded because of lack of code space  
                                                "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                                                f"6'h{cfg_test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                                                f"6'h{cfg_test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                                            ]
                                        ]       
                                        sw_write32_0(hex_lists, doPrint=False)
                                        
                                        iBitDn = nPix*3         # LSB position for programmed pixel
                                        iBitUp = (nPix+1)*3     # MSB position for programmed pixel
                                        arrayRow = 32
                                        
                                        if iBitDn % arrayRow > iBitUp % arrayRow and iBitUp % arrayRow !=0:
                                            wordList = [int((iBitDn)/32), int((iBitUp)/32)]
                                        else:
                                            wordList = [int((iBitDn)/32)]

                                        nWord = 24 
                                        # list(range(24))
                                        words = ["0"*32] * nWord

                                        for iW in wordList:

                                            # send read
                                            address = "8'h" + hex(iW)[2:]
                                            hex_lists = [
                                                ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                                            ]
                                            sw_write32_0(hex_lists,doPrint=False)
                                            sw_read32_0, _, _, _ = sw_read32(do_sw_read32_1 = False)
                                            # store data
                                            words[iW] = int_to_32bit(sw_read32_0)[::-1]
                                            
                                        s = [int(i) for i in "".join(words)]
                                        s = s[iBitDn:iBitUp]
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
        save_data = save_data.reshape(len(pixList), cnt, nsample, 3)
        # save_data = save_data[:,:,:,::-1]  # ON MAY 1ST 2025 LOOKING AT DATA WE REALIZED WE DONT NEED A FLIP FOR IP2 TEST 2
        save_data = save_data[:,:,:,:]
        # save to file
        outfileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outfileName, save_data)
        
    return None


# **********************************************************************************
# This function CALLS the function defined above  calibrationMatrixLowStat() 
# Can be used with different scanInjDly settings and BxCLK_DELAY settings
# **********************************************************************************


def calibrationMatrixLowStatExtraction():
    
    scanInjDlyList = ['1A','1B','1C','1D','1E','1F','20','21','22','23','24']

    # for  iSetting, scanInjDly  in enumerate(scanInjDlyList) :  
    for nPix in [9]:

        calibrationMatrixLowStat(
            scanLoadPhase = '26',
            tsleep2 = 0.5,
            loopbackBit=0, 
            nPix=nPix,
            scanFreq='28', 
            nsample=20,
            v_min = 0.001, 
            v_max = 0.4, 
            v_step = 0.034,
            bxclkDelay = '12',
            scanInjDly = '1D',
            scanloadDly = '13',
            dateTime = None,
            dataDir = FNAL_SETTINGS["storageDirectory"],
            testType = "MatrixCalibration",
    )

# **********************************************************************************
# This function CALLS the function defined above calibrationMatrixHighStat() 
# Can be used with different scanInjDly settings and BxCLK_DELAY settings
# **********************************************************************************

def calibrationMatrixHighStatExtraction():
    
    scanInjDlyList = ['1E']
    bxclkDlyList = ['10','11','12']
    scanLoadPhaseList = ['24', '25', '26']
    # bxclkDlyList = ['10','11','12']
    # scanLoadPhaseList = ['24','25','26']

    # for  iSetting, scanInjDly  in enumerate(scanInjDlyList) :  
    for scanInjDly in scanInjDlyList:
        for (bxclkDelay, scanLoadPhase) in zip(bxclkDlyList,scanLoadPhaseList):
            print(f"scanInjDly = {scanInjDly}, bxclkDelay = {bxclkDelay}, scanLoadPhase = {scanLoadPhase}")
            calibrationMatrixHighStat(
                scanLoadPhase = scanLoadPhase,
                tsleep = 200e-6,
                tsleep2 = 0.5,
                loopbackBit=0, 
                pixMin=0,
                pixMax=255,
                scanFreq='28', 
                nsample=32,
                v_min = 0.001, 
                v_max = 0.4, 
                v_step = 0.034, 
                bxclkDelay = bxclkDelay,
                scanInjDly = scanInjDly,
                scanloadDly = '13',
                dateTime = None,
                dataDir = FNAL_SETTINGS["storageDirectory"],
                testType = "MatrixCalibration",
    )
