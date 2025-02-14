# spacely
from Master_Config import *

# python
import tqdm
import numpy as np
import h5py

def PreProgSCurve(scanloadDly='13', startBxclkState='0', bxclkDelay='0B', scanFreq='28',scanInjDly='1D', scanLoopBackBit='0', scanSampleDly='08', scanDly='08', vmin = 0.001, vmax=0.2, vstep=0.0005, nSample=1000):

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
    v_min = vmin
    v_max = vmax
    v_step = vstep
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of samples to run for each charge setting
    nsample = nSample
    nWord = 24  #number of 32bit word to read the scanChain

    nStream = nSample*n_step*nWord

         #number of sample for each charge settings

    outDir = datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + f"_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.3f}_nSample{nsample:.3f}"
    outDir = os.path.join("data", outDir)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)

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

            wordList = [0] # list(range(24))
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
        save_data = np.stack(save_data, 0)
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        np.savez(outFileName, **{"data": save_data})
    
    return None

def pixelProg_scanChain_CDF(pixelList=[0], pixelSettings=[2], scan_address=[0], vmin=0.025, vmax = 0.2, vstep = 0.0005, nsample =100):
    # STEP 1: WE PROGRAM THE PIXELS
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


    #prepare list of pixels
    pixelListToProgram =  pixelList
    pixelSettingsToProgram = pixelSettings
    pixelConfig = genPixelProgramList(pixelListToProgram, pixelSettingsToProgram)

    # Programming the NN weights and biases
    hex_lists = dnnConfig('/asic/projects/C/CMS_PIX_28/benjamin/verilog/workarea/cms28_smartpix_verification/PnR_cms28_smartpix_verification_A/tb/dnn/csv/l6/b5_w5_b2_w2_pixel_bin.csv', pixelConfig = pixelConfig)
    # print(hex_list)
    # print("Printing DNN config")
    sw_write32_0(hex_lists, doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32() #print_code = "ihb")

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
    time.sleep(1)



    #STEP 2 - WE EXTRACT THE S-CURVE

    # hex lists                                                                                                                    
    hex_lists = [

        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # w_cfg_static_0_reg_pack_data_array_0_IP2
         # SPARE bits:  "3'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2

    ]

    sw_write32_0(hex_lists,doPrint=False)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32()
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 24 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    VHLEV = 0.1


    S = 40e-6           #Charge Sensitivity in V/e-
    #npulse_step = 450    #number of charge settings 
    #npulse_step = 20

    # define range of asic voltages
    v_min = vmin #0.025
    v_max = vmax #0.1
    v_step = vstep # 0.0005
    n_step = int((v_max - v_min)/v_step)+1
    vasic_steps = np.linspace(v_min, v_max, n_step)

    # number of samples to run for each charge setting
    nsample = nsample #1000
    
         #number of sample for each charge settings
    pixNumber = pixelList[0]
    configBit= pixelSettings[0]
    scanAddress=scan_address[0]
    # test_path = "/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea/CMSPIX28_DAQ/spacely/PySpacely/data/2024-10-25_MATRIX"
    test_path = "/asic/projects/C/CMS_PIX_28/benjamin/testing/workarea/CMSPIX28_DAQ/spacely/PySpacely/data/test"
    now = datetime.now()

    #folder_name = now.strftime("%Y-%m-%d_%H-%M-%S") + f"_scanAddress{scanAddress}" # Format: YYYY-MM-DD_HH-MM-SS
    #folder_name = now.strftime("%Y-%m-%d") + f"_scanAddress{scanAddress}" # Format: YYYY-MM-DD_HH-MM-SS
    #full_folder_path = os.path.join(test_path, folder_name)

    # Create the new directory
    #os.makedirs(full_folder_path, exist_ok=True)  # Create the folder


    outDir =  f"pixel{pixNumber}_config{configBit}_scanAddress{scanAddress}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}"
    outDir = os.path.join(test_path, outDir)
    print(f"Saving results to {outDir}")
    os.makedirs(outDir, exist_ok=True)

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
                    "6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
                    "1'h0",  # 1 bit for w_execute_cfg_test_loopback
                    "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
                    "6'h08", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
                    "6'h08"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
                ]
            ]           
  
            sw_write32_0(hex_lists, doPrint=False)
 
            wordList = scan_address #[0] # list(range(24))
            words = ["0"*32] * 24
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
                sw_read32_0, sw_read32_1, _, _ = sw_read32(do_sw_read32_1=False)
     

                # store data
                # words.append(int_to_32bit(sw_read32_0)[::-1])
                words[iW] = int_to_32bit(sw_read32_0)[::-1]
            
            #read_time=time.process_time()-start_readback

            #print(f"readback_time={read_time}")
            
            s = [int(i) for i in "".join(words)]
            save_data.append(s)

        # save the data to a file
        save_data = np.stack(save_data, 0)
        # outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.h5")
        # np.savez(outFileName, **{"data": save_data})
        with h5py.File(outFileName, 'w') as hf:
            hf.create_dataset("data", data=save_data)

    return None

def IterMatrixSCurve():
    nsample = 10
    vstep = 0.001
    scanList = [0, 1, 2, 6, 7, 8, 12, 13, 14, 18, 19, 20]   # we scanonly the right side of the matrix
    # scanList = [ 20]   # we scanonly the right side of the matrix
    for i in scanList:
        for j in range(int(i*32/3)+((i*32/3)>int(i*32/3)),round((i+1)*32/3)):   #we only test the pixels which have the 3 bits in a single DATA_ARRAY_) address
            pixelProg_scanChain_CDF(pixelList=[j], pixelSettings=[1], scan_address=[i], vmin=0.02, vmax = 0.1, vstep = vstep, nsample =nsample)

    pixelProg_scanChain_CDF(pixelList=[7], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[8], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[9], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[10], pixelSettings=[2], scan_address=[0], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # #pixelProg_scanChain_CDF(pixelList=[11], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.001, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[12], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[13], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[14], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[15], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[16], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[17], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[18], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[19], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    pixelProg_scanChain_CDF(pixelList=[20], pixelSettings=[2], scan_address=[1], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    pixelProg_scanChain_CDF(pixelList=[21], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[22], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[23], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[24], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[25], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[26], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[27], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[28], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[29], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[30], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[31], pixelSettings=[2], scan_address=[2], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # pixelProg_scanChain_CDF(pixelList=[64], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[65], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[66], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[67], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[68], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[69], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[70], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[71], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[72], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[73], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # #pixelProg_scanChain_CDF(pixelList=[74], pixelSettings=[2], scan_address=[6], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

    # pixelProg_scanChain_CDF(pixelList=[75], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[76], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[77], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[78], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[79], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[80], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[81], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[82], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[83], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[84], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # #pixelProg_scanChain_CDF(pixelList=[85], pixelSettings=[2], scan_address=[7], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)    

    # pixelProg_scanChain_CDF(pixelList=[128], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[129], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[130], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[80], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[81], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[82], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[83], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)
    # pixelProg_scanChain_CDF(pixelList=[84], pixelSettings=[2], scan_address=[8], vmin=0.02, vmax = 0.1, vstep = 0.0005, nsample =nsample)

