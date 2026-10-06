# spacely
from Master_Config import *

# python modules
import sys
try:
    pass 
except ImportError as e:
    loud_message(header_import_error, f"{__file__}: {str(e)}")
    sys.exit(1)  # Exit script immediately
    
def ScanChainOneShot(
        scan_load_delay='13', 
        startBxclkState='0', 
        bxclk_delay='0B', 
        bxclk_period='28',
        injection_delay='1D', 
        scanLoopBackBit='0', 
        test_sample='08', 
        test_delay='03', 
        scanLoadPhase='20'
):
    x = bin(int(scanLoadPhase, 16))[2:].zfill(6)
    scanLoadPhase1= hex(int(x[:2], 2))[2:]
    scanLoadPhase0= hex(int(x[2:], 2))[2:]
    nsampleHex = int_to_32bit_hex(1)
    nPixHex = int_to_32bit_hex(0)
    # hex lists                                                                                                                    
    hex_lists = [
        ["4'h2", "4'h2", f"4'h{scanLoadPhase0}", "1'h0",f"6'h{scan_load_delay}", "1'h1", f"1'h{startBxclkState}", f"5'h{bxclk_delay}", f"6'h{bxclk_period}"],
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # SPARE bits:  "4'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"
        ["4'h2", "4'h4", "3'h3", f"2'h{scanLoadPhase1}", f"11'h{nsampleHex}", f"8'h{nPixHex}"],       
    ]

    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ibh")
    
    # each write CFG_ARRAY_0 is writing 16 bits. 768/16 = 48 writes in total.
    nwrites = 240 # updated from 48

    # hex lists to write - FORCE ALL NONE USED BIT TO 1
    hex_lists = [["4'h2", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(nwrites)]
    sw_read32_0_expected_list = [int_to_32bit_hex(0)]*len(hex_lists)

    # call sw_write32_0
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
       
    hex_lists = [
        [
            "4'h2",  # firmware id
            "4'hF",  # op code for execute
            "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
            #"6'h1D", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            f"6'h{injection_delay}", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
            f"1'h{scanLoopBackBit}",  # 1 bit for w_execute_cfg_test_loopback
            # "4'h8",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
            "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - NO SCANCHAIN - JUST DNN TEST          
            f"6'h{test_sample}", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
            f"6'h{test_delay}"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
        ]
    ] 
    sw_write32_0(hex_lists)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code="ihb")
   
    # boolean to store overall test pass or fail
    PASS = True

    # OP_CODE_R_DATA_ARRAY_0 24 times = address 0, 1, 2, ... until I read all 24 words (32 bits). 
    # we'll have stored 24 words * 32 bits/word = 768. read sw_read32_0
    wordList =   list(range(24)) #[23]
    words = []

    start_readback = time.process_time()
    for iW in wordList: #range(nwords):

        # send read
        address = "8'h" + hex(iW)[2:]
        hex_lists = [
            ["4'h2", "4'hC", address, "16'h0"] # OP_CODE_R_DATA_ARRAY_0
        ]
        sw_write32_0(hex_lists)
        
        # read back data
        sw_read32_0, sw_read32_1, _, _ = sw_read32(print_code = "ihb")
        
        # update
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(int_to_32bit(sw_read32_0)[::-1])
    
    s = ''.join(words)
    print(len(words), s)
    return None
