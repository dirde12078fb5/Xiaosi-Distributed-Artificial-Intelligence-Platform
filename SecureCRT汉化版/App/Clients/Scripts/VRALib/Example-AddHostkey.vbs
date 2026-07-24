'*** This file will be overwritten when the ClientPack is upgraded.      ***
'*** If you wish to modify the file, please make your changes in a copy. ***
'
' Description:
'   This short example script shows how to add keys to
'   the SSH2 host key database.

Set License = CreateObject("vralib.License")
License.AcceptEvaluationLicense

Set obj = CreateObject("vralib.HostKeyDatabase")

' Fill in the key information below
obj.AddKey "my.ssh.server", "192.168.143.193", "c:\temp\hostkey.pub"
obj.AddKey "my.ssh.server:22222", "192.168.143.193", "c:\temp\hostkey.pub"

WScript.Echo "Keys written to: " & obj.Path

