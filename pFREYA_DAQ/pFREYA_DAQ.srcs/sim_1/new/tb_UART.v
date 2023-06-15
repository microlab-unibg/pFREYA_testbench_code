`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 06/13/2023 06:17:25 PM
// Design Name: 
// Module Name: tb_UART
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


module tb_UART;
    // AXI 4 interface
    // Slave (actual FPGA code expected)
    reg uart_s_axi_aclk;
    reg uart_s_axi_aresetn;
    reg uart_s_axi_awvalid, uart_s_axi_wvalid, uart_s_axi_bready, uart_s_axi_arvalid, uart_s_axi_rready;
    wire uart_s_axi_awready, uart_s_axi_wready, uart_s_axi_bvalid, uart_s_axi_rvalid, uart_s_axi_arready;
    reg[3:0] uart_s_axi_awaddr, uart_s_axi_araddr;
    reg[31:0] uart_s_axi_wdata;
    wire[31:0] uart_s_axi_rdata;
    reg[3:0] uart_s_axi_wstrb;
    wire[1:0] uart_s_axi_bresp, uart_s_axi_rresp;
    // UART interface
    wire uart_interrupt, uart_rx, uart_tx;
    // example processing
    reg[7:0] data;

    // AXI 4 interface
    // Master (simulating python backend)
    reg uartmaster_s_axi_aclk;
    reg uartmaster_s_axi_aresetn;
    reg uartmaster_s_axi_awvalid, uartmaster_s_axi_wvalid, uartmaster_s_axi_bready, uartmaster_s_axi_arvalid, uartmaster_s_axi_rready;
    wire uartmaster_s_axi_awready, uartmaster_s_axi_wready, uartmaster_s_axi_bvalid, uartmaster_s_axi_rvalid, uartmaster_s_axi_arready;
    reg[3:0] uartmaster_s_axi_awaddr, uartmaster_s_axi_araddr;
    reg[31:0] uartmaster_s_axi_wdata;
    wire[31:0] uartmaster_s_axi_rdata;
    reg[3:0] uartmaster_s_axi_wstrb;
    wire[1:0] uartmaster_s_axi_bresp, uartmaster_s_axi_rresp;
    // UART interface
    wire uartmaster_interrupt, uartmaster_rx, uartmaster_tx;
    // example processing
    reg[7:0] datamaster;

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

    // AXI-UART lite interface
    axi_uartlite_pFREYA axi_uartlite_master (
        .s_axi_aclk    (uartmaster_s_axi_aclk),    // input wire s_axi_aclk
        .s_axi_aresetn (uartmaster_s_axi_aresetn), // input wire s_axi_aresetn
        .interrupt     (uartmaster_interrupt),     // output wire interrupt
        .s_axi_awaddr  (uartmaster_s_axi_awaddr),  // input wire [3 : 0] s_axi_awaddr
        .s_axi_awvalid (uartmaster_s_axi_awvalid), // input wire s_axi_awvalid
        .s_axi_awready (uartmaster_s_axi_awready), // output wire s_axi_awready
        .s_axi_wdata   (uartmaster_s_axi_wdata),   // input wire [31 : 0] s_axi_wdata
        .s_axi_wstrb   (uartmaster_s_axi_wstrb),   // input wire [3 : 0] s_axi_wstrb
        .s_axi_wvalid  (uartmaster_s_axi_wvalid),  // input wire s_axi_wvalid
        .s_axi_wready  (uartmaster_s_axi_wready),  // output wire s_axi_wready
        .s_axi_bresp   (uartmaster_s_axi_bresp),   // output wire [1 : 0] s_axi_bresp
        .s_axi_bvalid  (uartmaster_s_axi_bvalid),  // output wire s_axi_bvalid
        .s_axi_bready  (uartmaster_s_axi_bready),  // input wire s_axi_bready
        .s_axi_araddr  (uartmaster_s_axi_araddr),  // input wire [3 : 0] s_axi_araddr
        .s_axi_arvalid (uartmaster_s_axi_arvalid), // input wire s_axi_arvalid
        .s_axi_arready (uartmaster_s_axi_arready), // output wire s_axi_arready
        .s_axi_rdata   (uartmaster_s_axi_rdata),   // output wire [31 : 0] s_axi_rdata
        .s_axi_rresp   (uartmaster_s_axi_rresp),   // output wire [1 : 0] s_axi_rresp
        .s_axi_rvalid  (uartmaster_s_axi_rvalid),  // output wire s_axi_rvalid
        .s_axi_rready  (uartmaster_s_axi_rready),  // input wire s_axi_rready
        .rx            (uartmaster_rx),            // input wire rx
        .tx            (uartmaster_tx)             // output wire tx
    );

    initial begin
        // slave
        // system
        uart_s_axi_aclk = 1'b0;
        uart_s_axi_aresetn = 1'b0;
        // write
        uart_s_axi_awaddr = 1'b0;
        uart_s_axi_wdata = 32'd0;
        uart_s_axi_awvalid = 1'b0;
        uart_s_axi_bready = 1'b0;
        // read
        uart_s_axi_araddr = 1'b0;
        uart_s_axi_arvalid = 1'b0;
        uart_s_axi_rready = 1'b0;
        // example processing
        data = 32'd0;

        // master
        // system
        uartmaster_s_axi_aclk = 1'b0;
        uartmaster_s_axi_aresetn = 1'b0;
        // write
        uartmaster_s_axi_awaddr = 1'b0;
        uartmaster_s_axi_wdata = 32'd0;
        uartmaster_s_axi_awvalid = 1'b0;
        uartmaster_s_axi_bready = 1'b0;
        // read
        uartmaster_s_axi_araddr = 1'b0;
        uartmaster_s_axi_arvalid = 1'b0;
        uartmaster_s_axi_rready = 1'b0;
        // example processing
        datamaster = 32'd0;
    end

//================SLAVE========================================
    // UART slave ck
    always begin
        forever #1000 assign uart_s_axi_aclk = ~uart_s_axi_aclk;
    end

    // Control UART write regs
    always @(negedge uart_s_axi_awready) begin
        uart_s_axi_awaddr = 32'h00;
        uart_s_axi_wdata = 32'h00;
        uart_s_axi_awvalid = 1'b0;
        uart_s_axi_wvalid = 1'b0;
    end

    // Control UART b regs
    always @(negedge uart_s_axi_bvalid) begin
        uart_s_axi_bready = 1'b0;
    end

    // Control UART read regs
    always @(negedge uart_s_axi_rvalid) begin
        uart_s_axi_arvalid = 1'b0;
        uart_s_axi_rready = 1'b0;
    end

    // example processing on data
    always @(posedge uart_s_axi_aclk) begin
        if (uart_s_axi_rvalid) begin
            data = 8'h01;
        end else begin
            data = data;
        end
    end
//================END SLAVE====================================

//================MASTER=======================================
    // UART master ck
    always begin
        forever #500 assign uartmaster_s_axi_aclk = ~uartmaster_s_axi_aclk;
    end

    // Control UART write regs
    always @(negedge uartmaster_s_axi_awready) begin
        uartmaster_s_axi_awaddr = 32'h00;
        uartmaster_s_axi_wdata = 32'h00;
        uartmaster_s_axi_awvalid = 1'b0;
        uartmaster_s_axi_wvalid = 1'b0;
    end

    // Control UART b regs
    always @(negedge uartmaster_s_axi_bvalid) begin
        uartmaster_s_axi_bready = 1'b0;
    end

    // Control UART read regs
    always @(negedge uartmaster_s_axi_rvalid) begin
        uartmaster_s_axi_arvalid = 1'b0;
        uartmaster_s_axi_rready = 1'b0;
    end

    // example processing on data
    always @(posedge uartmaster_s_axi_aclk) begin
        if (uartmaster_s_axi_rvalid) begin
            data = 8'h01;
        end else begin
            data = data;
        end
    end
//================END MASTER===================================

    // DUT testing
    always begin
        #9000 uart_s_axi_aresetn = 1'b1;
            uartmaster_s_axi_aresetn = 1'b1;
        // set ctrl register (h08)
        // first prepare reg address to write to
        // then prepare data to be written
        // then signal that you are ready to send
        #10000 uart_s_axi_awaddr = 4'h0C;
            // reserved, interrupt, reserved, clear rx fifo, clear tx fifo
            uart_s_axi_wdata = {27'd0, 1'b0, 2'b00, 1'b1, 1'b1};
            uart_s_axi_awvalid = 1'b1;
            uart_s_axi_wvalid = 1'b1;
            uart_s_axi_bready = 1'b1;

            uartmaster_s_axi_awaddr = 4'h0C;
            // reserved, interrupt, reserved, clear rx fifo, clear tx fifo
            uartmaster_s_axi_wdata = {27'd0, 1'b0, 2'b00, 1'b1, 1'b1};
            uartmaster_s_axi_awvalid = 1'b1;
            uartmaster_s_axi_wvalid = 1'b1;
            uartmaster_s_axi_bready = 1'b1;
        
        // master transmit a word (h04)
        #10000 uartmaster_s_axi_awaddr = 4'h04;
            // reserved, word
            uartmaster_s_axi_wdata = {27'd0, 8'h000F};
            uartmaster_s_axi_awvalid = 1'b1;
            uartmaster_s_axi_wvalid = 1'b1;
            uartmaster_s_axi_bready = 1'b1;

        // check status
        #10000 uartmaster_s_axi_araddr = 4'h08;
            // reserved, word
            uartmaster_s_axi_arvalid = 1'b1;
            uartmaster_s_axi_rready = 1'b1;
        // slave receive example word (h00)
        // same as above
        #10000 uart_s_axi_araddr = 4'h00;
            // reserved, word
            uart_s_axi_arvalid = 1'b1;
            uart_s_axi_rready = 1'b1;
        #20000 uart_s_axi_aresetn = 1'b1;
            uartmaster_s_axi_aresetn = 1'b1;
        $stop;
    end
endmodule
