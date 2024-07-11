# pFREYA DAQ
This project contains the code for the design of the DAQ for pFREYA ASIC testing.

## Table of Content
The contents in both the Ultrascale+ and the Genesys 2 folder are organised as:
- [pFREYA DAQ](#pfreya-daq)
	- [Table of Content](#table-of-content)
	- [Hardware](#hardware)
	- [Software](#software)
	- [TODO](#todo)
	- [License](#license)

## Hardware
- [KCU116 Evaluation Kit](https://www.xilinx.com/products/boards-and-kits/ek-u1-kcu116-g.html), mounting in particular an [UltraScale+ XCKU5P-2FFVB676](https://www.xilinx.com/products/silicon-devices/fpga/kintex-ultrascale-plus.html#productTable) FPGA.
- [Genesys 2](https://digilent.com/reference/programmable-logic/genesys-2/start), mounting in particular an [Kintex-7 XC7K325-TFFG900-2](https://www.amd.com/en/products/adaptive-socs-and-fpgas/fpga/kintex-7.html#product-table) FPGA.
- pFREYA_PCB custom PCB developed for testing, aka mother board.
- pFREYA16 or pFREYATS ASIC mounted on top of a daughter board.

## Software
The software in the repo is written in Verilog and related dialects. The products used for the development are:
- [Vivado Suite](https://www.xilinx.com/products/design-tools/vivado.html).
- [VSCode](https://code.visualstudio.com/).

## TODO
- [ ] Everything lol.

## License
Distributed under the MIT License. See `LICENSE.md` for more information.