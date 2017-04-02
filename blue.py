#!/usr/bin/env python3

import bluetooth
import logging
import time
import threading
import struct
import sys

HFP_TIMEOUT = 1.0
HFP_CONNECT_AUDIO_TIMEOUT = 10.0

# from specs
SOL_BLUETOOTH = 274
SOL_SCO = 17
BT_VOICE = 11
BT_VOICE_TRANSPARENT = 0x0003
BT_VOICE_CVSD_16BIT = 0x0060
SCO_OPTIONS = 1
L2CAP_UUID = "0100"

class HFPException(bluetooth.btcommon.BluetoothError):
    pass

class HFPDevice:
	def __init__(self, addr):
		self.audio = None
		self.addr = addr
		channel = self._find_channel(addr)
		if not channel:
			raise HFPException('HSP/HFP not found')
		logging.info('HSP/HFP found on RFCOMM channel ' + str(channel))

		self.hfp = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		try:
			self.hfp.connect((addr, channel))
		except bluetooth.btcommon.BluetoothError as e:
			self.hfp.close()
			raise HFPException('Failed to establish ervice level connection: ' + str(e))
		self.hfp.settimeout(HFP_TIMEOUT)
		self.pt = threading.Thread(target=self.parse_channel)
		self.pt.start()
		logging.info('HSP/HFP service level connection is established')

	def parse_channel(self):
		audio_time = time.time() + HFP_CONNECT_AUDIO_TIMEOUT
		sevice_notice = True
		while self.pt:
			data = self._read_at()
			if data:
				if b'AT+BRSF=' in data:
					self._send_at(b'+BRSF: 0')
					self._send_ok()
				elif b'AT+CIND=?\r' == data:
					self._send_at(b'+CIND: ("service",(0,1)),("call",(0,1))')
					self._send_ok()
				elif b'AT+CIND?\r' == data:
					self._send_at(b'+CIND: 1,0')
					self._send_ok()
				elif b'AT+CMER=' in data:
					self._send_ok()
					# after this command we can establish audio connection
					sevice_notice = False
					self._connect_audio()
				elif b'AT+CHLD=?\r' == data:
					self._send_at(b'+CHLD: 0')
					self._send_ok()
				else:
					self._send_error()
			# if we don't get service level connection, try audio anyway
			if not self.audio:
				if audio_time < time.time():
					if sevice_notice:
						logging.warning('Service connection timed out, try audio anyway...')
						sevice_notice = False
					self._connect_audio();

	def _connect_audio(self):
		if not self.audio:
			audio = bluetooth.BluetoothSocket(bluetooth.SCO)
			# socket config
			opt = struct.pack ("H", BT_VOICE_CVSD_16BIT)
			audio.setsockopt(SOL_BLUETOOTH, BT_VOICE, opt)
			try:
				audio.connect((self.addr,))
			except bluetooth.btcommon.BluetoothError as e:
				audio.close()
				logging.info('Failed to establish audio connection: ' + str(e))
				return
			opt = audio.getsockopt(SOL_SCO, SCO_OPTIONS, 2)
			self.mtu = struct.unpack('H', opt)[0]
			logging.info('Audio connection is established, mtu = ' + str(self.mtu))
			self.audio = audio

	def _find_channel(self, addr):
		# discovery RFCOMM channell, prefer HFP.
		hsp_channel = None
		generic_channel = None
		services = bluetooth.find_service(address=addr, uuid=L2CAP_UUID)
		for svc in services:
			for c in svc["service-classes"]:
				service_class = c.lower()
				if bluetooth.HANDSFREE_CLASS.lower() == service_class:
					return int(svc["port"])
				elif bluetooth.HEADSET_CLASS.lower() == service_class:
					hsp_channel = int(svc["port"])
				elif bluetooth.GENERIC_AUDIO_CLASS.lower() == service_class:
					generic_channel = int(svc["port"])
		if hsp_channel:
			return hsp_channel
		return generic_channel

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
		if self.audio:
			self.audio.close()
		self.hfp.close()
		t = self.pt
		self.pt = None
		t.join()

	def read(self):
		if not self.audio:
			return None
		return self.audio.recv(self.mtu)

	def write(self, data):
		if not self.audio:
			return 0
		return self.audio.send(data)


def demo_ring(hf):
	time.sleep(1)
	hf._send_at(b'RING')

def main():
	logging.basicConfig(level=logging.DEBUG, format='%(message)s')

	if len(sys.argv) == 1:
		print("Please specify device MAC address or 'scan' to scan it.")
		sys.exit(1)
	if sys.argv[1] == 'scan':
		nearby_devices = bluetooth.discover_devices(duration=4,lookup_names=True,
			flush_cache=True, lookup_class=False)
		print(nearby_devices)
		return
	if not bluetooth.is_valid_address(sys.argv[1]):
		print("Wrong device address.")
		return
	hf = HFPDevice(sys.argv[1])

	# Make a test RING from headset
	#threading.Thread(target=demo_ring, args=[hf]).start()
	try:
		while True:
			d = hf.read()
			if d:
				hf.write(d)
			# generate noise
			#hf.write(bytes(i for i in range(48)))
	except KeyboardInterrupt:
		pass
	hf.close()
	logging.info('\nExiting...')

if __name__ == '__main__':
	main()

