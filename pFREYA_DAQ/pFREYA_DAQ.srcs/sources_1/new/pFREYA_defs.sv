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
    // Sizes
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

    // Slow ctrl default values
    `define CSA_MODE_N_DEF 2'b10
    `define INJ_EN_N_DEF   1'b0
    `define SHAP_MODE_DEF  1'b10
    `define CH_EN_DEF      1'b1
    `define INJ_MODE_N_DEF 1'b0
    endpackage

    import GAPS_defs::*;
`endif
