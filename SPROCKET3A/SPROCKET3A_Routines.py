import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

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
def ROUTINE_i2c_debug():

    bus = 1
    component_addr = 0x40


    for i in range(7):
        print(sg.INSTR["car"].car_i2c_read(bus, component_addr, i, 2))




#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_check_fw():
    """Write + readback a single value to FW to make sure the firmware is flashed."""

    #Short alias for Caribou system
    car = sg.INSTR["car"]

    TEST_VAL = 0b1010101010

    car.set_memory("spi_address",TEST_VAL)

    val = car.get_memory("spi_address")

    if val == TEST_VAL:
        sg.log.info("FW check passed!")
    else:
        sg.log.error(f"FW check failed: TEST_VAL={TEST_VAL}, read back {val}")




#<<Registered w/ Spacely as ROUTINE 3, call as ~r3>>
def ROUTINE_check_spi_loopback():
    """Write a register over SPI and read back its value to confirm the SPI interface is working."""
    pass
    # spi_write(xyz, 123)
    # val = spi_read(xyz)
    # if val != 123:
    #   sg.log.error("Failed!")



#<<Registered w/ Spacely as ROUTINE 4, call as ~r4>>
def ROUTINE_scan_chain_loopback():
    """Write 10b of data into the scan chain and read it back (slide 16)"""
    pass

#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_config_chain_loopback():
    """Write 29b of data into the scan chain and read it back (slide 18)"""
    pass


#<<Registered w/ Spacely as ROUTINE 6, call as ~r6>>
def ROUTINE_basic_signals():
    """Program some basic patterns in the pattern generator and observe outputs"""


    #Try to replicate the commands sent in slides 23, 24, and 25
    #First, observe the results with oscilloscope
    #We can also add some basic firmware that will grab these signals as digital values.

    #Make sure you exercise all the potential options of the PG.

    #EXAMPLE:
    #50 cycles = 78.125 ns
    spi_write(COMP_RISE_CALC, 0)
    spi_write(COMP_FALL_CALC, 50)

    input("CHECK: Is PW of 78.125 ns observed on calc? (Press enter to continue)")
    
