#<<Registered w/ Spacely as ROUTINE 8, call as ~r8>>
def ROUTINE_clk_divide():

    # create hex lists
    hex_lists = []

    # 1st parameter of the hex code (right to left)
    # this number divides the original 400 MHz down for the BxCLK_ana and BxCLK
    # 400 MHz / clk_divide
    clk_divides = range(10, 41)

    # loop over clk_divides from 10 to 40
    for divide in clk_divides:
        # get clk_divide value
        clk_divide = "6'h" + hex(divide)[2:] # removes the 0x prefix, ex. 0x28 -> 28
        # create hex list
        hex_list = ["4'h2", "4'h2", "11'h0", "1'h0", "1'h0", "5'h4", clk_divide]
        hex_lists.append(hex_list)

    print(f"Writing {len(hex_lists)} hex lists to register sw_write32_0")

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)

#<<Registered w/ Spacely as ROUTINE 9, call as ~r9>>
def ROUTINE_clk_delay():
    
    # create hex lists
    hex_lists = []

    # 2nd parameter of hex code (right to left)
    # change the amount of the delay
    delays = range(0,6)
    
    # 3rd parameter of hex code (right to left)
    # change the sign of the delay
    # 1'h0 = positive offset of analog clock w.r.t digital clock = rising edge of analog clock and the rising egde of the digital clock
    # 1'h1 = negative offset of analog clock w.r.t digital clock = rising edge of analog clock and the falling edge of the digital clock
    signs = ["1'h0", "1'h1"]

    # create hex list to be easy to see on the scope
    for sign in signs:

        for delay in delays:

            # get clk_divide value
            clk_delay = "5'h" + hex(delay)[2:] # removes the 0x prefix, ex. 0x28 -> 28

            # create hex list
            hex_list = ["4'h2", "4'h2", "11'h0", "1'h0", sign, clk_delay, "6'h28"]
            hex_lists.append(hex_list)
        
    print(f"Writing {len(hex_lists)} hex lists to register sw_write32_0")

    # call ROUTINE_sw_write32_0
    ROUTINE_sw_write32_0(hex_lists)
