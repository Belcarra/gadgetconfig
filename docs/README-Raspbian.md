# Raspbian Gadget Config
## Stuart Lynne 
## Tue Mar 03 15:40:40 PST 2020 

To use *gadgetconfig* with the Raspbery Pi in Raspbian you need to ensure that the correct modules are loaded.



## DWC2

Enable dwc2 by editing */boot/config.txt* and adding the following lines to the end of the file:
```
# enable dwc2
dtoverlay=dwc2
```

## LIBCOMPOSITE

To get the libcomposite module loaded, edit the */etc/modules* file and add the following to the end of the file:
```
# load libcomposite
libcomposite
```

### Reboot

It will be necessary to reboot the Raspberry Pi to make these changes.



## Supported Raspberry Pi systems

Currently tested with:

- Raspberry Pi Zero
- Raspberry Pi Zero/W
- Raspberry Pi 4


## Raspberry Pi Zero and Zero/W Notes

There are two Micro USB connectors on the Pi Zero and Zero/W boards. The out most one is for power. 
The one in the middle is the OTG USB port. A standard USB A to Micro USB cable can be used to connect
the Pi Zero / Zero/W to the USB Host.

## Raspberry Pi 4 Notes

The Raspberry Pi 4 has a USB C port that is used to power it. 
A USB C to USB 3.0 cable with a 56k Ohm resistor cable can be used to plug the Pi into a USB Host
for both Power and it can act as a USB Device to enumerate to that USB Host.


