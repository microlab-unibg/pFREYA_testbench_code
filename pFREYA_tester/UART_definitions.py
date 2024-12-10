# UART parameters
COM_PORT = 'COM3' # COM4 on the other pc
BAUD_RATE = 115200

# general
PIXEL_N = 8*2

# Slow ctrl sizes
N_CSA_MODE  = 2  # N of CSA mode bits
N_SHAP_MODE = 2  # N of SHAP mode bits

# CK counter sizes
CK_CNT_N  = 12

# Data default values
# 12 bits of reg implies need of 2 packets. Implemented as slow ctrl
# DATA UART packet is |1(1)|LAST(1)|DATA(6)| where LAST is 1 if this is the last packet, else 0
# DATA packet is |DATA(12)|
PACKET_INDEX_N = 8
DATA_PACKET_LENGTH = 12
DATA_REG_LENGTH = 16
DATA_UART_DATA_POS = 5
DATA_UART_DATA_LAST_POS = 4

WIDTH_ENTRY = len(str(2**DATA_PACKET_LENGTH))

# Slow ctrl default values
# 7 * 8 * 2 = 112 is the length of the word. It can be sent by 14 8-bit packets but 2 bits
#   are needed to identify the cmd and last packet. So 19 6-bit packets will be used (last will be 4 bits).
# SLOW_CTRL UART packet is |1(1)|LAST(1)|DATA(6)| where LAST is 1 if this is the last packet, else 0
# SLOW_CTRL packet is |DATA(112)|
SLOW_CTRL_N_BITS = 7
SLOW_CTRL_PACKET_LENGTH = 112
SLOW_CTRL_UART_DATA_POS = 5
SLOW_CTRL_UART_DATA_LAST_POS = 3
LAST_UART_PACKET = '1'
NOTLAST_UART_PACKET = '0'

# DAC config default values
# 24 is the length of the word. It can be sent by 3 8-bit packets but 2 bits
#   are needed to identify the cmd and last packet. So 4 6-bit packets will be used (no last).
# DAC UART packet is |1(1)|LAST(1)|DATA(6)| where LAST is 1 if this is the last packet, else 0
# DAC ADDRESS byte is |ADDR_PRESET(4)|ADDR(3)|R/W(1)| (not used, for I2C)
# DAC full packet is |CMD_PADDING(4)|CMD(4)|DATA(16)|
# see below (macro) for addrs and cmds
#DAC_ADDR_PACKET_LENGTH = 8 # only for I2C
DAC_PACKET_LENGTH = 24
DAC_UART_DATA_POS = 5
DAC_UART_DATA_LAST_POS = 5

# fast ctrl feature sizes
FAST_CTRL_N = 12
FAST_CTRL_FLAG_N = 2

# pixel selection sizes
PIXEL_ROW_N = 3
PIXEL_COL_N = 3

# UART command properties
UART_PACKET_SIZE = 8
# Header
CMD_PACKET = '0'
DATA_PACKET = '1'
# CMD packet is |0(1)|CMD_CODE(4)|SIGNAL_CODE(3)|
CMD_CODE_SIZE    = 4
CMD_START_POS    = 6
CMD_END_POS      = 3
SIGNAL_START_POS = 2
SIGNAL_END_POS   = 0
# DATA packet is |1(1)|LAST(1)|DATA(6)|
DATA_SIZE        = 6
DATA_START_POS   = 5
DATA_END_POS     = 0
# fast control state (for generation)
FAST_CTRL_DELAY = '00'
FAST_CTRL_LOW   = '01'
FAST_CTRL_HIGH  = '10'

# UART commands
SET_CK_CMD          = '0000'   # for general CK (calls for clock map)
SET_DELAY_CMD       = '0001'   # for fast ctrl (call for fast control map)
SET_HIGH_CMD        = '0010'   # for fast ctrl
SET_LOW_CMD         = '0011'   # for fast ctrl
SET_SLOW_CTRL_CMD   = '0100'   # for slow ctrl
SET_DAC_CMD         = '0101'   # for DAC config
SET_PIXEL_CMD       = '0110'   # for pixel selection
SEND_SLOW_CTRL_CMD  = '0111'   # for sending the slow ctrl to the asic
SEND_DAC_CMD        = '1000'   # for sending the DAC config
SEND_PIXEL_SEL_CMD  = '1001'   # for sending the pixel selection to the asic
SYNC_TIME_BASE_CMD  = '1110'   # for synchronising the signal generated to a same baseline
RESET_FPGA_CMD      = '1111'   # for resetting the FPGA just as with the button

# Slow control default values
CSA_MODE_N_DEF = '10'
INJ_EN_N_DEF   = '0'
SHAP_MODE_DEF  = '10'
CH_EN_DEF      = '1'
INJ_MODE_N_DEF = '0'

# Clock map
SLOW_CTRL_CK_CODE = '000'
SEL_CK_CODE       = '001'
ADC_CK_CODE       = '010'
INJ_STB_CODE      = '011'
SER_CK_CODE       = '100'
DAC_SCK_CODE      = '101'
UNUSED_CODE       = '111'

# Fast control map
CSA_RESET_N_CODE       = '000'
SH_INF_CODE            = '001'
SH_SUP_CODE            = '010'
ADC_START_CODE         = '011'
# Slow control map
SER_RESET_N_CODE       = '100'
SER_READ_CODE          = '101'

# Pixel selection
PIXEL_ROW_CODE         = '000'
PIXEL_COL_CODE         = '001'

# cmd padding
CMD_PADDING            = '0'

# DAC macros
# In I2C mode, the packet is 8 bit of address and 24 of data.
# In SPI mode, the packet is just 24 bits of data.

# Address byte (for I2C, not used in SPI)
# DAC_ADDR_PRESET        = '1001
# DAC_ADDR_AGND          = '000
# DAC_ADDR_VDD           = '001
# DAC_ADDR_SDA           = '010
# DAC_ADDR_SCL           = '011
# DAC_ADDR_READ          = '0'
# DAC_ADDR_WRITE         = '1'

# Command byte
DAC_CMD_PADDING            = '0000'
DAC_CMD_NOOP               = '0000'
DAC_CMD_DEVID              = '0001'
DAC_CMD_SYNC               = '0010'
DAC_CMD_CONFIG             = '0011'
DAC_CMD_GAIN               = '0100'
DAC_CMD_TRIGGER            = '0101'
DAC_CMD_STATUS             = '0111'
DAC_CMD_DATA               = '1000'

# Data byte
# DAC_DATA_NOOP is RW and does nothing
DAC_DATA_NOOP           = '0000_0000_0000_0000'

# DAC_DATA_DEVID is R. = '0RRR_0000_L000_0000.
# RRR is resolution 0020h for DAC6051, 12-bit.
# L is RSTSEL DAC power on reset, which is 0h for sero scale or 1h for midscale (should be midscale in our scenario).
# Cannot be used in SPI since its no bidirectional.

# DAC_DATA_SYNC is RW. = '0000_0000_0000_000X
# 15 bits are reserved and X is to enable sync mode (1) or async mode (0).
# Default async so that no trigger needs to be provided.
DAC_DATA_SYNC_PADDING   = '0000_0000_0000_000'
DAC_DATA_SYNC_EN        = '1'
DAC_DATA_SYNC_DIS       = '0'

# DAC_DATA_CONFIG is RW. = '0000_000X_0000_000Y
# 7+7 bits are reserved, X is to enable external (1) or internal reference (0), and Y is to set power down mode (1).
DAC_DATA_CONFIG_PADDING   = '0000_000'
DAC_DATA_CONFIG_REF_EXT   = '0'
DAC_DATA_CONFIG_REF_INT   = '1'
DAC_DATA_CONFIG_PWDWN_DIS = '0'
DAC_DATA_CONFIG_PWDWN_EN  = '1'

# DAC_DATA_GAIN is RW. = '0000_000X_0000_000Y
# 7+7 bits are reserved, X is to set VREF divider to 1 (0) or 2 (1), and Y is to set buffer gain to 1 (0) or 2 (1).
# Make sure there is enough voltage headroom for the right div and gain.
DAC_DATA_GAIN_PADDING     = '0000_000'
DAC_DATA_GAIN_DIV1        = '0'
DAC_DATA_GAIN_DIV2        = '1'
DAC_DATA_GAIN_BUF1        = '0'
DAC_DATA_GAIN_BUF2        = '1'

# DAC_DATA_TRIGGER is W. = '0000_0000_000X_YYYY
# 12 bits are reserved, X is to set LDAC sync mode (1) and it is self resetting, and YYYY is to set soft_reset (1010).
# This is not used in this implementation
DAC_DATA_TRIGGER_PADDING     = '0000_0000_000'
DAC_DATA_TRIGGER_LDAC_SET    = '1'
DAC_DATA_TRIGGER_SOFT_RESET  = '1010'

# DAC_DATA_STATUS is R. = '0000_0000_0000_000X
# 15 bits are reserved, X is alarm (1) if VREF - VDD is below threshold.
# Cannot be used in SPI since its no bidirectional.

# DAC_DATA_REGISTER is RW. = 'XXXX_XXXX_XXXX_0000
# no bits are reserved, 16 bits are data, left-aligned. For DAC6051 the last 4 bits are 0 since it is 12-bit.
# Make sure there is enough voltage headroom for the right div and gain.
DAC_BITS = 12
DAC_DATA_REGISTER_PADDING = '0000'

# Current level through power source
CURRENT_LEVEL_MIN = -20 # uA
CURRENT_LEVEL_MAX = 1 # uA