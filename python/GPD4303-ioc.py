#!/usr/bin/env python3

import re
import sys
import yaml
import time
import pyvisa
import socket
import threading

from epics import PV
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
   def __init__(self, port, kwargs=None):
      threading.Thread.__init__(self, args=(), kwargs=None) 

      self.name = "MonitorThread"
      self.daemon = True
      self.rm = pyvisa.ResourceManager()
      try:
         self.psu = self.rm.open_resource(f'ASRL{port}::INSTR')
      except Exception as e:
         print(e)
         exit(-1)
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

      print(f'{threading.current_thread().name} exit')

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

class HttpThread(threading.Thread):
   def __init__(self, kwargs=None):
      threading.Thread.__init__(self, args=(), kwargs=None)
         
      self.name = "HttpThread"
      self.hostname = kwargs['hostname']
      self.url = kwargs['url']
      self.username = kwargs.get('username', None)
      self.password = kwargs.get('password', None)
      self.pvprefix = kwargs['pvprefix']

      self.pvs = []
      for pvname in pvdb:
         self.pvs.append(PV(f'{self.pvprefix}{pvname}'))

      print(self.pvs)
      
      self.daemon = True
   
   def run(self):
      print(f'{threading.current_thread().name}')
      while True:
         for pv in self.pvs:
            print(pv)

         time.sleep(1)          ##
      print(f'{threading.current_thread().name} exit')

   def get_influx_payload(self, pv, value):
      None

if __name__ == '__main__':

   # get hostname
   hostname = socket.gethostname().split(".")[0] 

   # default PVs prefix
   prefix = "PS:"

   # default psu port
   port = "/dev/ttyUSB0"

   threads = []

   # read config file to setup and start threads
   config = {}
   try:
      with open(f"{sys.path[0]}/config.yaml", "r") as stream:
         try:
            config = yaml.safe_load(stream)
         except yaml.YAMLError as e:
            print(e) exit(-1)
         else:
            for section in config:

               if 'psu' in section:
                  port = section['psu'].get('port', '/dev/ttyUSB0')

               if 'epics' in section:
                  # resolve macro
                  prefix = section['epics'].get('prefix', 'PS:')
                  prefix = re.sub('\$hostname', hostname, prefix.lower()).upper()

               if 'http' in section:
                  if section['http'].get('enable', False):
                     args = {}
                     args['hostname'] = hostname
                     args['url'] = section['http'].get('url', None)
                     if args['url'] is None:
                        print("ERROR: HTTP section enabled but 'url' parameter is not provided")
                        exit(-1)
                     args['username'] = section['http'].get('username', None)
                     args['password'] = section['http'].get('password', None)
                     args['pvprefix'] = prefix
                     threads.append(HttpThread(kwargs=args))

   except (FileNotFoundError, PermissionError) as e:
      print(f'WARNING: {e} - running with defaults')
      pass

   server = SimpleServer()
   server.createPV(prefix, pvdb)
   driver = myDriver()

   threads.append(MonitorThread(port))

   for t in threads:
      t.start()

   # process CA transactions
   while True:
      try:
         server.process(0.1)
      except KeyboardInterrupt:
         print("Ctrl+C pressed...")
         del(server)
         break;

