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
`include "../../sources_1/new/pFREYA_defs.sv"

module tb_pFREYA_DAQ;
    // ASIC params
    parameter GENERAL_CK_PERIOD = 10;
    
    // UART params
    parameter UART_CKS_PER_BIT = 87;
    parameter UART_CK_PERIOD = 100;
    parameter UART_BIT_PERIOD = 8600;
    

//===========DAQ======================================
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
    reg  daq_ck;
    reg  btn_reset;
    reg  cmd_available;
    reg  data_available;
    // for UART
    reg  [UART_PACKET_SIZE-1:0] uart_data;
    reg  uart_valid;

    // UART signals
    reg  uart_ck;
    reg  rx_ser;
    //output [UART_PACKET_SIZE-1:0] rx_byte, -> uart_data
    //output rx_dv, -> uart_valid

    reg  tx_dv;
    reg  [UART_PACKET_SIZE-1:0] tx_byte;
    wire tx_done, tx_active, tx_ser;
//===========END DAQ==================================

//=========== tb SIGNALS =============================
    // UART signals
    // reg  uart_ck_master;
    // wire [UART_PACKET_SIZE-1:0] rx_byte_master;
    // wire rx_dv_master;

    // reg  tx_dv_master;
    // reg  [UART_PACKET_SIZE-1:0] tx_byte_master;
    // wire tx_done_master, tx_active_master;
    reg [UART_PACKET_SIZE-1:0] uart_to_send;
//=========== END tb SIGNALS =========================

    // // Simple UART
    // uart_IF uart_IF_inst (
    //     .uart_ck    (uart_ck),
    //     .rx_ser     (tx_ser),
    //     .rx_dv      (rx_dv_master),
    //     .rx_byte    (rx_byte_master),
    //     .tx_dv      (tx_dv_master),
    //     .tx_byte    (tx_byte_master),
    //     .tx_active  (tx_active_master),
    //     .tx_ser     (rx_ser),
    //     .tx_done    (tx_done_master)
    // );

    // pFREYA_DAQ interface (integrating UART)
    pFREYA_DAQ #(.CKS_PER_BIT(UART_CKS_PER_BIT)) pFREYA_DAQ_inst (
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
        .daq_ck             (daq_ck),
        .btn_reset          (btn_reset),
        .uart_data          (uart_data),
        .uart_valid         (uart_valid),
        .cmd_available      (cmd_available),
        .data_available     (data_available),
        // UART
        .uart_ck            (uart_ck),
        .rx_ser             (rx_ser),
        .tx_dv              (tx_dv),
        .tx_byte            (tx_byte),
        .tx_active          (tx_active),
        .tx_ser             (tx_ser),
        .tx_done            (tx_done)
    );

//=========== TASKS ==================================
// Takes in input byte and serializes it 
    task uart_write_byte;
        input [UART_PACKET_SIZE-1:0] data;
        integer i;
        begin
            // Send Start Bit
            rx_ser <= 1'b0;
            #(UART_BIT_PERIOD);
            #1000;
            
            // Send Data Byte
            for (i=0; i<8; i=i+1)
            begin
                rx_ser <= data[i];
                #(UART_BIT_PERIOD);
            end
            
            // Send Stop Bit
            rx_ser <= 1'b1;
            #(UART_BIT_PERIOD);
        end
    endtask // UART_WRITE_BYTE

// Takes generates and send slow ctrl data
    task uart_slow_ctrl_send;
        integer i;
        reg [32-1:0] uart_slow_ctrl_packet_temp; // urandom generates 32 bits
        begin
            cmd_available <= 1'b0;
            data_available <= 1'b0;

            uart_slow_ctrl_packet_temp <= $urandom(42069); // 42 is the seed and the packet is repeated for each pixel
            #10;
            // Send slow ctrl packet
            // must be done 15 times (see defs) with 0 as first bit
            for (i=0; i<=14; i=i+1)
            begin
                uart_to_send[6:0] <= uart_slow_ctrl_packet_temp[6:0]; // last 7 bits
                #10;
                uart_to_send[7] <= NOTLAST_SLOW_CTRL_PACKET; // first bit
                #10;
                uart_write_byte(uart_to_send);
                #20000;
            end
            
            // Send last packet (16th)
            uart_to_send[6:0] <= uart_slow_ctrl_packet_temp[6:0]; // last 7 bits
            #10;
            uart_to_send[7] <= LAST_SLOW_CTRL_PACKET; // first bit
            #10;
            cmd_available <= 1'b0;
            data_available <= 1'b1;
            uart_write_byte(uart_to_send);
            #20000;
        end
    endtask // uart_slow_ctrl_send
//=========== END TASKS ===============================

    // send command process
    

    // read data process
    

    // simulate the event
    

    // simulate the SPI
    
    
    // setup initial values of all signals
    initial begin
        // tb UART
        // uart_ck <= 1'b0;
        // tx_dv_master <= '0;
        // tx_byte_master <= '0;
        uart_to_send <= '0;

        // DAQ - pFREYA_IF
        ser_out <= 1'b0;
        daq_ck <= 1'b0;
        btn_reset <= 1'b1;
        uart_data <= '0;
        uart_valid <= 1'b0;
        // DAQ - UART
        uart_ck <= 1'b0;
        rx_ser <= 1'b1;
        tx_dv <= 1'b0;
        tx_byte <= '0;
        cmd_available <= 1'b0;
        data_available <= 1'b0;
    end

    // ASIC ck
    always begin
        forever #(GENERAL_CK_PERIOD/2) daq_ck = ~daq_ck;
    end

    // UART ck
    always begin
        forever #(UART_CK_PERIOD/2) uart_ck = ~uart_ck;
    end

    // UART master ck
    // always begin
    //     forever #(UART_CK_PERIOD) uart_ck_master = ~uart_ck_master;
    // end

// exercise the DUT
    always begin
        // reset the DUT
        #100 btn_reset <= 1'b0;
        // send a command to set selection divider
        // CMD packet is |CMD_CODE(4)|SIGNAL_CODE(3)|PADDING(1)|
        #100 uart_to_send <= {`SET_CK_CMD,`SEL_CK_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              uart_write_byte(uart_to_send);
        // set selection divider
        // DATA packet is |DATA(8)|
        #20000 uart_to_send <= 5;
        #1000 cmd_available <= 1'b0;
               data_available <= 1'b1;
               uart_write_byte(uart_to_send);

        // send a command to set sel_init_n delay divider
        #20000 uart_to_send <= {`SET_PIXEL_CMD,`PIXEL_ROW_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);
        // set sel_init_n delay divider
        #20000 uart_to_send <= 7;
        #1000 cmd_available <= 1'b0;
               data_available <= 1'b1;
               uart_write_byte(uart_to_send);
        // send a command to set sel_init_n delay divider
        #20000 uart_to_send <= {`SET_PIXEL_CMD,`PIXEL_COL_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);
        // set sel_init_n delay divider
        #20000 uart_to_send <= 7;
        #1000 cmd_available <= 1'b0;
               data_available <= 1'b1;
               uart_write_byte(uart_to_send);
        
        // sel pixel
        // signal is not used
        #20000 uart_to_send <= {`SEND_PIXEL_SEL_CMD,`UNUSED_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);

        // // send a command to set sel_init_n delay divider
        // #20000 uart_to_send <= {`SET_DELAY_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set sel_init_n delay divider
        // #20000 uart_to_send <= 2;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);
        // // send a command to set sel_init_n high divider
        // #20000 uart_to_send <= {`SET_HIGH_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set sel_init_n high divider
        // #20000 uart_to_send <= 100;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);
        // // send a command to set sel_init_n low divider
        // #20000 uart_to_send <= {`SET_LOW_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set sel_init_n low divider
        // #20000 uart_to_send <= 7;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);

        // send a command to set slow ctrl word
        // signal is not used
        #20000 uart_to_send <= {`SET_SLOW_CTRL_CMD,`UNUSED_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);
        // set slow ctrl word
        #20000 uart_slow_ctrl_send();
        
        // send a command to set slow ctrl div
        #20000 uart_to_send <= {`SET_CK_CMD,`SLOW_CTRL_CK_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);
        // set slow ctrl div
        #20000 uart_to_send <= 5;
        #1000 cmd_available <= 1'b0;
               data_available <= 1'b1;
               uart_write_byte(uart_to_send);
        
        // send a command to send slow ctrl
        #20000 uart_to_send <= {`SEND_SLOW_CTRL_CMD,`UNUSED_CODE,`CMD_PADDING};
        #1000 cmd_available <= 1'b1;
              data_available <= 1'b0;
              uart_write_byte(uart_to_send);
        
        // // swnd slow ctrl
        // #20000 uart_to_send <= 5;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);

        // // send a command to set slow_ctrl_init_n delay divider
        // #20000 uart_to_send <= {`SET_DELAY_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set slow_ctrl_init_n delay divider
        // #20000 uart_to_send <= 2;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);
        // // send a command to set slow_ctrl_init_n high divider
        // #20000 uart_to_send <= {`SET_HIGH_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set slow_ctrl_init_n high divider
        // #20000 uart_to_send <= 100;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);
        // // send a command to set slow_ctrl_init_n low divider
        // #20000 uart_to_send <= {`SET_LOW_CMD,`SEL_INIT_N_CODE,`CMD_PADDING};
        // #1000 cmd_available <= 1'b1;
        //       data_available <= 1'b0;
        //       uart_write_byte(uart_to_send);
        // // set slow_ctrl_init_n low divider
        // #20000 uart_to_send <= 7;
        // #1000 cmd_available <= 1'b0;
        //        data_available <= 1'b1;
        //        uart_write_byte(uart_to_send);
        
        #100000 cmd_available <= 1'b0;
                data_available <= 1'b0;
                $stop;
    end
endmodule