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
        // UART Lite interface
        // TODO port connection
        axi_uartlite_IP UartLite_IF (
            .s_axi_aclk(s_axi_aclk),        // input wire s_axi_aclk
            .s_axi_aresetn(s_axi_aresetn),  // input wire s_axi_aresetn
            .interrupt(interrupt),          // output wire interrupt
            .s_axi_awaddr(s_axi_awaddr),    // input wire [3 : 0] s_axi_awaddr
            .s_axi_awvalid(s_axi_awvalid),  // input wire s_axi_awvalid
            .s_axi_awready(s_axi_awready),  // output wire s_axi_awready
            .s_axi_wdata(s_axi_wdata),      // input wire [31 : 0] s_axi_wdata
            .s_axi_wstrb(s_axi_wstrb),      // input wire [3 : 0] s_axi_wstrb
            .s_axi_wvalid(s_axi_wvalid),    // input wire s_axi_wvalid
            .s_axi_wready(s_axi_wready),    // output wire s_axi_wready
            .s_axi_bresp(s_axi_bresp),      // output wire [1 : 0] s_axi_bresp
            .s_axi_bvalid(s_axi_bvalid),    // output wire s_axi_bvalid
            .s_axi_bready(s_axi_bready),    // input wire s_axi_bready
            .s_axi_araddr(s_axi_araddr),    // input wire [3 : 0] s_axi_araddr
            .s_axi_arvalid(s_axi_arvalid),  // input wire s_axi_arvalid
            .s_axi_arready(s_axi_arready),  // output wire s_axi_arready
            .s_axi_rdata(s_axi_rdata),      // output wire [31 : 0] s_axi_rdata
            .s_axi_rresp(s_axi_rresp),      // output wire [1 : 0] s_axi_rresp
            .s_axi_rvalid(s_axi_rvalid),    // output wire s_axi_rvalid
            .s_axi_rready(s_axi_rready),    // input wire s_axi_rready
            .rx(rx),                        // input wire rx
            .tx(tx)                         // output wire tx
        );
    );
endmodule
