import cdl_desc
from cdl_desc import CdlModule, CdlSimVerilatedModule, CModel, CSrc

class Library(cdl_desc.Library):
    name="jtag"
    pass

class JtagModules(cdl_desc.Modules):
    name = "jtag"
    src_dir      = "cdl"
    tb_src_dir   = "tb_cdl"
    libraries = {"std":True, "apb":True}
    cdl_include_dirs = ["cdl"]
    export_dirs = cdl_include_dirs + [ src_dir ]
    modules = []
    modules += [ CdlModule("jtag_tap") ]
    modules += [ CdlModule("jtag_tap_apb") ]
    modules += [ CdlModule("apb_target_jtag") ]
    modules += [ CdlModule("tb_jtag_apb_timer", src_dir=tb_src_dir) ]
    pass

