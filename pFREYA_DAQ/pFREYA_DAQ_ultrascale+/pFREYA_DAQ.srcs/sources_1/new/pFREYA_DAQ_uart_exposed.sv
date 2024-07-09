`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 05/18/2023 06:15:21 PM
// Design Name: 
// Module Name: pFREYA_DAQ
// Project Name: pFREYA_DAQ
// Target Devices: KCU116
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
`include "pFREYA_defs_uart_exposed.sv"

module pFREYA_DAQ_uart_exposed
#(parameter CKS_PER_BIT=87)
(
    // ASIC signals
    output dac_sdin, dac_sync_n, dac_sck,
    output sel_init_n,
    output sel_ckcol, sel_ckrow,
    input  ser_out,
    output ser_read, ser_reset_n,
    output ser_ck,
    output inj_stb,
    output csa_reset_n,
    output adc_ck, adc_start,
    output sh_phi1d_sup, sh_phi1d_inf,
    output slow_ctrl_in, slow_ctrl_reset_n, slow_ctrl_ck,
    // Internal signals
    input  daq_ck, btn_reset,
    input  cmd_available, data_available,
    // for UART
    output  [UART_PACKET_SIZE-1:0] uart_data,
    output  uart_valid,

    // UART signals
    input  uart_ck,
    input  rx_ser,
    //output [UART_PACKET_SIZE-1:0] rx_byte, -> uart_data
    //output rx_dv, -> uart_valid

    input  tx_dv,
    input  [UART_PACKET_SIZE-1:0] tx_byte,
    output tx_done, tx_active, tx_ser
);

    // Simple UART
    uart_IF #(.CKS_PER_BIT(CKS_PER_BIT)) uart_IF_inst (
        .uart_ck    (uart_ck),
        .rx_ser     (rx_ser),
        .rx_dv      (uart_valid),
        .rx_byte    (uart_data),
        .tx_dv      (tx_dv),
        .tx_byte    (tx_byte),
        .tx_active  (tx_active),
        .tx_ser     (tx_ser),
        .tx_done    (tx_done)
    );

    // pFREYA_ASIC interface
    pFREYA_IF_uart_exposed pFREYA_IF_uart_exposed_inst (
        .dac_sdin           (dac_sdin),
        .dac_sync_n         (dac_sync_n),
        .dac_sck            (dac_sck),
        .sel_init_n         (sel_init_n),
        .sel_ckcol          (sel_ckcol),
        .sel_ckrow          (sel_ckrow),
        .ser_out            (ser_out),
        .ser_read           (ser_read),
        .ser_reset_n        (ser_reset_n),
        .ser_ck             (ser_ck),
        .inj_stb            (inj_stb),
        .csa_reset_n        (csa_reset_n),
        .adc_ck             (adc_ck),
        .adc_start          (adc_start),
        .sh_phi1d_sup       (sh_phi1d_sup),
        .sh_phi1d_inf       (sh_phi1d_inf),
        .slow_ctrl_in       (slow_ctrl_in),
        .slow_ctrl_reset_n  (slow_ctrl_reset_n),
        .slow_ctrl_ck       (slow_ctrl_ck),
        .ck                 (daq_ck),
        .reset              (btn_reset),
        .uart_data          (uart_data),
        .uart_valid         (uart_valid),
        .cmd_available      (cmd_available),
        .data_available     (data_available)
    );
endmodule
