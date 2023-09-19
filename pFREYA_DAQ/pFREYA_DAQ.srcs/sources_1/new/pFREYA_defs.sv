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

    package pFREYA_defs;

    // Slow ctrl sizes
    parameter N_CSA_MODE  = 2;  // N of CSA mode bits
    parameter N_SHAP_MODE = 2;  // N of SHAP mode bits

    // CK counter sizes
    parameter SLOW_CNT_N = 8;
    parameter SEL_CNT_N  = 8;
    parameter ADC_CNT_N  = 8;
    parameter INJ_CNT_N  = 8;
    parameter SER_CNT_N  = 8;

    // Slow ctrl default values
    parameter SLOW_CTRL_PACKET_LENGTH = 7 * 8 * 2;
    parameter SLOW_CTRL_IDX_N = 7;

    // fast ctrl feature sizes
    parameter FAST_CTRL_N = 8;

    // pixel selection sizes
    parameter PIXEL_ROW_N = 1;
    parameter PIXEL_COL_N = 3;

    // UART command properties
    parameter UART_PACKET_SIZE = 8;
    // CMD packet is |CMD_CODE(4)|SIGNAL_CODE(3)|PADDING(1)|
    parameter CMD_CODE_SIZE    = 4;
    parameter CMD_START_POS    = 7;
    parameter CMD_END_POS      = 4;
    parameter SIGNAL_START_POS = 3;
    parameter SIGNAL_END_POS   = 1;
    // DATA packet is |DATA(8)|
    parameter DATA_SIZE        = 8;
    parameter DATA_START_POS   = 7;
    parameter DATA_END_POS     = 0;

    // Slow ctrl packet
    typedef struct packed {
        logic [N_CSA_MODE-1:0] csa_mode_n;
        logic inj_en_n;
        logic [N_SHAP_MODE-1:0] shap_mode;
        logic ch_en;
        logic inj_mode_n;
    } slow_ctrl_pack;

    // UART commands
    `define SET_CK_CMD         4'b0000   // for general CK (calls for clock map)
    `define SET_DELAY_CMD      4'b0001   // for fast ctrl (call for fast control map)
    `define SET_HIGH_CMD     4'b0010   // for fast ctrl
    `define SET_LOW_CMD      4'b0011   // for fast ctrl
    `define SET_SLOW_CTRL_CMD  4'b0100   // for slow ctrl
    `define SET_DAC_LVL_CMD    4'b0101   // for injection
    `define SET_PIXEL_CMD      4'b0110   // for pixel selection
    `define SEND_SLOW_CTRL_CMD 4'b0111   // for sending the slow ctrl to the asic
    `define SEND_PIXEL_SEL_CMD 4'b1000   // for sending the pixel selection to the asic

    // Slow control default values
    `define CSA_MODE_N_DEF 2'b10
    `define INJ_EN_N_DEF   1'b0
    `define SHAP_MODE_DEF  2'b10
    `define CH_EN_DEF      1'b1
    `define INJ_MODE_N_DEF 1'b0

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
    `define CMD_PADDING            1'b0
    endpackage

    import pFREYA_defs::*;
`endif
