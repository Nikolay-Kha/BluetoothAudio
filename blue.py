#!/usr/bin/env python3

import bluetooth
import logging
import time

RFCOMM_CHANNEL = 1
HFP_TIMEOUT = 5.0

class HFPException(Exception):
    pass

class HFPDevice:
	def __init__(self, addr):
		self.hfp = bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
		self.hfp.connect((addr, RFCOMM_CHANNEL))

		self.hfp.settimeout(HFP_TIMEOUT)

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

		# Optional fields
		if b'AT+CHLD=?\r' == self._read_at():
			self._send_at(b'+CHLD: 0')
			self._send_ok()

		self.hfp.settimeout(None)

		logging.info('HFP connection is established')

		self.audio = bluetooth.BluetoothSocket(bluetooth.SCO) 
		self.audio.connect((addr,))

		logging.info('Audio connection is established')


	def _read_at(self):
		try:
			return self.hfp.recv(1024)
		except bluetooth.btcommon.BluetoothError:
			return None

	def _send(self, data):
		self.hfp.send(data)

	def _send_at(self, data):
		self._send(data + b'\r')

	def _send_result(self, data):
		self._send_at(b'\r\n' + data + b'\r\n')

	def _send_ok(self):
		self._send_result(b'OK')

	def _send_error(self):
		self._send_result(b'ERROR')

	def close(self):
		self.hfp.close()

	def read(self, size):
		return self.audio.recv(size)

	def write(self, data):
		return self.audio.send(data)

def main():
	#nearby_devices = bluetooth.discover_devices(duration=4,lookup_names=True,
	#	flush_cache=True, lookup_class=False)
	#print(nearby_devices)
	logging.basicConfig(level=logging.DEBUG, format='%(message)s')

	hf = HFPDevice('00:13:7B:4A:51:F5')

	try:
		while True:
			#time.sleep(0.5)
			d = hf.read(8096);
			#print('Got audio ' + str(len(d)))
			#hf.write(d)
			#print('Sent audio')
	except KeyboardInterrupt:
		pass
	hf.close()
	logging.info('Exiting...')

if __name__ == '__main__':
	main()
