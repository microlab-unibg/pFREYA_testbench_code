//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 05/18/2023 06:43:31 PM
// Design Name: 
// Module Name: pFREYA_defs
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

`ifndef DEFS
    `define DEFS

    package pFREYA_defs
    // Slow ctrl sizes
    parameter N_CSA_MODE  = 2;  // N of CSA mode bits
    parameter N_SHAP_MODE = 2;  // N of SHAP mode bits

    // Slow ctrl packet
    typedef struct packed {
        logic [N_CSA_MODE-1:0] csa_mode_n;
        logic inj_en_n;
        logic [N_SHAP_MODE-1:0] shap_mode;
        logic ch_en;
        logic inj_mode_n;
    } slow_ctrl_pack;

    // CK counter sizes
    `define SLOW_CNT_N '8
    `define SEL_CNT_N  '8
    `define ADC_CNT_N  '8
    `define INJ_CNT_N  '8
    `define SER_CNT_N  '8

    // Slow ctrl default values
    `define SLOW_CTRL_PACKET_LENGTH '7 * '8 * '2
    `define CSA_MODE_N_DEF          2'b10
    `define INJ_EN_N_DEF            1'b0
    `define SHAP_MODE_DEF           2'b10
    `define CH_EN_DEF               1'b1
    `define INJ_MODE_N_DEF          1'b0

    // UART command properties
    `define CMD_START_POS    7
    `define CMD_END_POS      5
    `define SIGNAL_START_POS 4
    `define SIGNAL_END_POS   2

    // UART commands
    `define UART_PACKET_SIZE   '8
    `define CMD_SIZE           '4
    `define SET_CK_CMD         4'b0000   // for general CK (calls for clock map)
    `define SET_DELAY_CMD      4'b0001   // for fast ctrl (call for fast control map)
    `define SET_PERIOD_CMD     4'b0010   // for fast ctrl
    `define SET_WIDTH_CMD      4'b0011   // for fast ctrl
    `define SET_SLOW_CTRL_CMD  4'b0100   // for slow ctrl
    `define SET_DAC_LVL_CMD    4'b0101   // for injection
    `define SET_PIXEL_CMD      4'b0110   // for pixel selection
    `define SEND_SLOW_CTRL_CMD 4'b0111   // for sending the slow ctrl to the asic
    `define SEND_PIXEL_SEL_CMD 4'b1000   // for sending the pixel selection to the asic

    // Clock map
    `define SLOW_CTRL_CK_CODE 3'b000
    `define SEL_CK_CODE       3'b001
    `define ADC_CK_CODE       3'b010
    `define INJ_DAC_CK_CODE   3'b011
    `define SER_CK_CODE       3'b100

    // Fast control map
    `define CSA_RESET_N_CODE       3'b000
    `define SH_INF_CODE            3'b001
    `define SH_SUP_CODE            3'b010
    `define ADC_START_CODE         3'b011
    `define SER_RESET_N_CODE       3'b100
    `define SER_READ_CODE          3'b101

    // cmd padding
    `define CMD_PADDING            2'b00
    endpackage

    import pFREYA_defs::*;
`endif
