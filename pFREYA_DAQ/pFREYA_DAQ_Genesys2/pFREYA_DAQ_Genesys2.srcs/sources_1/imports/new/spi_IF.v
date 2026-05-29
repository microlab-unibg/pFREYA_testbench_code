`timescale 1ns / 1ps

module spi_IF
#(parameter CKS_PER_BIT=2)
(
    input dac_clk,
    // Clock di sistema a 200 MHz per ritardi assoluti
    input sys_clk,
    input [15:0] tx_data,
    input tx_dv,   
    output dac_sclk,  
    output dac_clr,   
    output dac_cs,    
    output dac_din
);


    spi_tx #(.CKS_PER_BIT(CKS_PER_BIT)) spi_tx_inst (
        .i_Clk(dac_clk),
        // Passa il clock a 200 MHz al modulo di trasmissione
        .i_Sys_Clk(sys_clk),
        .i_Tx_Data(tx_data),
        .i_Tx_DV(tx_dv),   
        .o_SPI_Sclk(dac_sclk),  
        .o_SPI_Clr(dac_clr),   
        .o_SPI_Cs(dac_cs),    
        .o_SPI_Din(dac_din)
    );

endmodule