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
        inout  logic sel_init_n,
        output logic sel_ckcol, sel_ckrow,
        input  logic ser_out,
        inout  logic ser_read, ser_reset_n,
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
    (* syn_encoding = "one-hot" *) enum logic [7:0] {
        RESET,
        CMD_EVAL,
        CMD_ERR,
        READ_REG_DATA,
        READ_DATA,
        DATA_END,
        SEND_DATA
    } state, next;

    // internal
    logic [SLOW_CNT_N-1:0] slow_ctrl_counter, slow_ctrl_divider;
    logic [ADC_CNT_N-1:0] adc_counter, adc_divider;
    logic [SER_CNT_N-1:0] ser_counter, ser_divider;

    // slow ctrl clock generation
    always_ff @(posedge ck, posedge reset) begin: slow_ctrl_ck_generation
        if (reset) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_counter <= '0;
            slow_ctrl_in <= 1'b0;
        end
        else if (~slow_ctrl_reset_n) begin
            slow_ctrl_ck <= 1'b0;
            slow_ctrl_counter <= '0;
            slow_ctrl_in <= 1'b0;
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

    // ADC clock generation
    always_ff @(posedge ck, posedge reset) begin: adc_ck_generation
        if (reset) begin
            adc_ck <= 1'b0;
            adc_counter <= '0;
            adc_in <= 1'b0;
        end
        else if (adc_start) begin
            adc_ck <= 1'b0;
            adc_counter <= '0;
            adc_in <= 1'b0;
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

    // serialiser clock generation
    always_ff @(posedge ck, posedge reset) begin: ser_ck_generation
        if (reset) begin
            ser_ck <= 1'b0;
            ser_counter <= '0;
            ser_in <= 1'b0;
        end
        else if (ser_start) begin
            ser_ck <= 1'b0;
            ser_counter <= '0;
            ser_in <= 1'b0;
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
                if (uart_valid)
                    next = CMD_EVAL;
                else
                    next = RESET;
            CMD_EVAL:
                case (cmd)
                    // if the command is a set one, next read which signal to set
                    `SET_CK_CMD,
                    `SET_DELAY_CMD,
                    `SET_PERIOD_CMD,
                    `SET_WIDTH_CMD,
                    `SET_SLOW_CTRL_CMD,
                    `SET_DAC_LVL_CMD,
                    `SET_PIXEL_CMD:
                        next = READ_DATA;
                    
                    default:
                        next = CMD_ERR;
                endcase
                cmd_available <= '0;
            CMD_ERR:
                next <= CMD_ERR;
            READ_DATA:
                if (uart_valid)
                    next = END_DATA;
                else
                    next = READ_DATA;
            END_DATA:
                
            default:
                next <= CMD_ERR;
        endcase
    end

    always_ff @(posedge clk, posedge reset) begin: state_machine_next
        if (reset)
            state <= RESET;
        else
            state <= next;
    end

    always_ff @(posedge clk, posedge reset) begin: state_machine_set_output
        if (reset)
            reset_all();
        else begin
            case (state)
                RESET:
                    reset_reg();
                CMD_EVAL:
                    // dont really know TODO
                READ_DATA:
                    if (uart_valid) begin
                        case (cmd_code)
                            `SET_CK_CMD:
                                set_ck_divider(signal_code, data);
                            `SET_DELAY_CMD:
                                set_fast_signal_delay(signal_code, data);
                            `SET_PERIOD_CMD:
                                set_fast_signal_period(signal_code, data);
                            `SET_WIDTH_CMD:
                                set_fast_signal_width(signal_code, data);
                        endcase
                    end
                
            endcase
        end
    end

    // function to reset all the signals and registers
    function reset_all();
        slow_ctrl_counter <= '0;
        slow_ctrl_divider <= '0;
        adc_counter <= '0;
        adc_divider <= '0;
        ser_counter <= '0;
        ser_divider <= '0;
    endfunction

    // function to reset all the registers
    function reset_reg();
    
    endfunction

    function set_ck_divider(signal_code, data);
        case (signal_code)
            `SLOW_CTRL_CK_CODE:
                slow_ctrl_divider <= data;
            `SEL_ROW_CK_CODE:
                sel_row_ck_divider <= data;
            `SEL_COL_CK_CODE:
                sel_col_ck_divider <= data;
            `ADC_CK_CODE:
                adc_ck_divider <= data;
            `INJ_DAC_CK_CODE:
                inj_dac_ck_divider <= data;
            `SER_CK_CODE:
                ser_ck_divider <= data;
        endcase
    endfunction

    function set_fast_signal_delay(signal_code, data);
        case (signal_code)
            `SLOW_CTRL_RESET_N_CODE:
                slow_ctrl_reset_n_code_delay <= data;
            `SEL_INIT_N_CODE:
                slow_ctrl_reset_n_code_delay <= data;
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
            'SER_READ_CODE:
                ser_read_code_delay <= data;
        endcase
    endfunction
    
    function set_fast_signal_period(signal_code, data);
        case (signal_code)
            `SLOW_CTRL_RESET_N_CODE:
                slow_ctrl_reset_n_code_period <= data;
            `SEL_INIT_N_CODE:
                slow_ctrl_reset_n_code_period <= data;
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
            'SER_READ_CODE:
                ser_read_code_period <= data;
        endcase
    endfunction

    function set_fast_signal_width(signal_code, data);
        case (signal_code)
            `SLOW_CTRL_RESET_N_CODE:
                slow_ctrl_reset_n_code_width <= data;
            `SEL_INIT_N_CODE:
                slow_ctrl_reset_n_code_width <= data;
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
            'SER_READ_CODE:
                ser_read_code_width <= data;
        endcase
    endfunction

endmodule
