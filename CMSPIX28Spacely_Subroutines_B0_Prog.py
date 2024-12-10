# spacely
from Master_Config import *

def ProgPixelsOnly():

    #FW reset followed with Status reset
    fw_status_clear()

    hex_list = [
        ["4'h1", "4'h1", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_RST_FW
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
 

    hex_list = [
        ["4'h1", "4'h2", "16'h0", "1'h1", "7'h64"], # OP_CODE_W_CFG_STATIC_0 : we set the config clock frequency to 100KHz
        ["4'h1", "4'h3", "16'h0", "1'h1", "7'h64"] # OP_CODE_R_CFG_STATIC_0 : we read back
    ]

    # call sw_write32_0
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    hex_list = [
        ["4'h1", "4'he", "16'h0", "1'h1", "7'h64"] # OP_CODE_W_STATUS_FW_CLEAR
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")

    # write on array0    
    hex_list = [["4'h1", "4'h6", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    # write on array1
    # pixels are programmed between addresses [68] and [99] (see figure 6 from report)    
    array0 = hex_list
    hex_list = [["4'h1", "4'h8", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]
    #hex_list[69] = ["4'h1", "4'h8", "8'h45", "16'h0000"]    
    #hex_list[68] = ["4'h1", "4'h8", "8'h44", "16'h003F"]
    #hex_list[67] = ["4'h1", "4'h8", "8'h43", "16'hFFFF"]  
    #hex_list[0] = ["4'h1", "4'h8", "8'h00", "16'hFF00"]
    array1 = hex_list

    # write on array2
    #hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'hAAAA"] for i in range(256)]
    hex_list = [["4'h1", "4'hA", "8'h" + hex(i)[2:], "16'h0000"] for i in range(256)]

    # testing programming 4 pixels
    #hex_list[120] = ["4'h1", "4'hA", "8'h78", "16'h0100"]
    hex_list[112] = ["4'h1", "4'hA", "8'h70", "16'h0002"] 
    hex_list[128] = ["4'h1", "4'hA", "8'h80", "16'h0000"]
    #hex_list[115] = ["4'h1", "4'hA", "8'h73", "16'h0020"]
    #hex_list[136] = ["4'h1", "4'hA", "8'h88", "16'h2000"]   
    array2 = hex_list

    hex_list =  array2+array1+array0   


    sw_write32_0(hex_list)

    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
    hex_list = [
        [
            "4'h1",  # firmware id
            "4'hf",  # op code d for execute
            "1'h0",  # 1 bit for w_execute_ch0fg_test_mask_reset_not_index
            "4'h0", # 3 bits for spare_index_max
            "1'h0",  # 1 bit for w_execute_cfg_test_loopback
            "4'h1",  # 3 bits for test number
            "7'h4", # 6 bits test sample
            "7'h3F"  # 6 bits for test delay
        ]
        
    ]
    sw_write32_0(hex_list)
    sw_read32_0, sw_read32_1, sw_read32_0_pass, sw_read32_1_pass = sw_read32(print_code = "ihb")
    time.sleep(1)

def ProgShiftRegs():
    pass
