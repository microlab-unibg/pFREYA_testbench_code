// Codice per la dichiarazione del modulo dell'SPI per comunicare con il DAC 

module spi_tx
    #(parameter CKS_PER_BIT=2)
    (
        // Internal clock at 10 MHz
        input i_Clk,
        input [15:0] i_Tx_Data,
        // Input Data Valid
        input i_Tx_DV,   
        
        // Output clock to the DAC at 5 MHz
        output o_SPI_Sclk,
        output o_SPI_Clr,
        output o_SPI_Cs,
        output o_SPI_Din    // For serial transmission
    );

    // Possible transmission states 
    parameter   s_IDLE      = 2'b00;
    parameter   s_TRANSFER  = 2'b01; 

    // State Machine status for main transmission (4 states) 
    reg [1:0]   r_SM_Main = 0;
    reg [3:0]   r_Bit_Count = 0;
    reg [15:0]  r_Data_Local = 0;
    
    wire        w_Master_Ready;

    always @(posedge i_Clk)
    begin
        case(r_SM_Main)
            
            IDLE: 
            begin
                o_SPI_Cs <= 1'b1; 

                if( i_Tx_DV == 1'b1 )
                begin
                    r_Data_Local <= i_Tx_Data;
                    r_SM_Main <= TRANSFER; 
                end
                else
                    r_SM_Main <= s_IDLE;
            end
            
            TRANSFER:
            begin
                if( w_Master_Ready )
                begin
                    o_SPI_Cs <= 1'b1;
                end 
            end 
        default: 
    end

endmodule;