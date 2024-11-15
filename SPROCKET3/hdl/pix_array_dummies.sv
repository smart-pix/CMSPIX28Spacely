module SPROCKET3_PIX_Array_x20 #(parameter COUNTER_BITS = 14,
                        parameter NUM_SUPER_ROWS = 2,
                        parameter NUM_SUPER_COLS = 10,
                        parameter ADC_BITS = 10, 
                        parameter ADDRESS_BITS = 10,
                        parameter NUM_ROWS = 16, 
                        parameter NUM_COLS = 16,
                        parameter PIXEL_ROW_NUM = 2,
                        parameter PIXEL_COL_NUM = 2, 
                        parameter CONFIG_BITS = 28,
                        parameter SCANCHAIN_BITS = 10,
                        parameter NUM_ARRAYS_PER_SERIALIZER = 28,
		                parameter NUM_PHYSICAL_ARRAYS = 20)
 
(

    // Inputs into the arrays
    input 			       reset_b,
    input 			       fullReadout,
    input 			       array_serialClk,

    input 			       global_configClk,
    input 			       global_configIn,
    input 			       global_configEn,
    input [(SCANCHAIN_BITS - 1):0]     global_scanIn,
    input 			       global_scanClk,
    input 			       global_scanEn,

    input 			       phi1_global,
    input 			       phi2_global,
    input 			       read_delay,
    input 			       DACclr,
    input 			       calc,
    input 			       capClk,
    input 			       read,
    input 			       Rst,
    input 			       bufsel,
    input 			       Qequal,


    input [NUM_PHYSICAL_ARRAYS - 1:0]  array_select,

    // Outputs out of the arrays
    output [NUM_PHYSICAL_ARRAYS - 1:0] array_serial, //Serial bit stream from each array.
    output [NUM_PHYSICAL_ARRAYS - 1:0] array_done, //Output from each array telling it is done.
    output 			       global_configOut,
    output [(SCANCHAIN_BITS - 1):0]    global_scanOut,

    // Inouts of the arrays
    inout 			       Vtest, 
    inout 			       Vref_fe, 
    inout 			       Vref_adc, 
    inout 			       Vdd12, 
    inout 			       Vclamp, 
    inout 			       Iterm, 
    inout 			       Icomp, 
    inout 			       Ibuf, 
    inout 			       Ib1, 
    inout 			       Ib2, 
    inout 			       vdda, 
    inout 			       vssa, 
    inout 			       gnda
			 
);


   assign array_serial = '0;
   


endmodule // SPROCKET3_PIX_Array_x20


module DEL005(input logic I,
	      output logic Z);


   assign #0.5 Z = I;


endmodule // DEL005

module DEL01(input logic I,
	      output logic Z);


   assign #1 Z = I;


endmodule // DEL01

module CKBD2(input logic I,
	      output logic Z);


   assign Z = I;


endmodule // CKBD2
