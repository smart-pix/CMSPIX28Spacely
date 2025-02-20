# spacely
from Master_Config import *

# python
import tqdm
import numpy as np
import h5py

def PreProgSCurve(
        scanloadDly='13', startBxclkState='0', bxclkDelay='0B', 
        scanFreq='28',scanInjDly='1D', scanLoopBackBit='0', 
        scanSampleDly='08', scanDly='08', 
        v_min = 0.001, v_max=0.2, v_step=0.0005, nsample=1000, 
        SuperPix=False, nPix=0
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

    # create output directory
    outDir = os.path.join(
        FNAL_SETTINGS["storageDirectory"],
        ("SuperPixV2" if V_LEVEL["SUPERPIX"] == 0.9 else "SuperPixV1") if SuperPix == True else "",
        datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + f"_nPix{nPix}_vMin{v_min:.3f}_vMax{v_max:.3f}_vStep{v_step:.5f}_nSample{nsample:.3f}_vdda{V_LEVEL['vdda']:.3f}_VTH{V_LEVEL['VTH']:.3f}"
    )
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
        save_data = np.stack(save_data, 0)
        outFileName = os.path.join(outDir, f"vasic_{v_asic:.3f}.npz")
        np.savez(outFileName, **{"data": save_data})
    
    return None

def IterMatrixSCurve():
    nPix = 256
    for i in range(nPix):
        ProgPixelsOnly( progFreq='64', progDly='5', progSample='20',progConfigClkGate='1',pixelList = [i], pixelValue=[1])
        
        PreProgSCurve(
            scanloadDly='13', 
            startBxclkState='0', 
            bxclkDelay='0B', 
            scanFreq='28', 
            scanInjDly='1D', 
            scanLoopBackBit='0', 
            scanSampleDly='08', 
            scanDly='08', 
            vmin = 0.001, 
            vmax=0.2, 
            vstep=0.001, 
            nSample=1000, 
            SuperPix=True, 
            nPix=i,
        )
    
    

