#!/usr/bin/env python3

import re
import sys
import yaml
import pyvisa
import socket
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

   # get hostname
   hostname = socket.gethostname().split(".")[0] 

   # read config file to setup and start backend threads

   config = {}
   with open(f"{sys.path[0]}/config.yaml", "r") as stream:
      try:
         config = yaml.safe_load(stream)
      except yaml.YAMLError as e:
         print(e)
         exit(-1)

   for backend in config:

      if 'epics' in backend:
         # resolve macro
         prefix = backend['epics'].get('prefix', 'PS:')
         prefix = re.sub('\$hostname', hostname, prefix.lower()).upper()
         args = {}
         args['prefix'] = prefix

         server = SimpleServer()
         server.createPV(prefix, pvdb)
         driver = myDriver()

         monitor = MonitorThread()
         monitor.start()

   # process CA transactions
   while True:
      server.process(0.1)

   monitor.join()
