#a Copyright
#  
#  This file 'apb_target_jtag.py' copyright Gavin J Stark 2020
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

#a Imports
from cdl.utils.csr   import Csr, CsrField, CsrFieldZero, Map, MapCsr, CsrFieldResvd

#a CSRs
class StatusCsr(Csr):
    _fields = { 0:  CsrField(width=6, name="bits_valid", brief="bv", doc="Number of bits valid in Tdo register"),
                6:  CsrFieldZero(width=2),
                8:  CsrField(width=1, name="mode", brief="mode", doc="If 0 use OpenOCD mode; otherwise use nybble mode"),
                9:  CsrFieldZero(width=15),
               24:  CsrField(width=1, name="tms", brief="tms", doc="Value of TMS 'pin'"),
               25:  CsrField(width=1, name="tdi", brief="tdo", doc="Value of TDI 'pin'"),
               26:  CsrField(width=1, name="tdo", brief="tdi", doc="Value of TDO 'pin'"),
               27: CsrFieldZero(width=5),
              }
class TdoCsr(Csr):
    _fields = {0:  CsrField(width=32, name="tdo_sr", brief="tdo", doc="32-bit shift register value from TDO being right-shifted in"),
              }

class DataCsr(Csr):
    _fields = {0:   CsrField(width=8, name="byte0", brief="b0", doc="byte of JTAG control data; in OpenOCD mode 0x30-0x37 ('0' to '7') control tdi, tms and tck; 0x52 ('R') shifts TDO in"),
               8:   CsrField(width=8, name="byte1", brief="b1", doc="byte of JTAG control data; in OpenOCD mode 0x30-0x37 ('0' to '7') control tdi, tms and tck; 0x52 ('R') shifts TDO in"),
               16:  CsrField(width=8, name="byte2", brief="b2", doc="byte of JTAG control data; in OpenOCD mode 0x30-0x37 ('0' to '7') control tdi, tms and tck; 0x52 ('R') shifts TDO in"),
               24:  CsrField(width=8, name="byte3", brief="b3", doc="byte of JTAG control data; in OpenOCD mode 0x30-0x37 ('0' to '7') control tdi, tms and tck; 0x52 ('R') shifts TDO in"),
              }

class TimerAddressMap(Map):
    _map = [ MapCsr(reg=0, name="status",    brief="sts",  csr=StatusCsr, doc="read-only"),
             MapCsr(reg=2, name="tdo",       brief="tdo",  csr=TdoCsr, doc="read-only"),
             MapCsr(reg=3, name="tdo_clear", brief="tdoc", csr=TdoCsr, doc="read-only"),
             MapCsr(reg=4, name="data1",     brief="d1",   csr=DataCsr, doc="write-only"),
             MapCsr(reg=5, name="data2",     brief="d2",   csr=DataCsr, doc="write-only"),
             MapCsr(reg=6, name="data3",     brief="d3",   csr=DataCsr, doc="write-only"),
             MapCsr(reg=7, name="data4",     brief="d4",   csr=DataCsr, doc="write-only"),
             ]
             
