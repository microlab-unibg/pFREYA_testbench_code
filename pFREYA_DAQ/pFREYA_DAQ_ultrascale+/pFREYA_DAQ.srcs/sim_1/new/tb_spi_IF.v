`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 14.04.2026 14:38:19
// Design Name: 
// Module Name: tb_spi_IF
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



module tb_spi_IF;

    // ingressi
    reg dac_clk;
    reg [15:0] tx_data;
    reg tx_dv;

    // uscite
    wire dac_sclk;
    wire dac_clr;
    wire dac_cs;
    wire dac_din;

    // clock 10 ns a periodo
    always #5 dac_clk = ~dac_clk;

    spi_IF uut (
        .dac_clk(dac_clk),
        .tx_data(tx_data),
        .tx_dv(tx_dv),
        .dac_sclk(dac_sclk),
        .dac_clr(dac_clr),
        .dac_cs(dac_cs),
        .dac_din(dac_din)
    );

    initial begin
        // inizializzazione
        dac_clk = 0;
        tx_data = 16'h0000;
        tx_dv = 0;

        // Aspetta che il GSR (Global Set/Reset) di Xilinx si rilasci.
        // In post-synthesis simulation, il GSR blocca tutti i FF per 100ns
        // (ROC_WIDTH = 100000 ps nel modulo glbl). Bisogna aspettare oltre
        // quel periodo prima di applicare stimoli, altrimenti vengono ignorati.
        #200;

        // invia un dato
        tx_data = 16'hA5A5;
        tx_dv = 1;
        #10;
        tx_dv = 0;

        // aspetta fine trasmissione
        #1000;

        $finish;
    end

endmodule
