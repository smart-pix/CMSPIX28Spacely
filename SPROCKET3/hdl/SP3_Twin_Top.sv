module top();

   logic SFP0_RX_P;

   test_data_source tds ( /*AXI_INTERFACE(0x400005000)*/);
   

   sp3_dual_rx u_sp3_dual_rx(/*AXI_INTERFACE(0x400002000)*/
			     SFP0_RX_P);
   

   sync_counter sc_a (/*AXI_INTERFACE(0x400003000)*/);

   sync_counter sc_b (/*AXI_INTERFACE(0x400004000)*/);
   


endmodule // SP3_Twin_Top
