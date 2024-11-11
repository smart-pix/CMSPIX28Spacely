`timescale 1ns/1ps
module CaribouDigitalTwinTop();

   logic SFP0_RX_P;

   test_data_source_top tds ( /*AXI_INTERFACE(0x400005000)*/
			      .axi_clk(AXI_ACLK),
			      .axi_resetn(AXI_ARESETN));
   

   //sync_counter_top sc_a (/*INTERFACE(0x400003000)*/);

   //sync_counter_top sc_b (/*INTERFACE(0x400004000)*/);
   

endmodule // SP3_Twin_Top
