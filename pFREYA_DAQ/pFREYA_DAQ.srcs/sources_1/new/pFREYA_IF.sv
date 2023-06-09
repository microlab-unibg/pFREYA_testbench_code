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
    logic [FAST_CTRL_N-1:0] csa_reset_n_code_delay, csa_reset_n_code_period, csa_reset_n_code_width;
    logic [FAST_CTRL_N-1:0] sh_inf_code_delay, sh_inf_code_period, sh_inf_code_width;
    logic [FAST_CTRL_N-1:0] sh_sup_code_delay, sh_sup_code_period, sh_sup_code_width;
    logic [FAST_CTRL_N-1:0] adc_start_code_delay, adc_start_code_period, adc_start_code_width;
    logic [FAST_CTRL_N-1:0] ser_reset_n_code_delay, ser_reset_n_code_period, ser_reset_n_code_width;
    logic [FAST_CTRL_N-1:0] ser_read_code_delay, ser_read_code_period, ser_read_code_width;

    // control logic
    logic uart_valid, cmd_available, data_available, slow_ctrl_packet_available, slow_ctrl_packet_sent, sel_available, sel_sent, pixel_available, sel_ckcol_sent, sel_ckrow_sent;
    // data
    logic slow_ctrl_packet_index;
    logic [UART_PACKET_SIZE-1:0] slow_ctrl_packet, pixel_row, pixel_col, data;
    logic [CMD_CODE_SIZE-1:0] cmd_code;
    logic [DATA_SIZE-1:0] signal_code;

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
                    case (cmd_code)
                        // if the command is a known one
                        // next read which signal to set
                        `SET_CK_CMD,
                        `SET_DELAY_CMD,
                        `SET_PERIOD_CMD,
                        `SET_WIDTH_CMD,
                        `SET_SLOW_CTRL_CMD,
                        `SET_DAC_LVL_CMD,
                        `SET_PIXEL_CMD:
                            next = CMD_READ_DATA;
                        // next send slow control
                        `SEND_SLOW_CTRL_CMD:
                            next = SEND_SLOW_CTRL;
                        // next send slow control
                        `SEND_PIXEL_SEL_CMD:
                            next = SEND_PIXEL_SEL;
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
            CMD_READ_DATA:
                if (data_available)
                    // if data has been read wait for new command
                    next = CMD_EVAL;
                else
                    // if data is not fully read continue
                    next = CMD_READ_DATA;
            SEND_SLOW_CTRL:
                if (slow_ctrl_packet_available & ~slow_ctrl_packet_sent)
                    next = SEND_SLOW_CTRL;
                else
                    next = CMD_EVAL;
            SEND_PIXEL_SEL:
                if (sel_available & ~sel_sent)
                    next = SEND_PIXEL_SEL;
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
            reset_all();
        else begin
            case (state)
                RESET:
                    reset_all();
                CMD_EVAL: begin
                    keep_reg();
                    if (uart_valid) begin
                        cmd_code <= data[CMD_START_POS:CMD_END_POS];
                        cmd_available <= 1'b1;
                    end
                end
                CMD_READ_DATA: begin
                    keep_reg();
                    signal_code <= data[SIGNAL_START_POS:SIGNAL_END_POS];
                    case (cmd_code)
                        `SET_CK_CMD:
                            set_ck_divider(signal_code, data);
                        `SET_DELAY_CMD:
                            set_fast_signal_delay(signal_code, data);
                        `SET_PERIOD_CMD:
                            set_fast_signal_period(signal_code, data);
                        `SET_WIDTH_CMD:
                            set_fast_signal_width(signal_code, data);
                        `SET_SLOW_CTRL_CMD:
                            set_slow_ctrl(data);
                        `SET_PIXEL_CMD:
                            set_pixel(data);
                    endcase
                    data_available <= 1'b1;
                    cmd_available <= 1'b0;
                end
                SEND_SLOW_CTRL: begin
                    if (slow_ctrl_packet_sent)
                        slow_ctrl_reset_n <= 1'b0;
                    else
                        slow_ctrl_reset_n <= 1'b1;
                end
                SEND_PIXEL_SEL: begin
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

//======================= FUNCTIONS ================================
    // function to reset all the signals and registers
    function reset_all();
        slow_ctrl_counter <= '0;
        slow_ctrl_divider <= '0;
        adc_counter <= '0;
        adc_divider <= '0;
        ser_counter <= '0;
        ser_divider <= '0;
    endfunction

    // function to keep data as it was the previous step
    function keep_reg();
        slow_ctrl_counter <= slow_ctrl_counter;
        slow_ctrl_divider <= slow_ctrl_divider;
        adc_counter <= adc_counter;
        adc_divider <= adc_divider;
        ser_counter <= ser_divider;
        ser_counter <= ser_counter;
    endfunction

    function set_ck_divider(signal_code, data);
        case (signal_code)
            `SLOW_CTRL_CK_CODE:
                slow_ctrl_divider <= data;
            `SEL_CK_CODE:
                sel_divider <= data;
            `ADC_CK_CODE:
                adc_divider <= data;
            `INJ_DAC_CK_CODE:
                inj_divider <= data;
            `SER_CK_CODE:
                ser_divider <= data;
        endcase
    endfunction

    function set_fast_signal_delay(signal_code, data);
        case (signal_code)
            `CSA_RESET_N_CODE:
                csa_reset_n_code_delay <= data;
            `SH_INF_CODE:
                sh_inf_code_delay <= data;
            `SH_SUP_CODE:
                sh_sup_code_delay <= data;
            `ADC_START_CODE:
                adc_start_code_delay <= data;
            `SER_RESET_N_CODE:
                ser_reset_n_code_delay <= data;
            `SER_READ_CODE:
                ser_read_code_delay <= data;
        endcase
    endfunction
    
    function set_fast_signal_period(signal_code, data);
        case (signal_code)
            `CSA_RESET_N_CODE:
                csa_reset_n_code_period <= data;
            `SH_INF_CODE:
                sh_inf_code_period <= data;
            `SH_SUP_CODE:
                sh_sup_code_period <= data;
            `ADC_START_CODE:
                adc_start_code_period <= data;
            `SER_RESET_N_CODE:
                ser_reset_n_code_period <= data;
            `SER_READ_CODE:
                ser_read_code_period <= data;
        endcase
    endfunction

    function set_fast_signal_width(signal_code, data);
        case (signal_code)
            `CSA_RESET_N_CODE:
                csa_reset_n_code_width <= data;
            `SH_INF_CODE:
                sh_inf_code_width <= data;
            `SH_SUP_CODE:
                sh_sup_code_width <= data;
            `ADC_START_CODE:
                adc_start_code_width <= data;
            `SER_RESET_N_CODE:
                ser_reset_n_code_width <= data;
            `SER_READ_CODE:
                ser_read_code_width <= data;
        endcase
    endfunction

    function set_slow_ctrl(data);
        slow_ctrl_packet <= data;
        slow_ctrl_packet_index <= '0;
        slow_ctrl_packet_available <= 1'b1;
    endfunction
    
    function set_pixel(data);
        pixel_row <= data;
        pixel_col <= data;
        pixel_available <= 1'b1;
    endfunction
//======================= END FUNCTIONS ================================

endmodule
