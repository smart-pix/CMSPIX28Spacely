import random
import time

#Import Spacely functions
from Master_Config import *
import Spacely_Globals as sg
from Spacely_Utils import *

import itertools


#<<Registered w/ Spacely as ROUTINE 0, call as ~r0>>
def ROUTINE_test_axi_read():
    """Evaluate AXI Multi-data Read"""

    sg.INSTR["car"].set_memory("tds_control",4) #Clear
    sg.INSTR["car"].set_memory("tds_control",2) #Increment after every rdStrobe.

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
