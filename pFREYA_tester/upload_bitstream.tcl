# Connect to the hardware server
open_hw_manager
connect_hw_server

# Open the target FPGA device
set hw_target [get_hw_targets *]
open_hw_target $hw_target
puts "Available hardware targets: $hw_target"

# Select the device
set hw_device [lindex [get_hw_devices] 0]
refresh_hw_device $hw_device

# Program the FPGA with the bitstream
set_property PROGRAM.FILE "../pFREYA_DAQ/pFREYA_DAQ_ultrascale+/pFREYA_DAQ.runs/impl_1/pFREYA_DAQ.bit" $hw_device
set_property PROBES.FILE "../pFREYA_DAQ/pFREYA_DAQ_ultrascale+/pFREYA_DAQ.runs/impl_1/pFREYA_DAQ.ltx" [lindex [get_hw_devices] 0]
program_hw_devices $hw_device

# Close the hardware server connection
disconnect_hw_server
exit

