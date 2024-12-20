`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
// 
// Create Date: 05/10/2023 12:08:58 PM
// Design Name: 
// Module Name: pFREYA_IF
// Project Name: pFREYA_DAQ
// Target Devices: KCU116
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

`include "pFREYA_defs.sv"

module pFREYA_IF(
        output logic dac_sdin, 
        output logic dac_sync_n, 
        output logic dac_sck,
        output logic sel_init_n,
        output logic sel_ckcol, 
        output logic sel_ckrow,
        input  logic ser_out,
        output logic ser_read, 
        output logic ser_reset_n,
        output logic ser_ck,
        output logic inj_stb,
        output logic csa_reset_n,
        output logic adc_ck,
        output logic adc_start,
        output logic sh_phi1d_sup,
        output logic sh_phi1d_inf,
        output logic slow_ctrl_in,
        output logic slow_ctrl_reset_n,
        output logic slow_ctrl_ck,
        // internal
        input  logic ck,
        input  logic reset,
        // for UART
        input  logic [UART_PACKET_SIZE-1:0] uart_data,
        input  logic uart_valid
    );

    // state machine code
    (* syn_encoding = "one-hot" *) enum logic [9:0] {
        CMD_ERR,
        CMD_EVAL,
        CMD_READ_DATA,
        CMD_SEL_PIX,
        CMD_SEND_DAC,
        CMD_SEND_SLOW,
        CMD_SET_LONG,
        CMD_SET,
        CMD_SYNC_TIME_BASE,
        RESET
    } state, next;

    // CK internal
    // generated with counters that reach a divisor
    logic [CK_CNT_N-1:0] slow_ctrl_cnt = -1;
    logic [CK_CNT_N-1:0] slow_ctrl_div= '0;
    logic [CK_CNT_N-1:0] sel_cnt = -1;
    logic [CK_CNT_N-1:0] sel_div= '0;
    logic [CK_CNT_N-1:0] adc_cnt = -1;
    logic [CK_CNT_N-1:0] adc_div= '0;
    logic [CK_CNT_N-1:0] inj_cnt = -1;
    logic [CK_CNT_N-1:0] inj_div= '0;
    logic [CK_CNT_N-1:0] ser_cnt = -1;
    logic [CK_CNT_N-1:0] ser_div= '0;
    logic [CK_CNT_N-1:0] dac_sck_cnt = -1;
    logic [CK_CNT_N-1:0] dac_sck_div= '0;
    // for selection
    logic sel_ck = 1'b0; // internal clock temporisation
    logic [PIXEL_COL_N-1:0] sel_ckcol_cnt= '0;
    logic [PIXEL_ROW_N-1:0] sel_ckrow_cnt= '0;
    // for injection
    logic inj_start = 1'b0;
    // for slow ctrl
    logic slow_ctrl_mask = 1'b0;
    logic slow_ctrl_reset_request = 1'b0;
    // for sh inf (TS)
    logic sh_phi1d_inf_mask = 1'b0;
    logic slow_ctrl_in_mask = 1'b0;
    logic sh_phi1d_inf = 1'b0;
    // fast control timing
    // generated with counter that reach a divisor, where the divisor changes based on flag
    // flag value is 0 for delay, 1 for HIGH, 2 for LOW (the actual polarity is in the name of the signal)
    logic [FAST_CTRL_FLAG_N-1:0] csa_reset_n_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_FLAG_N-1:0] sh_phi1d_inf_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_FLAG_N-1:0] sh_phi1d_sup_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_FLAG_N-1:0] adc_start_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_FLAG_N-1:0] ser_reset_n_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_FLAG_N-1:0] ser_read_flag = FAST_CTRL_DELAY;
    logic [FAST_CTRL_N-1:0] csa_reset_n_cnt = -1;
    logic [FAST_CTRL_N-1:0] csa_reset_n_delay_div= '0;
    logic [FAST_CTRL_N-1:0] csa_reset_n_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] csa_reset_n_LOW_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_inf_cnt = -1;
    logic [FAST_CTRL_N-1:0] sh_phi1d_inf_delay_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_inf_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_inf_LOW_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_sup_cnt = -1;
    logic [FAST_CTRL_N-1:0] sh_phi1d_sup_delay_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_sup_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] sh_phi1d_sup_LOW_div= '0;
    logic [FAST_CTRL_N-1:0] adc_start_cnt = -1;
    logic [FAST_CTRL_N-1:0] adc_start_delay_div= '0;
    logic [FAST_CTRL_N-1:0] adc_start_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] adc_start_LOW_div= '0;
    logic [FAST_CTRL_N-1:0] ser_reset_n_cnt = -1;
    logic [FAST_CTRL_N-1:0] ser_reset_n_delay_div= '0;
    logic [FAST_CTRL_N-1:0] ser_reset_n_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] ser_reset_n_LOW_div= '0;
    logic [FAST_CTRL_N-1:0] ser_read_cnt = -1;
    logic [FAST_CTRL_N-1:0] ser_read_delay_div= '0;
    logic [FAST_CTRL_N-1:0] ser_read_HIGH_div= '0;
    logic [FAST_CTRL_N-1:0] ser_read_LOW_div= '0;

    // control logic
    logic data_packet_available = 1'b0;
    logic slow_ctrl_packet_available = 1'b0;
    logic slow_ctrl_packet_sent = 1'b0;
    logic dac_packet_available = 1'b0;
    logic dac_packet_sent = 1'b0;
    logic sel_ckcol_sent = 1'b0;
    logic sel_ckrow_sent = 1'b0;
    logic sync_time_base_flag = 1'b0;
    // data
    logic [PACKET_INDEX_N-1:0] data_packet_index_send= '0;
    logic [PACKET_INDEX_N-1:0] data_packet_index_receive= '0;

    reg [DATA_REG_LENGTH-1:0] data_packet= '0;

    logic [PACKET_INDEX_N-1:0] slow_ctrl_packet_index_send= '0;
    logic [PACKET_INDEX_N-1:0] slow_ctrl_packet_index_receive= '0;

    reg [SLOW_CTRL_REG_LENGTH-1:0] slow_ctrl_packet= '0;

    logic [PACKET_INDEX_N-1:0] dac_packet_index_send= '0;
    logic [PACKET_INDEX_N-1:0] dac_packet_index_receive= '0;

    reg [DAC_PACKET_REG_LENGTH-1:0] dac_packet= '0;

    logic [DATA_SIZE-1:0] pixel_row= '0;
    logic [DATA_SIZE-1:0] pixel_col= '0;
    logic [DATA_SIZE-1:0] signal= '0;
    logic [CMD_CODE_SIZE-1:0] cmd= '0;
    // check UART rising edge
    logic uart_valid_last;
    // check cmd or data
    logic cmd_available;
    logic data_available;

//======================= COMB and FF ================================
//======================= STD CLOCKS =================================
// Standard means that should repeat with duty cycle = 50%
    // slow ctrl clock generation
    always_ff @(posedge ck, posedge reset) begin: slow_ctrl_ck_generation
        if (reset) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_cnt <= -1;
        end
        // <= 2 to allow for half period sample
        else if (slow_ctrl_div <= 2 || sync_time_base_flag) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_cnt <= -1;
        end
        // the second check is to assure that the last HIGH is the same semiperiod as the others
        else if (!slow_ctrl_mask & slow_ctrl_ck == 1'b0) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_cnt <= -1;
        end
        else if (slow_ctrl_cnt == slow_ctrl_div-1) begin
            slow_ctrl_ck <= ~slow_ctrl_ck;
            slow_ctrl_cnt <= '0;
        end
        else begin
            slow_ctrl_ck <= slow_ctrl_ck;
            slow_ctrl_cnt <= slow_ctrl_cnt + 1'b1;
        end
    end

    // Pixel selection clock generation (to temporise col and row)
    always_ff @(posedge ck, posedge reset) begin: sel_ck_generation
        if (reset) begin
            sel_ck <= 1'b0;
            sel_cnt <= -1;
        end
        else if (sel_init_n || sel_div == '0 || sync_time_base_flag) begin
            sel_ck <= 1'b0;
            sel_cnt <= -1;
        end
        else if (sel_cnt == sel_div-1) begin
            sel_ck <= ~sel_ck;
            sel_cnt <= '0;
        end
        else begin
            sel_ck <= sel_ck;
            sel_cnt <= sel_cnt + 1'b1;
        end
    end

    // ADC clock generation
    always_ff @(posedge ck, posedge reset) begin: adc_ck_generation
        if (reset) begin
            adc_ck <= 1'b0;
            adc_cnt <= -1;
        end
        else if (!adc_start || adc_div == '0 || sync_time_base_flag) begin
            adc_ck <= 1'b0;
            adc_cnt <= -1;
        end
        else if (adc_cnt == adc_div-1) begin
            adc_ck <= ~adc_ck;
            adc_cnt <= '0;
        end
        else begin
            adc_ck <= adc_ck;
            adc_cnt <= adc_cnt + 1'b1;
        end
    end

    // INJ strobe generation
    always_ff @(posedge ck, posedge reset) begin: inj_stb_generation
        if (reset) begin
            inj_stb <= 1'b0;
            inj_cnt <= -1;
        end
        else if (inj_div == '0 || sync_time_base_flag) begin
            inj_stb <= 1'b0;
            inj_cnt <= -1;
        end
        else if (inj_cnt == inj_div-1) begin
            inj_stb <= ~inj_stb;
            inj_cnt <= '0;
        end
        else begin
            inj_stb <= inj_stb;
            inj_cnt <= inj_cnt + 1'b1;
        end
    end

    // serialiser clock generation
    always_ff @(posedge ck, posedge reset) begin: ser_ck_generation
        if (reset) begin
            ser_ck <= 1'b0;
            ser_cnt <= -1;
        end
        else if (!ser_reset_n || ser_div == '0 || sync_time_base_flag) begin
            ser_ck <= 1'b0;
            ser_cnt <= -1;
        end
        else if (ser_cnt == ser_div-1) begin
            ser_ck <= ~ser_ck;
            ser_cnt <= '0;
        end
        else begin
            ser_ck <= ser_ck;
            ser_cnt <= ser_cnt + 1'b1;
        end
    end

    // dac SCK clock generation
    always_ff @(posedge ck, posedge reset) begin: dac_sck_generation
        if (reset) begin
            dac_sck <= 1'b0;
            dac_sck_cnt <= -1;
        end
        else if (dac_sync_n || dac_sck_div == '0 || sync_time_base_flag) begin
            dac_sck <= 1'b0;
            dac_sck_cnt <= -1;
        end
        else if (dac_sck_cnt == dac_sck_div-1) begin
            dac_sck <= ~dac_sck;
            dac_sck_cnt <= '0;
        end
        else begin
            dac_sck <= dac_sck;
            dac_sck_cnt <= dac_sck_cnt + 1'b1;
        end
    end
//===================== END STD CLOCKS ===============================

//====================== FAST CONTROL ================================
// These are the fast controls, managed in a similar ways as the clocks, with two different dividers for high and low state
    always_ff @(posedge ck, posedge reset) begin: csa_reset_n_generation
        if (reset) begin
            csa_reset_n <= 1'b0;
            csa_reset_n_cnt <= -1;
            csa_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (sync_time_base_flag ||
            (csa_reset_n_flag == FAST_CTRL_DELAY && csa_reset_n_delay_div == '0) ||
            (csa_reset_n_HIGH_div == '0 || csa_reset_n_LOW_div == '0)) begin
            csa_reset_n <= 1'b0;
            csa_reset_n_cnt <= -1;
            csa_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (csa_reset_n_flag == FAST_CTRL_DELAY &&
                 csa_reset_n_cnt == csa_reset_n_delay_div-1) begin
            csa_reset_n <= ~csa_reset_n;
            csa_reset_n_cnt <= '0;
            csa_reset_n_flag <= FAST_CTRL_HIGH;
        end
        else if (csa_reset_n_flag == FAST_CTRL_HIGH &&
                 csa_reset_n_cnt == csa_reset_n_HIGH_div-1) begin
            csa_reset_n <= ~csa_reset_n;
            csa_reset_n_cnt <= '0;
            csa_reset_n_flag <= FAST_CTRL_LOW;
        end
        else if (csa_reset_n_flag == FAST_CTRL_LOW &&
                 csa_reset_n_cnt == csa_reset_n_LOW_div-1) begin
            csa_reset_n <= ~csa_reset_n;
            csa_reset_n_cnt <= '0;
            csa_reset_n_flag <= FAST_CTRL_HIGH;
        end
        else begin
            csa_reset_n <= csa_reset_n;
            csa_reset_n_cnt <= csa_reset_n_cnt + 1'b1;
        end
    end

    always_ff @(posedge ck, posedge reset) begin: sh_phi1d_inf_generation
        if (reset) begin
            sh_phi1d_inf <= 1'b0;
            sh_phi1d_inf_cnt <= -1;
            sh_phi1d_inf_flag <= FAST_CTRL_DELAY;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b0; // (TS)
        end
        else if (slow_ctrl_in_mask) begin
            sh_phi1d_inf <= 1'b0;
            sh_phi1d_inf_cnt <= -1;
            sh_phi1d_inf_flag <= FAST_CTRL_DELAY;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b0; // (TS)
        end
        else if (sync_time_base_flag ||
            (sh_phi1d_inf_flag == FAST_CTRL_DELAY && sh_phi1d_inf_delay_div == '0) ||
            (sh_phi1d_inf_HIGH_div == '0 || sh_phi1d_inf_LOW_div == '0)) begin
            sh_phi1d_inf <= 1'b0;
            sh_phi1d_inf_cnt <= -1;
            sh_phi1d_inf_flag <= FAST_CTRL_DELAY;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b1; // (TS)
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_DELAY &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_delay_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_HIGH;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b1; // (TS)
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_HIGH &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_HIGH_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_LOW;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b1; // (TS)
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_LOW &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_LOW_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_HIGH;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b1; // (TS)
        end
        else begin
            sh_phi1d_inf <= sh_phi1d_inf;
            sh_phi1d_inf_cnt <= sh_phi1d_inf_cnt + 1'b1;
            // Due to PCB layout error
            sh_phi1d_inf_mask <= 1'b1; // (TS)
        end
    end

    always_ff @(posedge ck, posedge reset) begin: sh_phi1d_sup_generation
        if (reset) begin
            sh_phi1d_sup <= 1'b0;
            sh_phi1d_sup_cnt <= -1;
            sh_phi1d_sup_flag <= FAST_CTRL_DELAY;
        end
        else if (sync_time_base_flag ||
            (sh_phi1d_sup_flag == FAST_CTRL_DELAY && sh_phi1d_sup_delay_div == '0) ||
            (sh_phi1d_sup_HIGH_div == '0 || sh_phi1d_sup_LOW_div == '0)) begin
            sh_phi1d_sup <= 1'b0;
            sh_phi1d_sup_cnt <= -1;
            sh_phi1d_sup_flag <= FAST_CTRL_DELAY;
        end
        else if (sh_phi1d_sup_flag == FAST_CTRL_DELAY &&
                 sh_phi1d_sup_cnt == sh_phi1d_sup_delay_div-1) begin
            sh_phi1d_sup <= ~sh_phi1d_sup;
            sh_phi1d_sup_cnt <= '0;
            sh_phi1d_sup_flag <= FAST_CTRL_HIGH;
        end
        else if (sh_phi1d_sup_flag == FAST_CTRL_HIGH &&
                 sh_phi1d_sup_cnt == sh_phi1d_sup_HIGH_div-1) begin
            sh_phi1d_sup <= ~sh_phi1d_sup;
            sh_phi1d_sup_cnt <= '0;
            sh_phi1d_sup_flag <= FAST_CTRL_LOW;
        end
        else if (sh_phi1d_sup_flag == FAST_CTRL_LOW &&
                 sh_phi1d_sup_cnt == sh_phi1d_sup_LOW_div-1) begin
            sh_phi1d_sup <= ~sh_phi1d_sup;
            sh_phi1d_sup_cnt <= '0;
            sh_phi1d_sup_flag <= FAST_CTRL_HIGH;
        end
        else begin
            sh_phi1d_sup <= sh_phi1d_sup;
            sh_phi1d_sup_cnt <= sh_phi1d_sup_cnt + 1'b1;
        end
    end

    always_ff @(posedge ck, posedge reset) begin: adc_start_generation
        if (reset) begin
            adc_start <= 1'b0;
            adc_start_cnt <= -1;
            adc_start_flag <= FAST_CTRL_DELAY;
        end
        else if (sync_time_base_flag ||
            (adc_start_flag == FAST_CTRL_DELAY && adc_start_delay_div == '0) ||
            (adc_start_HIGH_div == '0 || adc_start_LOW_div == '0)) begin
            adc_start <= 1'b0;
            adc_start_cnt <= -1;
            adc_start_flag <= FAST_CTRL_DELAY;
        end
        else if (adc_start_flag == FAST_CTRL_DELAY &&
                 adc_start_cnt == adc_start_delay_div-1) begin
            adc_start <= ~adc_start;
            adc_start_cnt <= '0;
            adc_start_flag <= FAST_CTRL_HIGH;
        end
        else if (adc_start_flag == FAST_CTRL_HIGH &&
                 adc_start_cnt == adc_start_HIGH_div-1) begin
            adc_start <= ~adc_start;
            adc_start_cnt <= '0;
            adc_start_flag <= FAST_CTRL_LOW;
        end
        else if (adc_start_flag == FAST_CTRL_LOW &&
                 adc_start_cnt == adc_start_LOW_div-1) begin
            adc_start <= ~adc_start;
            adc_start_cnt <= '0;
            adc_start_flag <= FAST_CTRL_HIGH;
        end
        else begin
            adc_start <= adc_start;
            adc_start_cnt <= adc_start_cnt + 1'b1;
        end
    end

    always_ff @(posedge ck, posedge reset) begin: ser_reset_n_generation
        if (reset) begin
            ser_reset_n <= 1'b0;
            ser_reset_n_cnt <= -1;
            ser_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (sync_time_base_flag ||
            (ser_reset_n_flag == FAST_CTRL_DELAY && ser_reset_n_delay_div == '0) ||
            (ser_reset_n_HIGH_div == '0 || ser_reset_n_LOW_div == '0)) begin
            ser_reset_n <= 1'b0;
            ser_reset_n_cnt <= -1;
            ser_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (ser_reset_n_flag == FAST_CTRL_DELAY &&
                 ser_reset_n_cnt == ser_reset_n_delay_div-1) begin
            ser_reset_n <= ~ser_reset_n;
            ser_reset_n_cnt <= '0;
            ser_reset_n_flag <= FAST_CTRL_HIGH;
        end
        else if (ser_reset_n_flag == FAST_CTRL_HIGH &&
                 ser_reset_n_cnt == ser_reset_n_HIGH_div-1) begin
            ser_reset_n <= ~ser_reset_n;
            ser_reset_n_cnt <= '0;
            ser_reset_n_flag <= FAST_CTRL_LOW;
        end
        else if (ser_reset_n_flag == FAST_CTRL_LOW &&
                 ser_reset_n_cnt == ser_reset_n_LOW_div-1) begin
            ser_reset_n <= ~ser_reset_n;
            ser_reset_n_cnt <= '0;
            ser_reset_n_flag <= FAST_CTRL_HIGH;
        end
        else begin
            ser_reset_n <= ser_reset_n;
            ser_reset_n_cnt <= ser_reset_n_cnt + 1'b1;
        end
    end

    always_ff @(posedge ck, posedge reset) begin: ser_read_generation
        if (reset) begin
            ser_read <= 1'b0;
            ser_read_cnt <= -1;
            ser_read_flag <= FAST_CTRL_DELAY;
        end
        else if (sync_time_base_flag || 
            (ser_read_flag == FAST_CTRL_DELAY && ser_read_delay_div == '0) ||
            (ser_read_HIGH_div == '0 || ser_read_LOW_div == '0)) begin
            ser_read <= 1'b0;
            ser_read_cnt <= -1;
            ser_read_flag <= FAST_CTRL_DELAY;
        end
        else if (ser_read_flag == FAST_CTRL_DELAY &&
                 ser_read_cnt == ser_read_delay_div-1) begin
            ser_read <= ~ser_read;
            ser_read_cnt <= '0;
            ser_read_flag <= FAST_CTRL_HIGH;
        end
        else if (ser_read_flag == FAST_CTRL_HIGH &&
                 ser_read_cnt == ser_read_HIGH_div-1) begin
            ser_read <= ~ser_read;
            ser_read_cnt <= '0;
            ser_read_flag <= FAST_CTRL_LOW;
        end
        else if (ser_read_flag == FAST_CTRL_LOW &&
                 ser_read_cnt == ser_read_LOW_div-1) begin
            ser_read <= ~ser_read;
            ser_read_cnt <= '0;
            ser_read_flag <= FAST_CTRL_HIGH;
        end
        else begin
            ser_read <= ser_read;
            ser_read_cnt <= ser_read_cnt + 1'b1;
        end
    end
//===================== END FAST CONTROL =============================

    // state machine control
    always_comb begin : state_machine_ctrl
        case (state)
            RESET:
                next <= CMD_EVAL;
            CMD_EVAL:
                if (!uart_valid && cmd_available) begin
                    case (cmd)
                        // if the command is a known one
                        // next read which signal to set
                        `SET_CK_CMD,
                        `SET_DELAY_CMD,
                        `SET_HIGH_CMD,
                        `SET_LOW_CMD,
                        `SET_PIXEL_CMD:
                            next <= CMD_SET;
                        `SET_SLOW_CTRL_CMD: begin
                            if (slow_ctrl_packet_available)
                                next <= CMD_EVAL;
                            else
                                next <= CMD_SET;
                        end
                        `SET_DAC_CMD: begin
                            if (dac_packet_available)
                                next <= CMD_EVAL;
                            else
                                next <= CMD_SET;
                        end
                        // next send slow control
                        `SEND_SLOW_CTRL_CMD:
                            next <= CMD_SEND_SLOW;
                        // next send DAC config
                        `SEND_DAC_CMD:
                            next <= CMD_SEND_DAC;
                        // next send sel pixel
                        `SEND_PIXEL_SEL_CMD:
                            next <= CMD_SEL_PIX;
                        // next sync time base
                        `SYNC_TIME_BASE_CMD:
                            next <= CMD_SYNC_TIME_BASE;
                        // next reset fpga
                        `RESET_FPGA_CMD:
                            next <= RESET;
                        // if the command is not known error
                        default:
                            next <= CMD_ERR;
                    endcase
                end
                else
                    // if no comms or command is available recheck
                    next <= CMD_EVAL;
            CMD_ERR:
                // it just stays here
                // TODO change
                next <= CMD_ERR;
            CMD_SET:
                // for slow ctl and dac need to wait for more packets
                if (cmd == `SET_SLOW_CTRL_CMD)
                    if (slow_ctrl_packet_available)
                        next <= CMD_EVAL;
                    else
                        next <= CMD_SET;
                else if (cmd == `SET_DAC_CMD)
                    if (dac_packet_available)
                        next <= CMD_EVAL;
                    else
                        next <= CMD_SET;
                else
                    if (data_packet_available)
                        // if data has been read wait for new command
                        next <= CMD_EVAL;
                    else
                        next <= CMD_SET;
            CMD_SEND_SLOW:
                if (slow_ctrl_packet_available & !slow_ctrl_packet_sent)
                    next <= CMD_SEND_SLOW;
                else if (!slow_ctrl_mask)
                    // this is to ensure slow_ctrl_mask goes down
                    next <= CMD_EVAL;
                else
                    next <= CMD_SEND_SLOW;
            CMD_SEND_DAC:
                if (dac_packet_available & !dac_packet_sent)
                    next <= CMD_SEND_DAC;
                else
                    next <= CMD_EVAL;
            CMD_SEL_PIX:
                if (sel_ckrow_sent & sel_ckcol_sent)
                    next <= CMD_EVAL;
                else
                    next <= CMD_SEL_PIX;
            CMD_SYNC_TIME_BASE:
                next <= CMD_EVAL;
            default:
                next <= CMD_ERR;
        endcase
    end

    // state machine next state control
    always_ff @(posedge ck, posedge reset) begin: state_machine_next
        if (reset)
            state <= RESET;
        else
            state <= next;
    end

    // save last uart valid to detect rising edge
    always_ff @(posedge ck, posedge reset) begin: uart_valid_last_logic
        if (reset)
            uart_valid_last <= 1'b0;
        else
            uart_valid_last <= uart_valid;
    end

    // check for cmd or data
    always_ff @(posedge ck, posedge reset) begin: check_cmd_data_available
        if (reset) begin
            cmd_available <= 1'b0;
            data_available <= 1'b0;
        end
        else begin
            if (uart_valid) begin
                if (uart_data[7] == CMD_PACKET) begin
                    cmd_available <= 1'b1;
                    data_available <= 1'b0;
                end
                else begin
                    cmd_available <= 1'b0;
                    data_available <= 1'b1;
                end
            end
            else begin
                cmd_available <= 1'b0;
                data_available <= 1'b0;
            end
        end
    end

    // what to do on each state
    always_ff @(posedge ck, posedge reset) begin: state_machine_set_output
        if (reset) begin
            // reset all div
            slow_ctrl_div <= '0;
            adc_div <= '0;
            ser_div <= '0;
            sel_div <= '0;
            inj_div <= '0;
            dac_sck_div <= '0;
                                    
            csa_reset_n_delay_div <= '0;
            sh_phi1d_inf_delay_div <= '0;
            sh_phi1d_sup_delay_div <= '0;
            adc_start_delay_div <= '0;
            ser_reset_n_delay_div <= '0;
            ser_read_delay_div <= '0;
            
            csa_reset_n_HIGH_div <= '0;
            sh_phi1d_inf_HIGH_div <= '0;
            sh_phi1d_sup_HIGH_div <= '0;
            adc_start_HIGH_div <= '0;
            ser_reset_n_HIGH_div <= '0;
            ser_read_HIGH_div <= '0;

            csa_reset_n_LOW_div <= '0;
            sh_phi1d_inf_LOW_div <= '0;
            sh_phi1d_sup_LOW_div <= '0;
            adc_start_LOW_div <= '0;
            ser_reset_n_LOW_div <= '0;
            ser_read_LOW_div <= '0;
            
            // reset all resets
            slow_ctrl_mask <= 1'b0;
            slow_ctrl_reset_n <= 1'b0;
            slow_ctrl_in_mask <= 1'b1; // (TS)
            //sh_phi1d_inf_mask <= 1'b0; // (TS)
            dac_sync_n <= 1'b1;
            sel_init_n <= 1'b1;
            inj_start <= 1'b0;

            // reset all vars
            slow_ctrl_packet_available <= 1'b0;
            //slow_ctrl_packet_sent <= 1'b0;
            dac_packet_available <= 1'b0;
            //dac_packet_sent <= 1'b0;
            //sel_ckcol_sent <= 1'b0;
            //sel_ckrow_sent <= 1'b0;

            //slow_ctrl_packet_index_send <= '0;
            slow_ctrl_packet_index_receive <= '0;
            //dac_packet_index_send <= '0;
            dac_packet_index_receive <= '0;
            dac_packet <= '0;
            pixel_row <= '0;
            pixel_col <= '0;
            cmd <= '0;
            signal <= '0;

            inj_start <= '0;

            //slow_ctrl_in <= '0;
            //dac_sdin <= '0;

            slow_ctrl_packet = 0;
            dac_packet = 0;
        end
        else begin
            case (state)
                RESET: begin
                    // reset all div
                    slow_ctrl_div <= '0;
                    adc_div <= '0;
                    ser_div <= '0;
                    sel_div <= '0;
                    inj_div <= '0;
                    dac_sck_div <= '0;
                                            
                    csa_reset_n_delay_div <= '0;
                    sh_phi1d_inf_delay_div <= '0;
                    sh_phi1d_sup_delay_div <= '0;
                    adc_start_delay_div <= '0;
                    ser_reset_n_delay_div <= '0;
                    ser_read_delay_div <= '0;
                    
                    csa_reset_n_HIGH_div <= '0;
                    sh_phi1d_inf_HIGH_div <= '0;
                    sh_phi1d_sup_HIGH_div <= '0;
                    adc_start_HIGH_div <= '0;
                    ser_reset_n_HIGH_div <= '0;
                    ser_read_HIGH_div <= '0;

                    csa_reset_n_LOW_div <= '0;
                    sh_phi1d_inf_LOW_div <= '0;
                    sh_phi1d_sup_LOW_div <= '0;
                    adc_start_LOW_div <= '0;
                    ser_reset_n_LOW_div <= '0;
                    ser_read_LOW_div <= '0;
                    
                    // reset all resets
                    slow_ctrl_mask <= 1'b0;
                    slow_ctrl_reset_n <= 1'b0;
                    slow_ctrl_in_mask <= 1'b1; // (TS)
                    //sh_phi1d_inf_mask <= 1'b0; // (TS)
                    dac_sync_n <= 1'b1;
                    sel_init_n <= 1'b1;
                    inj_start <= 1'b0;

                    // reset all vars
                    slow_ctrl_packet_available <= 1'b0;
                    //slow_ctrl_packet_sent <= 1'b0;
                    dac_packet_available <= 1'b0;
                    //dac_packet_sent <= 1'b0;
                    //sel_ckcol_sent <= 1'b0;
                    //sel_ckrow_sent <= 1'b0;

                    //slow_ctrl_packet_index_send <= '0;
                    slow_ctrl_packet_index_receive <= '0;
                    //dac_packet_index_send <= '0;
                    dac_packet_index_receive <= '0;
                    dac_packet <= '0;
                    pixel_row <= '0;
                    pixel_col <= '0;
                    cmd <= '0;
                    signal <= '0;

                    inj_start <= '0;

                    //slow_ctrl_in <= '0;
                    //dac_sdin <= '0;

                    slow_ctrl_packet = 0;
                    dac_packet = 0;
                end
                CMD_EVAL: begin
                    // evaluate command if available
                    // serial to be sure value are stored in cmd and sig
                    if (cmd_available) begin
                        cmd = uart_data[CMD_START_POS:CMD_END_POS];
                        signal = uart_data[SIGNAL_START_POS:SIGNAL_END_POS];
                        case (cmd)
                            `SET_CK_CMD,
                            `SET_DELAY_CMD,
                            `SET_HIGH_CMD,
                            `SET_LOW_CMD,
                            `SET_PIXEL_CMD:
                                data_packet_available = 1'b0;
                            `SET_SLOW_CTRL_CMD: begin
                                //slow_ctrl_packet_available <= 1'b0;
                                slow_ctrl_packet_index_receive = '0;
                                slow_ctrl_packet = '0;

                                slow_ctrl_reset_n = 1'b0;
                                slow_ctrl_mask = 1'b0;
                                slow_ctrl_in_mask <= 1'b1; // (TS)
                                //sh_phi1d_inf_mask <= 1'b0; // (TS)
                                // cannot set directly index_send and _sent so let's use a flag
                                slow_ctrl_reset_request = 1'b1;

                                data_packet_available = 1'b0;
                            end
                            `SET_DAC_CMD:
                                dac_packet_available = 1'b0;
                        endcase
                    end
                    else begin
                        cmd <= cmd;
                        signal <= signal;
                        data_packet_available <= data_packet_available;
                    end
                    // make sure the time_base_flag is off
                    sync_time_base_flag <= 1'b0;
                end
                CMD_SET: begin
                    if (data_available) begin
                        case (cmd)
                            `SET_CK_CMD: begin
                                if (!uart_valid & uart_valid_last) begin
                                    // set clocks divider
                                    case (signal)
                                        `SLOW_CTRL_CK_CODE:
                                            slow_ctrl_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SEL_CK_CODE:
                                            sel_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `ADC_CK_CODE:
                                            adc_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `INJ_STB_CODE:
                                            inj_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_CK_CODE:
                                            ser_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `DAC_SCK_CODE:
                                            dac_sck_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                    endcase
                                    if (uart_data[DATA_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        data_packet_index_receive <= '0;
                                        data_packet_available <= 1'b1;
                                    end else begin
                                        data_packet[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_UART_DATA_POS:DATA_END_POS];
                                        data_packet_index_receive <= data_packet_index_receive + DATA_UART_DATA_POS + 1; // 6 bit per time
                                        data_packet_available <= 1'b0;
                                    end
                                end
                            end
                            `SET_DELAY_CMD: begin
                                if (!uart_valid & uart_valid_last) begin
                                    // set delay divider
                                    case (signal)
                                        `CSA_RESET_N_CODE:
                                            csa_reset_n_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_INF_CODE:
                                            sh_phi1d_inf_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_SUP_CODE:
                                            sh_phi1d_sup_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `ADC_START_CODE:
                                            adc_start_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_RESET_N_CODE:
                                            ser_reset_n_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_READ_CODE:
                                            ser_read_delay_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                    endcase
                                    if (uart_data[DATA_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        data_packet_index_receive <= '0;
                                        data_packet_available <= 1'b1;
                                    end else begin
                                        data_packet[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_UART_DATA_POS:DATA_END_POS];
                                        data_packet_index_receive <= data_packet_index_receive + DATA_UART_DATA_POS + 1; // 6 bit per time
                                        data_packet_available <= 1'b0;
                                    end
                                end
                            end
                            `SET_HIGH_CMD: begin
                                if (!uart_valid & uart_valid_last) begin
                                    // set HIGH divider
                                    case (signal)
                                        `CSA_RESET_N_CODE:
                                            csa_reset_n_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_INF_CODE:
                                            sh_phi1d_inf_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_SUP_CODE:
                                            sh_phi1d_sup_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `ADC_START_CODE:
                                            adc_start_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_RESET_N_CODE:
                                            ser_reset_n_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_READ_CODE:
                                            ser_read_HIGH_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                    endcase
                                    if (uart_data[DATA_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        data_packet_index_receive <= '0;
                                        data_packet_available <= 1'b1;
                                    end else begin
                                        data_packet[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_UART_DATA_POS:DATA_END_POS];
                                        data_packet_index_receive <= data_packet_index_receive + DATA_UART_DATA_POS + 1; // 6 bit per time
                                        data_packet_available <= 1'b0;
                                    end
                                end
                            end
                            `SET_LOW_CMD: begin
                                if (!uart_valid & uart_valid_last) begin
                                    // set LOW divider
                                    case (signal)
                                        `CSA_RESET_N_CODE:
                                            csa_reset_n_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_INF_CODE:
                                            sh_phi1d_inf_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SH_SUP_CODE:
                                            sh_phi1d_sup_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `ADC_START_CODE:
                                            adc_start_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_RESET_N_CODE:
                                            ser_reset_n_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                        `SER_READ_CODE:
                                            ser_read_LOW_div[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_START_POS:DATA_END_POS];
                                    endcase
                                    if (uart_data[DATA_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        data_packet_index_receive <= '0;
                                        data_packet_available <= 1'b1;
                                    end else begin
                                        data_packet[data_packet_index_receive +: DATA_UART_DATA_POS+1] <= uart_data[DATA_UART_DATA_POS:DATA_END_POS];
                                        data_packet_index_receive <= data_packet_index_receive + DATA_UART_DATA_POS + 1; // 6 bit per time
                                        data_packet_available <= 1'b0;
                                    end
                                end
                            end
                            `SET_SLOW_CTRL_CMD: begin
                                slow_ctrl_reset_request <= 1'b0;
                                if (!uart_valid & uart_valid_last) begin
                                    slow_ctrl_packet[slow_ctrl_packet_index_receive +: SLOW_CTRL_UART_DATA_POS+1] <= uart_data[SLOW_CTRL_UART_DATA_POS:DATA_END_POS];
                                    slow_ctrl_packet_index_receive <= slow_ctrl_packet_index_receive + SLOW_CTRL_UART_DATA_POS + 1; // 6 bit per time
                                    if (uart_data[SLOW_CTRL_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        slow_ctrl_packet_available <= 1'b1;
                                    end else begin
                                        slow_ctrl_packet_available <= 1'b0;
                                    end
                                end
                                else begin
                                    slow_ctrl_packet <= slow_ctrl_packet;
                                    slow_ctrl_packet_index_receive <= slow_ctrl_packet_index_receive; // 6 bit per time
                                    slow_ctrl_packet_available <= slow_ctrl_packet_available;
                                end
                            end
                            `SET_DAC_CMD: begin
                                if (!uart_valid & uart_valid_last) begin
                                    if (uart_data[DAC_UART_DATA_POS+1] == LAST_UART_PACKET) begin
                                        // last 3 bits
                                        dac_packet[DAC_PACKET_LENGTH-(DAC_UART_DATA_LAST_POS+1) +: DAC_UART_DATA_LAST_POS+1] <= uart_data[DAC_UART_DATA_LAST_POS:DATA_END_POS];
                                        dac_packet_index_receive <= '0;
                                        dac_packet_available <= 1'b1;
                                    end else begin
                                        dac_packet[dac_packet_index_receive +: DATA_SIZE-1] <= uart_data[DAC_UART_DATA_POS:DATA_END_POS];
                                        dac_packet_index_receive <= dac_packet_index_receive + DATA_SIZE + 6'd1; // 6 bit per time
                                        dac_packet_available <= 1'b0;
                                    end
                                end
                                else begin
                                    dac_packet <= dac_packet;
                                    dac_packet_index_receive <= dac_packet_index_receive; // 6 bit per time
                                    dac_packet_available <= dac_packet_available;
                                end
                            end
                            `SET_PIXEL_CMD: begin
                                // set row/col number
                                case (signal)
                                    `PIXEL_ROW_CODE:
                                        pixel_row <= uart_data[DATA_START_POS:DATA_END_POS];
                                    `PIXEL_COL_CODE:
                                        pixel_col <= uart_data[DATA_START_POS:DATA_END_POS];
                                    default: begin
                                        pixel_row <= pixel_row;
                                        pixel_col <= pixel_col;
                                    end
                                endcase
                            end
                        endcase
                    end
                end
                CMD_SEND_SLOW: begin
                    // this way we are checking on the falling edge and no ck is sent after the signal is on
                    if (slow_ctrl_packet_sent) begin
                        slow_ctrl_reset_n <= 1'b1;
                        slow_ctrl_mask <= 1'b0;
                        slow_ctrl_in_mask <= 1'b0; // (TS)
                        slow_ctrl_packet_available <= 1'b0;
                    end
                    else begin
                        slow_ctrl_reset_n <= 1'b1;
                        slow_ctrl_mask <= 1'b1;
                        slow_ctrl_in_mask <= 1'b1; // (TS)
                        slow_ctrl_packet_available <= slow_ctrl_packet_available;
                    end
                end
                CMD_SEND_DAC: begin
                    // this way we are checking on the falling edge and no ck is sent after the signal is on
                    if (dac_packet_sent)
                        dac_sync_n <= 1'b1;
                    else
                        dac_sync_n <= 1'b0;
                end
                CMD_SEL_PIX: begin
                    // this way we are checking on the falling edge and no ck is sent after the signal is off
                    if (sel_ckrow_sent && sel_ckcol_sent)
                        sel_init_n <= 1'b1;
                    else
                        sel_init_n <= 1'b0;
                end
                CMD_SYNC_TIME_BASE:
                    sync_time_base_flag <= 1'b1;
            endcase
        end
    end

    // if slow ctrl is posedge then data need to be transmitted
    always_ff @(posedge ck, posedge reset) begin: slow_ctrl_data_send
        if (reset || slow_ctrl_reset_request) begin
            slow_ctrl_in <= 1'b0;
            slow_ctrl_packet_index_send <= SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS; // skip the unneeded bits
            slow_ctrl_packet_sent <= 1'b0;
        end
        else if (slow_ctrl_mask) begin
            if (slow_ctrl_ck == 1'b0 && slow_ctrl_cnt == slow_ctrl_div/2) begin
                if (slow_ctrl_packet_index_send != SLOW_CTRL_PACKET_LENGTH + SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS) begin
                    slow_ctrl_in <= slow_ctrl_packet[slow_ctrl_packet_index_send];
                    slow_ctrl_packet_index_send <= slow_ctrl_packet_index_send + 1;
                    slow_ctrl_packet_sent <= 1'b0;
                end
                else begin
                    slow_ctrl_in <= slow_ctrl_in;
                    slow_ctrl_packet_index_send <= slow_ctrl_packet_index_send;
                    slow_ctrl_packet_sent <= slow_ctrl_packet_sent;
                end
            end
            else if (slow_ctrl_ck == 1'b1 && slow_ctrl_cnt == slow_ctrl_div/2) begin
                if (slow_ctrl_packet_index_send == SLOW_CTRL_PACKET_LENGTH + SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS) begin
                    slow_ctrl_packet_index_send <= SLOW_CTRL_PACKET_LENGTH + SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS;
                    slow_ctrl_in <= 1'b0;
                    slow_ctrl_packet_sent <= 1'b1;
                end
                else begin
                    slow_ctrl_packet_index_send <= slow_ctrl_packet_index_send;
                    slow_ctrl_in <= slow_ctrl_in;
                    slow_ctrl_packet_sent <= slow_ctrl_packet_sent;
                end
            end
            else begin
                slow_ctrl_packet_index_send <= slow_ctrl_packet_index_send;
                slow_ctrl_in <= slow_ctrl_in;
                slow_ctrl_packet_sent <= slow_ctrl_packet_sent;
            end
        end
        else if (sh_phi1d_inf_mask) begin
            // this is due to PCB layout problems!! Check constraint files!
            slow_ctrl_packet_sent <= 1'b0;
            slow_ctrl_packet_index_send <= SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS;
            slow_ctrl_in <= sh_phi1d_inf;
        end
        else begin
            slow_ctrl_packet_sent <= 1'b0;
            slow_ctrl_packet_index_send <= SLOW_CTRL_UART_DATA_POS - SLOW_CTRL_UART_DATA_LAST_POS; // skip the unneeded bits
            slow_ctrl_in <= 1'b0;
        end
    end

    // if slow ctrl is posedge then data need to be transmitted
    always_ff @(posedge ck, posedge reset) begin: dac_data_send
        if (reset) begin
            dac_sdin <= 1'b0;
            dac_packet_index_send <= '0;
            dac_packet_sent <= 1'b0;
        end
        else if (!dac_sync_n) begin
            if (dac_sck == 1'b0 && dac_sck_cnt == dac_sck_div-1) begin
                if (dac_packet_index_send < DAC_PACKET_LENGTH) begin
                    dac_sdin <= dac_packet[dac_packet_index_send];
                    dac_packet_index_send <= dac_packet_index_send + 1;
                end 
                else begin
                    dac_sdin <= dac_sdin;
                    dac_packet_index_send <= dac_packet_index_send;
                end
            end
            else if (dac_sck == 1'b1 && dac_sck_cnt == dac_sck_div-1) begin
                if (dac_packet_index_send >= DAC_PACKET_LENGTH) begin
                    dac_packet_sent <= 1'b1;
                    dac_packet_index_send <= '0;
                    dac_sdin <= 1'b0;
                end
                else begin
                    dac_packet_sent <= dac_packet_sent;
                    dac_packet_index_send <= dac_packet_index_send;
                    dac_sdin <= dac_sdin;
                end
            end
            else begin
                dac_packet_sent <= dac_packet_sent;
                dac_packet_index_send <= dac_packet_index_send;
                dac_sdin <= dac_sdin;
            end
        end
        else begin
            dac_packet_sent <= 1'b0;
            dac_packet_index_send <= '0;
            dac_sdin <= 1'b0;
        end
    end

    // if sel_ck is posedge then col or row ck might need to commute
    always_ff @(posedge ck, posedge reset) begin: pixel_sel_send_posedge
        if (reset) begin
            sel_ckrow <= 1'b0;
            sel_ckcol <= 1'b0;
            sel_ckrow_cnt <= 0;
            sel_ckcol_cnt <= 0;
            sel_ckrow_sent <= 1'b0;
            sel_ckcol_sent <= 1'b0;
        end
        // here one triggers if sel_init_n is low
        else if (!sel_init_n) begin
            // if posedge sel_ck
            if (sel_ck == 1'b0 && sel_cnt == sel_div-1) begin
                // row
                if (!sel_ckrow_sent) begin
                    if (sel_ckrow_cnt == pixel_row) begin
                        // if everything was transmitted, reset index
                        sel_ckrow <= 1'b0;
                        sel_ckrow_cnt <= '0;
                    end
                    else begin
                        sel_ckrow <= ~sel_ck;
                        sel_ckrow_cnt <= sel_ckrow_cnt + 1'b1;
                    end
                end
                else begin
                    sel_ckrow <= sel_ckrow;
                    sel_ckrow_cnt <= sel_ckrow_cnt;
                end
                // col
                if (!sel_ckcol_sent) begin
                    if (sel_ckcol_cnt == pixel_col) begin
                        // if everything was transmitted, reset index
                        sel_ckcol <= 1'b0;
                        sel_ckcol_cnt <= '0;
                    end
                    else begin
                        sel_ckcol <= ~sel_ck;
                        sel_ckcol_cnt <= sel_ckcol_cnt + 1'b1;
                    end
                end
                else begin
                    sel_ckcol <= sel_ckcol;
                    sel_ckcol_cnt <= sel_ckcol_cnt;
                end
            end
            // if negedge sel_ck
            else if (sel_ck == 1'b1 && sel_cnt == sel_div-1) begin
                // check on negedge to have it ready and not to waste a sel_ck
                if (sel_ckrow_cnt == pixel_row) begin
                    // if everything was transmitted, set sel_ckrow_sent
                    sel_ckrow_sent <= 1'b1;
                end
                else
                    sel_ckrow_sent <= sel_ckrow_sent;
                
                if (sel_ckcol_cnt == pixel_col) begin
                    // if everything was transmitted, set sel_ckcol_sent
                    sel_ckcol_sent <= 1'b1;
                end
                else
                    sel_ckcol_sent <= sel_ckcol_sent;

                if (!sel_ckrow_sent)
                    sel_ckrow <= ~sel_ck;
                else
                    sel_ckrow <= sel_ckrow;

                if (!sel_ckcol_sent)
                    sel_ckcol <= ~sel_ck;
                else
                    sel_ckcol <= sel_ckcol;
            end
        end
    end
//======================= END COMB and FF ================================

//======================= FUNCTIONS ======================================
// // This function resets all the dividers
// function void reset_div;
//     slow_ctrl_div <= '0;
//     adc_div <= '0;
//     ser_div <= '0;
//     sel_div <= '0;
//     inj_div <= '0;
//     dac_sck_div <= '0;
                            
//     csa_reset_n_delay_div <= '0;
//     sh_phi1d_inf_delay_div <= '0;
//     sh_phi1d_sup_delay_div <= '0;
//     adc_start_delay_div <= '0;
//     ser_reset_n_delay_div <= '0;
//     ser_read_delay_div <= '0;
    
//     csa_reset_n_HIGH_div <= '0;
//     sh_phi1d_inf_HIGH_div <= '0;
//     sh_phi1d_sup_HIGH_div <= '0;
//     adc_start_HIGH_div <= '0;
//     ser_reset_n_HIGH_div <= '0;
//     ser_read_HIGH_div <= '0;

//     csa_reset_n_LOW_div <= '0;
//     sh_phi1d_inf_LOW_div <= '0;
//     sh_phi1d_sup_LOW_div <= '0;
//     adc_start_LOW_div <= '0;
//     ser_reset_n_LOW_div <= '0;
//     ser_read_LOW_div <= '0;
// endfunction

// // This function resets all the resets
// function void reset_reset;
//     slow_ctrl_mask <= 1'b0;
//     slow_ctrl_reset_n <= 1'b0;
//     dac_sync_n <= 1'b1;
//     sel_init_n <= 1'b1;
//     inj_start <= 1'b0;
// endfunction

// // This function resets all the variables
// function void reset_vars;
//     slow_ctrl_packet_available <= 1'b0;
//     slow_ctrl_packet_sent <= 1'b0;
//     dac_packet_available <= 1'b0;
//     dac_packet_sent <= 1'b0;
//     sel_ckcol_sent <= 1'b0;
//     sel_ckrow_sent <= 1'b0;

//     slow_ctrl_packet_index_send <= '0;
//     slow_ctrl_packet_index_receive <= '0;
//     dac_packet_index_send <= '0;
//     dac_packet_index_receive <= '0;
//     dac_packet <= '0;
//     pixel_row <= '0;
//     pixel_col <= '0;
//     cmd <= '0;
//     signal <= '0;

//     inj_start <= '0;

//     slow_ctrl_in <= '0;
//     dac_sdin <= '0;

//     slow_ctrl_packet = 0;
//     dac_packet = 0;
// endfunction

// This function manages general clocks signal that will not change in time
// DOESNT WORK IN ALWAYS APPARENTLY
// function void manage_clock(input logic glob_reset, sign_reset,
//                       ref logic sign_ck,
//                       ref logic [CK_CNT_N-1:0] sign_div, sign_cnt);
//     if (glob_reset) begin
//         sign_ck <= 1'b0;
//         sign_cnt <= '0;
//     end
//     else if (sign_reset) begin
//         sign_ck <= 1'b0;
//         sign_cnt <= '0;
//     end
//     else if (sign_div == '0) begin
//         sign_ck <= 1'b0;
//         sign_cnt <= '0;
//     end
//     else if (inj_cnt == sign_div) begin
//         sign_ck <= ~sign_ck;
//         sign_cnt <= '0;
//     end
//     else begin
//         sign_ck <= sign_ck;
//         sign_cnt <= sign_cnt + 1'b1;
//     end
// endfunction
//======================= END FUNCTIONS ==================================

// data keep from one clock to the other
/*
slow_ctrl_cnt <= slow_ctrl_cnt;
slow_ctrl_div <= slow_ctrl_div;
adc_cnt <= adc_cnt;
adc_div <= adc_div;
ser_cnt <= ser_cnt;
ser_div <= ser_div;
sel_cnt <= sel_cnt;
sel_div <= sel_div;
inj_cnt <= inj_cnt;
inj_div <= inj_div;
csa_reset_n_flag <= csa_reset_n_flag;
csa_reset_n_cnt <= csa_reset_n_cnt;
csa_reset_n_delay_div <= csa_reset_n_delay_div;
csa_reset_n_HIGH_div <= csa_reset_n_HIGH_div;
csa_reset_n_LOW_div <= csa_reset_n_LOW_div;
sh_phi1d_inf_flag <= sh_phi1d_inf_flag;
sh_phi1d_inf_cnt <= sh_phi1d_inf_cnt;
sh_phi1d_inf_delay_div <= sh_phi1d_inf_delay_div;
sh_phi1d_inf_HIGH_div <= sh_phi1d_inf_HIGH_div;
sh_phi1d_inf_LOW_div <= sh_phi1d_inf_LOW_div;
sh_phi1d_sup_flag <= sh_phi1d_sup_flag;
sh_phi1d_sup_cnt <= sh_phi1d_sup_cnt;
sh_phi1d_sup_delay_div <= sh_phi1d_sup_delay_div;
sh_phi1d_sup_HIGH_div <= sh_phi1d_sup_HIGH_div;
sh_phi1d_sup_LOW_div <= sh_phi1d_sup_LOW_div;
adc_start_flag <= adc_start_flag;
adc_start_cnt <= adc_start_cnt;
adc_start_delay_div <= adc_start_delay_div;
adc_start_HIGH_div <= adc_start_HIGH_div;
adc_start_LOW_div <= adc_start_LOW_div;
ser_reset_n_flag <= ser_reset_n_flag;
ser_reset_n_cnt <= ser_reset_n_cnt;
ser_reset_n_delay_div <= ser_reset_n_delay_div;
ser_reset_n_HIGH_div <= ser_reset_n_HIGH_div;
ser_reset_n_LOW_div <= ser_reset_n_LOW_div;
ser_read_flag <= ser_read_flag;
ser_read_cnt <= ser_read_cnt;
ser_read_delay_div <= ser_read_delay_div;
ser_read_HIGH_div <= ser_read_HIGH_div;
ser_read_LOW_div <= ser_read_LOW_div;
slow_ctrl_packet <= slow_ctrl_packet;
slow_ctrl_packet_index <= slow_ctrl_packet_index;
slow_ctrl_packet_available <= slow_ctrl_packet_available;
pixel_row <= pixel_row;
pixel_col <= pixel_col;
pixel_available <= pixel_available;
*/

endmodule
