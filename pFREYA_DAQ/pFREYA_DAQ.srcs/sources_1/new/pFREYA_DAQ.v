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

module pFREYA_DAQ(
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
    input  btn_reset,
    // UART signals
    input  uart_clk,
    input  rx_ser, tx_dv, tx_byte,
    output rx_dv, rx_byte, tx_active, tx_ser, tx_done
);

    // Simple UART
    // uart rx
    uart_rx #(.CLKS_PER_BIT(CKS_PER_BIT)) uart_rx_inst (
        .i_Clock(uart_clk),
        .i_Rx_Serial(rx_ser),
        .o_Rx_DV(rx_dv),
        .o_Rx_Byte(rx_byte)
    );
    //uart tx
    uart_tx #(.CLKS_PER_BIT(CKS_PER_BIT)) uart_tx_inst (
        .i_Clock(uart_clk),
        .i_Tx_DV(tx_dv),
        .i_Tx_Byte(tx_byte),
        .o_Tx_Active(tx_active),
        .o_Tx_Serial(tx_ser),
        .o_Tx_Done(tx_done)
    );

    // pFREYA_ASIC interface
    pFREYA_IF pFREYA_IF_inst (
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
        .ck                 (ck),
        .reset              (btn_reset)
    );
endmodule
