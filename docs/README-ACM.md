# Gadget USB Device ACM and systemd
## Copyright (c) 2020, Stuart.Lynne@belcarra.com
## Sat Mar 14 13:29:12 PDT 2020 


Using the Gadget serial function (CDC-ACM protocol) to support a console login works well but requires some integration with systemd.


## Gadget Device Definition

Your device definition will need to add the acm function, e.g.:
```
        "functions": {
            "acm.GS0": {},
            "acm.GS1": {}
        },
```

And in the configuration area:
```
        "functions": [
            {
                "name": "acm.GS0",
                "function": "acm.GS0"
            },
            {
                "name": "acm.GS1",
                "function": "acm.GS1"
            }
        ]

```

Irregardless of the names used in the above, the Gadget serial driver will always instantiate *ttyGSn* style names.


## Systemd 

### Override file

There is a generic getty service definition that can be used to support the ttyGS devices. But some changes are required.

Add the following file (or files if multiple devices are required):
```
        /etc/systemd/system/getty@ttyGS0.service.d/override.conf
        /etc/systemd/system/getty@ttyGS1.service.d/override.conf
```

These files will contain:
```
        [Service]
        TTYReset=no
        TTYVHangup=no
        TTYVTDisallocate=no

```

### Life Cycle of an ACM device

To get a login enabled:

1. gadgetconfig --add belcarra-acm.json
2. gadgetconfig --enable belcarra-acm
3. systemctl enable getty@ttyGS0
4. systemctl start getty@ttyGS0

To disable:

1. systemctl stop getty@ttyGS0
2. gadgetconfig --disable 
3. gadgetconfig --remove belcarra-acm

### Cautions

It is safe to leave the getty@ttyGS0 service enabled and started. Agetty will wait for the ttyGS0 device to become available.

Attempting to remove the Gadget definition *WILL HANG* until service is stopped. 






