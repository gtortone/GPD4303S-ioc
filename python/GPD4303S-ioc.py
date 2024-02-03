#!/usr/bin/env python3

import re
import sys
import yaml
import time
import serial
import socket
import requests
import threading

from pcaspy import SimpleServer, Driver
from epics import PV

requests.packages.urllib3.disable_warnings()

# IOC scan period (in seconds)
freq = 1

pvdb = {
   'IDN' : {
      'type': 'string',
      'cmd': b'*IDN?\n',
      'value': '',
   },
   'OUTSTATUS' : {
      'type': 'int',
      'mdel': -1,
      'scan': freq,
      'cmd': b'STATUS?\n',
      'value': 0,
   },
   'OUT' : {
      'type': 'int',
      'cmd': b'OUT',
   },
   'CH1:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'VOUT1?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH1:VSET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'VSET1?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH1:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'IOUT1?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH1:ISET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'ISET1?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH2:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'VOUT2?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH2:VSET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'VSET2?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH2:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'IOUT2?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH2:ISET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'ISET2?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH3:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'VOUT3?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH3:VSET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'VSET3?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH3:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'IOUT3?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH3:ISET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'ISET3?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH4:VOLTAGE': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'VOUT4?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH4:VSET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'VSET4?\n',
      'unit': 'V',
      'value': 0,
   },
   'CH4:CURRENT': {
      'prec' : 3,
      'mdel': -1,
      'scan' : freq,
      'cmd': b'IOUT4?\n',
      'unit': 'A',
      'value': 0,
   },
   'CH4:ISET': {
      'prec' : 3,
      'mdel': -1,
      'cmd': b'ISET4?\n',
      'unit': 'A',
      'value': 0,
   },
}

class myDriver(Driver):
   def __init__(self, port):
      super(myDriver, self).__init__()

      self.ser = serial.Serial(port)
      self.ser.timeout = 2 

      # set baudrate to 115200 bps
      self.ser.write(b'BAUD0\n')
      self.ser.baudrate = 115200

      # flush buffers
      self.ser.read_until()

      self.mutex = threading.Lock()

   def read(self, reason):
      if reason == 'OUT':
         return self.getParam(reason)

      if reason in pvdb:
         try:
            with self.mutex:
               self.ser.write(pvdb[reason]['cmd'])
               s = self.ser.read_until().decode('utf-8')
               #print(reason, s)
         except Exception as e:
            print(f'ERROR during query: {pvdb[reason]["cmd"]} - {e}')
         else:
            if reason.find('CH') != -1:
               # channel metric
               try:
                  value = float(re.split("[A-Z]", s)[0])
               except Exception as e:
                  print(f'ERROR during conversion of {s} = {e} {reason}')
            elif reason == 'IDN':
               value = s.rstrip()
            elif reason == 'OUTSTATUS':
               value = int(s[5])
            
            pvdb[reason]['value'] = value
            #print(reason, value, len(s))
      else:
         value = self.getParam(reason)
   
      return value

   def write(self, reason, value):
      if reason == 'OUT':
         if value != 0 and value != 1:
            return False
         try:
            with self.mutex:
               cmd = pvdb[reason]['cmd'] + str(value).encode('utf-8') + b'\n'
               s = self.ser.write(cmd)
         except Exception as e:
            print(f'ERROR during write: {cmd} - {e}')

         self.setParam(reason, value)
            
      return True

class HttpThread(threading.Thread):
   def __init__(self, kwargs=None):
      threading.Thread.__init__(self, args=(), kwargs=None)
         
      self.name = "HttpThread"
      self.hostname = kwargs['hostname']
      self.url = kwargs['url']
      self.session = requests.Session()
      self.username = kwargs.get('username', None)
      self.password = kwargs.get('password', None)
      self.pvprefix = kwargs['pvprefix']
      self.payloads = []
      self.pvs = []
      self.mutex = threading.Lock()
      self.daemon = True
   
   def run(self):
      print(f'{threading.current_thread().name}')

      # wait for PV valid values
      time.sleep(2)
      
      ignore = ['IDN', 'OUTSTATUS', 'OUT']
      for k,v in pvdb.items():
         if k in ignore:
            continue
         p = PV(f'{self.pvprefix}{k}')
         p.add_callback(self.get_influx_payload)
         self.pvs.append(p)

      httperror = False

      self.session.auth = (self.username, self.password)
      self.session.verify = False

      while True:
         if len(self.payloads) >= 100:
            with self.mutex:
               try:
                  res = self.session.post(self.url, data='\n'.join(self.payloads[0:100]))
               except Exception as e:
                  if httperror == False:
                     print(f'{time.ctime()}: {e}')
                     httperror = True
               else:
                  if httperror == True:
                     print(f'{time.ctime()}: HTTP connection recovered')
                     httperror = False
                  if res.ok == True and res.status_code != 400:
                     del(self.payloads[0:100])
                  else:
                     print(f'HTTP error: {res.text}')

         if len(self.payloads) >= 100:
            # there are payloads waiting to be sent
            time.sleep(1)
         else:
            # relax CPU
            time.sleep(2)
   
      print(f'{threading.current_thread().name} exit')

   def get_influx_payload(self, pvname=None, value=None, char_value=None, **kw):

      timestamp = int(kw['timestamp'] * 1E9)
      metric = pvname.split(':')[-1].lower()
      channel = re.findall(r'\d+',pvname.split(':')[-2])[0]

      payload = f'psu,host={self.hostname},channel={channel},metric={metric} value={value} {timestamp}'
      #print(payload)

      with self.mutex:
         self.payloads.append(payload)
      
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
            print(e) 
            exit(-1)
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
   driver = myDriver(port)

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
