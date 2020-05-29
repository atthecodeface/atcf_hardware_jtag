#a Copyright
#  
#  This file 'jtag_module.py' copyright Gavin J Stark 2018
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
import Queue
import socket
import select
import simple_tb

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

#a Classes
#c openocd_server
class openocd_server(simple_tb.base_th.tcp_server_thread):
    def __init__(self, **kwargs):
        simple_tb.base_th.tcp_server_thread.__init__(self, **kwargs)
        self.queue_recvd   = Queue.Queue()
        self.queue_to_send = Queue.Queue()
        self.data_to_send = ""
        pass
    def update_data_to_send(self):
        while not self.queue_to_send.empty():
            self.data_to_send += self.queue_to_send.get()
            pass
        return self.data_to_send
    def did_send_data(self, n):
        self.data_to_send = self.data_to_send[n:]
        pass
    def received_data(self, data):
        self.queue_recvd.put(data)
        pass
    pass
        
