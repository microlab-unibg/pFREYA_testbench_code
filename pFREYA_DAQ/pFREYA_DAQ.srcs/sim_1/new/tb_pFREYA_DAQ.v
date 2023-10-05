`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 09/26/2023 06:04:56 PM
// Design Name: 
// Module Name: tb_pFREYA_DAQ
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

module tb_pFREYA_DAQ;
    // ASIC params
    parameter GENERAL_CK_NS = 10;
    
    // UART params
    parameter UART_CK_NS = 100;
    parameter UART_BIT_PERIOD = 8600;

    reg ck;

    // ASIC signals
    wire dac_sdin, dac_sync_n, dac_sck;
    wire sel_init_n;
    wire sel_ckcol, sel_ckrow;
    reg  ser_out;
    wire ser_read, ser_reset_n;
    wire ser_ck;
    wire inj_stb;
    wire csa_reset_n;
    wire adc_ck, adc_start;
    wire sh_phi1d_sup, sh_phi1d_inf;
    wire slow_ctrl_in, slow_ctrl_reset_n, slow_ctrl_ck;
    // Internal signals
    reg  btn_reset;
    // UART signals
    reg uart_ck;
    reg rx_ser;
    wire [7:0] rx_byte;
    wire rx_dv;

    reg tx_dv;
    reg [7:0] tx_byte;
    wire tx_done, tx_active, tx_ser;

    // tb signals
    

    // Simple UART
    uart_IF uart_IF_inst (
        .uart_ck   (uart_ck),
        .rx_ser     (rx_ser),
        .rx_dv      (rx_dv),
        .rx_byte    (rx_byte),
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
        .ck                 (ck),
        .reset              (btn_reset)
    );

    // send command process


    // read data process
    

    // simulate the event
    

    // simulate the SPI
    
    
    // setup initial values of all signals
    initial begin
        ck = 1'b0;
        uart_ck = 1'b0;

        ser_out <= 1'b0;
        // Internal signals
        btn_reset <= 1'b1;
        // UART signals
        rx_ser <= 1'b1;

        tx_dv <= 1'b0;
        tx_byte <= 8'b00;
    end

    // ASIC ck
    always begin
        forever #(GENERAL_CK_NS) ck = ~ck;
    end

    // UART ck
    always begin
        forever #(UART_CK_NS) uart_ck = ~uart_ck;
    end

// exercise the DUT
    always begin
        #100 btn_reset <=1'b0;
        #100000;
        $stop;
    end
endmodule