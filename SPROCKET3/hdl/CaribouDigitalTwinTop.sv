`timescale 1ns/1ps
module CaribouDigitalTwinTop();

   // SPI Interface
   logic reset_b, pico, poci, cs_b, spi_clk, trig;
   

   test_data_source_top tds ( /*AXI_INTERFACE(0x400005000)*/
			      .axi_clk(AXI_ACLK),
			      .axi_resetn(AXI_ARESETN));


   logic_clk_div_top spi_clk_div (/*AXI_INTERFACE(0x400000000)*/
				  .master_clk(AXI_ACLK),
				  .output_clk(spi_clk),
				  .axi_resetn(AXI_ARESETN),
				  .axi_clk(AXI_ACLK));
   

   Arbitrary_Pattern_Generator_top #(.NUM_SIG(4), .NUM_SAMP(256))  spi_apg(/*AXI_INTERFACE(0x400001000)*/
								       .axi_clk(AXI_ACLK),
								       .axi_resetn(AXI_ARESETN),
								       .wave_clk(spi_clk),
								       .input_signals({4'b0,poci}),
								       .output_signals({trig,reset_b,cs_b,pico}));
   
					   
   

   // The ASIC
   SPROCKET3_Top dut(.reset_b(reset_b),
		     .pico(pico),
		     .poci(poci),
		     .cs_b(cs_b),
		     .spi_clk(spi_clk),
		     .trig(trig));
   
   
endmodule // CaribouDigitalTwinTop
