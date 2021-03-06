#a Copyright
#  
#  This file 'jtag_module.py' copyright Gavin J Stark 2018-2020
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

#a Useful functions
def int_of_bits(bits):
    l = len(bits)
    m = 1<<(l-1)
    v = 0
    for b in bits:
        v = (v>>1) | (m*b)
        pass
    return v

#a Classes
#c JtagModuleBase
class JtagModuleBase:
    #b __init__
    def __init__(self, bfm_wait, tcken, tms, tdi, tdo, mixin=None):
        self.bfm_wait = bfm_wait
        self.tck_enable = tcken
        self.jtag__tms = tms
        self.jtag__tdi = tdi
        self.tdo = tdo
        if mixin is not None:
            mixin.jtag_reset = self.jtag_reset
            mixin.jtag_tms   = self.jtag_tms
            mixin.jtag_shift = self.jtag_shift
            mixin.jtag_reset = self.jtag_reset
            mixin.jtag_read_idcodes = self.jtag_read_idcodes
            mixin.jtag_write_irs = self.jtag_write_irs
            mixin.jtag_write_drs = self.jtag_write_drs
        pass

    #f jtag_reset
    def jtag_reset(self):
        """
        Reset the jtag - this requires 5 clocks with TMS high.

        This leaves the JTAG state machine in reset
        """
        self.tck_enable.drive(1)
        self.bfm_wait(1)
        self.jtag__tms.drive(1)
        self.jtag__tdi.drive(0)
        self.bfm_wait(5)
        pass

    #f jtag_tms
    def jtag_tms(self, tms_values):
        """
        Scan in a number of TMS values, to move the state machine on
        """
        for tms in tms_values:
            self.jtag__tms.drive(tms)
            self.bfm_wait(1)
            pass
        pass

    #f jtag_shift
    def jtag_shift(self, tdi_values):
        """
        Shift in data from tdi_values, and transition out of shift mode
        Record the shifted out data and return it.
        Leave the JTAG state machine in Exit1.

        This assumes the state machine is in a shift mode to start
        with.  It runs the JTAG with TMS low for all except the last
        tdi_values bit.  Then it runs with TMS high so that the last
        bit is shifted in, and the state machine moves to exit1.

        """
        bits = []
        self.jtag__tms.drive(0)
        for tdi in tdi_values[:-1]:
            self.jtag__tdi.drive(tdi)
            self.bfm_wait(1)
            bits.append(self.tdo.value())
            pass
        self.jtag__tms.drive(1)
        self.jtag__tdi.drive(tdi_values[-1])
        self.bfm_wait(1)
        bits.append(self.tdo.value())
        return bits

    #f jtag_read_idcodes
    def jtag_read_idcodes(self):
        """
        Read the JTAG idcodes on the scan chain. Return a list of 32-bit integer IDCODEs.

        This resets the JTAG state machine, and then enters shift-dr.
        In reset the JTAG TAP controllers should set the IR for IDCODE reading.
        IDCODEs are guaranteed to be 32 bits, with a bottom bit set.

        Hence one can scan out 32-bit values from the chain while the first bit out is set.

        Leaves the state machine in shift-dr
        """
        self.jtag_reset()
        self.jtag_tms([0,1,0,0]) # Put in to shift-dr
        idcodes = []
        while True:
            bits = []
            self.bfm_wait(1)
            bits.append(self.tdo.value())
            if bits[0]==0: break
            for i in range(31):
                self.bfm_wait(1)
                bits.append(self.tdo.value())
                pass
            idcode = int_of_bits(bits)
            idcodes.append(idcode)
            pass
        return idcodes

    #f jtag_write_irs
    def jtag_write_irs(self,ir_bits):
        """
        Requires the JTAG state machine to be in reset or idle

        Move to shift-ir, and shift in the bits, then revert back to idle (not through reset!)
        """
        self.jtag_tms([0,1,1,0,0]) # Put in Shift-IR
        self.jtag_shift(ir_bits) # Leaves it in Exit1-IR
        self.jtag_tms([1,0]) # Dump it back in to idle
        pass

    #f jtag_write_drs
    def jtag_write_drs(self,dr_bits):
        """
        Scan data into the data register, and return data scanned out.
        Requires the JTAG state machine to be in reset or idle.

        Move to shift-dr, and shift in the bits, then revert back to idle (not through reset!)
        """
        self.jtag_tms([0,1,0,0]) # Put in Shift-DR
        data = self.jtag_shift(dr_bits) # Leaves it in Exit1-DR
        self.jtag_tms([1,0]) # Dump it back in to idle
        return data
    pass
#c JtagModule
class JtagModule(JtagModuleBase):
    pass
#c JtagModuleApbBase
class JtagModuleApbBase(JtagModuleBase):
    def __init__(self, th, apb_bfm, jtag_map):
        th.jtag_reset = self.jtag_reset
        th.jtag_tms   = self.jtag_tms
        th.jtag_shift = self.jtag_shift
        th.jtag_reset = self.jtag_reset
        th.jtag_read_idcodes = self.jtag_read_idcodes
        th.jtag_write_irs = self.jtag_write_irs
        th.jtag_write_drs = self.jtag_write_drs
        self.bfm_wait = th.bfm_wait
        self.apb_bfm = apb_bfm
        self.jtag_map = jtag_map
        self.jtag_status_reg = self.apb_bfm.reg(self.jtag_map.status)
        self.jtag_tdo_reg   = self.apb_bfm.reg(self.jtag_map.tdo)
        self.jtag_tdocl_reg = self.apb_bfm.reg(self.jtag_map.tdoc)
        self.jtag_data1_reg = self.apb_bfm.reg(self.jtag_map.data1)
        self.jtag_data4_reg = self.apb_bfm.reg(self.jtag_map.data4)
        pass

    #f jtag_reset
    def jtag_reset(self):
        """
        Reset the jtag - this requires 5 clocks with TMS high.

        This leaves the JTAG state machine in reset
        """
        self.jtag_data4_reg.write(0x36363636)
        self.jtag_data1_reg.write(0x36)
        pass

    #f jtag_tms
    def jtag_tms(self, tms_values):
        """
        Scan in a number of TMS values, to move the state machine on
        """
        for tms in tms_values:
            self.jtag_data1_reg.write(0x34+(tms<<1))
            pass
        pass

    #f jtag_shift
    def jtag_shift(self, tdi_values, last_tms=1):
        """
        Shift in data from tdi_values, and transition out of shift mode
        Record the shifted out data and return it.
        Leave the JTAG state machine in Exit1.

        This assumes the state machine is in a shift mode to start
        with.  It runs the JTAG with TMS low for all except the last
        tdi_values bit.  Then it runs with TMS high so that the last
        bit is shifted in, and the state machine moves to exit1.

        """
        bits = []
        n = 0
        w=32
        for tdi in tdi_values[:-1]:
            self.jtag_data1_reg.write(0x52)
            self.jtag_data1_reg.write(0x34 + (tdi&1))
            n+=1
            if n==w:
                r = self.jtag_tdocl_reg.read()
                for i in range(n):
                    bits.append((r>>(w-n+i))&1)
                    pass
                n = 0
                pass
            pass
        self.jtag_data1_reg.write(0x52)
        self.jtag_data1_reg.write(0x34 + (last_tms<<1) + (tdi_values[-1]&1))
        n+=1
        r = self.jtag_tdocl_reg.read()
        for i in range(n):
            bits.append((r>>(w-n+i))&1)
            pass
        return bits

    #f jtag_read_idcodes
    def jtag_read_idcodes(self):
        """
        Read the JTAG idcodes on the scan chain. Return a list of 32-bit integer IDCODEs.

        This resets the JTAG state machine, and then enters shift-dr.
        In reset the JTAG TAP controllers should set the IR for IDCODE reading.
        IDCODEs are guaranteed to be 32 bits, with a bottom bit set.

        Hence one can scan out 32-bit values from the chain while the first bit out is set.

        Leaves the state machine in shift-dr
        """
        self.jtag_reset()
        self.jtag_tms([0,1,0,0]) # Put in to shift-dr
        idcodes = []
        while True:
            bits = self.jtag_shift([0]*1,last_tms=0)
            if bits[0]==0: break
            bits += self.jtag_shift([0]*31,last_tms=0)
            idcode = int_of_bits(bits)
            idcodes.append(idcode)
            pass
        return idcodes

    pass

#c JtagModuleApbSlow
class JtagModuleApbSlow(JtagModuleApbBase):
    pass
#c JtagModuleApbFast
class JtagModuleApbFast(JtagModuleApbBase):
    #f jtag_reset
    def jtag_reset(self):
        """
        Reset the jtag - this requires 5 clocks with TMS high.

        This leaves the JTAG state machine in reset
        """
        self.jtag_data1_reg.write(0x80 + ((4)<<2) )
        pass

    #f jtag_tms
    def jtag_tms(self, tms_values):
        """
        Scan in a number of TMS values, to move the state machine on
        """
        x=0
        for i in range(len(tms_values)):
            x += tms_values[i]<<i
            pass
        self.jtag_tdo_reg.write(x)
        self.jtag_data1_reg.write(0x81 + ((len(tms_values)-1)<<2))
        pass

    #f jtag_shift
    def jtag_shift(self, tdi_values, last_tms=1):
        """
        Shift in data from tdi_values, and transition out of shift mode
        Record the shifted out data and return it.
        Leave the JTAG state machine in Exit1.

        This assumes the state machine is in a shift mode to start
        with.  It runs the JTAG with TMS low for all except the last
        tdi_values bit.  Then it runs with TMS high so that the last
        bit is shifted in, and the state machine moves to exit1.

        """
        bits = []
        n = 0
        w = 32
        total = len(tdi_values)
        i = 0
        while i<total:
            n = total-i
            if n>32: n=32
            set_last_tms = 0
            if last_tms and ((i+n)==total): set_last_tms=1
            x = 0
            for b in range(n):
                x += tdi_values[i+b]<<b
                pass
            self.jtag_tdo_reg.write(x)
            self.jtag_data1_reg.write(0x82 + set_last_tms + ((n-1)<<2))
            i += n
            r = self.jtag_tdocl_reg.read()
            for b in range(n):
                bits.append((r>>(w-n+b))&1)
                pass
            pass
        return bits

