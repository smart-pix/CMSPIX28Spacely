# spacely
from Master_Config import *

def ScanChainOneShot():

    # hex lists                                                                                                                    
    hex_lists = [
        #["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"],#BSDG7102A and CARBOARD and long cable
        ["4'h2", "4'h2", "3'h0", "1'h0", "1'h0","6'h13", "1'h1", "1'h0", "5'h0B", "6'h28"], #BSDG7102A and CARBOARD
          
         # BxCLK is set to 10MHz : "6'h28"
         # BxCLK starts with a delay: "5'h4"
         # BxCLK starts LOW: "1'h0"
         # Superpixel 0 is selected: "1'h0"
         # scan load delay is set : "6'h0A"                 
         # scan_load delay is disabled is set to 0 -> so it is enabled (we are not using the carboard): "1'h0"
         # SPARE bits:  "4'h0"
         # Register Static 0 is programmed : "4'h2"
         # IP 2 is selected: "4'h2"

  

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

    # send an execute for test 1 and loopback enabled
    # https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L251-L260
    # hex_lists = [
    #     [
    #         "4'h2",  # firmware id
    #         "4'hF",  # op code for execute
    #         "1'h1",  # 1 bit for w_execute_cfg_test_mask_reset_not_index
    #         "6'h1C", # 6 bits for w_execute_cfg_test_vin_test_trig_out_index_max
    #         "1'h0",  # 1 bit for w_execute_cfg_test_loopback
    #         "4'h2",  # 4 bits for w_execute_cfg_test_number_index_max - w_execute_cfg_test_number_index_min
    #         "6'h1A", # 6 bits for w_execute_cfg_test_sample_index_max - w_execute_cfg_test_sample_index_min
    #         "6'h18"  # 6 bits for w_execute_cfg_test_delay_index_max - w_execute_cfg_test_delay_index_min
    #     ]
    # ]
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
        sw_read32_0_expected = int(sw_read32_0_expected_list[iW], 16)
        sw_read32_1_expected = int("10100000100010",2) # from running op codes. see here for the mapping https://github.com/SpacelyProject/spacely-caribou-common-blocks/blob/cg_cms_pix28_fw/cms_pix_28_test_firmware/src/fw_ip2.sv#L179-L196
        sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(sw_read32_0_expected = sw_read32_0_expected, sw_read32_1_expected = sw_read32_1_expected, sw_read32_1_nbitsToCheck = 14, print_code = "ihb")
        sw_read32_0, sw_read32_1, _, _ = sw_read32(print_code = "ihb")
        
        # update
        PASS = PASS and sw_read32_0_pass and sw_read32_1_pass

        # store data
        words.append(int_to_32bit(sw_read32_0)[::-1])
    
    s = ''.join(words)
    #s = split_bits_to_numpy(s[22:-10],3)
    
    print(len(words), s)
    # start = 0
    # npix = []
    # deadpix = []
    # deadbit = []
    # while True:
    #     index = s.find("111", start)
    #     if index == -1:
    #         break
    #     npix.append(index/3)
    #     start = index +1

    # start = 0
    # while True:
    #     index_deadbit = s.find("1", start)
    #     if index_deadbit == -1:
    #         break
    #     deadpix.append(int((index_deadbit+1)/3))
    #     deadbit.append(round(((((index_deadbit+1)/3)-int((index_deadbit+1)/3))*3)))
    #     start = index_deadbit +1
    # print(f"pixel number {npix} is programmed")
    # {print(f"pixel number {deadpix[ind]}, bit {deadbit[ind]} is dead") for ind in range(len(deadbit))}
    return None
