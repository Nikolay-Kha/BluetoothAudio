# Description
This project shows how to capture and play audio with bluetooth HSP/HFP device without pulseaudio or any other sound sy1stem, i.e. directly via bluetooth. It initialise bluetooth audio device and playback microphone data back in loop.
HSP/HFP profile actually is a two connections via Bluetooth, service and audio. Service is a bluetooth RFCOMM connection which operates with AT commands. Audio connection is a bluetooth SCO connection.

# Hardware
Please note that not all bluetooth adapters support HSP/HFP. For example, BCM20702 does support A2DP pefrectly, but there is no sound with HSP/HFP.  
Upd: BCM20702 need proprietary firmware on Linux - http://plugable.com/2014/06/23/plugable-usb-bluetooth-adapter-solving-hfphsp-profile-issues-on-linux/  
This project was tested with CSR bluetooth 4.0 USB dongle.

# Specs
HFP v1.7 specs https://www.bluetooth.org/docman/handlers/downloaddoc.ashx?doc_id=292287  
AT command specs http://www.3gpp.org/ftp/Specs/archive/07_series/07.07/0707-780.zip  

# Dependencies
```
sudo apt install libbluetooth-dev gcc python3-dev python3-pip
sudo pip3 install pybluez
```


