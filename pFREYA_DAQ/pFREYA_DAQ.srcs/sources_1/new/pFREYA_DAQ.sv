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
`include "pFREYA_defs.sv"

module pFREYA_DAQ
#(parameter CKS_PER_BIT=87)
(
    // ASIC signals
    output logic dac_sdin, dac_sync_n, dac_sck,
    output logic sel_init_n,
    output logic sel_ckcol, sel_ckrow,
    input  logic ser_out,
    output logic ser_read, ser_reset_n,
    output logic ser_ck,
    output logic inj_stb,
    output logic csa_reset_n,
    output logic adc_ck, adc_start,
    output logic sh_phi1d_sup, sh_phi1d_inf,
    output logic slow_ctrl_in, slow_ctrl_reset_n, slow_ctrl_ck,
    // Internal signals
    input  logic btn_reset,

    // UART signals
    input  logic rx_ser,
    output logic tx_ser,

    // sys clk
    input  logic sys_clk_p,
    input  logic sys_clk_n
);

    // for UART
    //logic uart_ck;
    //logic [CK_CNT_N-1:0] uart_cnt;
    // Base clock 200 MHz, UART 10 MHz. It's 10 not 20 cause its counting just on the rising edge, therefore counting to 1 is the same as dividing by 2.
    //parameter uart_div = 10;

    logic [UART_PACKET_SIZE-1:0] uart_data;
    logic uart_valid;
    logic tx_done, tx_active;
    logic tx_dv;
    logic [UART_PACKET_SIZE-1:0] tx_byte;

    // clock wizard
    wire locked;

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
        .ck                 (daq_ck),
        .reset              (btn_reset),
        .uart_data          (uart_data),
        .uart_valid         (uart_valid)
    );

    clk_wiz_clocks clk_wiz_clocks_inst (
        // Clock out ports
        .daq_ck(daq_ck),     // output daq_ck
        .uart_ck(uart_ck),     // output uart_ck
        // Status and control signals
        .reset(btn_reset), // input reset
        .locked(locked),       // output locked
        // Clock in ports
        .clk_in1_p(sys_clk_p),    // input clk_in1_p
        .clk_in1_n(sys_clk_n)    // input clk_in1_n
    );

    always_ff @(posedge daq_ck, posedge btn_reset) begin: reset_daq
        if (btn_reset) begin
            // reset all registers
            tx_dv <= 1'b0;
            tx_byte <= 1'b0;
        end
    end
endmodule
