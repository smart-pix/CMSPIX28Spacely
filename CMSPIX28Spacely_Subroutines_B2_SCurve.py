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
# PreProgSCurve function
#-----------------------------------------------------------------------
# This function assumes the ASIC pixels are already configured 
# It can work with 1 or all pixels programmed 
# Lower noise can only be achieved by programming a single pixel with minimum gain setting 
# 1. Set static array 0 and static array 1 to configure the correct frequency and scanLoad arrival time and phases 
# 2. loop over the input pulse amplitude (ie: Qin) over the range v_min, v_max, v_step
# 3. Execute IP2 test 2
# 4. read the scan chain and store the data into a numpy array
#-----------------------------------------------------------------------
    
def PreProgSCurve(
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
        testType = "Single"
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
    
    # 400MHz is the FPGA clock
    bxclk_period_inMhz = 400/int(bxclk_period, 16) 
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    # create output directory
    print(V_LEVEL['VTH'])
    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixVTH":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLK{bxclk_period_inMhz:.2f}_nPix{nPix}"
        pixelInfo = f"VTH{V_LEVEL['VTH']:.3f}"
    elif testType == "Single":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{bxclk_period_inMhz:.2f}_nPix{nPix}"
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

            # prepare the word list to read
            if(int(((nPix-1)*3+1)/32)==int(((nPix-1)*3+3)/32)):
                wordList = [int(((nPix-1)*3+1)/32)]
            else:
                wordList = [int(((nPix-1)*3+1)/32),int(((nPix-1)*3+3)/32)]

            # allocate array for the words
            words = ["0"*32] * nWord

            # loop over the words to read
            for iW in wordList:

                # send read
                address = "8'h" + hex(iW)[2:]
                hex_lists = [
                    ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
                ]
                sw_write32_0(hex_lists)
               
                # # stream read back
                # sw_read32_0_stream, sw_read32_1, _, _ = sw_readStream(N=nWord)
                # no stream read back
                sw_read32_0, sw_read32_1_old, _, _ = sw_read32() 

                # store data
                # ROUTINE_PreProgSCurve(vmin = 0.1, vmax=0.2, vstep=0.01, nSample=200)
                words[iW] = int_to_32bit(sw_read32_0)[::-1]
            
            # save words
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        save_data = save_data[:, 1:-2]
        save_data = save_data.reshape(-1, 255, 3)
        # save_data = save_data.reshape(-1, 256, 3)
        save_data = save_data[:,nPix]
        # save the output file
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)
    
    return None

#-----------------------------------------------------------------------
# PreProgSCurveBurst function
#-----------------------------------------------------------------------
# This test allow to extract the S-curve of a single pixel with max statitics and optimized run time
# This function assumes a single ASIC pixel have already been configured 
# It can only work with a single programmed as it selects the 3-bit of that pixels from the 768-bit scan chain
# it then stacks these 3-bit from bottom to top into DATA_ARRAY_1 until the ARRAY is filled
# DATA_ARRAY_1 is 4096-bit long so 1365 samples can be stored at a maximum
# 1. Set static array 0 and static array 1 to configure the correct frequency and scanLoad arrival time and phases. 
# 2. Static array 1 needs to be configured also with the number of samples (nSample) and the pixel number to stack (nPix)
# 3. loop over the input pulse amplitude (ie: Qin) over the range v_min, v_max, v_step
# 4. Execute IP2 test 5
# 6. read the scan chain and store the data into a numpy array
#-----------------------------------------------------------------------

def PreProgSCurveBurst(
        scan_load_delay = '13', 
        startBxclkState = '0', 
        bxclk_delay = '12', #'11', 
        bxclk_period = '28',
        injection_delay = '1E', #'17', 
        scanLoopBackBit = '0', 
        test_sample = '0F', 
        scanLoadPhase = '26',
        test_delay = '14', 
        tsleep = 100e-3,
        v_min = 0.001, 
        v_max = 0.4, 
        v_step = 0.01, 
        nsample = 1365,
        nIter = 1,
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

        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"11'h{nsampleHex}", f"8'h{nPixHex}"],           
         # 8 - bits to identify pixel number
         # 11 - bit to program number of samples
         # SPARE bits:  "4'h0"
         # Register Static 1 is programmed : "4'h4"
         # IP 2 is selected: "4'h2"
    ]

    sw_write32_0(hex_lists)
    sw_read32_0= sw_read32()

    # define range of asic voltages
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # 400MHz is the FPGA clock
    bxclk_period_inMhz = 400/int(bxclk_period, 16)
    injection_delay_in_ns = int(injection_delay,16)*2.5
    bxclk_delay_in_ns = int(bxclk_delay,16)*2.5

    # create output directory
    print(V_LEVEL['VTH'])
    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    # testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{bxclk_period_inMhz:.2f}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixVTH":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_nPix{nPix}"
        pixelInfo = f"VTH{V_LEVEL['VTH']:.3f}"
    elif testType == "Single":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_nPix{nPix}"
        pixelInfo = ""

    # output directory
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # loop over the voltage steps
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):
        
        # vasic step
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0 
            return 
        
        # The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
        # each voltage step is then set with 2.vstep
        # 1mV equals 25e- (TBD!!!!!)
        SDG7102A_SWEEP(v_asic*2)
        # BK4600HLEV_SWEEP(v_asic*2)
        time.sleep(tsleep) #added time for pulse generator to settle

        # save data
        save_data = []
        for j in tqdm.tqdm(range(nIter), desc="Number of Samples", leave=False):

            # write configuration
            hex_lists = [
                [
                    "4'h2",  # firmware id
                    "4'hF",  # op code for execute
                    "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
                    #"6'h1D", # 6 bits for w_execute_cfg_test_injection_delay_index_max
                    f"6'h{injection_delay}", # 6 bits for w_execute_cfg_test_injection_delay_index_max
                    f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h3",  # Test 5 is the only test none thermometrically encoded because of lack of code space
                    #"4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    #"4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
                    f"6'h{test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    f"6'h{test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ] 
            sw_write32_0(hex_lists)

            # prepare the word list to read 
            maxWordFWArray = 128
            nword = math.ceil(nsample*3/32)
            wordList =  list(range(maxWordFWArray-nword,maxWordFWArray))  # VERIFY THIS : we list from 128-nword to 127
            words = ["0"*32] * nword
            # added time for burst to complete
            time.sleep(100e-6*nsample) 
            
            # loop over the words to read
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
                sw_write32_0(hex_lists)

                # read back data
                sw_read32_0, _, _, _ = sw_read32(do_sw_read32_1 = False) 
                words[(maxWordFWArray-1)-iW] = int_to_32bit(sw_read32_0)
            
            # save words
            s = [int(i) for i in "".join(words)]
            # Cutting last bit because 3x1365 = 4095
            s = s[:nsample*3]
            save_data.append(s)

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        # Bit order might have to be reversed in the next line since b2-b1-b0
        save_data = save_data.reshape(nsample*nIter, 3)
        save_data = save_data[:,::-1]
        # save data
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)
    
    return None


#-----------------------------------------------------------------------
# SCurveMatrix function
#-----------------------------------------------------------------------
# This function runs PreProgSCurveBurst function over the entire matrix
#-----------------------------------------------------------------------

def SCurveMatrix():

    # global settings
    nPix = 256
    # create an output directory
    dataDir = FNAL_SETTINGS["storageDirectory"]
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    for i in range(nPix):
        ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk ='1', pixelList = [i], pixelValue=[1])
        
        PreProgSCurveBurst(
            scan_load_delay = '13', 
            startBxclkState = '0', 
            bxclk_delay = '11',         #superpix1 '11', superpix2 '12',
            bxclk_period = '28', 
            injection_delay = '1C',     #superpix1 '1C', superpix2 '1E',
            scanLoopBackBit = '0', 
            test_sample = '0F', 
            scanLoadPhase ='25',        #superpix1 '25', superpix2 '26',
            test_delay = '14', 
            v_min = 0.001, 
            v_max = 0.4, 
            v_step = 0.001, 
            nsample = 1365, 
            nPix = i,
            nIter=1,
            dataDir = dataDir,
            dateTime = now,
            testType = "MatrixNPix"
        )

    
#-----------------------------------------------------------------------
# SCurveSweep function
#-----------------------------------------------------------------------
# This function runs PreProgSCurveBurst function over a single pixel for different biases/power voltage
# the voltage being sweep is currently set to VTH but could be changed to VDDA or VDDD
# This is useful to extract linearity
#-----------------------------------------------------------------------
        
def SCurveSweep(nPix=0):

# This function programs a single pixel and extrac Scurve while sweeping a bias voltage
# the voltage being sweep is VTH but could be changed to VDDA or VDDD
# This is useful to extract linearity

    print(nPix)
    #program single pixel
    ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk ='1', pixelList = [nPix], pixelValue=[1])
    

    # create an output directory/mnt/local/CMSPIX28/Scurve/data/ChipVersion1_ChipID9_SuperPix2/2025.02.25_08.36.02_Matrix_vMin0.001_vMax0.600_vStep0.00100_nSample1000.000_vdda0.900_VTH0.800_BXCLK10.00/nPix0.8
    dataDir = FNAL_SETTINGS["storageDirectory"]
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    # Sweep range
    #vthList = np.arange(0.6,1.4,0.1)
    vthList = [0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4]
    # vthList = [1.5,1.6]
    for i in vthList:
        V_PORT["VTH"].set_voltage(i)
        V_LEVEL["VTH"] = i

        PreProgSCurveBurst(
            scan_load_delay = '13', 
            startBxclkState = '0', 
            bxclk_delay = '12', #'0B', 
            bxclk_period = '28', 
            injection_delay = '1E', #'1D', 
            scanLoopBackBit = '0', 
            test_sample = '0F', 
            scanLoadPhase ='26',
            test_delay = '14', 
            v_min = 0.001, 
            v_max = 0.4, 
            v_step = 0.001, 
            nsample = 1365, 
            nPix = nPix,
            nIter=1,
            dataDir = dataDir,
            dateTime = now,
            testType = "MatrixVTH"
        )


