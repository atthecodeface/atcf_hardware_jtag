#a Copyright
#  
#  This file 'test_jtag.py' copyright Gavin J Stark 2017
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

#a Documentation
"""
These tests use the JTAG TAP and JTAG TAP_APB module,
as well as the simple APB timer, and test the JTAG
functionality, and then JTAG to APB.

Only a single configuration of the JTAG TAP is tested.
"""

#a Imports
from regress.apb.structs import t_apb_request, t_apb_response
from regress.apb.bfm     import ApbMaster
from regress.jtag import apb_target_jtag
from regress.jtag.jtag_module import JtagModule, JtagModuleApb
from cdl.sim     import ThExecFile
from cdl.sim     import HardwareThDut
from cdl.sim     import TestCase
from cdl.utils   import csr

#a Useful functions
def int_of_bits(bits):
    l = len(bits)
    m = 1<<(l-1)
    v = 0
    for b in bits:
        v = (v>>1) | (m*b)
        pass
    return v

def bits_of_n(nbits, n):
    bits = []
    for i in range(nbits):
        bits.append(n&1)
        n >>= 1
        pass
    return bits

#a Test classes
#c ApbAddressMap
class ApbAddressMap(csr.Map):
    _width=32
    _select=0
    _address=0
    _shift=0
    _address_size=0
    _map=[csr.MapMap(offset=0, name="jtag", map=apb_target_jtag.JtagAddressMap),
         ]
    pass
#c c_jtag_apb_time_test_base
class c_jtag_apb_time_test_base(ThExecFile):
    """
    Base methods for JTAG interaction, really
    """
    #f __init__
    def __init__(self, use_apb_target_jtag=False, **kwargs):
        self.use_apb_target_jtag = use_apb_target_jtag
        super(c_jtag_apb_time_test_base,self).__init__(**kwargs)
        pass
    #f run__init - invoked by submodules
    def run__init(self):
        self.bfm_wait(10)
        if self.use_apb_target_jtag:
            self.apb = ApbMaster(self, "apb_request",  "apb_response")
            self.apb_map = ApbAddressMap()
            self.jtag_map  = self.apb_map.jtag # This is an ApbAddressMap()
            self.jtag_module = JtagModuleApb(self, self.apb, self.jtag_map)
            pass
        else:
            self.jtag_module = JtagModule(self.bfm_wait, self.tck_enable, self.jtag__tms, self.jtag__tdi, self.tdo, self)
            pass
        pass

    #f apb_write
    def apb_write(self, address, data, write_ir=False):
        """
        Requires the JTAG state machine to be in reset or idle.

        Writes the IR to be 'access' if required, then does the appropriate write access.
        """
        if write_ir:
            self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)
            pass
        if self.use_apb_target_jtag: self.jtag_tms([0,0,0,0,0,0])
        data = self.jtag_write_drs(dr_bits = bits_of_n(50,((address&0xffff)<<34)|((data&0xffffffff)<<2)|(2)))
        return data

    #f apb_read_slow
    def apb_read_slow(self, address, write_ir=False):
        """
        Requires the JTAG state machine to be in reset or idle.

        Writes the IR to be 'access' if required, then does the appropriate read access; it then waits and does another operation to get the data back
        """
        if write_ir:
            self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)
            pass
        if self.use_apb_target_jtag: self.jtag_tms([0,0,0,0,0,0])
        data = self.jtag_write_drs(dr_bits = bits_of_n(50,((address&0xffff)<<34)|(0<<2)|(1)))
        self.bfm_wait(100)
        if self.use_apb_target_jtag: self.jtag_tms([0,0,0,0,0,0])
        data = self.jtag_write_drs(dr_bits = bits_of_n(50,0))
        return int_of_bits(data)

    #f apb_read_pipelined
    def apb_read_pipelined(self, address):
        """
        Requires the JTAG state machine to be in reset or idle.

        Peforms the appropriate read access and returns the last data
        """
        if self.use_apb_target_jtag: self.jtag_tms([0,0,0,0,0,0])
        data = self.jtag_write_drs(dr_bits = bits_of_n(50,((address&0xffff)<<34)|(0<<2)|(1)))
        return int_of_bits(data)

    #f run
    def run(self):
        self.passtest("Test completed")
        pass
    #f run__finalize
    def run__finalize(self):
        # self.verbose.error("%s"%(self.global_cycle()))
        pass

#c c_jtag_apb_time_test_idcode
class c_jtag_apb_time_test_idcode(c_jtag_apb_time_test_base):
    """
    Test the TAP controller and APB master are attached to the JTAG, by reading the IDCODE
    """
    #f run
    def run(self):
        idcodes = self.jtag_read_idcodes()
        if len(idcodes)==1:
            if idcodes[0] != 0xabcde6e3:
                self.failtest("Expected idcode of 0xabcde6e3 but got %08x"%idcodes[0])
                pass
            pass
        else:
            self.failtest("Expected a single idcode")
            pass

        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_bypass
class c_jtag_apb_time_test_bypass(c_jtag_apb_time_test_base):
    """
    Test the TAP controller with value 11111 in IR is in bypass

    Run data through DR expecting to see a single register bit, once IR is all 1s.
    """
    ir_value = 0x1f
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,self.ir_value)) # bypass mode

        for test_data in [0x0,
                          0x8000000000000000,                          
                          0xffffffffffffffff,
                          0x123456789abcdef0,
                          0xdeadbeefcafefeed,
                          ]:
            pattern_bits = bits_of_n(64,test_data) + [0]
            data = self.jtag_write_drs(dr_bits = pattern_bits)
            check_value = int_of_bits(data)>>1 # Lose the first bit that is in the Bypass 1-bit shift register
            self.compare_expected("Expected bypass to be a 1-bit shift register",check_value,test_data)
            self.verbose.info("Received back %016x when in bypass - put in %016x - so these should match"%(check_value, test_data))
            pass

        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_bypass2
class c_jtag_apb_time_test_bypass2(c_jtag_apb_time_test_bypass):
    """
    Test the TAP controller with value 00000 in IR is in bypass

    Run data through DR expecting to see a single register bit, once IR is all 1s.
    """
    ir_value = 0
    pass

#c c_jtag_apb_time_test_time_slow
class c_jtag_apb_time_test_time_slow(c_jtag_apb_time_test_base):
    """
    Test the TAP controller, APB master, and APB reads work to timer, by reading timer and expecting it to provide repeatable timer reads
    """
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x10)) # Send in 0x10 (apb_control)
        self.jtag_write_drs(dr_bits = bits_of_n(32,0))   # write apb_control of 0

        timer_readings = []
        for i in range(5):
            timer_readings.append(self.apb_read_slow(0x1200, write_ir=True))
            self.verbose.info("APB timer read returned address/data/status of %016x"%(timer_readings[-1]<<2))
            self.compare_expected("Expected APB op to have succeeded", timer_readings[-1]&3, 0)
            pass
        timer_diffs = []
        total_diff = 0
        for i in range(len(timer_readings)-1):
            timer_diffs.append( (timer_readings[i+1] - timer_readings[i])>>2 )
            total_diff += timer_diffs[-1]
            pass

        avg_diff = total_diff / (0. + len(timer_diffs))

        for t in timer_diffs:
            if abs(t-avg_diff)>2:
                self.failtest("Expected timer diff between reads (%d) to be not far from average of %d"%(t,avg_diff))
            pass
        self.verbose.info("Timer differences (which should all be roughly the same): %s"%(str(timer_diffs)))
        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_time_fast
class c_jtag_apb_time_test_time_fast(c_jtag_apb_time_test_base):
    """
    Test the TAP controller, APB master, and APB reads work to timer, by reading timer and expecting it to provide repeatable timer reads at a higher speed
    """
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x10)) # Send in 0x10 (apb_control)
        self.jtag_write_drs(dr_bits = bits_of_n(32,0))   # write apb_control of 0
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)

        timer_readings = []
        for i in range(10):
            timer_readings.append(self.apb_read_pipelined(0x1200))
            self.jtag_tms([0,0,0,0,0,0]) # 6 TMS ticks for JTAG TCK sync
            self.jtag_tms([0,0]) # 2 TMS ticks for APB clocks
            self.verbose.info("APB timer read returned address/data/status of %016x"%(timer_readings[-1]<<2))
            self.compare_expected("Expected APB op to have succeeded", timer_readings[-1]&3, 0)
            pass

        timer_readings = timer_readings[2:]
        timer_diffs = []
        total_diff = 0
        for i in range(len(timer_readings)-1):
            timer_diffs.append( (timer_readings[i+1] - timer_readings[i])>>2 )
            total_diff += timer_diffs[-1]
            pass

        avg_diff = total_diff / (0. + len(timer_diffs))

        for t in timer_diffs:
            if abs(t-avg_diff)>2:
                self.failtest("Expected timer diff between reads (%d) to be not far from average of %d"%(t,avg_diff))
            pass
        pass

        self.verbose.info("Timer differences %s"%(str(timer_diffs)))

        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_time_fast2
class c_jtag_apb_time_test_time_fast2(c_jtag_apb_time_test_base):
    """
    Test the timer with pipelined reads, and determine that the timer is ticking (or constant)
    """
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x10)) # Send in 0x10 (apb_control)
        self.jtag_write_drs(dr_bits = bits_of_n(32,0))   # write apb_control of 0
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)

        timer_readings = []
        for i in range(10):
            timer_readings.append(self.apb_read_pipelined(0x1200))
            self.bfm_wait(20) # Delay so that the next read captures the result of this request (provide update to capture delay that exceeds APB transaction + sync time)
            self.verbose.info("APB timer read returned address/data/status of %016x"%(timer_readings[-1]<<2))
            self.compare_expected("Expected APB op to have succeeded", timer_readings[-1]&3, 0)
            pass

        timer_readings = timer_readings[1:]
        timer_diffs = []
        total_diff = 0
        for i in range(len(timer_readings)-1):
            timer_diffs.append( (timer_readings[i+1] - timer_readings[i])>>2 )
            total_diff += timer_diffs[-1]
            pass

        avg_diff = total_diff / (0. + len(timer_diffs))

        for t in timer_diffs:
            if abs(t-avg_diff)>2:
                self.failtest("Expected timer diff between reads (%d) to be not far from average of %d"%(t,avg_diff))
            pass
        pass

        self.verbose.info("Timer differences (which should all be roughly the same): %s"%(str(timer_diffs)))

        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_time_fast3
    """
    Test the timer with pipelined reads, and determine that the timer is ticking and at what rate compared to JTAG tck
    """
class c_jtag_apb_time_test_time_fast3(c_jtag_apb_time_test_base):
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x10)) # Send in 0x10 (apb_control)
        self.jtag_write_drs(dr_bits = bits_of_n(32,0))   # write apb_control of 0
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)

        timer_readings = []
        for i in range(10):
            timer_readings.append(self.apb_read_pipelined(0x1200))
            self.bfm_wait(20 + i*10) # Delay so that the next read captures the result of this request (provide update to capture delay that exceeds APB transaction + sync time)
            self.verbose.info("APB timer read returned address/data/status of %016x"%(timer_readings[-1]<<2))
            self.compare_expected("Expected APB op to have succeeded", timer_readings[-1]&3, 0)
            pass

        timer_readings = timer_readings[1:]
        timer_diffs = []
        total_diff = 0
        for i in range(len(timer_readings)-1):
            timer_diffs.append( (timer_readings[i+1] - timer_readings[i])>>2 )
            total_diff += timer_diffs[-1]
            pass

        self.verbose.info("Timer differences (which are increasing): %s"%(str(timer_diffs)))

        timer_readings = timer_diffs
        timer_diffs = []
        total_diff = 0
        for i in range(len(timer_readings)-1):
            timer_diffs.append( (timer_readings[i+1] - timer_readings[i]) )
            total_diff += timer_diffs[-1]
            pass

        avg_diff = total_diff / (0. + len(timer_diffs))

        for t in timer_diffs[1:]:
            if abs(t-avg_diff)>2:
                self.failtest("Expected timer diff between reads (%d) to be not far from average of %d"%(t,avg_diff))
            pass
        pass

        print("Jtag clock is %4.2f%% of APB clock"%(100.0 / avg_diff * 10))
        self.verbose.info("Timer differences (which should all be roughly the same): %s"%(str(timer_diffs)))
        self.passtest("Test completed")
        pass
    pass

#c c_jtag_apb_time_test_comparator
class c_jtag_apb_time_test_comparator(c_jtag_apb_time_test_base):
    """
    Test the timer with APB writes, testing TAP/APB write path.
    Use timer comparator and check that the timer counts past it
    """
    #f run
    def run(self):
        self.jtag_reset()
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x10)) # Send in 0x10 (apb_control)
        self.jtag_write_drs(dr_bits = bits_of_n(32,0))   # write apb_control of 0
        self.jtag_write_irs(ir_bits = bits_of_n(5,0x11)) # Send in 0x11 (apb_access)

        self.apb_read_pipelined(0x1200)
        self.bfm_wait(20)
        data0 = self.apb_read_pipelined(0x1200)
        self.bfm_wait(20)
        data1 = self.apb_read_pipelined(0x1200)
        self.bfm_wait(20)
        time0 = (data0>>2)&0x7fffffff
        time_delta = (data1 - data0)>>2

        self.apb_write(0x1204, time0 + time_delta*5)
        timer_passed = 0
        for i in range(10):
            data = (self.apb_read_pipelined(0x1204)>>2) & 0xffffffff
            self.bfm_wait(10)
            self.verbose.info("Read %08x back from timer comparator"%data)
            if (data>>31)&1: timer_passed += 1
            pass

        self.compare_expected("Expected to see one occurence of 'comparator met'", timer_passed, 1 )
        self.passtest("Test completed")
        pass
    pass

#a Hardware classes
#c jtag_apb_timer_hw
t_jtag = {"ntrst":1, "tms":1, "tdi":1,}
class jtag_apb_timer_hw(HardwareThDut):
    clock_desc = [("jtag_tck",(0,3,3)),
                  ("apb_clock",(0,1,1)),
    ]
    reset_desc = {"name":"reset_n", "init_value":0, "wait":5}
    module_name = "tb_jtag_apb_timer"
    dut_inputs  = {"apb_request":t_apb_request,
                   "tck_enable" : 1,
                   "jtag":t_jtag,
    }
    dut_outputs = { "apb_response":t_apb_response,
                    "tdo" : 1,
    }
    pass

#a Simulation test classes
#c JtagApbTimer
class JtagApbTimer(TestCase):
    hw = jtag_apb_timer_hw
    kwargs = {"th_args":{"use_apb_target_jtag":False}}
    _tests = {
        "idcode"      : (c_jtag_apb_time_test_idcode,2*1000,     kwargs),
        "bypass"      : (c_jtag_apb_time_test_bypass,4*1000,     kwargs),
        "bypass2"     : (c_jtag_apb_time_test_bypass2,4*1000,    kwargs),
        "timer_slow"  : (c_jtag_apb_time_test_time_slow,8*1000,  kwargs),
        "timer_fast"  : (c_jtag_apb_time_test_time_fast,8*1000,  kwargs),
        "timer_fast2" : (c_jtag_apb_time_test_time_fast2,6*1000, kwargs),
        "timer_fast3" : (c_jtag_apb_time_test_time_fast3,10*1000,kwargs),
        "comparator"  : (c_jtag_apb_time_test_comparator,10*1000,kwargs),

        "smoke"  : (c_jtag_apb_time_test_time_slow,8*1000,  kwargs),
    }
    pass

#c ApbTargetJtag
class ApbTargetJtag(TestCase):
    hw = jtag_apb_timer_hw
    # "verbosity":0,
    kwargs = {"th_args":{"use_apb_target_jtag":True},}
    _tests = {
       "idcode"      : (c_jtag_apb_time_test_idcode,       4*1000,  kwargs),
       "bypass"      : (c_jtag_apb_time_test_bypass,      20*1000,  kwargs),
       "bypass2"     : (c_jtag_apb_time_test_bypass2,     20*1000,  kwargs),
       "timer_slow"  : (c_jtag_apb_time_test_time_slow,   40*1000,  kwargs),
       "timer_fast"  : (c_jtag_apb_time_test_time_fast,   40*1000,  kwargs),
       "timer_fast2" : (c_jtag_apb_time_test_time_fast2,  40*1000,  kwargs),
       "timer_fast3" : (c_jtag_apb_time_test_time_fast3,  40*1000, kwargs),
        "comparator"  : (c_jtag_apb_time_test_comparator, 45*1000, kwargs),

        "smoke"  : (c_jtag_apb_time_test_time_slow,40*1000,  kwargs),
    }
    pass

