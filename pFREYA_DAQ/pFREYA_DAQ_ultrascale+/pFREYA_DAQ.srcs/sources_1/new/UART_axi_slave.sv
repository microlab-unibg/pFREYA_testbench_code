`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 06/15/2023 03:35:40 PM
// Design Name: 
// Module Name: UART_slave
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments: Testing UARTlite interface with the board
// 
//////////////////////////////////////////////////////////////////////////////////


module UART_test(
        input logic uart_s_axi_aclk,
        input logic uart_s_axi_aresetn,
        input reg enable_read, enable_write,
        input reg data_read_available, data_write_available,
        input logic[7:0] data_write,
        output logic[7:0] data_read
    );

    // AXI 4 interface
    logic uart_s_axi_awvalid, uart_s_axi_wvalid, uart_s_axi_bready, uart_s_axi_arvalid, uart_s_axi_rready;
    wire uart_s_axi_awready, uart_s_axi_wready, uart_s_axi_bvalid, uart_s_axi_rvalid, uart_s_axi_arready;
    logic[3:0] uart_s_axi_awaddr, uart_s_axi_araddr;
    logic[31:0] uart_s_axi_wdata;
    wire[31:0] uart_s_axi_rdata;
    logic[3:0] uart_s_axi_wstrb;
    wire[1:0] uart_s_axi_bresp, uart_s_axi_rresp;
    // UART interface
    wire uart_interrupt, uart_rx, uart_tx;

    // AXI-UART lite interface
    axi_uartlite_pFREYA axi_uartlite_inst (
        .s_axi_aclk    (uart_s_axi_aclk),    // input wire s_axi_aclk
        .s_axi_aresetn (uart_s_axi_aresetn), // input wire s_axi_aresetn
        .interrupt     (uart_interrupt),     // output wire interrupt
        .s_axi_awaddr  (uart_s_axi_awaddr),  // input wire [3 : 0] s_axi_awaddr
        .s_axi_awvalid (uart_s_axi_awvalid), // input wire s_axi_awvalid
        .s_axi_awready (uart_s_axi_awready), // output wire s_axi_awready
        .s_axi_wdata   (uart_s_axi_wdata),   // input wire [31 : 0] s_axi_wdata
        .s_axi_wstrb   (uart_s_axi_wstrb),   // input wire [3 : 0] s_axi_wstrb
        .s_axi_wvalid  (uart_s_axi_wvalid),  // input wire s_axi_wvalid
        .s_axi_wready  (uart_s_axi_wready),  // output wire s_axi_wready
        .s_axi_bresp   (uart_s_axi_bresp),   // output wire [1 : 0] s_axi_bresp
        .s_axi_bvalid  (uart_s_axi_bvalid),  // output wire s_axi_bvalid
        .s_axi_bready  (uart_s_axi_bready),  // input wire s_axi_bready
        .s_axi_araddr  (uart_s_axi_araddr),  // input wire [3 : 0] s_axi_araddr
        .s_axi_arvalid (uart_s_axi_arvalid), // input wire s_axi_arvalid
        .s_axi_arready (uart_s_axi_arready), // output wire s_axi_arready
        .s_axi_rdata   (uart_s_axi_rdata),   // output wire [31 : 0] s_axi_rdata
        .s_axi_rresp   (uart_s_axi_rresp),   // output wire [1 : 0] s_axi_rresp
        .s_axi_rvalid  (uart_s_axi_rvalid),  // output wire s_axi_rvalid
        .s_axi_rready  (uart_s_axi_rready),  // input wire s_axi_rready
        .rx            (uart_rx),            // input wire rx
        .tx            (uart_tx)             // output wire tx
    );

    // prepare read data procedure
    always_ff @(posedge uart_s_axi_aclk) begin : set_read_data_axi
        if (enable_read) begin
            uart_s_axi_araddr <= 4'h08;
            uart_s_axi_arvalid <= 1'b1;
            uart_s_axi_rready <= 1'b1;
            data_read_available <= 1'b0;
        end else begin
            uart_s_axi_araddr <= 4'h00;
            uart_s_axi_arvalid <= 1'b0;
            uart_s_axi_rready <= 1'b0;
            data_read_available <= 1'b0;
        end
    end

    // read data procedure
    always_ff @(posedge uart_s_axi_aclk) begin : read_data_axi
        if (uart_s_axi_rvalid) begin
            data_read <= uart_s_axi_rdata;
            data_read_available <= 1'b1;
            enable_read <= 1'b0;
        end else begin
            data_read <= data_read;
            data_read_available <= 1'b0;
        end
    end

    // write data procedure
    always_ff @(posedge uart_s_axi_aclk) begin : write_data_axi
        if (enable_write) begin
            uart_s_axi_awaddr <= 4'h08;
            uart_s_axi_wdata <= data_write;
            uart_s_axi_awvalid <= 1'b1;
            uart_s_axi_wvalid <= 1'b1;
            uart_s_axi_bready <= 1'b1;
            data_write_available <= 1'b1;
        end else begin
            uart_s_axi_awaddr <= 4'h00;
            uart_s_axi_wdata <= 32'd0;
            uart_s_axi_awvalid <= 1'b0;
            uart_s_axi_wvalid <= 1'b0;
            uart_s_axi_bready <= 1'b0;
            data_write_available <= 1'b0;
        end
    end

    // after write data procedure
    always_ff @(posedge uart_s_axi_aclk) begin : after_write_data_axi
        if (uart_s_axi_bvalid) begin
            uart_s_axi_awaddr <= 4'h00;
            uart_s_axi_wdata <= 32'd0;
            uart_s_axi_awvalid <= 1'b0;
            uart_s_axi_wvalid <= 1'b0;
            uart_s_axi_bready <= 1'b0;
            enable_write <= 1'b0;
        end else begin
            uart_s_axi_awaddr <= uart_s_axi_awaddr;
            uart_s_axi_wdata <= uart_s_axi_wdata;
            uart_s_axi_awvalid <= uart_s_axi_awvalid;
            uart_s_axi_wvalid <= uart_s_axi_wvalid;
            uart_s_axi_bready <= uart_s_axi_bready;
            enable_write <= enable_write;
        end
    end
endmodule

