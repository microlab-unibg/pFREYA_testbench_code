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
        // internal for timing
        input  logic ck, reset
    );

    // state machine code
    (* syn_encoding = "one-hot" *) enum logic [5:0] {
        RESET,
        CMD_EVAL,
        CMD_ERR,
        CMD_READ_DATA,
        SEND_SLOW_CTRL,
        SEND_PIXEL_SEL
    } state, next;

    // CK internal
    // generated with counters that reach a divisor
    logic [SLOW_CNT_N-1:0] slow_ctrl_counter, slow_ctrl_divider;
    logic [SEL_CNT_N-1:0] sel_counter, sel_divider;
    logic [ADC_CNT_N-1:0] adc_counter, adc_divider;
    logic [INJ_CNT_N-1:0] inj_counter, inj_divider;
    logic [SER_CNT_N-1:0] ser_counter, ser_divider;
    // for selection
    logic sel_ck, sel_in; // internal clock temporisation
    logic [PIXEL_COL_N-1:0] sel_ckcol_cnt;
    logic [PIXEL_ROW_N-1:0] sel_ckrow_cnt;
    // for injection
    logic inj_start;
    // fast control timing
    // generated with counter that reach a divisor, where the divisor changes based on flag
    // flag value is 0 for delay, 1 for HIGH, 2 for LOW (the actual polarity is in the name of the signal)
    logic [FAST_CTRL_N-1:0] csa_reset_n_flag, csa_reset_n_counter, csa_reset_n_delay_divider, csa_reset_n_HIGH_divider, csa_reset_n_LOW_divider;
    logic [FAST_CTRL_N-1:0] sh_inf_flag, sh_inf_counter, sh_inf_delay_divider, sh_inf_HIGH_divider, sh_inf_LOW_divider;
    logic [FAST_CTRL_N-1:0] sh_sup_flag, sh_sup_counter, sh_sup_delay_divider, sh_sup_HIGH_divider, sh_sup_LOW_divider;
    logic [FAST_CTRL_N-1:0] adc_start_flag, adc_start_counter, adc_start_delay_divider, adc_start_HIGH_divider, adc_start_LOW_divider;
    logic [FAST_CTRL_N-1:0] ser_reset_n_flag, ser_reset_n_counter, ser_reset_n_delay_divider, ser_reset_n_HIGH_divider, ser_reset_n_LOW_divider;
    logic [FAST_CTRL_N-1:0] ser_read_flag, ser_read_counter, ser_read_delay_divider, ser_read_HIGH_divider, ser_read_LOW_divider;

    // control logic
    logic uart_valid, cmd_available, data_available, slow_ctrl_packet_available, slow_ctrl_packet_sent, sel_available, sel_sent, pixel_available, sel_ckcol_sent, sel_ckrow_sent;
    // data
    logic [FAST_CTRL_N-1:0] slow_ctrl_packet_index;
    logic [UART_PACKET_SIZE-1:0] slow_ctrl_packet, pixel_row, pixel_col, data;
    logic [CMD_SIZE-1:0] cmd;
    logic [DATA_SIZE-1:0] signal;

//======================= COMB and FF ================================
    // slow ctrl clock generation
    always_ff @(posedge ck, posedge reset) begin: slow_ctrl_ck_generation
        if (reset) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_counter <= '0;
        end
        else if (~slow_ctrl_reset_n) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_counter <= '0;
        end
        else if (slow_ctrl_counter == slow_ctrl_divider) begin
            slow_ctrl_ck <= ~slow_ctrl_ck;
            slow_ctrl_counter <= '0;
        end
        else begin
            slow_ctrl_ck <= slow_ctrl_ck;
            slow_ctrl_counter <= slow_ctrl_counter + 1'b1;
        end
    end

    // Pixel selection clock generation (to temporise col and row)
    always_ff @(posedge ck, posedge reset) begin: sel_ck_generation
        if (reset) begin
            sel_ck <= 1'b0;
            sel_counter <= '0;
        end
        else if (~sel_init_n) begin
            sel_ck <= 1'b0;
            sel_counter <= '0;
        end
        else if (sel_counter == sel_divider) begin
            sel_ck <= ~sel_ck;
            sel_counter <= '0;
        end
        else begin
            sel_ck <= sel_ck;
            sel_counter <= sel_counter + 1'b1;
        end
    end

    // ADC clock generation
    always_ff @(posedge ck, posedge reset) begin: adc_ck_generation
        if (reset) begin
            adc_ck <= 1'b0;
            adc_counter <= '0;
        end
        else if (adc_start) begin
            adc_ck <= 1'b0;
            adc_counter <= '0;
        end
        else if (adc_counter == adc_divider) begin
            adc_ck <= ~adc_ck;
            adc_counter <= '0;
        end
        else begin
            adc_ck <= adc_ck;
            adc_counter <= adc_counter + 1'b1;
        end
    end

    // INJ strobe generation
    always_ff @(posedge ck, posedge reset) begin: inj_stb_generation
        if (reset) begin
            inj_stb <= 1'b0;
            inj_counter <= '0;
        end
        else if (inj_start) begin
            inj_stb <= 1'b0;
            inj_counter <= '0;
        end
        else if (inj_counter == inj_divider) begin
            inj_stb <= ~inj_stb;
            inj_counter <= '0;
        end
        else begin
            inj_stb <= inj_stb;
            inj_counter <= inj_counter + 1'b1;
        end
    end

    // serialiser clock generation
    always_ff @(posedge ck, posedge reset) begin: ser_ck_generation
        if (reset) begin
            ser_ck <= 1'b0;
            ser_counter <= '0;
        end
        else if (~ser_reset_n) begin
            ser_ck <= 1'b0;
            ser_counter <= '0;
        end
        else if (ser_counter == ser_divider) begin
            ser_ck <= ~ser_ck;
            ser_counter <= '0;
        end
        else begin
            ser_ck <= ser_ck;
            ser_counter <= ser_counter + 1'b1;
        end
    end

    // state machine control
    always_comb begin : state_machine_ctrl
        case (state)
            RESET:
                next = CMD_EVAL;
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
                        `SET_DAC_LVL_CMD,
                        `SET_PIXEL_CMD:
                            next = CMD_SET;
                        // next send slow control
                        `SEND_SLOW_CTRL_CMD:
                            next = CMD_SEND_SLOW;
                        // next send slow control
                        `SEND_PIXEL_SEL_CMD:
                            next = CMD_SEL_PIX;
                        // if the command is not known error
                        default:
                            next = CMD_ERR;
                    endcase
                end else
                    // if no comms or command is available recheck
                    next = CMD_EVAL;
            CMD_ERR:
                // it just stays here
                // TODO change
                next <= CMD_ERR;
            CMD_SET:
                if (data_available)
                    // if data has been read wait for new command
                    next = CMD_EVAL;
                else
                    // if data is not fully read continue
                    next = CMD_SET;
            CMD_SEND_SLOW:
                if (slow_ctrl_packet_available & ~slow_ctrl_packet_sent)
                    next = CMD_SEND_SLOW;
                else
                    next = CMD_EVAL;
            CMD_SEL_PIX:
                if (sel_available & ~sel_sent)
                    next = CMD_SEL_PIX;
                else
                    next = CMD_EVAL;
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

    // what to do on each state
    always_ff @(posedge ck, posedge reset) begin: state_machine_set_output
        if (reset)
            // reset all registers
            slow_ctrl_counter <= '0;
            slow_ctrl_divider <= '0;
            adc_counter <= '0;
            adc_divider <= '0;
            ser_counter <= '0;
            ser_divider <= '0;
        else begin
            case (state)
                RESET:
                    // reset all registers
                    slow_ctrl_counter <= '0;
                    slow_ctrl_divider <= '0;
                    adc_counter <= '0;
                    adc_divider <= '0;
                    ser_counter <= '0;
                    ser_divider <= '0;
                CMD_EVAL: begin
                    // keep unused register values
                    slow_ctrl_counter <= slow_ctrl_counter;
                    slow_ctrl_divider <= slow_ctrl_divider;
                    adc_counter <= adc_counter;
                    adc_divider <= adc_divider;
                    ser_counter <= ser_divider;
                    ser_counter <= ser_counter;
                    // evaluate command if available
                    if (uart_valid) begin
                        cmd <= data[CMD_START_POS:CMD_END_POS];
                        cmd_available <= 1'b1;
                    end
                end
                CMD_SET: begin
                    // command to set signals specified by signal code
                    signal <= data[SIGNAL_START_POS:SIGNAL_END_POS];
                    // keep every signal flag
                    csa_reset_n_flag <= csa_reset_n_flag;
                    sh_inf_flag <= sh_inf_flag;
                    sh_sup_flag <= sh_sup_flag;
                    adc_start_flag <= adc_start_flag;
                    ser_reset_n_flag <= ser_reset_n_flag;
                    ser_read_flag <= ser_read_flag;
                    // update cmd and data availability
                    data_available <= 1'b1;
                    cmd_available <= 1'b0;
                    case (cmd)
                        `SET_CK_CMD:
                            // keep wahtever is not a divider
                            slow_ctrl_counter <= slow_ctrl_counter;
                            adc_counter <= adc_counter;
                            ser_counter <= ser_counter;
                            sel_counter <= sel_counter;
                            inj_counter <= inj_counter;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                            csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                            csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_delay_divider <= sh_inf_delay_divider;
                            sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                            sh_inf_LOW_divider <= sh_inf_LOW_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_delay_divider <= sh_sup_delay_divider;
                            sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                            sh_sup_LOW_divider <= sh_sup_LOW_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_delay_divider <= adc_start_delay_divider;
                            adc_start_HIGH_divider <= adc_start_HIGH_divider;
                            adc_start_LOW_divider <= adc_start_LOW_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                            ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                            ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_delay_divider <= ser_read_delay_divider;
                            ser_read_HIGH_divider <= ser_read_HIGH_divider;
                            ser_read_LOW_divider <= ser_read_LOW_divider;
                            slow_ctrl_packet <= slow_ctrl_packet;
                            slow_ctrl_packet_index <= slow_ctrl_packet_index;
                            slow_ctrl_packet_available <= slow_ctrl_packet_available;
                            pixel_row <= pixel_row;
                            pixel_col <= pixel_col;
                            pixel_available <= pixel_available;
                            // set clocks divider
                            case (signal)
                                `SLOW_CTRL_CK:
                                    slow_ctrl_divider <= data;
                                    adc_divider <= adc_divider;
                                    ser_divider <= ser_divider;
                                    sel_divider <= sel_divider;
                                    inj_divider <= inj_divider;
                                `SEL_CK:
                                    slow_ctrl_divider <= slow_ctrl_divider;
                                    adc_divider <= adc_divider;
                                    ser_divider <= ser_divider;
                                    sel_divider <= data;
                                    inj_divider <= inj_divider;
                                `ADC_CK:
                                    slow_ctrl_divider <= slow_ctrl_divider;
                                    adc_divider <= data;
                                    ser_divider <= ser_divider;
                                    sel_divider <= sel_divider;
                                    inj_divider <= inj_divider;
                                `INJ_DAC_CK:
                                    slow_ctrl_divider <= slow_ctrl_divider;
                                    adc_divider <= adc_divider;
                                    ser_divider <= ser_divider;
                                    sel_divider <= sel_divider;
                                    inj_divider <= data;
                                `SER_CK:
                                    slow_ctrl_divider <= slow_ctrl_divider;
                                    adc_divider <= adc_divider;
                                    ser_divider <= data;
                                    sel_divider <= sel_divider;
                                    inj_divider <= inj_divider;
                            endcase
                        `SET_DELAY_CMD:
                            // keep everything that is not a delay divider
                            slow_ctrl_counter <= slow_ctrl_counter;
                            slow_ctrl_divider <= slow_ctrl_divider;
                            adc_counter <= adc_counter;
                            adc_divider <= adc_divider;
                            ser_counter <= ser_counter;
                            ser_divider <= ser_divider;
                            sel_counter <= sel_counter;
                            sel_divider <= sel_divider;
                            inj_counter <= inj_counter;
                            inj_divider <= inj_divider;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                            csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                            sh_inf_LOW_divider <= sh_inf_LOW_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                            sh_sup_LOW_divider <= sh_sup_LOW_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_HIGH_divider <= adc_start_HIGH_divider;
                            adc_start_LOW_divider <= adc_start_LOW_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                            ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_HIGH_divider <= ser_read_HIGH_divider;
                            ser_read_LOW_divider <= ser_read_LOW_divider;
                            slow_ctrl_packet <= slow_ctrl_packet;
                            slow_ctrl_packet_index <= slow_ctrl_packet_index;
                            slow_ctrl_packet_available <= slow_ctrl_packet_available;
                            pixel_row <= pixel_row;
                            pixel_col <= pixel_col;
                            pixel_available <= pixel_available;
                            // set delay divider
                            case (signal)
                                `CSA_RESET_N:
                                    csa_reset_n_delay_divider <= data;
                                    sh_inf_delay_divider <= sh_inf_delay_divider;
                                    sh_sup_delay_divider <= sh_sup_delay_divider;
                                    adc_start_delay_divider <= adc_start_delay_divider;
                                    ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                                    ser_read_delay_divider <= ser_read_delay_divider;
                                `SH_INF:
                                    csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                                    sh_inf_delay_divider <= data;
                                    sh_sup_delay_divider <= sh_sup_delay_divider;
                                    adc_start_delay_divider <= adc_start_delay_divider;
                                    ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                                    ser_read_delay_divider <= ser_read_delay_divider;
                                `SH_SUP:
                                    csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                                    sh_inf_delay_divider <= sh_inf_delay_divider;
                                    sh_sup_delay_divider <= data;
                                    adc_start_delay_divider <= adc_start_delay_divider;
                                    ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                                    ser_read_delay_divider <= ser_read_delay_divider;
                                `ADC_START:
                                    csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                                    sh_inf_delay_divider <= sh_inf_delay_divider;
                                    sh_sup_delay_divider <= sh_sup_delay_divider;
                                    adc_start_delay_divider <= data;
                                    ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                                    ser_read_delay_divider <= ser_read_delay_divider;
                                `SER_RESET_N:
                                    csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                                    sh_inf_delay_divider <= sh_inf_delay_divider;
                                    sh_sup_delay_divider <= sh_sup_delay_divider;
                                    adc_start_delay_divider <= adc_start_delay_divider;
                                    ser_reset_n_delay_divider <= data;
                                    ser_read_delay_divider <= ser_read_delay_divider;
                                `SER_READ:
                                    csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                                    sh_inf_delay_divider <= sh_inf_delay_divider;
                                    sh_sup_delay_divider <= sh_sup_delay_divider;
                                    adc_start_delay_divider <= adc_start_delay_divider;
                                    ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                                    ser_read_delay_divider <= data;
                            endcase
                        `SET_HIGH_CMD:
                            // keep everything that is not a HIGH divider
                            slow_ctrl_counter <= slow_ctrl_counter;
                            slow_ctrl_divider <= slow_ctrl_divider;
                            adc_counter <= adc_counter;
                            adc_divider <= adc_divider;
                            ser_counter <= ser_counter;
                            ser_divider <= ser_divider;
                            sel_counter <= sel_counter;
                            sel_divider <= sel_divider;
                            inj_counter <= inj_counter;
                            inj_divider <= inj_divider;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                            csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_delay_divider <= sh_inf_delay_divider;
                            sh_inf_LOW_divider <= sh_inf_LOW_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_delay_divider <= sh_sup_delay_divider;
                            sh_sup_LOW_divider <= sh_sup_LOW_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_delay_divider <= adc_start_delay_divider;
                            adc_start_LOW_divider <= adc_start_LOW_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                            ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_delay_divider <= ser_read_delay_divider;
                            ser_read_LOW_divider <= ser_read_LOW_divider;
                            slow_ctrl_packet <= slow_ctrl_packet;
                            slow_ctrl_packet_index <= slow_ctrl_packet_index;
                            slow_ctrl_packet_available <= slow_ctrl_packet_available;
                            pixel_row <= pixel_row;
                            pixel_col <= pixel_col;
                            pixel_available <= pixel_available;
                            // set HIGH divider
                            case (signal)
                                `CSA_RESET_N:
                                    csa_reset_n_HIGH_divider <= data;
                                    sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                                    sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                                    adc_start_HIGH_divider <= adc_start_HIGH_divider;
                                    ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                                    ser_read_HIGH_divider <= ser_read_HIGH_divider;
                                `SH_INF:
                                    csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                                    sh_inf_HIGH_divider <= data;
                                    sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                                    adc_start_HIGH_divider <= adc_start_HIGH_divider;
                                    ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                                    ser_read_HIGH_divider <= ser_read_HIGH_divider;
                                `SH_SUP:
                                    csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                                    sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                                    sh_sup_HIGH_divider <= data;
                                    adc_start_HIGH_divider <= adc_start_HIGH_divider;
                                    ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                                    ser_read_HIGH_divider <= ser_read_HIGH_divider;
                                `ADC_START:
                                    csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                                    sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                                    sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                                    adc_start_HIGH_divider <= data;
                                    ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                                    ser_read_HIGH_divider <= ser_read_HIGH_divider;
                                `SER_RESET_N:
                                    csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                                    sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                                    sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                                    adc_start_HIGH_divider <= adc_start_HIGH_divider;
                                    ser_reset_n_HIGH_divider <= data;
                                    ser_read_HIGH_divider <= ser_read_HIGH_divider;
                                `SER_READ:
                                    csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                                    sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                                    sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                                    adc_start_HIGH_divider <= adc_start_HIGH_divider;
                                    ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                                    ser_read_HIGH_divider <= data;
                            endcase
                        `SET_LOW_CMD:
                            // keep everything that is not a LOW divider
                            slow_ctrl_counter <= slow_ctrl_counter;
                            slow_ctrl_divider <= slow_ctrl_divider;
                            adc_counter <= adc_counter;
                            adc_divider <= adc_divider;
                            ser_counter <= ser_counter;
                            ser_divider <= ser_divider;
                            sel_counter <= sel_counter;
                            sel_divider <= sel_divider;
                            inj_counter <= inj_counter;
                            inj_divider <= inj_divider;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                            csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_delay_divider <= sh_inf_delay_divider;
                            sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_delay_divider <= sh_sup_delay_divider;
                            sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_delay_divider <= adc_start_delay_divider;
                            adc_start_HIGH_divider <= adc_start_HIGH_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                            ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_delay_divider <= ser_read_delay_divider;
                            ser_read_HIGH_divider <= ser_read_HIGH_divider;
                            slow_ctrl_packet <= slow_ctrl_packet;
                            slow_ctrl_packet_index <= slow_ctrl_packet_index;
                            slow_ctrl_packet_available <= slow_ctrl_packet_available;
                            pixel_row <= pixel_row;
                            pixel_col <= pixel_col;
                            pixel_available <= pixel_available;
                            case (signal)
                                `CSA_RESET_N:
                                    csa_reset_n_LOW_divider <= data;
                                    sh_inf_LOW_divider <= sh_inf_LOW_divider;
                                    sh_sup_LOW_divider <= sh_sup_LOW_divider;
                                    adc_start_LOW_divider <= adc_start_LOW_divider;
                                    ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                                    ser_read_LOW_divider <= ser_read_LOW_divider;
                                `SH_INF:
                                    csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                                    sh_inf_LOW_divider <= data;
                                    sh_sup_LOW_divider <= sh_sup_LOW_divider;
                                    adc_start_LOW_divider <= adc_start_LOW_divider;
                                    ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                                    ser_read_LOW_divider <= ser_read_LOW_divider;
                                `SH_SUP:
                                    csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                                    sh_inf_LOW_divider <= sh_inf_LOW_divider;
                                    sh_sup_LOW_divider <= data;
                                    adc_start_LOW_divider <= adc_start_LOW_divider;
                                    ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                                    ser_read_LOW_divider <= ser_read_LOW_divider;
                                `ADC_START:
                                    csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                                    sh_inf_LOW_divider <= sh_inf_LOW_divider;
                                    sh_sup_LOW_divider <= sh_sup_LOW_divider;
                                    adc_start_LOW_divider <= data;
                                    ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                                    ser_read_LOW_divider <= ser_read_LOW_divider;
                                `SER_RESET_N:
                                    csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                                    sh_inf_LOW_divider <= sh_inf_LOW_divider;
                                    sh_sup_LOW_divider <= sh_sup_LOW_divider;
                                    adc_start_LOW_divider <= adc_start_LOW_divider;
                                    ser_reset_n_LOW_divider <= data;
                                    ser_read_LOW_divider <= ser_read_LOW_divider;
                                `SER_READ:
                                    csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                                    sh_inf_LOW_divider <= sh_inf_LOW_divider;
                                    sh_sup_LOW_divider <= sh_sup_LOW_divider;
                                    adc_start_LOW_divider <= adc_start_LOW_divider;
                                    ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                                    ser_read_LOW_divider <= data;
                            endcase
                        `SET_SLOW_CTRL_CMD:
                            // keep everything that is not slow ctrl packet
                            slow_ctrl_counter <= slow_ctrl_counter;
                            slow_ctrl_divider <= slow_ctrl_divider;
                            adc_counter <= adc_counter;
                            adc_divider <= adc_divider;
                            ser_counter <= ser_counter;
                            ser_divider <= ser_divider;
                            sel_counter <= sel_counter;
                            sel_divider <= sel_divider;
                            inj_counter <= inj_counter;
                            inj_divider <= inj_divider;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                            csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                            csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_delay_divider <= sh_inf_delay_divider;
                            sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                            sh_inf_LOW_divider <= sh_inf_LOW_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_delay_divider <= sh_sup_delay_divider;
                            sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                            sh_sup_LOW_divider <= sh_sup_LOW_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_delay_divider <= adc_start_delay_divider;
                            adc_start_HIGH_divider <= adc_start_HIGH_divider;
                            adc_start_LOW_divider <= adc_start_LOW_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                            ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                            ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_delay_divider <= ser_read_delay_divider;
                            ser_read_HIGH_divider <= ser_read_HIGH_divider;
                            ser_read_LOW_divider <= ser_read_LOW_divider;
                            pixel_row <= pixel_row;
                            pixel_col <= pixel_col;
                            pixel_available <= pixel_available;

                            slow_ctrl_packet <= data;
                            slow_ctrl_packet_index <= '0;
                            slow_ctrl_packet_available <= 1'b1;
                        `SET_PIXEL_CMD:
                            slow_ctrl_counter <= slow_ctrl_counter;
                            slow_ctrl_divider <= slow_ctrl_divider;
                            adc_counter <= adc_counter;
                            adc_divider <= adc_divider;
                            ser_counter <= ser_counter;
                            ser_divider <= ser_divider;
                            sel_counter <= sel_counter;
                            sel_divider <= sel_divider;
                            inj_counter <= inj_counter;
                            inj_divider <= inj_divider;
                            csa_reset_n_counter <= csa_reset_n_counter;
                            csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
                            csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
                            csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
                            sh_inf_counter <= sh_inf_counter;
                            sh_inf_delay_divider <= sh_inf_delay_divider;
                            sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
                            sh_inf_LOW_divider <= sh_inf_LOW_divider;
                            sh_sup_counter <= sh_sup_counter;
                            sh_sup_delay_divider <= sh_sup_delay_divider;
                            sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
                            sh_sup_LOW_divider <= sh_sup_LOW_divider;
                            adc_start_counter <= adc_start_counter;
                            adc_start_delay_divider <= adc_start_delay_divider;
                            adc_start_HIGH_divider <= adc_start_HIGH_divider;
                            adc_start_LOW_divider <= adc_start_LOW_divider;
                            ser_reset_n_counter <= ser_reset_n_counter;
                            ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
                            ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
                            ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
                            ser_read_counter <= ser_read_counter;
                            ser_read_delay_divider <= ser_read_delay_divider;
                            ser_read_HIGH_divider <= ser_read_HIGH_divider;
                            ser_read_LOW_divider <= ser_read_LOW_divider;
                            slow_ctrl_packet <= slow_ctrl_packet;
                            slow_ctrl_packet_index <= slow_ctrl_packet_index;
                            slow_ctrl_packet_available <= slow_ctrl_packet_available;

                            pixel_row <= data;
                            pixel_col <= data;
                            pixel_available <= 1'b1;
                    endcase
                end
                CMD_SEND_SLOW: begin
                    if (slow_ctrl_packet_sent)
                        slow_ctrl_reset_n <= 1'b0;
                    else
                        slow_ctrl_reset_n <= 1'b1;
                end
                CMD_SEL_PIX: begin
                    if (sel_sent)
                        sel_init_n <= 1'b1;
                    else
                        sel_init_n <= 1'b0;
                end
            endcase
        end
    end

    // if slow ctrl is posedge then data need to be transmitted
    always_ff @(posedge slow_ctrl_ck, posedge reset) begin: slow_ctrl_data_send
        if (slow_ctrl_reset_n) begin
            if (slow_ctrl_packet_index < SLOW_CTRL_PACKET_LENGTH) begin
                slow_ctrl_in <= slow_ctrl_packet[slow_ctrl_packet_index];
                slow_ctrl_packet_index <= slow_ctrl_packet_index + 1'b1;
                slow_ctrl_packet_sent <= 1'b0;
            end else begin
                // if everything was transmitted, reset index
                slow_ctrl_packet_index <= 1'b0;
                slow_ctrl_packet_sent <= 1'b1;
                slow_ctrl_in <= 1'b0;
            end
        end
    end

    // if sel_ck is posedge then col or row ck might need to commute
    always_ff @(posedge sel_ck, posedge reset) begin: pixel_sel_send_posedge
        if (~sel_init_n) begin
            // row
            if (sel_ckrow_cnt < pixel_row) begin
                sel_ckrow <= sel_ck;
                sel_ckrow_cnt <= sel_ckrow_cnt + 1'b1;
                sel_sent <= 1'b0;
            end else begin
                // if everything was transmitted, reset index
                sel_ckrow_cnt <= 1'b0;
                sel_ckrow_sent <= 1'b1;
                sel_sent <= sel_ckcol_sent & 1'b1;
            end
            // col
            if (sel_ckcol_cnt < pixel_col) begin
                sel_ckcol <= sel_ck;
                sel_ckcol_cnt <= sel_ckcol_cnt + 1'b1;
                sel_sent <= 1'b0;
            end else begin
                // if everything was transmitted, reset index
                sel_ckcol_cnt <= 1'b0;
                sel_ckcol_sent <= 1'b1;
                sel_sent <= sel_ckrow_sent & 1'b1;
            end
        end
    end

    // if sel_ck is negedge then col or row ck might need to commute
    always_ff @(negedge sel_ck) begin: pixel_sel_send_negedge
        if (~sel_init_n) begin
            // row
            if (sel_ckrow_cnt < pixel_row) begin
                sel_ckrow <= sel_ck;
                // don't count or it will count twice one per edge
            end
            // col
            if (sel_ckcol_cnt < pixel_col) begin
                sel_ckcol <= sel_ck;
                // don't count or it will count twice one per edge
            end
        end
    end
//======================= END COMB and FF ================================

// data keep from one clock to the other
/*
slow_ctrl_counter <= slow_ctrl_counter;
slow_ctrl_divider <= slow_ctrl_divider;
adc_counter <= adc_counter;
adc_divider <= adc_divider;
ser_counter <= ser_counter;
ser_divider <= ser_divider;
sel_counter <= sel_counter;
sel_divider <= sel_divider;
inj_counter <= inj_counter;
inj_divider <= inj_divider;
csa_reset_n_flag <= csa_reset_n_flag;
csa_reset_n_counter <= csa_reset_n_counter;
csa_reset_n_delay_divider <= csa_reset_n_delay_divider;
csa_reset_n_HIGH_divider <= csa_reset_n_HIGH_divider;
csa_reset_n_LOW_divider <= csa_reset_n_LOW_divider;
sh_inf_flag <= sh_inf_flag;
sh_inf_counter <= sh_inf_counter;
sh_inf_delay_divider <= sh_inf_delay_divider;
sh_inf_HIGH_divider <= sh_inf_HIGH_divider;
sh_inf_LOW_divider <= sh_inf_LOW_divider;
sh_sup_flag <= sh_sup_flag;
sh_sup_counter <= sh_sup_counter;
sh_sup_delay_divider <= sh_sup_delay_divider;
sh_sup_HIGH_divider <= sh_sup_HIGH_divider;
sh_sup_LOW_divider <= sh_sup_LOW_divider;
adc_start_flag <= adc_start_flag;
adc_start_counter <= adc_start_counter;
adc_start_delay_divider <= adc_start_delay_divider;
adc_start_HIGH_divider <= adc_start_HIGH_divider;
adc_start_LOW_divider <= adc_start_LOW_divider;
ser_reset_n_flag <= ser_reset_n_flag;
ser_reset_n_counter <= ser_reset_n_counter;
ser_reset_n_delay_divider <= ser_reset_n_delay_divider;
ser_reset_n_HIGH_divider <= ser_reset_n_HIGH_divider;
ser_reset_n_LOW_divider <= ser_reset_n_LOW_divider;
ser_read_flag <= ser_read_flag;
ser_read_counter <= ser_read_counter;
ser_read_delay_divider <= ser_read_delay_divider;
ser_read_HIGH_divider <= ser_read_HIGH_divider;
ser_read_LOW_divider <= ser_read_LOW_divider;
slow_ctrl_packet <= slow_ctrl_packet;
slow_ctrl_packet_index <= slow_ctrl_packet_index;
slow_ctrl_packet_available <= slow_ctrl_packet_available;
pixel_row <= pixel_row;
pixel_col <= pixel_col;
pixel_available <= pixel_available;
*/

endmodule
