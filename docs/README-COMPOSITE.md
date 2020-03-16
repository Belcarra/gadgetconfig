# Gadget USB Composite Device
## Copyright (c) 2020, Stuart.Lynne@belcarra.com
## Sun Mar 15 16:34:40 PDT 2020

*Gadget USB Devices* support *USB Composite Device*.

A USB Composite Device is one that supports multiple functions in a configuration.

To work correctly your host must recognize composite configurations and be able to load
the appropriate *USB Class* drivers for each function in the configuration.

For example in Windows an INF file must be available to match the:
- Vendor ID
- Product ID
- Interface number

Because the host operating systems require a match by all three values, including the interface
number, it is important to specify the order of the functions used by a configuration in the 
correct order.

N.B. Some functions require multiple interfaces:
- eem 1
- acm 2
- ecm 2

## Example - eem - acm

In this example:
- interface 0 - eem
- interface 1 - acm


```
# Gadget Device Definition File
# 2020-03-15
{
    "belcarra-eem-acm": {
        # USB Device Descriptor Fields
        # USB Device Strings
        "strings": {
            "0x409": {}
        },
        # Gadget Functions list: see /sys/module/usb_f*,
        # E.g.: usb_f_acm, usb_f_ecm, usb_f_eem, usb_f_hid, usb_f_mass_storage
        #       usb_f_midi, usb_f_ncm, usb_f_obex, usb_f_rndis, usb_f_serial
        # Use: The function name (without prefix) is used with instantion name, e.g. eem.usb0 or acm.GS0
        "functions": {
            "acm.usb0": {},
            "acm.usb1": {},
            "eem.usb0": {}
        },
        # Gadget Configurations list
        "configs": {
            "config.1": {
                # Configuration Descriptor
                # bmAttributes: bit 5 support remote wakeup
                # bmAttributes: bit 6 self-powered
                # bmAttributes: bit 7 bus-powered
                # MaxPower: Power requirements in two-milliampere units, only valid of bit 7 is set
                "strings": {
                    # USB Device Configuration Strings
                    "0x409": {}
                },
                # The order of the functions here determines the order in the Configuration descriptor
                "functions": [
                    {
                        "name": "eem.usb0",
                        "function": "eem.usb0"
                    },
                    {
                        "name": "acm.GS0",
                        "function": "acm.usb0"
                    },
                    {
                        "name": "acm.GS1",
                        "function": "acm.usb1"
                    }
                ]
            }
        },
        # Microsoft OS Descriptors Support
        # C.f. https://docs.microsoft.com/en-us/previous-versions/gg463179(v=msdn.10)
        "os_desc": {}
    }
}
```


