'*** This file will be overwritten when the ClientPack is upgraded.      ***
'*** If you wish to modify the file, please make your changes in a copy. ***
'
' Description:
'   This sample script shows the basics of how to get connected;
'   it doesn't do anything with the connections it makes.

Set License = CreateObject("vralib.License")
License.AcceptEvaluationLicense

Set objConn = CreateObject("vralib.Connection")

' Uncomment the next two lines if you need to use a firewall
'objConn.FirewallType = "https"
'objConn.FirewallHostname = "myfirewall.mycompany.com:8080"

' Identify() does not authenticate to the server, but reads the ssh
' ident string and server key exchange information.  After Identify(),
' you can query for server version information (if it was included in
' the ssh ident string) and algorithms supported by the server.
'
' All of the functions in the "Echo" below can also be used after
' a call to Connect.
objConn.Identify "myserver.mydomain.com"
WScript.Echo objConn.RemoteProduct & vbNewLine & _
             objConn.RemoteVersion & vbNewLine & _
             objConn.RemoteIdentString & vbNewLine & _
             objConn.ServerCipherAlgorithms & vbNewLine & _
             objConn.ServerMacAlgorithms & vbNewLine & _
             objConn.ServerKexAlgorithms & vbNewLine & _
             objConn.ServerCompressionAlgorithms & vbNewLine & _
             objConn.ServerHostKeyAlgorithms & vbNewLine

' If you don't already have the host key saved in your host key database,
' you'll need the following line.
'objConn.AutoAcceptHostKey = true

' If you're having trouble connecting, the next two lines will get you
' a log.
'objConn.DebugLevel = 1
'objConn.DebugLogFile = "C:\temp\vralib.log"

' Uncomment the following lines if you need to configure authentication
' to connect the server.  If you have your public key in agent you should
' be able to connect without any additional configuration.
'
' If you are configured for gssapi (for example, you are in the same Windows domain
' as the server), you should also be able to connect without any additional configuration.
'
' Otherwise, you will probably have to specify a password in order to authentication
'objConn.Password = "My Password"

' Since we already used this connection object once, calling Connect without
' any arguments will reconnect to the same host.
objConn.Connect

' Here's an alternative way to specify the username, password, and port.
' Only the hostname is required.
' objConn.Connect "user:password@example.hostname.com"

' Disconnect the session.
' If the variable goes out of scope, this will happen automatically, so it's
' only necessary if you want to use objConn for another connection.
objConn.Disconnect