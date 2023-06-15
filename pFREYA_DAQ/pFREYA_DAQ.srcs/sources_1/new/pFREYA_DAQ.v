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
    input  uart_clk
);

    // UART 16550 interface
    // TODO port connection
    axi_uart16550_pFREYA axi_uart16550_pFREYA_inst (
        .s_axi_aclk    (uart_s_axi_aclk),    // input wire s_axi_aclk
        .s_axi_aresetn (uart_s_axi_aresetn), // input wire s_axi_aresetn
        .ip2intc_irpt  (uart_ip2intc_irpt),  // output wire ip2intc_irpt
        .freeze        (uart_freeze),        // input wire freeze
        .s_axi_awaddr  (uart_s_axi_awaddr),  // input wire [12 : 0] s_axi_awaddr
        .s_axi_awvalid (uart_s_axi_awvalid), // input wire s_axi_awvalid
        .s_axi_awready (uart_s_axi_awready), // output wire s_axi_awready
        .s_axi_wdata   (uart_s_axi_wdata),   // input wire [31 : 0] s_axi_wdata
        .s_axi_wstrb   (uart_s_axi_wstrb),   // input wire [3 : 0] s_axi_wstrb
        .s_axi_wvalid  (uart_s_axi_wvalid),  // input wire s_axi_wvalid
        .s_axi_wready  (uart_s_axi_wready),  // output wire s_axi_wready
        .s_axi_bresp   (uart_s_axi_bresp),   // output wire [1 : 0] s_axi_bresp
        .s_axi_bvalid  (uart_s_axi_bvalid),  // output wire s_axi_bvalid
        .s_axi_bready  (uart_s_axi_bready),  // input wire s_axi_bready
        .s_axi_araddr  (uart_s_axi_araddr),  // input wire [12 : 0] s_axi_araddr
        .s_axi_arvalid (uart_s_axi_arvalid), // input wire s_axi_arvalid
        .s_axi_arready (uart_s_axi_arready), // output wire s_axi_arready
        .s_axi_rdata   (uart_s_axi_rdata),   // output wire [31 : 0] s_axi_rdata
        .s_axi_rresp   (uart_s_axi_rresp),   // output wire [1 : 0] s_axi_rresp
        .s_axi_rvalid  (uart_s_axi_rvalid),  // output wire s_axi_rvalid
        .s_axi_rready  (uart_s_axi_rready),  // input wire s_axi_rready
        .baudoutn      (uart_baudoutn),      // output wire baudoutn
        .ctsn          (uart_ctsn),          // input wire ctsn
        .dcdn          (uart_dcdn),          // input wire dcdn
        .ddis          (uart_ddis),          // output wire ddis
        .dsrn          (uart_dsrn),          // input wire dsrn
        .dtrn          (uart_dtrn),          // output wire dtrn
        .out1n         (uart_out1n),         // output wire out1n
        .out2n         (uart_out2n),         // output wire out2n
        .rin           (uart_rin),           // input wire rin
        .rtsn          (uart_rtsn),          // output wire rtsn
        .rxrdyn        (uart_rxrdyn),        // output wire rxrdyn
        .sin           (uart_sin),           // input wire sin
        .sout          (uart_sout),          // output wire sout
        .txrdyn        (uart_txrdyn)         // output wire txrdyn
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
