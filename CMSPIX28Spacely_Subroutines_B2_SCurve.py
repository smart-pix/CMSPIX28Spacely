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
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pixPower{ipixel*0.9:.3f}_nPix{nPix}"
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
            # print(s)

        # save just the correct npix
        save_data = np.stack(save_data, 0)
        # print(save_data)
        save_data = save_data[:, 0:-3]
        # print(save_data)
        save_data = save_data.reshape(-1, 255, 3)
        # print(save_data)
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
        testType = "Single",
        parameter = None
):

    # Note we do not yet have a smoke test. verify this on scope as desired.
    nPixHex = int_to_32bit_hex(nPix)
    nsampleHex = int_to_32bit_hex(nsample)
    print(testType)

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

    ipixel = (V_PORT["vdda"].get_current())*1000000/(512*10)    # extract roughtly Ibias for a pixel. NEED TO KNOW I_testStructure!!!
    # configure chip info
    chipInfo = f"ChipVersion{FNAL_SETTINGS['chipVersion']}_ChipID{FNAL_SETTINGS['chipID']}_SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    # configure test info
    # testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}_BXCLK{bxclk_period_inMhz:.2f}"
    testInfo = (dateTime if dateTime else datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + f"_{testType}"
    # configure based on test type


    # TODO : STORE THE CURRENT/POWER INFO INSIDE EACH PIXEL FOLDER FOR ALL MATRIX TESTS
      
    if testType == "MatrixNPix":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_Ibias{V_LEVEL['Ibias']:.3f}"
        pixelInfo = f"nPix{nPix}"
    elif testType == "MatrixIbias":
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_nPix{nPix}"
        # pixelInfo = f"Ibias{V_LEVEL['Ibias']:.3f}"
        pixelInfo = f"Ibias{I_LEVEL['OUTsink']*1000000:.1f}uA"
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
        testInfo += f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_BXCLKf{bxclk_period_inMhz:.2f}_BxCLKDly{bxclk_delay_in_ns:.2f}_injDly{injection_delay_in_ns:.2f}_vth0-{V_LEVEL['vth0']:.3f}_vth1-{V_LEVEL['vth1']:.3f}_vth2-{V_LEVEL['vth2']:.3f}_pixPower{ipixel*0.9:.3f}_nPix{nPix}"
        pixelInfo = ""

    # output directory
    print(pixelInfo)
    outDir = os.path.join(dataDir, chipInfo, testInfo, pixelInfo)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)
    os.chmod(outDir, mode=0o777)

    # loop over the voltage steps
    for i in tqdm.tqdm(vasic_steps, desc="Voltage Step"):

        t_step_start = time.time()

        # vasic step
        v_asic = round(i, 3)
        if v_asic>0.9:
            v_asic = 0
            return

        # The Pulse generator voltage is divided by 2 at the ASIC input vin_test due to the 50ohm divider
        # each voltage step is then set with 2.vstep
        # 1mV equals 25e- (TBD!!!!!)
        t0 = time.time()
        SDG7102A_SWEEP(v_asic*2)
        # BK4600HLEV_SWEEP(v_asic*2)
        t_sweep = time.time() - t0
        time.sleep(tsleep) #added time for pulse generator to settle

        # save data
        save_data = []
        t_write_total = 0
        t_read_total = 0
        t_postproc_total = 0
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
            t0 = time.time()
            sw_write32_0(hex_lists)
            t_write_total += time.time() - t0

            # prepare the word list to read
            maxWordFWArray = 128
            nword = math.ceil(nsample*3/32)
            base_addr = maxWordFWArray - nword  # first word address to read: from 128-nword to 127
            words = ["0"*32] * nword
            # added time for burst to complete
            time.sleep(100e-6*nsample)

            # read all nword words from DATA_ARRAY_1 (opcode 0xD) in a single round trip
            t0 = time.time()
            raw_words, _, _, _ = sw_readStream(do_sw_read32_1 = False, N = nword, opcode = 0xD, base_addr = base_addr)
            t_read_total += time.time() - t0

            t0 = time.time()
            for i, iW in enumerate(range(base_addr, maxWordFWArray)):
                words[(maxWordFWArray-1)-iW] = int_to_32bit(raw_words[i])

            # save words
            s = [int(i) for i in "".join(words)]
            # Cutting last bit because 3x1365 = 4095
            s = s[:nsample*3]
            save_data.append(s)
            t_postproc_total += time.time() - t0

        # save just the correct npix
        t0 = time.time()
        save_data = np.stack(save_data, 0)
        # Bit order might have to be reversed in the next line since b2-b1-b0
        save_data = save_data.reshape(nsample*nIter, 3)
        save_data = save_data[:,::-1]
        # save data
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npy")
        np.save(outFileName, save_data)
        t_save = time.time() - t0

        t_step_total = time.time() - t_step_start
        burst_sleep_total = 100e-6*nsample*nIter
        print(f"[TIMING] v={v_asic:.3f} total={t_step_total:.3f}s | sweep={t_sweep:.3f}s settle_sleep={tsleep:.3f}s "
              f"write={t_write_total:.3f}s burst_sleep={burst_sleep_total:.3f}s read={t_read_total:.3f}s "
              f"postproc={t_postproc_total:.3f}s save={t_save:.3f}s")

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
            injection_delay = '1D',     #superpix1 '1C', superpix2 '1E',
            scanLoopBackBit = '0', 
            test_sample = '0F', 
            scanLoadPhase ='25',        #superpix1 '25', superpix2 '26',
            test_delay = '14', 
            v_min = 0.001, 
            v_max = 0.2, 
            v_step = 0.002, 
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
        
def SCurveSweepIbias(nPix=0):

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
    V_biasList = np.arange(0.5,0.8,0.01)

    I_biasList = np.arange(0,0.00002,0.000001)
    # I_biasList = [0.000001,0.0000011]
    # biasList = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]
    # vthList = [1.5,1.6]

    for i in I_biasList:
        # V_PORT["Ibias"].set_voltage(i)
        I_PORT["OUTsink"].set_current(i)
        I_LEVEL["OUTsink"] = i
        V_PORT["vdda"].get_current()
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
            testType = "MatrixIbias"
        )
    SDG7102A_INIT()

  
def SCurveSweepVTH(nPix=0):

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
    biasList = np.arange(0,0.3,0.01)
    # biasList = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8]
    # vthList = [1.5,1.6]
    for i in biasList:
        V_PORT["vth0"].set_voltage(i)
        V_LEVEL["vth0"] = i
        V_PORT["vth1"].set_voltage(i)
        V_LEVEL["vth1"] = i
        V_PORT["vth2"].set_voltage(i)
        V_LEVEL["vth2"] = i
        V_PORT["vdda"].get_current()
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

def SCurveSweepVTHPix():
    nPix = 256
    nPixList =  [192]
    for i in nPixList: #range(nPix):
        SCurveSweepVTH(nPix=i)


def SCurveSweep(nPix=0,  FWparameter = None, minPar = 10, maxPar = 28, stepPar = 1, PGparameter=None, minPG=5e-10, maxPG=10e-9, stepPG = 5e-10): 

# This function programs a single pixel and extrac Scurve while sweeping a bias voltage
# the voltage being sweep is VTH but could be changed to VDDA or VDDD
# This is useful to extract linearity
# bias is expected to be a string
# parameter is expected to match FW name and be a string

    #program single pixel
    ProgPixelsOnly(configclk_period='64', cfg_test_delay='5', cfg_test_sample='20',cfg_test_gate_config_clk ='1', pixelList = [nPix], pixelValue=[1])

    # create an output directory/mnt/local/CMSPIX28/Scurve/data/ChipVersion1_ChipID9_SuperPix2/2025.02.25_08.36.02_Matrix_vMin0.001_vMax0.600_vStep0.00100_nSample1000.000_vdda0.900_VTH0.800_BXCLK10.00/nPix0.8
    dataDir = FNAL_SETTINGS["storageDirectory"]
    now = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")

    if FWparameter:

        parmList = [f'{i:X}' for i in range(minPar, maxPar, stepPar)]

        for i in parmList:

            V_PORT["vdda"].get_current()
            PreProgSCurveBurst(
                scan_load_delay = '13', 
                startBxclkState = '0', 
                bxclk_delay = '12', #'12', 
                bxclk_period = '28', 
                injection_delay = i, 
                scanLoopBackBit = '0', 
                test_sample = '0F', 
                scanLoadPhase ='26',
                test_delay = '14', 
                v_min = 0.001, 
                v_max = 0.2, 
                v_step = 0.002, 
                nsample = 1365, 
                nPix = nPix,
                nIter=1,
                dataDir = dataDir,
                dateTime = now,
                testType = "MatrixInjDly", #"MatrixBxCKJDly", #
                parameter = i 
            )
    
    if PGparameter:

        parmList = np.arange(minPG,maxPG,stepPG)

        for i in parmList:
            SDG7102A_SWEEP_FALL(TFALL=i, max_retries=10, retry_delay=0.1)
            SDG7102A_QUERY()
            time.sleep(0.1) # added time for pulse generator to settle
            V_PORT["vdda"].get_current()
            PreProgSCurveBurst(
                scan_load_delay = '13', 
                startBxclkState = '0', 
                bxclk_delay = '12', #'0B', 
                bxclk_period = '28', 
                injection_delay = '1E', 
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
                testType = "MatrixPulseGenFall",
                parameter = i 
            )
            # PreProgSCurve(
            #     scanLoadPhase = '26',
            #     scan_load_delay = '13', 
            #     startBxclkState = '0', 
            #     bxclk_delay = '12', #'0B', 
            #     bxclk_period = '28',
            #     injection_delay = '1E', # vin_test_trig_out in the FW
            #     scanLoopBackBit = '0', 
            #     test_sample = '0F', 
            #     test_delay = '14', 
            #     v_min = 0.01, 
            #     v_max = 0.4, 
            #     v_step = 0.001, 
            #     nsample = 1000, 
            #     nPix = 0, 
            #     dataDir = FNAL_SETTINGS["storageDirectory"],
            #     dateTime = now,
            #     testType = "MatrixPulseGenFall",
            #     parameter = i
            # )
        SDG7102A_SWEEP_FALL(TFALL=5e-10, max_retries=10, retry_delay=0.1)



def analogPower(
    dataDir=FNAL_SETTINGS["storageDirectory"],
    dateTime=None,
    nIter=100,
    settle_s=1.0,
):
    testType = "AnalogPower"
    chipInfo = (
        f"ChipVersion{FNAL_SETTINGS['chipVersion']}_"
        f"ChipID{FNAL_SETTINGS['chipID']}_"
        f"SuperPix{2 if V_LEVEL['SUPERPIX'] == 0.9 else 1}"
    )

    testInfo = (dateTime if dateTime
                else datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + f"_{testType}")

    outDir = os.path.join(dataDir, chipInfo, testInfo)
    os.makedirs(outDir, exist_ok=True)
    try:
        os.chmod(outDir, 0o777)
    except PermissionError:
        pass

    print(f"Saving results to {outDir}")

    # === sweep ===
    ibiasList = np.arange(0.0, 0.00003, 0.000001, dtype=float)  # A

    # === fixed VTH setup ===
    for k in ("vth0", "vth1", "vth2"):
        V_PORT[k].set_voltage(0.1)
        V_LEVEL[k] = 0.1

    # === allocate raw data: shape (n_ibias, nIter) ===
    n_ibias = len(ibiasList)
    ivdda_raw = np.empty((n_ibias, nIter), dtype=float)

    # === measure: for each ibias, repeat nIter times ===
    for idx, ibias in enumerate(ibiasList):
        I_PORT["OUTsink"].set_current(float(ibias))
        I_LEVEL["OUTsink"] = float(ibias)

        # optional settle after changing ibias
        if settle_s and settle_s > 0:
            time.sleep(settle_s)

        for it in range(nIter):
            # if you want settle between repeats too, keep this:
            if settle_s and settle_s > 0:
                time.sleep(settle_s)

            ivdda_raw[idx, it] = float(V_PORT["vdda"].get_current())

        print(f"Ibias={ibias:.6e} A  Ivdda mean={ivdda_raw[idx].mean():.6e} A")

    # === reduce ===
    ivdda_mean = ivdda_raw.mean(axis=1)
    ivdda_std  = ivdda_raw.std(axis=1, ddof=1) if nIter > 1 else np.zeros_like(ivdda_mean)
    ivdda_sem  = ivdda_std / np.sqrt(nIter) if nIter > 1 else np.zeros_like(ivdda_mean)

    # === save NPZ with RAW ===
    outNpZ = os.path.join(outDir, "analogPower.npz")
    np.savez(
        outNpZ,
        ibias_A=ibiasList,
        ivdda_raw_A=ivdda_raw,          # (n_ibias, nIter)
        ivdda_mean_A=ivdda_mean,        # (n_ibias,)
        ivdda_std_A=ivdda_std,          # (n_ibias,)
        ivdda_sem_A=ivdda_sem,          # (n_ibias,)
        nIter=int(nIter),
        settle_s=float(settle_s),
    )

    # === save CSV with AVERAGE (plus std/sem) ===
    outCsv = os.path.join(outDir, "analogPower_avg.csv")
    csv_mat = np.column_stack([ibiasList, ivdda_mean, ivdda_std, ivdda_sem])
    header = "Ibias_A,Ivdda_mean_A,Ivdda_std_A,Ivdda_sem_A"
    np.savetxt(outCsv, csv_mat, delimiter=",", header=header, comments="")

    print(f"Saved NPZ (raw + summary): {outNpZ}")
    print(f"Saved CSV (average):       {outCsv}")
    return outNpZ
