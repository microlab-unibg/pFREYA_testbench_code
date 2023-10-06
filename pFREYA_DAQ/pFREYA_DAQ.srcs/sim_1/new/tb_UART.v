`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 09/26/2023 05:08:29 PM
// Design Name: 
// Module Name: tb_uart
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


module tb_uart();
    // Testbench uses a 10 MHz clock
    // Want to interface to 115200 baud UART
    // 10000000 / 115200 = 87 Clocks Per Bit.
    parameter CK_PERIOD    = 100; //ns
    parameter CKS_PER_BIT  = 87;
    parameter BIT_PERIOD   = 8600;

    reg clock = 0;

    reg rx_ser = 1;
    wire [7:0] rx_byte;
    wire rx_dv;

    reg tx_dv = 0;
    reg [7:0] tx_byte = 0;
    wire tx_done;
    wire tx_active;
    wire tx_ser;

    // uart rx
    uart_rx #(.CKS_PER_BIT(CKS_PER_BIT)) uart_rx_inst
    (.i_Clock(clock),
    .i_Rx_Serial(rx_ser),
    .o_Rx_DV(rx_dv),
    .o_Rx_Byte(rx_byte)
    );

    //uart tx
    uart_tx #(.CKS_PER_BIT(CKS_PER_BIT)) uart_tx_inst
    (.i_Clock(clock),
    .i_Tx_DV(tx_dv),
    .i_Tx_Byte(tx_byte),
    .o_Tx_Active(tx_active),
    .o_Tx_Serial(tx_ser),
    .o_Tx_Done(tx_done)
    );

    // Takes in input byte and serializes it 
    task uart_write_byte;
        input [7:0] data;
        integer i;
        begin
            // Send Start Bit
            rx_ser <= 1'b0;
            #(BIT_PERIOD);
            #1000;
            
            // Send Data Byte
            for (i=0; i<8; i=i+1)
            begin
                rx_ser <= data[i];
                #(BIT_PERIOD);
            end
            
            // Send Stop Bit
            rx_ser <= 1'b1;
            #(BIT_PERIOD);
        end
    endtask // UART_WRITE_BYTE

    // base ck
    always begin
        #(CK_PERIOD/2) clock <= !clock;
    end

    initial begin
        #1000 tx_dv = 1'b1;
              tx_byte = 8'hAB;

        #1000 tx_dv = 1'b0;

        #100000 uart_write_byte(8'h3F);
        
        #1000;
    end

endmodule
