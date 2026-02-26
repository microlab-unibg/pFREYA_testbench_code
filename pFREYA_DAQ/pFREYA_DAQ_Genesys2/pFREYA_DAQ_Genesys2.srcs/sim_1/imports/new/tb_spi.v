`timescale 1ns / 1ps
// This module contains the code for the SPI communication protocol with the DAC

module tb_spi();

    parameter 
    // Testbench uses a 10 MHz clock    => periodo  100 ns 
    // DAC works at 25 MHz              => periodo  40  ns
    parameter CKS_PER_BIT = 2;

    logic chip_select,
    logic clk,




/* //////////////////   APPUNTI     /////////////////////////// 
    CS va giu per dire a slave che inizia comunicazione
    SCLK parte per settare clock 
    DIN data input 

    CLR pulire l'input 





*/
