#!/usr/bin/env python3

import bluetooth
import logging
import time
import threading
import struct

RFCOMM_CHANNEL = 1
HFP_TIMEOUT = 1.0
HFP_INIT_TIMEOUT = 3.0

#from bluetooth.h
SOL_BLUETOOTH = 274
BT_VOICE = 11
BT_VOICE_TRANSPARENT = 0x0003
BT_VOICE_CVSD_16BIT = 0x0060

class HFPException(Exception):
    pass

class HFPDevice:
	def __init__(self, addr):
		self.hfp = bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
		self.hfp.connect((addr, RFCOMM_CHANNEL))

		self.hfp.settimeout(HFP_INIT_TIMEOUT)

		if b'AT+BRSF=' not in self._read_at():
			raise HFPException('Expect AT+BRSF command in initialisation')
		self._send_at(b'+BRSF: 0')
		self._send_ok()

		if b'AT+CIND=?\r' != self._read_at():
			raise HFPException('Expect AT+CIND=? command in initialisation')
		self._send_at(b'+CIND: ("service",(0,1)),("call",(0,1))')
		self._send_ok()

		if b'AT+CIND?\r' != self._read_at():
			raise HFPException('Expect AT+CIND? command in initialisation')
		self._send_at(b'+CIND: 1,0')
		self._send_ok()

		if b'AT+CMER=' not in self._read_at():
			raise HFPException('Expect AT+CMER command in initialisation')
		self._send_ok()

		self.hfp.settimeout(HFP_TIMEOUT)
		self.pt = threading.Thread(target=self.parse_channel)
		self.pt.start()

		logging.info('HSP/HFP connection is established')

		self.audio = bluetooth.BluetoothSocket(bluetooth.SCO)
		opt = struct.pack ("H", BT_VOICE_CVSD_16BIT)
		self.audio.setsockopt(SOL_BLUETOOTH, BT_VOICE, opt)
		self.audio.connect((addr,))
		logging.info('Audio connection is established')

	def parse_channel(self):
		while self.pt:
			data = self._read_at()
			if not data:
				return
			if data == b'AT+CHLD=?\r':
				self._send_at(b'+CHLD: 0')
				self._send_ok()
			else:
				self._send_error()

	def _read_at(self):
		try:
			d = self.hfp.recv(1024)
			logging.debug('> ' + d.decode('utf8'))
			return d
		except bluetooth.btcommon.BluetoothError:
			return None

	def _send(self, data):
		logging.debug('< ' + data.decode('utf8').replace('\r\n', ''))
		self.hfp.send(data)

	def _send_at(self, data):
		self._send(b'\r\n' + data + b'\r\n')

	def _send_ok(self):
		self._send_at(b'OK')

	def _send_error(self):
		self._send_at(b'ERROR')

	def close(self):
		self.audio.close()
		self.hfp.close()
		t = self.pt
		self.pt = None
		t.join()

	def read(self, size):
		return self.audio.recv(size)

	def write(self, data):
		return self.audio.send(data)


def demo_ring(hf):
	time.sleep(1)
	hf._send_at(b'RING')

def main():
	#nearby_devices = bluetooth.discover_devices(duration=4,lookup_names=True,
	#	flush_cache=True, lookup_class=False)
	#print(nearby_devices)
	logging.basicConfig(level=logging.DEBUG, format='%(message)s')

	hf = HFPDevice('00:13:7B:4A:51:F5')

	#threading.Thread(target=demo_ring, args=[hf]).start()
	try:
		while True:
			time.sleep(0.01)
			#d = hf.read(1024);
			#print('Got audio ' + str(len(d)))
			hf.write(b'zAzzzAzAzzzAzAzzzAzAzzzAzAzzzAzAzzzAzAzzzAzAzzzA')#d)
			#print('Sent audio')
	except KeyboardInterrupt:
		pass
	hf.close()
	logging.info('\nExiting...')

if __name__ == '__main__':
	main()

