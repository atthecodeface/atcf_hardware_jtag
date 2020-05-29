Q=@
CDL_REGRESS = ${CDL_ROOT}/libexec/cdl/cdl_regress.py

.PHONY:smoke
smoke:
	${CDL_REGRESS} --pyengine-dir=${BUILD_ROOT} --package-dir regress:${SRC_ROOT}/python --suite-dir=python --only-tests 'test_comparator' test_jtag

.PHONY:regress
regress:
	${CDL_REGRESS} --pyengine-dir=${BUILD_ROOT} --package-dir regress:${SRC_ROOT}/python --suite-dir=python test_jtag
