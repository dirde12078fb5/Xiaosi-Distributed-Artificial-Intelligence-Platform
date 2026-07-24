'*** This file will be overwritten when the ClientPack is upgraded.      ***
'*** If you wish to modify the file, please make your changes in a copy. ***
'
' Description:
'   This short example script prompts for the private key path and
'   passphrase and adds the key to the SSH2 authentication agent.

Set License = CreateObject("vralib.License")
License.AcceptEvaluationLicense

Set obj = CreateObject("vralib.Agent")
obj.AddKey InputBox("Private Key File", "Enter Private Key filename"), InputBox("Passphrase (will not be hidden)", "Enter passphrase")

WScript.Echo "Done"


