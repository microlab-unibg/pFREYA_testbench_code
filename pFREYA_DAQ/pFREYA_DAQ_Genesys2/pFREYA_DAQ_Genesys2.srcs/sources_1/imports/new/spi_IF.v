`timescale 1ns / 1ps

module spi_IF
#(parameter CKS_PER_BIT=87)
(
    // SPI signals
    output spi_ck,
    output spi_cs,
    output [15:0] dac_data_in,
    output dac_rst

);


    //uart tx
    uart_tx #(.CKS_PER_BIT(CKS_PER_BIT)) uart_tx_inst (
        .i_Clock(uart_ck),
        .i_Tx_DV(tx_dv),
        .i_Tx_Byte(tx_byte),
        .o_Tx_Active(tx_active),
        .o_Tx_Serial(tx_ser),
        .o_Tx_Done(tx_done)
    );

endmodule