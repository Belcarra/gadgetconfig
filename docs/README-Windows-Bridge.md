# Windows 10 Bridge Setup





## Remediation

The Windows 10 Bridge can get into a state where it appears to be working but will fail to allow
DHCP to be used to get an address for the Network Bridge on Windows or for any of the clients
on the attached networks. 

You may see a message that says "An unexpected error occured while configuring the Network Bridge".

The instructions here may help:

[Fix for unexpected error](https://www.kapilarya.com/fix-an-unexpected-error-occurred-while-configuring-the-network-bridge)


FIX: An Unexpected Error Occurred While Configuring The Network Bridge
Method 1 – Eliminate Network Adapters From Bridge
1. Run ncpa.cpl command to open Network Connections section inside Control Panel.

2. Right click on existing network bridge and select Properties.

3. On the property sheet, switch to General tab. Remove checks from network adapters that are installed on system and click OK.

4. Next, execute devmgmt.msc command to open Device Manager.

5. Expand Network Adapters, right click on MAC Bridge Miniport and select Uninstall. Click OK on confirmation prompt.

Check the status of issue, it should be resolved.

If the issue is still present, refer Method 2 mentioned below.

Method 2 – Using Command Prompt

This issue may occur if Windows Management Instrumentation (WMI) repository is blocking the network bridge from being configured. We can rename the repository and resolve this issue then. You need to follow these steps:

1. Right click on Start Button and choose Command Prompt (Admin). In case if you’re using Windows 8.1/7, you can open Command Prompt using Windows Search.

2. In administrative Command Prompt window, type following commands (mentioned in bold) one-by-one and press Enter key after each:
```
net stop winmgmt
```
Note: IP Helper service is dependent upon Windows Management Instrumentation service. So while stopping WMI service, you will be asked to terminate IP Helper service first, so do the needful. If Windows fails to terminate WMI service then, retry above mentioned stop command.
```
cd /d %windir%\system32\wbem
ren repository repository.old
net start winmgmt
```
3. Close Command Prompt. Windows may take few minutes to rebuild WMI database. After waiting a while, reboot your system.

After restarting your machine, issue will no longer appear.
