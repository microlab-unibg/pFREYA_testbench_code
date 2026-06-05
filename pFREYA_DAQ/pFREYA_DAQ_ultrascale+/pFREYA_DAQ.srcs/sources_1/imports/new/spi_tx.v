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
    parameter   s_IDLE        = 3'b000;
    parameter   s_WAIT_tCSH0  = 3'b001;
    parameter   s_WAIT_tCSS0  = 3'b010;
    parameter   s_TRANSFER    = 3'b011; 
    parameter   s_WAIT_tCSH1  = 3'b100;
    parameter   s_WAIT_tCSS1  = 3'b101;

    reg [2:0]   r_SM_Main     = s_IDLE;        // State Machine status  
    reg [3:0]   r_Bit_Count   = 15;       
    reg [15:0]  r_Data_Local  = 0;
    reg [1:0]   r_Clock_Count = 0;        
    
    // Contatore attesa CS timing (a 200MHz, 5ns/ciclo)
    parameter tCSH0_DELAY = 6;  // 7 cicli = 35ns
    parameter tCSS0_DELAY = 4;  // 5 cicli = 25ns 
    parameter tCSH1_DELAY = 3;  // 4 cicli = 20ns
    parameter tCSS1_DELAY = 3;  // 4 cicli = 20ns
    reg [3:0]   r_Sys_Delay_Count = 0;

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
                    o_SPI_Cs        <= 1'b1;
                    r_Bit_Count     <= 15;
                    o_SPI_Din       <= 1'b0;
                    r_Sys_Delay_Count <= 0;
                    r_SM_Main         <= s_WAIT_tCSH0; 
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
            
            s_WAIT_tCSH0: begin
                if ( r_Sys_Delay_Count < tCSH0_DELAY ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    o_SPI_Cs          <= 1'b0;
                    r_Sys_Delay_Count <= 0;
                    r_SM_Main         <= s_WAIT_tCSS0;
                end
            end

            s_WAIT_tCSS0: begin
                if ( r_Sys_Delay_Count < tCSS0_DELAY ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    r_Clock_Count     <= 0;
                    o_SPI_Din         <= r_Data_Local[15]; 
                    r_SM_Main         <= s_TRANSFER;
                end
            end

            s_TRANSFER:
            begin
                //if( w_Master_Ready ) 
                    if ( w_Clk_Rising && o_SPI_Sclk == 1'b0 && r_Clock_Count == (CKS_PER_BIT/2 - 1) )
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
                                    r_Sys_Delay_Count <= 0;
                                    r_SM_Main         <= s_WAIT_tCSH1;
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

            s_WAIT_tCSH1: begin
                if ( r_Sys_Delay_Count < tCSH1_DELAY ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    o_SPI_Cs          <= 1'b1; 
                    r_Sys_Delay_Count <= 0;
                    r_SM_Main         <= s_WAIT_tCSS1;
                end
            end

            s_WAIT_tCSS1: begin
                if ( r_Sys_Delay_Count < tCSS1_DELAY ) begin
                    r_Sys_Delay_Count <= r_Sys_Delay_Count + 1'b1;
                end
                else begin
                    r_SM_Main         <= s_IDLE;
                end
            end

            default: r_SM_Main <= s_IDLE;
        endcase
    end

endmodule
