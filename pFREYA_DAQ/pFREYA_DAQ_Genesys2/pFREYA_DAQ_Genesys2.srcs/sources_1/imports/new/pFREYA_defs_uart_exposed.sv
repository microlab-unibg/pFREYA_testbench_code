//////////////////////////////////////////////////////////////////////////////////
// Company: Microlab - Università degli Studi di Bergamo
// Engineer: Paolo Lazzaroni
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
    parameter CK_CNT_N  = 8;

    // Slow ctrl default values
    // 7 * 8 * 2 = 112 is the length of the word. It can be sent by 14 8-bit packets but a bit
    //   is needed to identify the last packet. So 16 7-bit packets will be used.
    // SLOW_CTRL UART packet is |LAST(1)|DATA(7)| where LAST is 1 if this is the last packet, else 0
    // SLOW_CTRL packet is |DATA(112)|
    parameter SLOW_CTRL_PACKET_LENGTH = 112;
    parameter SLOW_CTRL_IDX_N = 7;
    parameter LAST_UART_PACKET = 1'b1;
    parameter NOTLAST_UART_PACKET = 1'b0;

    // DAC config default values
    // 24 is the length of the word. It can be sent by 3 8-bit packets but a bit
    //   is needed to identify the last packet. So 4 7-bit packets will be used.
    // DAC UART packet is |LAST(1)|DATA(7)| where LAST is 1 if this is the last packet, else 0
    // DAC ADDRESS byte is |ADDR_PRESET(4)|ADDR(3)|R/W(1)| (not used, for I2C)
    // DAC full packet is |CMD_PADDING(4)|CMD(4)|DATA(16)|
    // see below (macro) for addrs and cmds
    //parameter DAC_ADDR_PACKET_LENGTH = 8; // only for I2C
    parameter DAC_PACKET_LENGTH = 24;

    // fast ctrl feature sizes
    parameter FAST_CTRL_N = 8;
    parameter FAST_CTRL_FLAG_N = 2;

    // pixel selection sizes
    parameter PIXEL_ROW_N = 3;
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
    // fast control state (for generation)
    parameter FAST_CTRL_DELAY = 2'b00;
    parameter FAST_CTRL_LOW   = 2'b01;
    parameter FAST_CTRL_HIGH  = 2'b10;

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
    `define SET_HIGH_CMD       4'b0010   // for fast ctrl
    `define SET_LOW_CMD        4'b0011   // for fast ctrl
    `define SET_SLOW_CTRL_CMD  4'b0100   // for slow ctrl
    `define SET_DAC_CMD        4'b0101   // for DAC config
    `define SET_PIXEL_CMD      4'b0110   // for pixel selection
    `define SEND_SLOW_CTRL_CMD 4'b0111   // for sending the slow ctrl to the asic
    `define SEND_DAC_CMD       4'b1000   // for sending the DAC config
    `define SEND_PIXEL_SEL_CMD 4'b1001   // for sending the pixel selection to the asic

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
    `define INJ_STB_CODE   3'b011
    `define SER_CK_CODE       3'b100
    `define DAC_SCK_CODE      3'b101
    `define UNUSED_CODE       3'b111

    // Fast control map
    `define CSA_RESET_N_CODE       3'b000
    `define SH_INF_CODE            3'b001
    `define SH_SUP_CODE            3'b010
    `define ADC_START_CODE         3'b011
    // Slow control map
    `define SER_RESET_N_CODE       3'b100
    `define SER_READ_CODE          3'b101

    // Pixel selection
    `define PIXEL_ROW_CODE         3'b000
    `define PIXEL_COL_CODE         3'b001

    // cmd padding
    `define CMD_PADDING            1'b0

    // DAC macros
    // In I2C mode, the packet is 8 bit of address and 24 of data.
    // In SPI mode, the packet is just 24 bits of data.

    // Address byte (for I2C, not used in SPI)
    // `define DAC_ADDR_PRESET        4'b1001
    // `define DAC_ADDR_AGND          3'b000
    // `define DAC_ADDR_VDD           3'b001
    // `define DAC_ADDR_SDA           3'b010
    // `define DAC_ADDR_SCL           3'b011
    // `define DAC_ADDR_READ          1'b0
    // `define DAC_ADDR_WRITE         1'b1

    // Command byte
    `define DAC_CMD_PADDING            4'b0000
    `define DAC_CMD_NOOP               4'b0000
    `define DAC_CMD_DEVID              4'b0001
    `define DAC_CMD_SYNC               4'b0010
    `define DAC_CMD_CONFIG             4'b0011
    `define DAC_CMD_GAIN               4'b0100
    `define DAC_CMD_TRIGGER            4'b0101
    `define DAC_CMD_STATUS             4'b0111
    `define DAC_CMD_DATA               4'b1000

    // Data byte
    // DAC_DATA_NOOP is RW and does nothing
    `define DAC_DATA_NOOP           16'b0000_0000_0000_0000

    // DAC_DATA_DEVID is R. 16'b0RRR_0000_L000_0000.
    // RRR is resolution 0020h for DAC6051, 12-bit.
    // L is RSTSEL DAC power on reset, which is 0h for sero scale or 1h for midscale (should be midscale in our scenario).
    // Cannot be used in SPI since its no bidirectional.

    // DAC_DATA_SYNC is RW. 16'b0000_0000_0000_000X
    // 15 bits are reserved and X is to enable sync mode (1) or async mode (0).
    // Default async so that no trigger needs to be provided.
    `define DAC_DATA_SYNC_PADDING   16'b0000_0000_0000_000
    `define DAC_DATA_SYNC_EN        1'b1
    `define DAC_DATA_SYNC_DIS       1'b0

    // DAC_DATA_CONFIG is RW. 16'b0000_000X_0000_000Y
    // 7+7 bits are reserved, X is to enable external (1) or internal reference (0), and Y is to set power down mode (1).
    `define DAC_DATA_CONFIG_PADDING   7'b0000_000
    `define DAC_DATA_CONFIG_REF_EXT   1'b0
    `define DAC_DATA_CONFIG_REF_INT   1'b1
    `define DAC_DATA_CONFIG_PWDWN_DIS 1'b0
    `define DAC_DATA_CONFIG_PWDWN_EN  1'b1

    // DAC_DATA_GAIN is RW. 16'b0000_000X_0000_000Y
    // 7+7 bits are reserved, X is to set VREF divider to 1 (0) or 2 (1), and Y is to set buffer gain to 1 (0) or 2 (1).
    // Make sure there is enough voltage headroom for the right div and gain.
    `define DAC_DATA_GAIN_PADDING     7'b0000_000
    `define DAC_DATA_GAIN_DIV1        1'b0
    `define DAC_DATA_GAIN_DIV2        1'b1
    `define DAC_DATA_GAIN_BUF1        1'b0
    `define DAC_DATA_GAIN_BUF2        1'b1

    // DAC_DATA_TRIGGER is W. 16'b0000_0000_000X_YYYY
    // 12 bits are reserved, X is to set LDAC sync mode (1) and it is self resetting, and YYYY is to set soft_reset (1010).
    // This is not used in this implementation
    `define DAC_DATA_TRIGGER_PADDING     7'b0000_0000_000
    `define DAC_DATA_TRIGGER_LDAC_SET    1'b1
    `define DAC_DATA_TRIGGER_SOFT_RESET  4'b1010

    // DAC_DATA_STATUS is R. 16'b0000_0000_0000_000X
    // 15 bits are reserved, X is alarm (1) if VREF - VDD is below threshold.
    // Cannot be used in SPI since its no bidirectional.

    // DAC_DATA_REGISTER is RW. 16'bXXXX_XXXX_XXXX_0000
    // no bits are reserved, 16 bits are data, left-aligned. For DAC6051 the last 4 bits are 0 since it is 12-bit.
    // Make sure there is enough voltage headroom for the right div and gain.
    `define DAC_DATA_REGISTER_PADDING 4'b0000
    endpackage

    import pFREYA_defs::*;
`endif
