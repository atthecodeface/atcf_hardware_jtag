# atcf_hardware_jtag

This repository contains the CDL source code and C models for the
ATCF JTAG modules

## Status

The repository is in use in the ATCF RISC-V systems grip repository

# Modules

## Jtag_tap

This is a JTAG test access port; this is a module that appears on a
JTAG chain, and provides an interface to a device to be controlled by
the JTAG chain.

The module should be configured with an instruction register length
*ir_length* set to the bit width of the device's instruction, and the
data register length *dr_length* set to the largest of the bit width of the device's
data registers (which of the device's registers is accessed depends on the IR value).

The device interfaces to the jtag_tap with a data port (in and out),
and instruction (driven in to the device), and an action; the
important actions are shift, capture and update.

A single bit of dr_tdi_mask must be driven high
indicating the topmost bit that is valid of the data register
indicated by the current value of *ir*

On shift the device must (combinationally) drive dr_out to be dr_in shifted right by one.

On capture the device must (combinationally) drive dr_out to be the
value of the data register specified by *ir*

On update the device must (on the next clock edge) start the update
that the value of *ir* and *dr_in* require.

*ir* of 1 is IDCODE, and requires a 32-bit register value of (20 bits
 manufacturer unique, 11 bits of manufacturer ID, 1b1)

## Jtag_tap_apb

This is a client module for jtag_tap that is an APB master. It is
derived from the RISC-V debug specification v0.13. It has a 5-bit IR
register, and 

It provides the following JTAG registers:

* IR=1: IDCODE of the value 'jtag_idcode' (a constant that may be
  changed at CDL compilation)

* IR=0x10: APB control, a 32 bit register (bits 2;10 indicate status)

* IR=0x11: APB access, a 16+32+2 bit register (16 bit address, 32 bit
  data, 2 bit access/status)

* IR=x: all other values are BYPASS (1 bit register, dr_out=dr_in)

On updates of APB control bits 2;16 are nonzero to reset the APB status.

On updates of APB access bits 2;0 are 1 for start an APB read, 2 for
start and APB write.

The APB status is two bits that are 2b00 for no errors, 2b11 if an APB
access is attempted before a previous access completes.


