#!/usr/bin/env python3

import re
import pyvisa
import argparse
import threading
from pcaspy import SimpleServer, Driver

# IOC scan period (in seconds)
freq = 1

pvdb = {
   'IDN' : {
      'type': 'string',
      'scan' : 10,
      'cmd': '*IDN?',
      'value': ''
   },
   'CH1:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VOUT1?',
      'unit': 'V',
      'value': 0,
   },
   'CH1:VSET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VSET1?',
      'unit': 'V',
      'value': 0,
   },
   'CH1:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'IOUT1?',
      'unit': 'A',
      'value': 0,
   },
   'CH1:ISET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'ISET1?',
      'unit': 'V',
      'value': 0,
   },
   'CH2:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VOUT2?',
      'unit': 'V',
      'value': 0,
   },
   'CH2:VSET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VSET2?',
      'unit': 'V',
      'value': 0,
   },
   'CH2:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'IOUT2?',
      'unit': 'A',
      'value': 0,
   },
   'CH2:ISET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'ISET2?',
      'unit': 'V',
      'value': 0,
   },
   'CH3:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VOUT3?',
      'unit': 'V',
      'value': 0,
   },
   'CH3:VSET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VSET3?',
      'unit': 'V',
      'value': 0,
   },
   'CH3:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'IOUT3?',
      'unit': 'A',
      'value': 0,
   },
   'CH3:ISET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'ISET3?',
      'unit': 'V',
      'value': 0,
   },
   'CH4:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VOUT4?',
      'unit': 'V',
      'value': 0,
   },
   'CH4:VSET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'VSET4?',
      'unit': 'V',
      'value': 0,
   },
   'CH4:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'IOUT4?',
      'unit': 'A',
      'value': 0,
   },
   'CH4:ISET': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': 'ISET4?',
      'unit': 'V',
      'value': 0,
   },
}

class MonitorThread(threading.Thread):
   def __init__(self, kwargs=None):
      threading.Thread.__init__(self, args=(), kwargs=None) 

      self.name = "MonitorThread"
      self.daemon = True
      self.rm = pyvisa.ResourceManager()
      self.psu = self.rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
      self.psu.timeout = 5000

   def run(self):
      print(f'{threading.current_thread().name}')

      while True:
         for k,v in pvdb.items():
            try:
               value = self.psu.query(pvdb[k]['cmd'])
            except:
               print(f'ERROR during query: {pvdb[k]["cmd"]}')
               continue
            
            if k != 'IDN':
               try:
                  value = float(re.split("[A-Z]", value)[0])
               except:
                  print(f'ERROR during conversion of {value}')
                  continue

            pvdb[k]['value'] = value

class myDriver(Driver):
   def __init__(self):
      super(myDriver, self).__init__()

      self.rm = pyvisa.ResourceManager()
      self.psu = self.rm.open_resource('ASRL/dev/ttyUSB0::INSTR')
      self.psu.timeout = 5000

   def read(self, reason):
      if reason in pvdb:
         value = pvdb[reason]['value']
      else:
         value = self.getParam(reason)
   
      return value

   def write(self, reason, value):
      # disable PV write (caput)
      return True

if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('-p', '--prefix', action='store', help='EPICS PV prefix (default: \'PS:\')', default="PS:")
   args = parser.parse_args()

   server = SimpleServer()
   server.createPV(args.prefix, pvdb)
   driver = myDriver()

   monitor = MonitorThread()
   monitor.start()

   # process CA transactions
   while True:
      server.process(0.1)

   monitor.join()
