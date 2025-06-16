`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 09/26/2023 06:09:39 PM
// Design Name: 
// Module Name: uart_IF
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module uart_IF
#(parameter CKS_PER_BIT=87)
(
    // UART signals
    input uart_ck,
    input rx_ser,
    output [7:0] rx_byte,
    output rx_dv,

    input tx_dv,
    input [7:0] tx_byte,
    output tx_done,
    output tx_active,
    output tx_ser
);
    
    // Simple UART
    // uart rx
    uart_rx #(.CKS_PER_BIT(CKS_PER_BIT)) uart_rx_inst (
        .i_Clock(uart_ck),
        .i_Rx_Serial(rx_ser),
        .o_Rx_DV(rx_dv),
        .o_Rx_Byte(rx_byte)
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
