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

`include "pFREYA_defs_uart_exposed.sv"

module pFREYA_IF_uart_exposed(
        output logic dac_sdin, dac_sync_n, dac_sck,
        output logic sel_init_n,
        output logic sel_ckcol, sel_ckrow,
        input  logic ser_out,
        output logic ser_read, ser_reset_n,
        output logic ser_ck,
        output logic inj_stb,
        output logic csa_reset_n,
        output logic adc_ck, adc_start,
        output logic sh_phi1d_sup, sh_phi1d_inf,
        output logic slow_ctrl_in, slow_ctrl_reset_n, slow_ctrl_ck,
        // internal
        input  logic ck, reset,
        input  logic cmd_available, data_available,
        // for UART
        input  logic [UART_PACKET_SIZE-1:0] uart_data,
        input  logic uart_valid
    );

    // state machine code
    (* syn_encoding = "one-hot" *) enum logic [5:0] {
        RESET,
        CMD_EVAL,
        CMD_ERR,
        CMD_READ_DATA,
        CMD_SET,
        CMD_SEND_SLOW,
        CMD_SEND_DAC,
        CMD_SEL_PIX
    } state, next;

    // CK internal
    // generated with counters that reach a divisor
    logic [CK_CNT_N-1:0] slow_ctrl_cnt, slow_ctrl_div;
    logic [CK_CNT_N-1:0] sel_cnt, sel_div;
    logic [CK_CNT_N-1:0] adc_cnt, adc_div;
    logic [CK_CNT_N-1:0] inj_cnt, inj_div;
    logic [CK_CNT_N-1:0] ser_cnt, ser_div;
    logic [CK_CNT_N-1:0] dac_sck_cnt, dac_sck_div;
    // for selection
    logic sel_ck; // internal clock temporisation
    logic [PIXEL_COL_N-1:0] sel_ckcol_cnt;
    logic [PIXEL_ROW_N-1:0] sel_ckrow_cnt;
    // for injection
    logic inj_start;
    // fast control timing
    // generated with counter that reach a divisor, where the divisor changes based on flag
    // flag value is 0 for delay, 1 for HIGH, 2 for LOW (the actual polarity is in the name of the signal)
    logic [FAST_CTRL_FLAG_N-1:0] csa_reset_n_flag;
    logic [FAST_CTRL_FLAG_N-1:0] sh_phi1d_inf_flag;
    logic [FAST_CTRL_FLAG_N-1:0] sh_phi1d_sup_flag;
    logic [FAST_CTRL_FLAG_N-1:0] adc_start_flag;
    logic [FAST_CTRL_FLAG_N-1:0] ser_reset_n_flag;
    logic [FAST_CTRL_FLAG_N-1:0] ser_read_flag;
    logic [FAST_CTRL_N-1:0] csa_reset_n_cnt, csa_reset_n_delay_div, csa_reset_n_HIGH_div, csa_reset_n_LOW_div;
    logic [FAST_CTRL_N-1:0] sh_phi1d_inf_cnt, sh_phi1d_inf_delay_div, sh_phi1d_inf_HIGH_div, sh_phi1d_inf_LOW_div;
    logic [FAST_CTRL_N-1:0] sh_phi1d_sup_cnt, sh_phi1d_sup_delay_div, sh_phi1d_sup_HIGH_div, sh_phi1d_sup_LOW_div;
    logic [FAST_CTRL_N-1:0] adc_start_cnt, adc_start_delay_div, adc_start_HIGH_div, adc_start_LOW_div;
    logic [FAST_CTRL_N-1:0] ser_reset_n_cnt, ser_reset_n_delay_div, ser_reset_n_HIGH_div, ser_reset_n_LOW_div;
    logic [FAST_CTRL_N-1:0] ser_read_cnt, ser_read_delay_div, ser_read_HIGH_div, ser_read_LOW_div;

    // control logic
    logic slow_ctrl_packet_available, slow_ctrl_packet_sent, dac_packet_available, dac_packet_sent, sel_ckcol_sent, sel_ckrow_sent;
    // data
    logic [FAST_CTRL_N-1:0] slow_ctrl_packet_index;
    logic [SLOW_CTRL_PACKET_LENGTH-1:0] slow_ctrl_packet;
    logic [FAST_CTRL_N-1:0] dac_packet_index;
    logic [DAC_PACKET_LENGTH-1:0] dac_packet;
    logic [UART_PACKET_SIZE-1:0] pixel_row, pixel_col;
    logic [DATA_SIZE-1:0] signal;
    logic [CMD_CODE_SIZE-1:0] cmd;
    // check UART rising edge
    logic uart_valid_last;

//======================= COMB and FF ================================
//======================= STD CLOCKS =================================
// Standard means that should repeat with duty cycle = 50%
    // slow ctrl clock generation
    always_ff @(posedge ck, posedge reset) begin: slow_ctrl_ck_generation
        if (reset) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_cnt <= -1;
        end
        // the second check is to assure that the last HIGH is the same semiperiod as the others
        else if (~slow_ctrl_reset_n & slow_ctrl_ck == 1'b0) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_cnt <= -1;
        end
        else if (slow_ctrl_div == '0) begin
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
        // the second check is to assure that the last HIGH is the same semiperiod as the others
        else if (sel_init_n) begin
            sel_ck <= 1'b0;
            sel_cnt <= -1;
        end
        else if (sel_div == '0) begin
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
        else if (~adc_start) begin
            adc_ck <= 1'b0;
            adc_cnt <= -1;
        end
        else if (adc_div == '0) begin
            adc_ck <= 1'b0;
            adc_cnt <= '0;
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
        else if (~inj_start) begin
            inj_stb <= 1'b0;
            inj_cnt <= -1;
        end
        else if (inj_div == '0) begin
            inj_stb <= 1'b0;
            inj_cnt <= '0;
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
        else if (~ser_reset_n) begin
            ser_ck <= 1'b0;
            ser_cnt <= -1;
        end
        else if (ser_div == '0) begin
            ser_ck <= 1'b0;
            ser_cnt <= '0;
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
        else if (dac_sync_n) begin
            dac_sck <= 1'b0;
            dac_sck_cnt <= -1;
        end
        else if (dac_sck_div == '0) begin
            dac_sck <= 1'b0;
            dac_sck_cnt <= '0;
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
        else if (csa_reset_n_flag == FAST_CTRL_DELAY &&
                 csa_reset_n_delay_div == '0) begin
            csa_reset_n <= 1'b0;
            csa_reset_n_cnt <= -1;
            csa_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (csa_reset_n_HIGH_div == '0 ||
                 csa_reset_n_LOW_div == '0    ) begin
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
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_DELAY &&
                 sh_phi1d_inf_delay_div == '0) begin
            sh_phi1d_inf <= 1'b0;
            sh_phi1d_inf_cnt <= -1;
            sh_phi1d_inf_flag <= FAST_CTRL_DELAY;
        end
        else if (sh_phi1d_inf_HIGH_div == '0 ||
                 sh_phi1d_inf_LOW_div == '0    ) begin
            sh_phi1d_inf <= 1'b0;
            sh_phi1d_inf_cnt <= -1;
            sh_phi1d_inf_flag <= FAST_CTRL_DELAY;
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_DELAY &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_delay_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_HIGH;
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_HIGH &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_HIGH_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_LOW;
        end
        else if (sh_phi1d_inf_flag == FAST_CTRL_LOW &&
                 sh_phi1d_inf_cnt == sh_phi1d_inf_LOW_div-1) begin
            sh_phi1d_inf <= ~sh_phi1d_inf;
            sh_phi1d_inf_cnt <= '0;
            sh_phi1d_inf_flag <= FAST_CTRL_HIGH;
        end
        else begin
            sh_phi1d_inf <= sh_phi1d_inf;
            sh_phi1d_inf_cnt <= sh_phi1d_inf_cnt + 1'b1;
        end
    end

    always_ff @(posedge ck, posedge reset) begin: sh_phi1d_sup_generation
        if (reset) begin
            sh_phi1d_sup <= 1'b0;
            sh_phi1d_sup_cnt <= -1;
            sh_phi1d_sup_flag <= FAST_CTRL_DELAY;
        end
        else if (sh_phi1d_sup_flag == FAST_CTRL_DELAY &&
                 sh_phi1d_sup_delay_div == '0) begin
            sh_phi1d_sup <= 1'b0;
            sh_phi1d_sup_cnt <= -1;
            sh_phi1d_sup_flag <= FAST_CTRL_DELAY;
        end
        else if (sh_phi1d_sup_HIGH_div == '0 ||
                 sh_phi1d_sup_LOW_div == '0    ) begin
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
        else if (adc_start_flag == FAST_CTRL_DELAY &&
                 adc_start_delay_div == '0) begin
            adc_start <= 1'b0;
            adc_start_cnt <= -1;
            adc_start_flag <= FAST_CTRL_DELAY;
        end
        else if (adc_start_HIGH_div == '0 ||
                 adc_start_LOW_div == '0    ) begin
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
        else if (ser_reset_n_flag == FAST_CTRL_DELAY &&
                 ser_reset_n_delay_div == '0) begin
            ser_reset_n <= 1'b0;
            ser_reset_n_cnt <= -1;
            ser_reset_n_flag <= FAST_CTRL_DELAY;
        end
        else if (ser_reset_n_HIGH_div == '0 ||
                 ser_reset_n_LOW_div == '0    ) begin
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
        else if (ser_read_flag == FAST_CTRL_DELAY &&
                 ser_read_delay_div == '0) begin
            ser_read <= 1'b0;
            ser_read_cnt <= -1;
            ser_read_flag <= FAST_CTRL_DELAY;
        end
        else if (ser_read_HIGH_div == '0 ||
                 ser_read_LOW_div == '0    ) begin
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
                if (uart_valid & cmd_available) begin
                    case (cmd)
                        // if the command is a known one
                        // next read which signal to set
                        `SET_CK_CMD,
                        `SET_DELAY_CMD,
                        `SET_HIGH_CMD,
                        `SET_LOW_CMD,
                        `SET_SLOW_CTRL_CMD,
                        `SET_DAC_CMD,
                        `SET_PIXEL_CMD:
                            next <= CMD_SET;
                        // next send slow control
                        `SEND_SLOW_CTRL_CMD:
                            next <= CMD_SEND_SLOW;
                        // next send DAC config
                        `SEND_DAC_CMD:
                            next <= CMD_SEND_DAC;
                        // next send sel pixel
                        `SEND_PIXEL_SEL_CMD:
                            next <= CMD_SEL_PIX;
                        // if the command is not known error
                        default:
                            next <= CMD_ERR;
                    endcase
                end else
                    // if no comms or command is available recheck
                    next <= CMD_EVAL;
            CMD_ERR:
                // it just stays here
                // TODO change
                next <= CMD_ERR;
            CMD_SET:
                if (uart_valid & data_available)
                    // if data has been read wait for new command
                    next <= CMD_EVAL;
                else
                    // if data is not fully read continue
                    next <= CMD_SET;
            CMD_SEND_SLOW:
                if (slow_ctrl_packet_available & ~slow_ctrl_packet_sent)
                    next <= CMD_SEND_SLOW;
                else
                    next <= CMD_EVAL;
            CMD_SEND_DAC:
                if (dac_packet_available & ~dac_packet_sent)
                    next <= CMD_SEND_DAC;
                else
                    next <= CMD_EVAL;
            CMD_SEL_PIX:
                if (sel_ckrow_sent & sel_ckcol_sent)
                    next <= CMD_EVAL;
                else
                    next <= CMD_SEL_PIX;
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

    // what to do on each state
    always_ff @(posedge ck, posedge reset) begin: state_machine_set_output
        if (reset) begin
            // reset all registers
            reset_reset();
            reset_div();
            reset_vars();
        end
        else begin
            case (state)
                RESET: begin
                    // reset all registers
                    reset_reset();
                    reset_div();
                    reset_vars();
                end
                CMD_EVAL: begin
                    // evaluate command if available
                    cmd <= uart_data[CMD_START_POS:CMD_END_POS];
                    signal <= uart_data[SIGNAL_START_POS:SIGNAL_END_POS];
                end
                CMD_SET: begin
                    case (cmd)
                        `SET_CK_CMD:
                            // set clocks divider
                            case (signal)
                                `SLOW_CTRL_CK_CODE:
                                    slow_ctrl_div <= uart_data;
                                `SEL_CK_CODE:
                                    sel_div <= uart_data;
                                `ADC_CK_CODE:
                                    adc_div <= uart_data;
                                `INJ_STB_CODE:
                                    inj_div <= uart_data;
                                `SER_CK_CODE:
                                    ser_div <= uart_data;
                                `DAC_SCK_CODE:
                                    dac_sck_div <= uart_data;
                            endcase
                        `SET_DELAY_CMD:
                            // set delay divider
                            case (signal)
                                `CSA_RESET_N_CODE:
                                    csa_reset_n_delay_div <= uart_data;
                                `SH_INF_CODE:
                                    sh_phi1d_inf_delay_div <= uart_data;
                                `SH_SUP_CODE:
                                    sh_phi1d_sup_delay_div <= uart_data;
                                `ADC_START_CODE:
                                    adc_start_delay_div <= uart_data;
                                `SER_RESET_N_CODE:
                                    ser_reset_n_delay_div <= uart_data;
                                `SER_READ_CODE:
                                    ser_read_delay_div <= uart_data;
                            endcase
                        `SET_HIGH_CMD:
                            // set HIGH divider
                            case (signal)
                                `CSA_RESET_N_CODE:
                                    csa_reset_n_HIGH_div <= uart_data;
                                `SH_INF_CODE:
                                    sh_phi1d_inf_HIGH_div <= uart_data;
                                `SH_SUP_CODE:
                                    sh_phi1d_sup_HIGH_div <= uart_data;
                                `ADC_START_CODE:
                                    adc_start_HIGH_div <= uart_data;
                                `SER_RESET_N_CODE:
                                    ser_reset_n_HIGH_div <= uart_data;
                                `SER_READ_CODE:
                                    ser_read_HIGH_div <= uart_data;
                            endcase
                        `SET_LOW_CMD:
                            // set HIGH divider
                            case (signal)
                                `CSA_RESET_N_CODE:
                                    csa_reset_n_LOW_div <= uart_data;
                                `SH_INF_CODE:
                                    sh_phi1d_inf_LOW_div <= uart_data;
                                `SH_SUP_CODE:
                                    sh_phi1d_sup_LOW_div <= uart_data;
                                `ADC_START_CODE:
                                    adc_start_LOW_div <= uart_data;
                                `SER_RESET_N_CODE:
                                    ser_reset_n_LOW_div <= uart_data;
                                `SER_READ_CODE:
                                    ser_read_LOW_div <= uart_data;
                            endcase
                        `SET_SLOW_CTRL_CMD: begin
                            if (uart_valid & ~uart_valid_last) begin
                                if (uart_data[UART_PACKET_SIZE-1] == LAST_UART_PACKET) begin
                                    // +: means starting from this bit get this much bits
                                    // assign byte0 = dword[0 +: 8];    // Same as dword[7:0]
                                    // 7 bits per assignment, not 8, cause the first is just the check
                                    slow_ctrl_packet[SLOW_CTRL_PACKET_LENGTH-UART_PACKET_SIZE+1 +: UART_PACKET_SIZE-1] <= uart_data[UART_PACKET_SIZE-2:0];
                                    slow_ctrl_packet_index <= '0;
                                    slow_ctrl_packet_available <= 1'b1;
                                end else begin
                                    slow_ctrl_packet[slow_ctrl_packet_index +: UART_PACKET_SIZE-1] <= uart_data[UART_PACKET_SIZE-2:0];
                                    slow_ctrl_packet_index <= slow_ctrl_packet_index + UART_PACKET_SIZE-1; // 7 bit per time
                                    slow_ctrl_packet_available <= 1'b0;
                                end
                            end
                        end
                        `SET_DAC_CMD: begin
                            if (uart_valid & ~uart_valid_last) begin
                                if (uart_data[UART_PACKET_SIZE-1] == LAST_UART_PACKET) begin
                                    // last 3 bits
                                    dac_packet[DAC_PACKET_LENGTH-1-3 +: 3] <= uart_data[2:0];
                                    dac_packet_index <= '0;
                                    dac_packet_available <= 1'b1;
                                end else begin
                                    dac_packet[dac_packet_index +: UART_PACKET_SIZE-1] <= uart_data[UART_PACKET_SIZE-2:0];
                                    dac_packet_index <= dac_packet_index + UART_PACKET_SIZE-1; // 7 bit per time
                                    dac_packet_available <= 1'b0;
                                end
                            end
                        end
                        `SET_PIXEL_CMD: begin
                            // set row/col number
                            case (signal)
                                `PIXEL_ROW_CODE:
                                    pixel_row <= uart_data;
                                `PIXEL_COL_CODE:
                                    pixel_col <= uart_data;
                            endcase
                        end
                    endcase
                end
                CMD_SEND_SLOW: begin
                    // this way we are checking on the falling edge and no ck is sent after the signal is on
                    if (slow_ctrl_packet_sent)
                        slow_ctrl_reset_n <= 1'b0;
                    else
                        slow_ctrl_reset_n <= 1'b1;
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
            endcase
        end
    end

    // if slow ctrl is posedge then data need to be transmitted
    always_ff @(posedge ck) begin: slow_ctrl_data_send
        if (slow_ctrl_reset_n) begin
            if (slow_ctrl_ck == 1'b0 && slow_ctrl_cnt == slow_ctrl_div-1) begin
                if (slow_ctrl_packet_index < SLOW_CTRL_PACKET_LENGTH) begin
                    slow_ctrl_in <= slow_ctrl_packet[slow_ctrl_packet_index];
                    slow_ctrl_packet_index <= slow_ctrl_packet_index + 1'b1;
                end else begin
                    // if everything was transmitted, reset index
                    slow_ctrl_packet_index <= 1'b0;
                    slow_ctrl_in <= 1'b0;
                end
            end
            else if (slow_ctrl_ck == 1'b1 && slow_ctrl_cnt == slow_ctrl_div-1) begin
                if (slow_ctrl_packet_index >= SLOW_CTRL_PACKET_LENGTH)
                    slow_ctrl_packet_sent <= 1'b1;
            end
        end
    end

    // if slow ctrl is posedge then data need to be transmitted
    always_ff @(posedge ck) begin: dac_data_sen
        if (~dac_sync_n) begin
            if (dac_sck == 1'b0 && dac_sck_cnt == dac_sck_div-1) begin
                if (dac_packet_index < DAC_PACKET_LENGTH) begin
                    dac_sdin <= dac_packet[dac_packet_index];
                    dac_packet_index <= dac_packet_index + 1'b1;
                end else begin
                    // if everything was transmitted, reset index
                    dac_packet_index <= 1'b0;
                    dac_sdin <= 1'b0;
                end
            end
            else if (dac_sck == 1'b1 && dac_sck_cnt == dac_sck_div-1) begin
                if (dac_packet_index >= DAC_PACKET_LENGTH)
                    dac_packet_sent <= 1'b1;
            end
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
            sel_ckrow_sent <= 1'b0;
        end
        // here one triggers if sel_init_n is low
        else if (~sel_init_n) begin
            // if posedge sel_ck
            if (sel_ck == 1'b0 && sel_cnt == sel_div-1) begin
                // row
                if (~sel_ckrow_sent) begin
                    if (sel_ckrow_cnt == pixel_row) begin
                        // if everything was transmitted, reset index
                        sel_ckrow <= 1'b0;
                        sel_ckrow_cnt <= '0;
                    end else begin
                        sel_ckrow <= ~sel_ck;
                        sel_ckrow_cnt <= sel_ckrow_cnt + 1'b1;
                    end
                end
                // col
                if (~sel_ckcol_sent) begin
                    if (sel_ckcol_cnt == pixel_col) begin
                        // if everything was transmitted, reset index
                        sel_ckcol <= 1'b0;
                        sel_ckcol_cnt <= '0;
                    end else begin
                        sel_ckcol <= ~sel_ck;
                        sel_ckcol_cnt <= sel_ckcol_cnt + 1'b1;
                    end
                end
            end
            // if negedge sel_ck
            else if (sel_ck == 1'b1 && sel_cnt == sel_div-1) begin
                // check on negedge to have it ready and not to waste a sel_ck
                if (sel_ckrow_cnt == pixel_row) begin
                    // if everything was transmitted, set sel_ckrow_sent
                    sel_ckrow_sent <= 1'b1;
                end
                if (sel_ckcol_cnt == pixel_col) begin
                    // if everything was transmitted, set sel_ckcol_sent
                    sel_ckcol_sent <= 1'b1;
                end
                if (~sel_ckrow_sent)
                    sel_ckrow <= ~sel_ck;
                if (~sel_ckcol_sent)
                    sel_ckcol <= ~sel_ck;
            end
        end
    end
//======================= END COMB and FF ================================

//======================= FUNCTIONS ======================================
// This function resets all the dividers
function void reset_div;
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
endfunction

// This function resets all the resets
function void reset_reset;
    slow_ctrl_reset_n <= 1'b0;
    dac_sync_n <= 1'b1;
    sel_init_n <= 1'b1;
    inj_start <= 1'b0;
endfunction

// This function resets all the variables
function void reset_vars;
    slow_ctrl_packet_available <= 1'b0;
    slow_ctrl_packet_sent <= 1'b0;
    dac_packet_available <= 1'b0;
    dac_packet_sent <= 1'b0;
    sel_ckcol_sent <= 1'b0;
    sel_ckrow_sent <= 1'b0;

    slow_ctrl_packet_index <= '0;
    slow_ctrl_packet <= '0;
    dac_packet_index <= '0;
    dac_packet <= '0;
    pixel_row <= '0;
    pixel_col <= '0;
    cmd <= '0;
    signal <= '0;

    inj_start <= '0;

    slow_ctrl_in <= '0;
    dac_sdin <= '0;
endfunction

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
