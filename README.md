# Gadget Config
## Stuart Lynne 
## Thu Apr 09 23:46:27 PDT 2020 

This package contains tools for configuring Gadget USB Devices and integrating with *systemd*.

It relies on the Gadget ConfigFS module libcomposite to create and manage Gadget USB Devices.


## Installation



To install:
```
    pip3 install gadgetconfig
```

To uninstall:
```
    pip3 uninstall gadgetconfig
```

If you have trouble getting it installed you can try:

```
    pip3 install --no-binary :all: gadgetconfig
```

N.B. --no-binary is needed with recent versions of pip to cope with a bug.
C.f.  https://stackoverflow.com/questions/40588634/how-to-install-data-files-to-absolute-path


## Gadget USB Device Overview

The Gadget USB Device implementation has three layers when using the new libcomposite
driver:

- Function Drivers, e.g. usb\_f\_acm, usb\_f\_ecm, usb\_f_\eem
- LibComposite, for selecting and configuring the device to use the Function Drivers
- UDC, to connect the Function Drivers to the underlying USB Device Controller hardware

The libcomposite implementation allows the USB Device configuration to be specified ad hoc
and changed as needed. 

A USB Device definition contains:
- idVendor, idProduct, bcdDevice and other attributes
- one of more configurations
- a list of functions that configurations may use
- strings describing the device

Each configuration contains:
- attributes
- list of functions to be used 
- strings describing the configuration


## Systemd Integration

A *gadget.service* file is installed which will use the following to start and stop
the gadget service:

```
/usr/lib/gadgetservice/gadget.start
/usr/lib/gadgetservice/gadget.stop
```

These rely on a default Gadget Device Definition file being present in:

```
/etc/gadgetservice/default.json
```

The service should auto-start when the system is rebooted. The *systemctl* command can also be used;

```
systemctl start gadget
systemctl stop gadget
```

See below for more information on Gadget Device Definition files.


## Gadget USB Device Lifecycle

The *gadgetconfig* program uses USB Device definitions stored in *JSON* files.

Gadget Libcomposite:

- Create: *gadgetconfig --create gadget-definition.json*
- Enable: *gadgetconfig --enable configuration_name*
- Disable: *gadgetconfig --disable*
- Destroy: *gadgetconfig --destroy*

Gadget UDC:
- Disconnect: *gadgetconfig --soft_connect disconnect*
- Connect: *gadgetconfig --soft_connect connect*


```
            +-------------------+
            |     No Gadget     |
            +-------------------+
                  |       ^             
                  |       |
               Create   Destroy
                  |       |
                  v       |
            +-------------------+
            | Distabled Gadget  |<---
            +-------------------+   |
                  |                 | 
                  |                 |
                Enable           Disable
                  |                 |
                  v                 |
            +-------------------+   |
            | Configured Gadget |---|
   Gadget   +-------------------+                                    
     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   UDC      +-------------------+  Disconnect   +-------------------+ 
            | Attached Gadget   |-------------->| Detached Gadget   |
            |                   |<------------- |                   |
            +-------------------+   Connect     +-------------------+
     - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
   Hardware                                                           


```
N.B.
1. Multiple Gadget USB Device Definitions can be created and co-exist.
2. Only a single Gadget USB Device can be *enabled* at one time.
3. Attempting to enable a Gadget USB Device will fail another Gadget Device is enabled.
3. When *enabled* a device defaults to *attached*.
4. An enabled Gadget Device cannot be *removed*.
5. Each of multiple Gadget Devices must be separately *removed*.


## Gadget USB Device Definition File

*Gadget USB Device Definition Files* are *JSON* files that contain all of the information to define
one or more USB Device's along with their attributes, strings, os descriptors, functions and configurations.

There is a close correspondence between the JSON definition file and the resulting Gadget ConfigFS information. 

N.B.
- multiple *USB Device Definitions* can be present and can be configured into the GadgetFS
- multiple *USB Device Functions* can be specified (from the list of Gadget Functions available)
- multiple *USB Device Configurations* can be specified, each with a different set of the available *USB Device Functions*
- within a configuration the array of *configuration function definitions* are used to create the symlinks pointing to the defined functions by the creation process.
- some entries in ConfigFS functions display Gadget generated data, notably acm port_num and ecm ifname are automatically created and not set from the definition file
- the os_desc entry rules are specific and designed to support Windows, see the RNDIS example for more information
- multiple languages can have strings by specifying separate LANG identifiers for each, for both the *USB Device Definition* and each *USB Device Configuration*

## Example

This defines a composite USB Device called *belcarra* containing two ACM and one ECM functions. There
is one configuration called "Belcarra Composite CDC 2xACM+ECM.1" which will be the default configuration
presented to the host during enumeration.

This is sample file:
```
# Gadget Device Definition File
# 2020-03-17
{
    "belcarra-acm-ecm": {
        # USB Device Descriptor Fields
        "idVendor": "0x15ec",
        "idProduct": "0xf102",
        "bcdDevice": "0x0001",
        "bDeviceClass": "0x00",
        "bDeviceSubClass": "0x00",
        "bDeviceProtocol": "0x00",
        "bcdUSB": "0x0200",
        "bMaxPacketSize0": "0x40",
        # USB Device Strings
        "strings": {
            "0x409": {
                "serialnumber": "0123456789",
                "product": "ACMx2-ECM Gadget",
                "manufacturer": "Belcarra Technologies Corp"
            }
        },
        # Gadget Functions list: see /sys/module/usb_f*,
        # E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage
        #       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial
        # Use: The function name (without prefix) is used with instantion name, e.g. eem.usb0 or acm.GS0
        "functions": {
            "acm.GS0": {},
            "acm.GS1": {},
            "ecm.usb0": {
                "qmult": "5",
                "host_addr": "c6:34:7c:45:a6:c5",
                "dev_addr": "0e:6a:8a:85:db:76"
            }
        },
        # Gadget Configurations list
        "configs": {
            "config.1": {
                # Configuration Descriptor
                # bmAttributes: bit 5 support remote wakeup
                # bmAttributes: bit 6 self-powered
                # bmAttributes: bit 7 bus-powered
                # MaxPower: Power requirements in two-milliampere units, only valid of bit 7 is set
                "bmAttributes": "0x80",
                "MaxPower": "2",
                "strings": {
                    # USB Device Configuration Strings
                    "0x409": {
                        "configuration": "CDC 2xACM+ECM"
                    }
                },
                # This determines the order in the Configuration descriptor
                "functions": [
                    {
                        # Host Match USB\VID_15EC&PID_F102&MI_00
                        "name": "acm.GS0",
                        "function": "acm.GS0"
                    },
                    {
                        # Host Match USB\VID_15EC&PID_F102&MI_02
                        "name": "ecm.usb0",
                        "function": "ecm.usb0"
                    },
                    {
                        # Host Match USB\VID_15EC&PID_F102&MI_04
                        "name": "acm.GS1",
                        "function": "acm.GS1"
                    }
                ]
            }
        },
        # Microsoft OS Descriptors Support
        # C.f. https://docs.microsoft.com/en-us/previous-versions/gg463179(v=msdn.10)
        "os_desc": {
            "qw_sign": "",
            "b_vendor_code": "0x00",
            "use": "0"
        }
    }
}

```
We can view the generated Gadget ConfigFS using *sysfstree*:
```
# gadgetconfig --add belcarra-2acm+ecm.json
# sysfstree_raspbian --gadget
[/sys/kernel/config/usb_gadget]
└──[belcarra]
    ├──bcdDevice: 0x0001
    ├──bcdUSB: 0x0200
    ├──bDeviceClass: 0x00
    ├──bDeviceProtocol: 0x00
    ├──bDeviceSubClass: 0x00
    ├──bMaxPacketSize0: 0x40
    ├──[configs]
    │   └──[Belcarra Composite CDC 2xACM+ECM.1]
    │       ├──acm.GS0 -> /sys/kernel/config/usb_gadget/belcarra/functions/acm.usb0
    │       ├──acm.GS1 -> /sys/kernel/config/usb_gadget/belcarra/functions/acm.usb1
    │       ├──bmAttributes: 0x80
    │       ├──ecm.usb0 -> /sys/kernel/config/usb_gadget/belcarra/functions/ecm.usb0
    │       ├──MaxPower: 2
    │       └──[strings]
    │           └──[0x409]
    │               ├──configuration: CDC 2xACM+ECM
    ├──[functions]
    │   ├──[acm.usb0]
    │   │   ├──port_num: 0
    │   ├──[acm.usb1]
    │   │   ├──port_num: 1
    │   └──[ecm.usb0]
    │       ├──dev_addr: 4e:28:20:f0:35:ab
    │       ├──host_addr: b6:fe:ea:86:2a:50
    │       ├──ifname: usb0
    │       ├──qmult: 5
    ├──idProduct: 0xd031
    ├──idVendor: 0x15ec
    ├──[os_desc]
    │   ├──b_vendor_code: 0x00
    │   ├──qw_sign:
    │   ├──use: 0
    ├──[strings]
    │   └──[0x409]
    │       ├──manufacturer: Belcarra Technologies
    │       ├──product: Composite CDC 2xACM+ECM
    │       ├──serialnumber: 0123456789
    ├──UDC: fe980000.usb
```

## Shell script

To facilitate installing Gadget definitions in an early boot environment a Gadget Definition file
can be converted to a simple shell script:
```
    gadgetconfig --sh-auto definitions/hid-example.json > hid-example.sh
```
Would produce:
```
    #!/bin/sh
    # Created from definitions/hid-example.json

    mkdir -p "/sys/kernel/config/usb_gadget/g2"
    echo "0x1d6b" > "/sys/kernel/config/usb_gadget/g2/idVendor"
    echo "0x0104" > "/sys/kernel/config/usb_gadget/g2/idProduct"
    echo "0x0001" > "/sys/kernel/config/usb_gadget/g2/bcdDevice"
    echo "0x00" > "/sys/kernel/config/usb_gadget/g2/bDeviceClass"
    echo "0x00" > "/sys/kernel/config/usb_gadget/g2/bDeviceSubClass"
    echo "0x00" > "/sys/kernel/config/usb_gadget/g2/bDeviceProtocol"
    echo "0x0200" > "/sys/kernel/config/usb_gadget/g2/bcdUSB"
    echo "0x40" > "/sys/kernel/config/usb_gadget/g2/bMaxPacketSize0"
    mkdir -p "/sys/kernel/config/usb_gadget/g2/strings/0x409"
    echo "0123456789" > "/sys/kernel/config/usb_gadget/g2/strings/0x409/serialnumber"
    echo "Bar Gadget" > "/sys/kernel/config/usb_gadget/g2/strings/0x409/product"
    echo "Foo Inc." > "/sys/kernel/config/usb_gadget/g2/strings/0x409/manufacturer"
    mkdir -p "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0"
    echo "235:0" > "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0/dev"
    echo "8" > "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0/report_length"
    echo "1" > "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0/protocol"
    echo "0" > "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0/subclass"
    echo -ne "\\x05\\x01\\x09\\x06\\xa1\\x01\\x05\\x07\\x19\\xe0\\x29\\xe7\\x15\\x00\\x25\\x01\\x75\\x01\\x95\\x08\\x81\\x02\\x95\\x01\\x75\\x08\\x81\\x03\\x95\\x05\\x75\\x01\\x05\\x08\\x19\\x01\\x29\\x05\\x91\\x02\\x95\\x01\\x75\\x03\\x91\\x03\\x95\\x06\\x75\\x08\\x15\\x00\\x25\\x65\\x05\\x07\\x19\\x00\\x29\\x65\\x81\\x00\\xc0" > "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0/report_desc"
    mkdir -p "/sys/kernel/config/usb_gadget/g2/configs/The only one.1"
    echo "0x80" > "/sys/kernel/config/usb_gadget/g2/configs/The only one.1/bmAttributes"
    echo "2" > "/sys/kernel/config/usb_gadget/g2/configs/The only one.1/MaxPower"
    mkdir -p "/sys/kernel/config/usb_gadget/g2/configs/The only one.1/strings/0x409"
    echo "1xHID" > "/sys/kernel/config/usb_gadget/g2/configs/The only one.1/strings/0x409/configuration"
    ln -s "/sys/kernel/config/usb_gadget/g2/functions/hid.usb0" "/sys/kernel/config/usb_gadget/g2/configs/The only one.1/some_name"

    basename /sys/class/udc/* > /sys/kernel/config/usb_gadget/g2/UDC
```



## Running Tests

gadgetconfig currently only has doctests.

Run tests with nose::

    nosetests --with-doctest src/gadgetconfig

Run tests with doctest::

    python -m doctest -v src/gadgetconfig/__init__.py

## Author
Stuart.Lynne@belcarra.com
Copyright (c) 2020 Belcarra Technologies (2005) Corp.

