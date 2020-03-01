# Gadget Configuration
## Stuart Lynne 
## Sun Mar 01 13:36:04 PST 2020 

## Inconsistent Nomenclature

### Function vs Device vs Gadget

In the context of USB, on the device side, a single USB Device can have several USB Functions. 

The original USB specification referred to *USB Devices* and *USB Functions* without rigorously defining the difference.

With respect to Linux Gadget USB, some documents refer to a single device as a USB Gadget. Which corresponds to
the complete USB Device.

To be able do define what is needed to specify a *USB Gadget* we will use *USB Device Definition*. That is 
intended to contain all of the information required to implement the *USB Device* using the *USB Gadget* infrastructure.

### Device vs Configuration

In the context of USB, on the device side, a single *USB Device* can define multiple *USB Device Configurations*.

With each *USB Device Configuration* having a different set of properties. 
During enumeration the *USB Host* can, if desired, query 
the *USB Device* to determine what each *USB Device Configuration* is and then select the desired 
*USB Device Configuration*.

Specifically within a *USB Device Definition*:
- a list of one or more *USB Functions* can be specified
- a list of one or more *USB Device Configurations* can be defined each specifying a sub-set of the available *USB Functions*.


### Gadget Device Configuration

Gadget Device Configuration is done through the Linux ConfigFS facility implemented by the *libcomposite* module. 

- Multiple *USB Device Definitions* can be created. 
- Each *USB Device Definition* can have multiple *USB Function Definitions*
- Each *USB Device Definition* can have multiple *USB Configurations*
- A single *USB Device Definition* can be selected for use


# Summary

The Gadget USB System in Linux allows for configuration through ConfigFS. Or more specifically by creating and
manipulating directories and files in:

    /sys/kernel/config/usb_gadget

Gadgets a created based on what a USB Device needs. This is a hierarchy of data that is used to define each
USB Device and all of the information that Gadget needs to create it.


Gadget will use a list of devices each with:

    USB Device Definition
        Device Attributes
            DeviceName
            idVendor
            idProduct
            bcdDevice
            bcdUSB
            bDeviceClass
            bDeviceSubClass
            bDeviceProtocol
            bMaxPacketSize0

        Operating System Descriptors
            config_id
            qw_sign
            b_vender_code

        Device Strings
            Lang
            List of strings
        
        USB Device Function Definitions List

            Function Name
            Instance
            Type
            Attributes

        USB Device Configuration Definitions List
            
            Configuration ID
            Configuration Name
            Configuration Attributes
            Configuration Strings
                Lang
                List of strings
            Configuration Functions List
                Function Name
                Function named in Device Function List

            Operating System Descriptors
                interface
                compatible_id
                sub_compatible_id

        UDC
            name of platform UDC or empty


Other than strings the Gadget ConfigFS does not appear to allow specification of individual configuration descriptors.
Those are implemented and defined (based on attributes provided in some cases) by the underlying gadget function drivers.

This design allows a single device to implement various different configurations to suit requirements.

For example a device might request three functions:

    acm
    ecm
    mass_storage

And implement multiple configurations:

    id=1 ecm+2xacm
    id=2 ecm+mass_storage
    id=3 ecm+acm+mass_storage

If the configuration is change the Gadget system will detach, switch to the new configuration and then reattach. 

The Gadget system also allows multiple devices to be set up. This allows for having different vendor/product id's etc.


## Sample *USB Device Definition JSON file*

This file defines a *USB Device* that has:

- three functions, two ACM and one ECM
- one configuration
- there are attributes for the device 
```
{
    "belcarra": {
        "idVendor": "0x15ec",
        "idProduct": "0xf021",
        "bcdDevice": "0x0001",
        "bDeviceClass": "0x00",
        "bDeviceSubClass": "0x00",
        "bDeviceProtocol": "0x00",
        "bcdUSB": "0x0200",
        "bMaxPacketSize0": "0x40",
        "strings": {
            "0x409": {
                "manufacturer": "Belcarra Test",
                "product": "CDC EEM",
                "serialnumber": "0123456789"
            }
        },
        "functions": {
            "eem.usb0": {
                "dev_addr": "4e:28:20:f0:35:ab",
                "host_addr": "b6:fe:ea:86:2a:50",
                "qmult": "5"
            }
        },
        "configs": {
            "Belcarra EEM.1": {
                "bmAttributes": "0x80",
                "MaxPower": "2",
                "strings": {
                    "0x409": {
                        "configuration": "CDC EEM"
                    }
                },
                "functions": [
                    {
                        "name": "eem.usb0",
                        "function": "eem.usb0"
                    }
                ]
            }
        },
        "os_desc": {
            "b_vendor_code": "0x00",
            "qw_sign": "",
            "use": "0"
        }
    }
}
```
