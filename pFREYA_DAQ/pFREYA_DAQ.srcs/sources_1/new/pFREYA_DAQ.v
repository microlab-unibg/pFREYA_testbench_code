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
        output logic dac_sdin, dac_sync_n, dac_sck,
        inout  logic sel_init_n,
        output logic sel_ckcol, sel_ckrow,
        input  logic ser_out,
        inout  logic ser_read, ser_reset_n,
        output logic ser_ck,
        output logic inj_stb,
        output logic csa_reset_n,
        output logic adc_ck, adc_start,
        output logic sh_phi1d_sup, sh_phi1d_inf,
        output logic slow_ctrl_in, slow_ctrl_reset_n, slow_ctrl_ck,
        // Internal signals
        input  logic btn_reset
        // UART signals
        input  logic uart_clk
    );

    // UART Lite interface
    // TODO port connection
    axi_uartlite_IP axi_uartlite_IP_inst (
        .s_axi_aclk     (s_axi_aclk),      // input wire s_axi_aclk
        .s_axi_aresetn  (s_axi_aresetn),   // input wire s_axi_aresetn
        .interrupt      (interrupt),       // output wire interrupt
        .s_axi_awaddr   (s_axi_awaddr),    // input wire [3 : 0] s_axi_awaddr
        .s_axi_awvalid  (s_axi_awvalid),   // input wire s_axi_awvalid
        .s_axi_awready  (s_axi_awready),   // output wire s_axi_awready
        .s_axi_wdata    (s_axi_wdata),     // input wire [31 : 0] s_axi_wdata
        .s_axi_wstrb    (s_axi_wstrb),     // input wire [3 : 0] s_axi_wstrb
        .s_axi_wvalid   (s_axi_wvalid),    // input wire s_axi_wvalid
        .s_axi_wready   (s_axi_wready),    // output wire s_axi_wready
        .s_axi_bresp    (s_axi_bresp),     // output wire [1 : 0] s_axi_bresp
        .s_axi_bvalid   (s_axi_bvalid),    // output wire s_axi_bvalid
        .s_axi_bready   (s_axi_bready),    // input wire s_axi_bready
        .s_axi_araddr   (s_axi_araddr),    // input wire [3 : 0] s_axi_araddr
        .s_axi_arvalid  (s_axi_arvalid),   // input wire s_axi_arvalid
        .s_axi_arready  (s_axi_arready),   // output wire s_axi_arready
        .s_axi_rdata    (s_axi_rdata),     // output wire [31 : 0] s_axi_rdata
        .s_axi_rresp    (s_axi_rresp),     // output wire [1 : 0] s_axi_rresp
        .s_axi_rvalid   (s_axi_rvalid),    // output wire s_axi_rvalid
        .s_axi_rready   (s_axi_rready),    // input wire s_axi_rready
        .rx             (rx),              // input wire rx
        .tx             (tx)               // output wire tx
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
