import random
import time


#Import Spacely functions
#from Master_Config import *
#import Spacely_Globals as sg
from Spacely_Utils import *

    
import itertools
import cocotb
from cocotb.triggers import FallingEdge, Timer

from Spacely_Cocotb import *


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_test_axi_read(dut=None):
    """Evaluate AXI Multi-data Read"""

    sg.INSTR["car"].set_memory("tds_control",4) #Clear
    #Increment after every rdStrobe.
    sg.INSTR["car"].set_memory("tds_control",2) 
    
    a = []
    a_gold = [0,1,2]
    for _ in range(3):
        a.append(sg.INSTR["car"].get_memory("tds_data"))

    print(f"Actual: {a}, Expected: {a_gold}")
    if a == a_gold:
        print("PASS!")
    else:
        print("FAIL!")


    print("Now let's test out streaming to file!")
    method = int(input("What method do you want to use? (1=get_memory, 2=stream_memory)"))

    if method == 1:
        print("get_memory!")
    elif method == 2:
        print("stream_memory!")
    else:
        print("Sorry, didn't understand that choice.")
        return

    
    try:
        while True:
            N = input("Number of Samples>>>")

            try:
                N = int(N)
            except ValueError:
                if N == 'q':
                    print("Quitting!")
                    break
                else:
                    print("Error, please enter an integer")
                    continue

            if method == 1:
                start_time = time.perf_counter()
                for n in range(N):
                    x = sg.INSTR["car"].get_memory("tds_data")
                end_time = time.perf_counter()
            elif method == 2:
                start_time = time.perf_counter()
                sg.INSTR["car"].stream_memory("tds_data",N)
                end_time = time.perf_counter()

            elapsed_time = end_time - start_time

            print(f"Words Read: {N} Time taken: {elapsed_time:.6f} seconds")

    except KeyboardInterrupt:
        print("Finishing!")


#<<Registered w/ Spacely as ROUTINE 1, call as ~r1>>
def ROUTINE_check_spi_loopback():
    """Write a register over SPI and read back its value to confirm the SPI interface is working."""


    sg.pr.update_io_defaults("spi_apg")
    
    for test_val in [49, 102, 1]:
        spi_write_reg("comp_fall_bufsel",test_val)
    
        val = spi_read_reg("comp_fall_bufsel")

        if val == 0:
            sg.log.warning("Read back 0. Retrying...")
            val = spi_read_reg("comp_fall_bufsel")

        if val == test_val:
            sg.log.info("SPI Loopback Passed!")
        else:
            sg.log.error(f"SPI Loopback Failed: Wrote {test_val} (bin:{bin(test_val)}), Read {val} (bin:{bin(val)})")
            return



#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def ROUTINE_demo_test(dut):
    """Minimal routine for testing Spacely Digital Twin."""
    dut.a.value = 1
    dut.b.value = 1

    awaitTimer(5, units="ns")

    assert(dut.c.value == 1)
    print(f"dut.c.value = {dut.c.value}")

    dut.a.value = 0
    dut.b.value = 0

    awaitTimer(5, units="ns")

    assert(dut.c.value == 0)
    print(f"dut.c.value = {dut.c.value}")
