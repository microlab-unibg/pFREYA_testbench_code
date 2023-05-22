# UART constraints
set_input_delay -clock clk_port -max 2 [get_ports rs232_uart_rxd]
set_input_delay -clock clk_port -min 1 [get_ports rs232_uart_rxd]
set_output_delay -clock clk_port -max 2 [get_ports rs232_uart_txd]
set_output_delay -clock clk_port -min 1 [get_ports rs232_uart_txd]