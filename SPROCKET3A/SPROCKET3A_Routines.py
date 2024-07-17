import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *


def onstartup():

    gen_fw("simple_serial","/asic/projects/S/SParkDream/aquinn/peary-firmware-sprocket3/submodules/spacely-caribou-common-blocks/simple_serial/simple_serial.fw_description")
    
    print("~ ~ SP3A CaR Board Default Setup ~ ~")
    init_car = input("Initializing CaR Board ('n' to skip)>>>")

    if 'n' in init_car:
        return

    sg.INSTR["car"].debug_memory = False
    
    if not 'n' in init_car:
        sg.INSTR["car"].init_car()
    
    set_cmos_voltage = input("Setting CMOS In/Out Voltage = 1.2V ('n' to skip)>>>")
    if not 'n' in set_cmos_voltage:
        sg.INSTR["car"].set_input_cmos_level(1.2)
        sg.INSTR["car"].set_output_cmos_level(1.2)

    config_si5345 = input("Configuring SI5345 w/ config option 1 ('n' to skip)>>>")
    if not 'n' in config_si5345:
        sg.INSTR["car"].configureSI5345(1)

    #Enable external SPI clock
    #sg.INSTR["car"].set_memory("use_ext_spi_clk",1)

    #Set all AXI GPIOs as outputs
    sg.INSTR["car"].set_memory("gpio_direction",0)

    assert_reset()
    time.sleep(0.1)
    deassert_reset()
        
    print("Finished SP3A CaR Board Default Setup")

def random_coords():
    return [random.randint(0,9),random.randint(0,9)]

#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_ZCU102_Demo_Game():

    USE_ZCU_INPUT = True
    
    player_coords = random_coords()
    candy_coords = [random_coords(), random_coords(), random_coords()]

    print(player_coords)
    print(candy_coords)

    while True:

        ate_candy_this_tick = False
        
        time.sleep(0.5)

        if USE_ZCU_INPUT:
            pushbutton_state = int(sg.INSTR["car"].get_memory("gpio_0_data"))
        else:
            pushbutton_state = int(input("pb state?"))
        print(f"Pushbutton State: {pushbutton_state}")

        if pushbutton_state == 2 and player_coords[0] < 9:
            player_coords[0] = player_coords[0]+1
        elif pushbutton_state == 4 and player_coords[1] < 9:
            player_coords[1] = player_coords[1]+1
        elif pushbutton_state == 8 and player_coords[0] > 0:
            player_coords[0] = player_coords[0]-1
        elif pushbutton_state == 16 and player_coords[1] > 0:
            player_coords[1] = player_coords[1]-1

        ## Game Ends if You Eat All Candy
        if len(candy_coords) == 0:
            break

        ## Print the Game Map
        print("Try to eat all the candy :) ")
        for i in range(10):
            print("")
            for j in range(10):

                if [i,j] == player_coords:
                    print("A",end='')

                    if [i,j] in candy_coords:
                        ate_candy_this_tick = True
                        for x in range(len(candy_coords)):
                            if candy_coords[x] == player_coords:
                                candy_coords.pop(x)
                                break

                elif [i,j] in candy_coords:
                    print("c",end='')
                else:
                    print(".",end='')

        if ate_candy_this_tick:
            print("You ate a piece of candy!")
        else:
            print("")
            


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_bit_bang_test():

    #0 = output, 1 = input
    sg.INSTR["car"].set_memory("gpio_direction",0x0)

    METHOD = int(input("Bitbang method?"))

    sg.log.info("Begin Bit Banging")
    try:
        while True:
            if METHOD == 1:
                sg.INSTR["car"].set_memory("gpio_data",0x2)
                sg.INSTR["car"].set_memory("gpio_data",0x0)
            elif METHOD == 2:
                x = sg.INSTR["car"].get_memory("gpio_data")
                sg.INSTR["car"].set_memory("gpio_data", 0x2 ^ x)
    except KeyboardInterrupt:
        sg.log.debug("Interrupted")

    sg.log.info("End Bit Banging")
        
    

#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_i2c_debug():

    bus = 1
    component_addr = 0x40


    for i in range(7):
        print(sg.INSTR["car"].car_i2c_read(bus, component_addr, i, 2))




#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_check_fw():
    """Write + readback a single value to FW to make sure the firmware is flashed."""

    #Short alias for Caribou system
    car = sg.INSTR["car"]

    TEST_VAL = 0b1010101010

    car.set_memory("spi_write_data",TEST_VAL)

    val = car.get_memory("spi_write_data")

    if val == TEST_VAL:
        sg.log.info("FW check passed!")
    else:
        sg.log.error(f"FW check failed: TEST_VAL={TEST_VAL}, read back {val}")




#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_check_spi_loopback():
    """Write a register over SPI and read back its value to confirm the SPI interface is working."""

    for test_val in [33, 102, 1]:
        spi_write_reg("comp_fall_bufsel",33)
    
        val = spi_read_reg("comp_fall_bufsel")

        if val == 0:
            sg.log.warning("Read back 0. Retrying...")
            val = spi_read_reg("comp_fall_bufsel")

        if val == 33:
            sg.log.info("SPI Loopback Passed!")
        else:
            sg.log.error(f"SPI Loopback Failed: Wrote 33, Read {val}")
            return

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_spi_address_mapping():
    """Sweep through possible SPI commands"""

    pattern_1 = 0b101010101
    pattern_2 = 0b101010001

    for offset in range(4,12,1):
        write_pattern = pattern_1 << offset
        read_pattern = pattern_2 << offset
        print(f"Write Bitstring: {bin(write_pattern)} ")

        sg.INSTR["car"].set_memory("spi_write_data", write_pattern)
        sg.INSTR["car"].set_memory("spi_data_len", 32)
        sg.INSTR["car"].set_memory("spi_trigger",1)

        time.sleep(0.1)
        print("Return Data:",bin(sg.INSTR["car"].get_memory("spi_read_data")))

        print(f"Read Bitstring: {bin(read_pattern)} ")

        sg.INSTR["car"].set_memory("spi_write_data", read_pattern)
        sg.INSTR["car"].set_memory("spi_data_len", 32)
        sg.INSTR["car"].set_memory("spi_trigger",1)

        time.sleep(0.1)
        print("Return Data:",bin(sg.INSTR["car"].get_memory("spi_read_data")))
    

#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_scan_chain_loopback():
    """Write 10b of data into the scan chain and read it back (slide 16)"""
    pass

#<<Registered w/ Spacely as ROUTINE 7, call as ~r7>>
def ROUTINE_config_chain_loopback():
    """Write 29b of data into the scan chain and read it back (slide 18)"""
    pass


#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_basic_signals():
    """Program some basic patterns in the pattern generator and observe outputs"""


    #Try to replicate the commands sent in slides 23, 24, and 25
    #First, observe the results with oscilloscope
    #We can also add some basic firmware that will grab these signals as digital values.

    #Make sure you exercise all the potential options of the PG.

    #EXAMPLE:
    #50 cycles = 78.125 ns
    # spi_write(COMP_RISE_CALC, 0)
    # spi_write(COMP_FALL_CALC, 50)

    #input("CHECK: Is PW of 78.125 ns observed on calc? (Press enter to continue)")
    

    # TEST 1: Check FULL_READOUT
    
    spi_write_reg("FULL_READOUT",0)

    glue = get_glue_wave(10)

    spi_write_reg("FULL_READOUT",1)

    glue = get_glue_wave(10)


#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_axi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    apg_registers = ["apg_run", "apg_write_channel", "apg_read_channel",
                     "apg_sample_count","apg_n_samples","apg_write_buffer_len",
                     "apg_next_read_sample","apg_wave_ptr","apg_status"]
    
    spi_registers = ["spi_write_data", "spi_read_data", "spi_data_len","spi_trigger",
                     "spi_transaction_count", "spi_status"]
    AXI_REGISTERS = spi_registers + apg_registers

    while True:

        # Print register contents
        i = 0
        for reg in AXI_REGISTERS:
            reg_contents = sg.INSTR["car"].get_memory(reg)

            if reg == "spi_status":
                reg_contents = SPI_Status(reg_contents)
            
            print(f"{i}. {reg : <16} -- {reg_contents}")
            i = i+1

        write_reg_num = input("write which?").strip()

        if write_reg_num == "":
            continue

        if write_reg_num == "q":
            return

        write_reg = AXI_REGISTERS[int(write_reg_num)]

        write_val = int(input("val?"))

        sg.INSTR["car"].set_memory(write_reg, write_val)



#<<Registered w/ Spacely as ROUTINE 10, call as ~r10>>
def ROUTINE_spi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    
    SPI_REGISTERS = list(SPI_REG.keys())

    while True:

        # Print register contents
        i = 0
        for reg in SPI_REGISTERS:
            #reg_contents = sg.INSTR["car"].get_memory(reg)

            #if reg == "spi_status":
            #    reg_contents = SPI_Status(reg_contents)
            
            print(f"{i}. {reg : <16} ")
            i = i+1

        write_reg_num = input("which reg?").strip()

        if write_reg_num == "":
            continue

        if write_reg_num == "q":
            return

        try:
            this_reg = SPI_REGISTERS[int(write_reg_num)]
        except ValueError:
            print("ERROR")
            continue

        operation = input("op (r/w)?").strip()

        if operation == "w":

            try:
                write_val = int(input("val?"))
            except ValueError:
                print("ERROR")
                continue

            spi_write_reg(this_reg,write_val)

        else:
            print(spi_read_reg(this_reg))


#<<Registered w/ Spacely as ROUTINE 11, call as ~r11>>
def ROUTINE_get_glue_wave():

    N = input("How many samples do you want to take?")
    N = int(N)

    get_glue_wave(N)


#<<Registered w/ Spacely as ROUTINE 12, call as ~r12>>
def ROUTINE_write_tx_config():
    spi_write_tx_config(TX_REG_DEFAULTS)
