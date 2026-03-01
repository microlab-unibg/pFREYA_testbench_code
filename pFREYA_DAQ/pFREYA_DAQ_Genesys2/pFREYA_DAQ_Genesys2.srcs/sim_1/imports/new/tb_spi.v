`timescale 1ns / 1ps
// This module contains the code for the SPI communication protocol with the DAC

module tb_spi();

    // Testbench uses a 10 MHz clock    => 100 ns period 
    // DAC works at 25 MHz              => 40  ns period 
    parameter CKS_PER_BIT   = 2;
    parameter CK_PERIOD     = 100; 

    reg         clk     = 0;
    reg [15:0]  tx_data = 0;
    reg         tx_dv   = 0;
    
    wire        spi_sclk;
    wire        spi_cs;
    wire        spi_din;
    //wire        spi_clr;

    spi_IF #(.CKS_PER_BIT(2)) spi_tx_inst (
        .dac_clk(clk),
        .tx_data(tx_data),
        .tx_dv(tx_dv),
        .dac_sclk(spi_sclk),
        //.dac_clr(spi_clr),
        .dac_cs(spi_cs),
        .dac_din(spi_din)
    );

    // Generate 10 MHz clock 
    always 
      begin
        #(CK_PERIOD/2) clk <= !clk;
      end

    initial 
      begin
        tx_data = 16'h0000;
        tx_dv   = 1'b0;
        
        #200; 
        
        // TEST 1 
        @(posedge clk);
        tx_data <= 16'h8501; 
        tx_dv   <= 1'b1;
        
        @(posedge clk);
        tx_dv   <= 1'b0; 
        
        #4000;

        // --- TEST 2
        @(posedge clk);
        tx_data <= 16'h5555; 
        tx_dv   <= 1'b1;
        
        @(posedge clk);
        tx_dv   <= 1'b0;

        #4000; 
    end

endmodule




/* //////////////////   APPUNTI     /////////////////////////// 
    CS va giu per dire a slave che inizia comunicazione
    SCLK parte per settare clock 
    DIN data input 

    CLR pulire l'input 
*/
