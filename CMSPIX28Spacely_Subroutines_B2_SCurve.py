# spacely
from Master_Config import *

# python
import tqdm
import numpy as np
import math
import h5py

def PreProgSCurve(
        scanloadDly = '13', 
        startBxclkState = '0', 
        bxclkDelay = '11', #'0B', 
        scanFreq = '28',
        scanInjDly = '17', #'1D', 
        scanLoopBackBit = '0', 
        scanSampleDly = '08', 
        scanDly = '08', 
        v_min = 0.001, 
        v_max = 0.3, 
        v_step = 0.01, 
        nsample = 1000, 
        SuperPix = False, 
        nPix = 0, 
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        testType = "Single"
):
    
    # Note we do not yet have a smoke test. verify this on scope as desired.
    
    # hex lists                                                                                                                    
    hex_lists = [
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h05", "1'h1", "1'h0", "5'h09", "6'h28"],  #BK4600HLEV
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h09", "6'h28"],  #BSDG7102A
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"]
        # ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h14", "1'h1", "1'h0", "5'h0B", "6'h28"],#BSDG7102A and CARBOARD new setup
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # w_cfg_static_0_reg_pack_data_array_0_IP2
         # SPARE bits:  "3'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"

  

    ]

    sw_write32_0(hex_lists,doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 24 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    VHLEV = 0.1

    #voltage step increment in the ASIC
    #The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
    #each voltage step is then set with 2.vstep
    #1mV equals 25e- (TBD!!!!!)
    #vstep_asic = 0.001
    #vstep_asic = 0.01

    S = 40e-6           #Charge Sensitivity in V/e-
    #npulse_step = 450    #number of charge settings 
    #npulse_step = 20

    # define range of asic voltages
    # v_min = vmin
    # v_max = vmax
    # v_step = vstep
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of samples to run for each charge setting
    # nsample = nSample
    nWord = 24  #number of 32bit word to read the scanChain
    nStream = nsample*n_step*nWord

    scanFreq_inMhz = 400/int(scanFreq, 16) # 400MHz is the FPGA clock
    scanInjDly_in_ns = int(scanInjDly,16)*2.5
    bxclkDelay_in_ns = int(bxclkDelay,16)*2.5
    # create output directory
    print(V_LEVEL['VTH'])
    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    # testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{scanFreq_inMhz:.2f}_BxCLKDly{bxclkDelay_in_ns:.2f}_injDly{scanInjDly_in_ns:.2f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixVTH":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLK{scanFreq_inMhz:.2f}_nPix{nPix}"
        pixelInfo = f"VTH{V_LEVEL['VTH']:.3f}"
    elif testType == "Single":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}_nPix{nPix}"
        pixelInfo = ""

    # configure per pixel info
    # pixelInfo = f"nPix{nPix}"
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # for i in tqdm.tqdm(range(1,npulse_step+1), desc="Voltage Step"):
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0 
            return 
        #BK4600HLEV_SWEEP(v_asic*2)
        SDG7102A_SWEEP(v_asic*2)

        #SDG7102A_SWEEP(v_asic)  # we used 50 ohm output load settings in the pulse generator

        save_data = []
        
        for j in tqdm.tqdm(range(nsample), desc="Number of Samples", leave=False):


            # SDG7102A SETTINGS
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                    f"6'h{scanSampleDly}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    f"6'h{scanDly}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ] 
            
            sw_write32_0(hex_lists, doPrint=False)

            if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                wordList = [int(((nPix-1)*3+1)/32)]
            else:
                wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

             # list(range(24))
            words = ["0"*32] * nWord
            #words = []

            #start_readback = time.process_time()
            for iW in wordList: #range(nwords):

                # send read
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                sw_write32_0(hex_lists,doPrint=False)
                # read back data
               
                #STREAN
                # sw_read32_0_stream, sw_read32_1, _, _ = sw_readStream(N=nWord)
                #no stream
                sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 

                # print(f"stream read data {sw_read32_0_stream}")
                # print(f"reg read data v1 {sw_read32_0_get}")
                # print(f"reg read data v2 {sw_read32_0}")
                # store data
                # ROUTINE_PreProgSCurve(vmin = 0.1, vmax=0.2, vstep=0.01, nSample=200)
                words[iW] = int_to_32bit(sw_read32_0)[::-1]
            
            #read_time=time.process_time()-start_readback

            #print(f"readback_time={read_time}")
            
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save the data to a file
        # save_data = np.stack(save_data, 0)
        # outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        # np.savez(outFileName, **{"data": save_data})

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        save_data = save_data.reshape(-1, 256, 3)
        save_data = save_data[:,nPix]
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)
    
    return None

def PreProgSCurveGinguMaster(
        scanloadDly = '13', 
        startBxclkState = '0', 
        bxclkDelay = '11', 
        scanFreq = '28',
        scanInjDly = '17', 
        scanLoopBackBit = '0', 
        scanSampleDly = '08', 
        scanDly = '08', 
        tsleep = 100e-3,
        v_min = 0.001, 
        v_max = 0.2, 
        v_step = 0.01, 
        nsample = 1000,
        nIter = 1,  
        SuperPix = False, 
        nPix = 0, 
        dataDir = FNAL_SETTINGS["storageDirectory"],
        dateTime = None,
        testType = "Single"
):

    # Note we do not yet have a smoke test. verify this on scope as desired.
    nPixHex = int_to_32bit_hex(nPix)
    nsampleHex = int_to_32bit_hex(nsample)
    print(nsampleHex, nsample)

    if nsample>1365:
        print("You asked for more samples per iteration that the firmware can achieve. Max allowed is nsample = 1365. Please increase nIter instead and rerun.")
        return
    
    # hex lists                                                                                                                    
    hex_lists = [
        # Setting up STATIC_ARRAY_0 for IP 2 test 5 - nothing change from other test
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0",f"6'h{scanloadDly}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclkDelay}", f"6'h{scanFreq}"],
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

        ["4'h2", "4'h4", "5'h3", f"11'h{nsampleHex}", f"8'h{nPixHex}"],          
         # 8 - bits to identify pixel number
         # 11 - bit to program number of samples
         # SPARE bits:  "4'h0"
         # Register Static 1 is programmed : "4'h4"
         # IP 2 is selected: "4'h2"
    ]

    sw_write32_0(hex_lists)
    sw_read32_0= sw_read32()


    # hex_lists = [
    #     ["4'h2", "4'h5", "24'h0"],
    # ]
    # sw_write32_0(hex_lists)
    # sw_read32_0 = sw_read32(print_code = "ihb")
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 24 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    VHLEV = 0.1

    #voltage step increment in the ASIC
    #The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
    #each voltage step is then set with 2.vstep
    #1mV equals 25e- (TBD!!!!!)
    #vstep_asic = 0.001
    #vstep_asic = 0.01

    S = 40e-6           #Charge Sensitivity in V/e-
    #npulse_step = 450    #number of charge settings 
    #npulse_step = 20

    # define range of asic voltages
    # v_min = vmin
    # v_max = vmax
    # v_step = vstep
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)


    scanFreq_inMhz = 400/int(scanFreq, 16) # 400MHz is the FPGA clock
    scanInjDly_in_ns = int(scanInjDly,16)*2.5
    bxclkDelay_in_ns = int(bxclkDelay,16)*2.5
    # create output directory
    print(V_LEVEL['VTH'])
    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    # testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{scanFreq_inMhz:.2f}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{scanFreq_inMhz:.2f}_BxCLKDly{bxclkDelay_in_ns:.2f}_injDly{scanInjDly_in_ns:.2f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixVTH":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{scanFreq_inMhz:.2f}_BxCLKDly{bxclkDelay_in_ns:.2f}_injDly{scanInjDly_in_ns:.2f}_nPix{nPix}"
        pixelInfo = f"VTH{V_LEVEL['VTH']:.3f}"
    elif testType == "Single":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{scanFreq_inMhz:.2f}_BxCLKDly{bxclkDelay_in_ns:.2f}_injDly{scanInjDly_in_ns:.2f}_nPix{nPix}"
        pixelInfo = ""

    # configure per pixel info
    # pixelInfo = f"nPix{nPix}"
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # for i in tqdm.tqdm(range(1,npulse_step+1), desc="Voltage Step"):
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0 
            return 
        #BK4600HLEV_SWEEP(v_asic*2)
        # if 0.160 < i < 0.200:
        #     time.sleep(0.2) #added time for pulse generator to settle
        #     if i ==0.185:
        #         time.sleep(0.5) # extra step for 0.185V
        SDG7102A_SWEEP(v_asic*2)
        time.sleep(tsleep) #added time for pulse generator to settle

        #SDG7102A_SWEEP(v_asic)  # we used 50 ohm output load settings in the pulse generator

        save_data = []
        
        for j in tqdm.tqdm(range(nIter), desc="Number of Samples", leave=False):


            # SDG7102A SETTINGS
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    f"6'h{scanInjDly}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h3",  # Test 5 is the only test none thermometrically encoded because of lack of code space
                    #"4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                    f"6'h{scanSampleDly}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    f"6'h{scanDly}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ] 

            sw_write32_0(hex_lists, doPrint=False)
            # sw_read32_0 = sw_read32(print_code = "ihb")
            # if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
            #     wordList = [int(((nPix-1)*3+1)/32)]
            # else:
            #     wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]
            maxWordFWArray = 128
            nword = math.ceil(nsample*3/32)
            wordList =  list(range(maxWordFWArray-nword,maxWordFWArray))  # VERIFY THIS : we list from 128-nword to 127
            words = ["0"*32] * nword
            time.sleep(100e-6*nsample) #added time for burst to complete
            # time.sleep(0.2) #added time for pulse generator to settle

            #read back DATA_ARRAY_0
            #data should be stored in the MSBs of row 0
            # address = "8'h" + hex(0)[2:]
            # hex_lists = [
            #     ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_1
            # ]

            # sw_write32_0(hex_lists,doPrint=False)
            # sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 
            # print("DATA_ARRAY_0")
            # print(int_to_32bit(sw_read32_0)[::-1])
            # #start_readback = time.process_time()

            # #read back DATA_ARRAY_1
            # #data should be stored in the MSBs of row 0
            # address = "8'h" + hex(127)[2:]
            # hex_lists = [
            #     ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_1
            # ]
            # print("DATA_ARRAY_1")
            # sw_write32_0(hex_lists,doPrint=False)
            # sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 
            # print(int_to_32bit(sw_read32_0))

            #start_readback = time.process_time()
            for iW in wordList:

                # DATA ARRAY 0 only contain LAST READ 
                address = "8'h" + hex(iW)[2:]
                # hex_lists = [
                #     ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                # ]
                 
                # DATA ARRAY 1 contains ALL READ 
                hex_lists = [
                    ["4'h2", "4'hD", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_1
                ]
                sw_write32_0(hex_lists,doPrint=False)

                # read back data
               
                #STREAM
                # sw_read32_0_stream, sw_read32_1, _, _ = sw_readStream(N=nWord)
                #no stream
                sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 
                # print(f"stream read data {sw_read32_0_stream}")
                # print(f"reg read data v1 {sw_read32_0_get}")
                # print(f"reg read data v2 {sw_read32_0}")
                # store data
                # ROUTINE_PreProgSCurve(vmin = 0.1, vmax=0.2, vstep=0.01, nSample=200)

                words[(maxWordFWArray-1)-iW] = int_to_32bit(sw_read32_0) #[::-1]
            
            # read_time=time.process_time()-start_readback

            # print(f"readback_time={read_time}")
            
            s = [int(i) for i in "".join(words)]
            # Cutting last bit because 3x1365 = 4095
            s = s[:nsample*3]
            save_data.append(s)

        # save the data to a file
        # save_data = np.stack(save_data, 0)
        # outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        # np.savez(outFileName, **{"data": save_data})

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        # Bit order might have to be reversed in the next line since b2-b1-b0
        save_data = save_data.reshape(nsample*nIter, 3)
        save_data = save_data[:,::-1]
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)
    
    return None

def IterMatrixSCurve():

    # global settings
    nPix = 256
    # create an output directory
    dataDir = FNAL_SETTINGS["storageDirectory"]
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
    for i in range(nPix):
        ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [i], pixelValue=[1])
        
        PreProgSCurveGinguMaster(
            scanloadDly = '13', 
            startBxclkState = '0', 
            bxclkDelay = '11', #'0B', 
            scanFreq = '28', 
            scanInjDly = '18', #'1D', 
            scanLoopBackBit = '0', 
            scanSampleDly = '07', #'08' 
            scanDly = '08', 
            v_min = 0.001, 
            v_max = 0.3, 
            v_step = 0.001, 
            nsample = 1365, 
            SuperPix = True, 
            nPix = i,
            nIter=1,
            dataDir = dataDir,
            dateTime = now,
            testType = "MatrixNPix"
        )
    
def IterSCurveSweep(nPix=0):

# This function programs a single pixel and extrac Scurve while sweeping a bias voltage
# the voltage being sweep is VTH but could be changed to VDDA or VDDD
# This is useful to extract linearity

    print(nPix)
    #program single pixel
    ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [nPix], pixelValue=[1])

    # create an output directory/mnt/local/CMSPIX28/Scurve/data/ChipVersion1_ChipID9_SuperPix2/2025.02.25_08.36.02_Matrix_vMin0.001_vMax0.600_vStep0.00100_nSample1000.000_vdda0.900_VTH0.800_BXCLK10.00/nPix0.8
    dataDir = FNAL_SETTINGS["storageDirectory"]
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    # Sweep range
    vthList = np.arange(0.5,2.0,0.05)
    # vthList = [0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9,0.95,1,1.05,1.1,1.15,1.2,1.25,1.3,1.35,1.4,1.45,1.5,1.55,1.6,1.65,1.7,1.75,1.8,1.85,1.9,1.95,2.0]
    # vthList = [1.5,1.55,1.6]
    for i in vthList:

        V_PORT["VTH"].set_voltage(i)
        V_LEVEL["VTH"] = i
        PreProgSCurveGinguMaster(
            scanloadDly = '13', 
            startBxclkState = '0', 
            bxclkDelay = '0B', 
            scanFreq = '28', 
            scanInjDly = '1D', 
            scanLoopBackBit = '0', 
            scanSampleDly = '08', 
            scanDly = '08', 
            v_min = 0.001, 
            v_max = 0.4, 
            v_step = 0.001, 
            nsample = 1365,
            nIter = 1,  
            SuperPix = True, 
            nPix = nPix,
            dataDir = dataDir,
            dateTime = now,
            testType = "MatrixVTH"
        )


