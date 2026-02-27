// Code to implement behavior of transmission via SPI to DAC 

module spi_tx
    #(parameter CKS_PER_BIT=2)
    (
        // Internal clock at 10 MHz, at least 2X SPI clock
        input i_Clk,
        input [15:0] i_Tx_Data,
        // Input Data Valid
        input i_Tx_DV,   
        
        // Output clock to the DAC at 5 MHz
        output o_SPI_Sclk,  // To establish bit reading by the DAC
        output o_SPI_Clr,   // To reset
        output o_SPI_Cs,    // To establish transmission
        output o_SPI_Din    // For serial transmission
    );

    // Possible transmission states 
    parameter   s_IDLE      = 2'b00;
    parameter   s_TRANSFER  = 2'b01; 

    // State Machine status for main transmission (4 states) 
    reg [1:0]   r_SM_Main = 0;
    reg [3:0]   r_Bit_Count = 16;
    reg [15:0]  r_Data_Local = 0;
    reg [3:0]   r_Data_Index = 0;
    reg [1:0]   r_Clock_Count = 0;
    
    wire        w_Master_Ready;

    always @(posedge i_Clk)
    begin
        case(r_SM_Main)
            
            IDLE: 
            begin
                o_SPI_Cs <= 1'b1; 

                if( i_Tx_DV == 1'b1 )
                begin
                    // Copy for guaranteed local data integrity 
                    r_Data_Local    <= i_Tx_Data;
                    // So that CS is already low on next posedge
                    o_SPI_Cs        <= 1'b0;
                    r_SM_Main       <= TRANSFER; 
                end
                else
                    r_SM_Main <= s_IDLE;
            end
            
            TRANSFER:
            begin
                if( w_Master_Ready )
                begin
                    if ( r_Clock_Count < CKS_PER_BIT )
                    begin
                        o_SPI_Din       <= r_Data_Local[r_Data_Index];
                        r_Clock_Count   <= r_Clock_Count + 1'b1;
                    end
                    else 
                    begin
                        r_Bit_Count     <= r_Bit_Count - 1'b1;
                        r_Clock_Count   <= 1'b0;  
                    end 
                end 
            end 
        default: 
    end

endmodule;