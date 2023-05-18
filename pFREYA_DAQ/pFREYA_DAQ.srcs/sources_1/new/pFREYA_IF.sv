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

    // state machine
    (* syn_encoding = "one-hot" *) enum logic [24:0] {
        SLOW_CTRL, SEND_DATA
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

    // state machine defs
    always_comb begin : state_machine
        case (state)
            SLOW_CTRL:
            default: 
        endcase
    end

endmodule
