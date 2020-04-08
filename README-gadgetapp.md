# Gadget USB Device Configuration App
## Copyright (c) 2020, Stuart.Lynne@belcarra.com
## Wed Mar 11 00:47:42 PDT 2020 

The *gadgetapp* is a simple GUI application that can be used to configure and enable Gadget USB Device configurations.


![GadgetApp Screenshot](file:gadgetapp.png) "Screen Shot"


## Installation

Pre-requisites:
- tkinter - apt install python3-tk


## X11

- install xauth
- touch .Xauthority
- chmod 600 .Xauthority

Gadgetapp must be run as root, if this fails with "X11 connection rejected because of wrong authentication"

Can be added to ~root/.bashrc:
```
xauth merge ~/.Xauthority
```

### sshd

```
X11Forwarding yes
```

### ssh
```
Host *
   ForwardAgent no
   ForwardX11 no
   ForwardX11Trusted yes
```

### .ssh
- authorized_keys2
-x

## UDC


## Add Definition


## Select Gadget Device Definition


## Enable Selected Definition


## Disable Selected Definition


## Information Tabs

These show the information form the SysFS file system using the *sysfstree* library and 
the equivalent *sysfstree_raspbian* commands.

- UDC State - shows a summary of the current UDC Driver state
- Gadget - shows summary of currently configured Gadget USB Device definitions
- systemd - shows if gadget service is started
- definitions - shows the Gadget USB Device definition for each named definition 

