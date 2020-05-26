/** Copyright (C) 2016-2020,  Gavin J Stark.  All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * @file   jtag_modules.h
 * @brief  Modules for JTAG TAP and APB access
 *
 * Header file for the modules for JTAG
 *
 */

/*a Includes */
include "apb::apb.h"
include "jtag.h"

/*a Modules */
/*m jtag_tap_apb */
extern module jtag_tap( clock jtag_tck,
                        input bit reset_n,
                        input t_jtag jtag,
                        output bit tdo,

                        output bit[5]ir,
                        output t_jtag_action dr_action,
                        output bit[50]dr_in,
                        input  bit[50]dr_tdi_mask,
                        input  bit[50]dr_out
    )
{
    timing to rising clock jtag_tck jtag, dr_tdi_mask, dr_out;
    timing from rising clock jtag_tck tdo, ir, dr_action, dr_in;
}

/*m jtag_tap_apb */
extern module jtag_tap_apb( clock jtag_tck,
                 input bit reset_n,

                 input bit[5]ir,
                 input t_jtag_action dr_action,
                 input  bit[50]dr_in,
                 output bit[50]dr_tdi_mask,
                 output bit[50]dr_out,

                 clock apb_clock,
                 output t_apb_request apb_request,
                 input t_apb_response apb_response
    )
{
    timing to rising clock jtag_tck ir, dr_action, dr_in;
    timing from rising clock jtag_tck dr_tdi_mask, dr_out;
    timing from rising clock apb_clock apb_request;
    timing to rising clock apb_clock apb_response;
    timing comb input dr_in, dr_action, ir;
    timing comb output dr_out, dr_tdi_mask;
}

/*m apb_target_jtag */
extern module apb_target_jtag( clock clk         "System clock",
                               input bit reset_n "Active low reset",

                               input  t_apb_request  apb_request  "APB request",
                               output t_apb_response apb_response "APB response",

                               output bit             jtag_tck_enable,
                               output t_jtag          jtag,
                               input  bit             jtag_tdo

    )
{
    timing to   rising clock clk apb_request;
    timing from rising clock clk apb_response;
    timing from rising clock clk jtag_tck_enable, jtag;
    timing to   rising clock clk jtag_tdo;
}

