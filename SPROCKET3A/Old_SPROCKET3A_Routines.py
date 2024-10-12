##
##  Routines which are no longer used, but may be helpful references for the future.
##


#<<Registered w/ Spacely as ROUTINE 2, call as ~r2>>
def _ROUTINE_i2c_debug():

    bus = 1
    component_addr = 0x40


    for i in range(7):
        print(sg.INSTR["car"].car_i2c_read(bus, component_addr, i, 2))




def _ROUTINE_check_fw():
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




def _ROUTINE_spi_address_mapping():
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
    


#<<Registered w/ Spacely as ROUTINE 16, call as ~r16>>
def _ROUTINE_stochastic_transmitter_analysis():

    m = monkey_state()

    EXPERIMENT = 2

    saved_paths = []

    if EXPERIMENT == 1:

        possible_paths = list(itertools.permutations([6,2,4,5,6]))

        try:
            for path in possible_paths:
                m.monkey_path(path)
                good = input("good?")
                
                if "y" in good:
                    saved_paths.append(path)
            
                m.monkey_path((2,4,5))

        except KeyboardInterrupt:
            print("interrupted!")

        print(saved_paths)
        return

    elif EXPERIMENT == 2:

        possible_paths = list(itertools.permutations([6,2,4,5,6]))
        paths_tried = 0
        paths_successful = 0

        try:
            for path in possible_paths:
                m.monkey_path([1])
                m.monkey_path(path)
            
                success = m.check_fpga()
                if success > 0:
                    print("SUCCESS!")
                    paths_successful = paths_successful + 1
                    saved_paths.append(path)

                paths_tried = paths_tried + 1

        except KeyboardInterrupt:
            print("interrupted!")

        print(f"Tried {paths_tried} paths of which {paths_successful} succeeded:")
        print(saved_paths)
        return
            

    
    m.monkey_path((1,6,2,4,5,6))

    input("?")

    m.monkey_path((1,5,2,4,6,6))

    input("?")



class monkey_state():

    def __init__(self):
        self.txDataRate = 1
        self.scramblerBypass = 1
        self.interleaverBypass = 1
        self.fecBypass = 1
        self.fecMode = 1
    
    def do_action(self, a):

        if a == 1:
            assert_reset()
            time.sleep(0.1)
            deassert_reset()

            spi_write_tx_config(TX_REG_DEFAULTS)

            self.txDataRate = 1
            self.scramblerBypass = 1
            self.interleaverBypass = 1
            self.fecBypass = 1
            self.fecMode = 1
    

        elif a == 2:
            self.scramblerBypass = 1-self.scramblerBypass
            spi_update_tx_reg("scramblerBypass",self.scramblerBypass)
            
        elif a == 3:
            self.interleaverBypass = 1-self.interleaverBypass
            spi_update_tx_reg("interleaverBypass",self.interleaverBypass)
        
        elif a == 4:
            self.fecBypass = 1-self.fecBypass
            spi_update_tx_reg("fecBypass",self.fecBypass)
            
        elif a == 5:
            self.fecMode = 1-self.fecMode
            spi_update_tx_reg("fecMode",self.fecMode)

        elif a == 6:
            self.txDataRate = 1-self.txDataRate
            sg.log.debug(f"{a} - txDataRate to {self.txDataRate}")
            spi_update_tx_reg("txDataRate",self.txDataRate)


    def monkey_path(self, path_actions):
        print(path_actions)
        for action in path_actions:
            self.do_action(action)


    def check_fpga(self):

        time.sleep(3)
        
        sg.INSTR["car"].set_memory("uplinkRst",1)

        time.sleep(0.1)

        sg.INSTR["car"].set_memory("uplinkRst",0)
        print(">  Reset FPGA state machine")

        time.sleep(3)
        
        rx_status_bin = sg.INSTR["car"].get_memory("lpgbtfpga_status")
         
        uplinkrdy = rx_status_bin & 0x1
         
        print(f"UPLINKRDY: {uplinkrdy}")
        
        return uplinkrdy
        
        
        
#<<Registered w/ Spacely as ROUTINE 5, call as ~r5>>
def ROUTINE_axi_shell():
    """Microshell to interact with the AXI registers and debug the design."""

    
    
   # spi_registers = ["spi_write_data", "spi_read_data", "spi_data_len","spi_trigger",
    #                 "spi_transaction_count", "spi_status"]

    for x in register_list.keys():
        print(x)
        
    fw_choice = input("Which fw module would you like to interact with?")
    
    AXI_REGISTERS = register_list[fw_choice]

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
        
        
        

def run_pattern_apg(pattern_glue, loop=False):

    #First, stop looping and wait for the pattern to end if necessary.
    sg.INSTR["car"].set_memory("apg_control",0)

    while True:
        apg_status = sg.INSTR["car"].get_memory("apg_status")
        if apg_status == 0:
            break
        else:
            sg.log.debug(f"Waiting for APG idle (status={apg_status})...")

    sg.INSTR["car"].set_memory("apg_n_samples",len(pattern_glue.vector))

    #Write the pattern glue into memory.
    for c in pattern_glue.vector:
        sg.INSTR["car"].set_memory("apg_write_channel",c)


    #Set up looping if requested
    if loop:
        sg.INSTR["car"].set_memory("apg_control",1)

    #Run
    sg.INSTR["car"].set_memory("apg_run",1)

    sg.log.info("APG Now Running!")
    
    
    
# Directly convert a waves dict to a Glue Wave, without going through
# the step of writing ASCII files.
def genpattern_from_waves_dict_fast(waves_dict, apg_name):

    max_pattern_len = max([len(x) for x in waves_dict.values()])
    
    vector = [0 for _ in range(max_pattern_len)]

    for key in waves_dict.keys():
        io_pos = sg.gc.IO_pos[key]

        vector = [vector[i] | (waves_dict[key][i] << io_pos) for i in range(min(len(vector),len(waves_dict[key])))]

    if DEBUG_SPI:
        sg.log.debug(f"Vector: {vector}")

    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    return GlueWave(vector,strobe_ps,f"Caribou/Caribou/{apg_name}")
    
    
#Caribou version of sg.pr.run_pattern()
# Right now, apg_name = "apg" or "spi_apg"
def run_pattern_caribou(glue_wave,apg_name):

    ## (0) Wait for idle, then clear the write buffer.
    apg_wait_for_idle(apg_name)
    sg.INSTR["car"].set_memory(f"{apg_name}_clear",1)
    
    #Parse glue file names OR python objects
    if type(glue_wave) == str:
        glue_wave = sg.gc.read_glue(glue_wave)


    ## (1) SET NUMBER OF SAMPLES
    N = glue_wave.len

    sg.INSTR["car"].set_memory(f"{apg_name}_n_samples", N)

    ## (2) WRITE PATTERN TO APG
    for n in range(N):
        sg.INSTR["car"].set_memory(f"{apg_name}_write_channel",glue_wave.vector[n])


    ## (3) RUN AND WAIT FOR IDLE
    sg.INSTR["car"].set_memory(f"{apg_name}_run", 1)

    time.sleep(0.1)
    apg_wait_for_idle(apg_name)

    ## (4) READ BACK SAMPLES
    samples = []

    for n in range(N):
        #dbg_error_val = sg.INSTR["car"].get_memory("spi_apg_next_read_sample")
        #sg.log.debug(f"nrs: {dbg_error_val}")
        samples.append(sg.INSTR["car"].get_memory(f"{apg_name}_read_channel"))


    APG_CLOCK_FREQUENCY = 10e6
    strobe_ps = 1/APG_CLOCK_FREQUENCY * 1e12
        
    glue = GlueWave(samples,strobe_ps,f"Caribou/Caribou/{apg_name}")

    sg.gc.write_glue(glue,"apg_samples.glue")

    return "apg_samples.glue"
    
    
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