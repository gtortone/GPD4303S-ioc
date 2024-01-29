TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = GPD4303Stest
# GPD4303Stest.dbd will be created and installed
DBD += GPD4303Stest.dbd

# GPD4303Stest.dbd will be made up from these files:
GPD4303Stest_DBD += base.dbd
GPD4303Stest_DBD += stream.dbd
GPD4303Stest_DBD += asyn.dbd
GPD4303Stest_DBD += drvAsynSerialPort.dbd

# Include dbd files from all support applications:
#GPD4303Stest_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
GPD4303Stest_LIBS += stream asyn
#GPD4303Stest_LIBS += stream

# GPD4303Stest_registerRecordDeviceDriver.cpp derives from GPD4303Stest.dbd
GPD4303Stest_SRCS += GPD4303Stest_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
GPD4303Stest_SRCS_DEFAULT += GPD4303StestMain.cpp
GPD4303Stest_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#GPD4303Stest_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
GPD4303Stest_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

