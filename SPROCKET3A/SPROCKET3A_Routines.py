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
def ROUTINE_gen_device():
    """Generate a peary device"""

    generate_peary_device("ZCU102_LED_Demo","/asic/projects/S/SParkDream/aquinn/ZCU102_LED_Demo/ZCU102_LED_Demo_mem_map.txt")
