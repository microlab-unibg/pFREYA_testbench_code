`timescale 1ns / 1ps 
// Code to implement behavior of transmission via SPI to DAC 
module spi_tx
    #(parameter CKS_PER_BIT=2)
    (
        // Internal clock at 10 MHz, at least 2X SPI clock
        input         i_Clk,
        // Clock di sistema a 200 MHz per attese CS
        input         i_Sys_Clk,
        input [15:0]  i_Tx_Data,
        input         i_Tx_DV,      // Input Data is Valid
        
        // Output clock to the DAC at 5 MHz
        output  reg o_SPI_Sclk = 1'b0,  // To establish bit reading by the DAC
        output  reg o_SPI_Clr  = 1'b1,  // To reset
        output  reg o_SPI_Cs   = 1'b1,    // To establish transmission
        output  reg o_SPI_Din  = 1'b0  // For serial transmission
    );

    // State Machine states 
    parameter   s_IDLE        = 2'b00;
    parameter   s_TRANSFER    = 2'b01; 
    // Nuovi stati per attese
    parameter   s_WAIT_CS_LOW  = 2'b10;
    parameter   s_WAIT_CS_HIGH = 2'b11;

    reg [1:0]   r_SM_Main     = s_IDLE;        // State Machine status  
    reg [3:0]   r_Bit_Count   = 15;       
    reg [15:0]  r_Data_Local  = 0;
    reg [1:0]   r_Clock_Count = 0;        
    
    // Contatore attesa 15ns (3 cicli a 200MHz)
    reg [1:0]   r_Sys_Delay_Count = 0;

    // Rilevamento fronte i_Clk a 200MHz
    reg         r_Clk_Last = 1'b0;
    always @(posedge i_Sys_Clk) begin
        r_Clk_Last <= i_Clk;
    end
    wire w_Clk_Rising = i_Clk & ~r_Clk_Last;

    //wire        w_Master_Ready;

    always @(posedge i_Sys_Clk)
    begin
        case(r_SM_Main)
            
            s_IDLE: begin
                if( i_Tx_DV )
                  begin
                    // Copy for guaranteed local data integrity 
                    r_Data_Local    <= i_Tx_Data;
                    o_SPI_Cs        <= 1'b0;
                    r_Bit_Count     <= 15;
                    // So that CS is already low on next posedge
                    o_SPI_Din       <= 1'b0;  // First bit is NOT pre-loaded to wait 15ns
                    // Va in attesa CS basso prima di trasmettere
                    r_Sys_Delay_Count <= 0;
                    r_SM_Main         <= s_WAIT_CS_LOW; 
                  end
                else begin
                  r_SM_Main <= s_IDLE;
                  o_SPI_Cs      <= 1'b1; 
                  o_SPI_Sclk    <= 1'b0;
                  r_Bit_Count   <= 15;
                  /*r_Clock_Count <= 1;  prima: se facessi cosi il primo conteggio avverrebbe troppo presto*/

                  r_Clock_Count <= 0; 
                end
            end
            
            s_WAIT_CS_LOW: begin
                // Aspetta 15ns (3 cicli clock 200MHz)
                if ( r_Sys_Delay_Count < 2'd2 ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    r_Clock_Count     <= 0;
                    o_SPI_Din         <= r_Data_Local[15]; // Invia il primo valore di dac_sdin DOPO l'attesa di 15ns!
                    r_SM_Main         <= s_TRANSFER;
                end
            end

            s_TRANSFER:
            begin
                //if( w_Master_Ready ) 
                  //begin
                    if ( o_SPI_Sclk == 0)
                      o_SPI_Din   <= r_Data_Local[r_Bit_Count];

                    // Conteggio sul fronte di salita di i_Clk
                    if ( w_Clk_Rising ) begin
                        if ( r_Clock_Count < (CKS_PER_BIT -1) ) 
                          begin 
                            r_Clock_Count   <= r_Clock_Count + 1'b1;
                          end 
                        else 
                          begin
                            r_Clock_Count   <= 1'b0;  
                            o_SPI_Sclk      <= ~o_SPI_Sclk;

                            if ( o_SPI_Sclk == 1'b1 )   // DAC reads                
                              begin 
                                if ( r_Bit_Count == 0 ) 
                                  begin
                                    // Keep CS low during the 15ns delay, deassert it after the wait
                                    // Va in attesa CS alto prima di IDLE
                                    r_Sys_Delay_Count <= 0;
                                    r_SM_Main         <= s_WAIT_CS_HIGH;
                                  end
                                else 
                                  begin    
                                    r_Bit_Count <= r_Bit_Count - 1'b1;
                                  end 
                              end 
                            //else                        // DAC not reading => update bit 
                            //  begin 
                                //o_SPI_Din   <= r_Data_Local[r_Bit_Count];
                            //  end 
                          end 
                    end
                  //end  
            end 

            s_WAIT_CS_HIGH: begin
                // Aspetta 15ns (3 cicli clock 200MHz)
                if ( r_Sys_Delay_Count < 2'd2 ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    o_SPI_Cs          <= 1'b1; // Alziamo CS a 1 dopo l'attesa di 15ns!
                    r_SM_Main         <= s_IDLE;
                end
            end

            default: r_SM_Main <= s_IDLE;
        endcase
    end

endmodule