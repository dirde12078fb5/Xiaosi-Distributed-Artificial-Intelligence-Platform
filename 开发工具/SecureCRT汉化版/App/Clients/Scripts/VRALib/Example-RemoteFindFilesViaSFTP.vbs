'*** This file will be overwritten when the ClientPack is upgraded.      ***
'*** If you wish to modify the file, please make your changes in a copy. ***
'
' Description:
'   This script creates a web page that can be used to
'   connect to a remote SSH2 server, specify a string
'   to search for in the current working directory and
'   subdirectories.
'
' Notes:
' - The files can be constrained by a start and end date.
' - Regular expressions are supported for the search string.
' - SFTP is used to get the list of files.

Set License = CreateObject("vralib.License")
License.AcceptEvaluationLicense

Set g_objNetwork = CreateObject("WScript.Network")

Set g_fso = CreateObject("Scripting.FileSystemObject")
Set g_shell = CreateObject("WScript.Shell")

' Set the log file to the desired location.
g_strLogFile = "C:\Temp\vralib-debug-sftp-find-files.log"
if g_fso.FileExists(g_strLogFile) then g_fso.DeleteFile g_strLogFile

Dim g_objConnection

g_strCurrentDirectory = "."
g_strHostname = ""
g_strProxy = ""
g_strPort = "22"
g_strUsername = g_objNetwork.Username
g_strPassword = ""
g_strDateStartValue = ""
g_strDateEndValue = ""

Dim g_strSearchPattern
g_strSearchPattern = "[tT]e[xs]t"

g_bContinue = True

Dim g_objIE

Main

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sub Main()

    DisplayCommandWindow
        
End Sub

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Function DisplayCommandWindow()
    ' Set up the Internet Explorer dialog
    DisplayCommandWindow = False
    strEscEnterHandlerCode = "onkeydown=if(window.event.keyCode==27){document.all('ButtonHandler').value='';}else{if(window.event.keyCode==13){document.all('ButtonHandler').value='CD';}};"
    strSearchPatternCode = Replace(strEscEnterHandlerCode, "'CD';", "'FindFiles';")
    strPasswordHandler = Replace(strEscEnterHandlerCode, "'CD';", "'Connect';")
    strHTMLBody = "<font color='DarkGray'><b>SSH2 Connection Information</b></font>" & _
        "<br>" & _
        "<b><u>H</u>ostname:</b><input name='Hostname' size='30' maxlength='512' AccessKey='H'>" & _
        "&nbsp;&nbsp;&nbsp;&nbsp;" & _
        "<b>Por<u>t</u>:</b><input name='Port' size='5' maxlength='5' AccessKey='t'>" & _
        "&nbsp;&nbsp;&nbsp;&nbsp;" & _
        "<input id=AcceptHostKey name=AcceptHostKey accessKey=y type=checkbox>Accept host ke<u>y</u>" & _
        "<br>" & _
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" & _
        "<b>Pro<u>x</u>y:</b><input name='Proxy' size='30' maxlength='512' AccessKey='x'>&nbsp;&nbsp;(SOCKS5, specify as <i>proxy:port</i>)" & _
        "<br>" & _
        "<b><u>U</u>sername:</b><input name='Username' size='40' maxlength='512' AccessKey='u'>" & _
        "<br>" & _
        "<b>Pass<u>w</u>ord:</b><input name='Password' type=password size='42' maxlength='512' AccessKey='w'" & strPasswordHandler & ">" & _
        "<br>" & _
        "<hr>" & _
         "<button name='Connect' AccessKey='c' " & _
            "Onclick=document.all('ButtonHandler').value='Connect';>" & _
            "<u>C</u>onnect</button>" & _
        "&nbsp;&nbsp;&nbsp;&nbsp;" & _
        "<button name='Disconnect' AccessKey='n' " & _
            "Onclick=document.all('ButtonHandler').value='Disconnect';>" & _
            "Disco<u>n</u>nect</button>" & _
        "<hr>" & _
        "<b>File <u>P</u>attern:</b>&nbsp;&nbsp;&nbsp" & _
        "<input name='SearchPattern' size='80' maxlength='512' AccessKey='p' " & strSearchPatternCode & ">" & _
        "&nbsp;" & _
        "<button name='FindFiles' AccessKey='f' " & _
            "Onclick=document.all('ButtonHandler').value='FindFiles';>" & _
            "<u>F</u>ind Files</button>" & _
        "&nbsp;" & _
        "<button name='Stop' AccessKey='s' " & _
            "Onclick=document.all('ButtonHandler').value='Stop';>" & _
            "<u>S</u>top</button>" & _
        "<br>" & _
        "<b>Current D<u>i</u>r: &nbsp;&nbsp;</b>" & _
        "<input name='CurrentDirectory' size='80' maxlength=1024 AccessKey='i' " & strEscEnterHandlerCode & ">" & _
        "<br>" & _
        "<b>D<u>a</u>te Range Start: &nbsp;&nbsp;&nbsp;</b><input name='DateStart' id='DateStart' size='72' maxlength='512' AccessKey='a' " & strDateFieldHandler & ">" & _
	"&nbsp;&nbsp;<i>mm/dd/yyyy</i>" & _
        "<br>" & _
        "<b>Date Ran<u>g</u>e End: &nbsp;&nbsp;&nbsp;</b><input name='DateEnd' id='DateEnd' size='73' maxlength='512' AccessKey='g' " & strDateFieldHandler & ">" & _
	"&nbsp;&nbsp;<i>mm/dd/yyyy</i>" & _
        "<hr>" & _
        "<i>Current File: &nbsp;</i>" & _
        "<input name='CurrentFile' size='80' maxlength=65535 READONLY >" & _
        "<br>" & _
        "<b>Search Results</b><br>" & _
        "<div NOWRAP name='TextArea' ID='TextArea' style='width: 750px; height: 435px; overflow: scroll; overflow-y: scroll" & _
        "scrollbar-arrow-color:blue; scrollbar-face-color: #e7e7e7; " & _
        "scrollbar-3dlight-color: #a0a0a0; scrollbar-darkshadow-color: #888888; " & _
        "border-width: 1px; " & _
        "border-style: solid; " & _
        "border-color: #999; " & _
        "padding: 3; '></div>" & _
        "<hr>" & _
        "<button name='Close' AccessKey='O' " & _
            "Onclick=document.all('ButtonHandler').value='Close';>" & _
            "Cl<u>o</u>se</button>" & _
        "<input name='ButtonHandler' type='hidden' value='Nothing Clicked Yet'>"
        
    Set g_objIE = CreateObject("InternetExplorer.Application")
    g_objIE.Offline = True
    g_objIE.navigate "about:blank"

    ' This loop is required to allow the IE object to finish loading.
    Do
        WScript.Sleep 100
    Loop While g_objIE.Busy

    ' Make the custom dialog font look more like standard Windows dialogs
    g_objIE.Document.body.Style.FontFamily = "Sans-Serif"

    g_objIE.Document.Body.innerHTML = strHTMLBody

    ' Prevent the MenuBar, StatusBar, AddressBar, and Toolbar from being
    ' displayed as part of the IE window
    g_objIE.MenuBar = False
    g_objIE.StatusBar = False
    g_objIE.AddressBar = False
    g_objIE.Toolbar = False

    ' Set the initial size of the IE Window
    g_objIE.height = 875
    g_objIE.width = 810
 
    g_objIE.document.Title = "VRALIB Example: Find Files Using SFTP"
    g_objIE.Visible = True

    ' This loop is required to allow the IE window to fully display.
    Do
        WScript.Sleep 100
    Loop While g_objIE.Busy

    ' Brings the IE window to the foreground.
    Set objShell = CreateObject("WScript.Shell")
    objShell.AppActivate g_objIE.document.Title

    g_objIE.Document.All("Stop").Disabled = True

    ' Once the dialog is displayed and has been brought to the foreground, 
    ' set focus to the "Connect" button.
    g_objIE.Document.All("Connect").Focus

    g_objIE.Document.All("Hostname").Value = g_strHostname
    g_objIE.Document.All("Proxy").Value = g_strProxy
    g_objIE.Document.All("Port").Value = g_strPort
    g_objIE.Document.All("Username").Value = g_strUsername
    g_objIE.Document.All("SearchPattern").Value = g_strSearchPattern
    g_objIE.Document.All("AcceptHostKey").Checked = True
    g_objIE.Document.All("Connect").Disabled = False
    g_objIE.Document.All("FindFiles").Disabled = True
    g_objIE.Document.All("Disconnect").Disabled = True
    g_objIE.Document.All("CurrentDirectory").Disabled = False
    g_objIE.Document.All("CurrentDirectory").Value = g_strCurrentDirectory
    g_objIE.Document.All("DateStart").Value = g_strDateStartValue
    g_objIE.Document.All("DateEnd").Value = g_strDateEndValue


    ' Create the connection object    
    SetIEText "Creating <b>Connection</b> object..."
    Set g_objConnection = CreateObject("VRALIB.Connection")
    SetIEText "Connection object created and ready."
    
    Do
        ' If the user closes the IE window by Alt+F4 or clicking on the 'X'
        ' button, we'll detect that here, and exit the script if necessary.
        On Error Resume Next
            strButtonValue = g_objIE.Document.All("ButtonHandler").Value
            if Err.Number <> 0 then exit do
        On Error Goto 0
        
        ' Check to see which buttons have been clicked, and address each one
        ' as it's clicked.
        Select Case strButtonValue
            Case "Close"
                ' The user clicked Cancel. Exit the dialog.
                g_objIE.quit
                Exit Function
                
            Case "Connect"
            
                g_objIE.Document.All("Connect").Disabled = True
                
                ' The user clicked OK.
                ' Capture the data from each field in the dialog.
                g_strProxy = g_objIE.Document.All("Proxy").Value
                g_strHostname = g_objIE.Document.All("Hostname").Value
                g_strPort = g_objIE.Document.All("Port").Value
                g_strUsername = g_objIE.Document.All("Username").Value
                g_strSearchPattern = g_objIE.Document.All("SearchPattern").Value
                g_strPassword = g_objIE.Document.All("Password").Value

                ' Put the values in the connection object
                g_objConnection.Hostname = g_strHostname
                g_objConnection.Port = g_strPort
                
                g_objConnection.Username = g_strUsername

                g_objConnection.AuthenticationMethods = "password"
                g_objConnection.Password = g_strPassword
                
                g_objConnection.DebugLevel = 9
                g_objConnection.DebugLogFile = g_strLogFile
                
                bAccept = g_objIE.Document.All("AcceptHostKey").Checked
                g_objConnection.AutoAcceptHostKey = bAccept
                
                ' Check the proxy setting.
                g_strProxy = Trim(g_strProxy)
                if g_strProxy <> "" then
                    if Instr(g_strProxy, ":") > 0 then
                        vProxyElems = Split(g_strProxy, ":")
                        g_objConnection.FirewallHostname = vProxyElems(0)
                        g_objConnection.FirewallPort = vProxyElems(1)
                        g_objConnection.FirewallType = "socks5"
                    else
                        SetIEText "Firewall Port not specified.<br>" & _
                            "Attempting to connect without firewall..."
                        WScript.Sleep 1000
                    end if
                Else
                    SetIEText "Proxy not specified for connection... skipping proxy configuration..."
                    WScript.Sleep 200
                end if
                
                SetIEText "Connecting to " & g_strHostname & ":" & g_strPort & "..."
                
                On Error Resume Next
                ' Try to connect
                g_objConnection.Connect
                If Err.Number <> 0 then
                    g_objIE.Document.All("Disconnect").Disabled = True
                    g_objIE.Document.All("Connect").Disabled = False
                    g_objIE.Document.All("FindFiles").Disabled = True
                    g_objIE.Document.All("CurrentDirectory").Disabled = True

                    SetIEText "Failed to connect: " & Err.Number & ": " & Err.Description               
                    ' Reset our button handler value...
                    g_objIE.Document.All("ButtonHandler").Value = ""
                    g_objIE.Document.All("SearchPattern").Focus
                    On Error Goto 0

                Else
                    SetIEText "Connected to " & g_objConnection.RemoteIP & _
                              "(" & g_objConnection.RemoteProduct & " " & _
                              g_objConnection.RemoteVersion & ")"
                        
                    Set objRemFSO = g_objConnection.FileSystemObject
                    Set objFolder = objRemFSO.GetFolder(".")
                    SetIEText "Current Directory: " & objFolder.Path
                    g_objIE.Document.All("Disconnect").Disabled = False
                    g_objIE.Document.All("FindFiles").Disabled = False
                    g_objIE.Document.All("CurrentDirectory").Disabled = False
                    g_objIE.Document.All("CurrentDirectory").Value = g_strCurrentDirectory
                    g_objIE.Document.All("ButtonHandler").Value = "CD"

                end if
                
                
            Case "CD"
            
                g_strCurrentDirectory = g_objIE.Document.All("CurrentDirectory").Value

                ' Only accept input from this if we're connected.  We'll only
                ' be connected if the "Connect" button is disabled.
                If g_objIE.Document.All("Connect").Disabled = True then
                    SetIEText "Changing directory to """ & g_strCurrentDirectory & """..."
                    On Error Resume Next
                    objRemFSO.ChangeDirectory g_strCurrentDirectory
                    If Err.Number <> 0 then
                        SetIEText "CD Failed: " & Err.Description
                    else
                        SetIEText "Current Directory is now: " & objRemFSO.GetFolder(".").Path
                    end if
                end if
            
                ' Reset our button handler value.
                g_objIE.Document.All("ButtonHandler").Value = ""
                g_objIE.Document.All("CurrentDirectory").Focus
                On Error Goto 0
            
            Case "Disconnect"
                g_objConnection.Disconnect
                SetIEText "Disconnected from remote host."
                g_objIE.Document.All("Disconnect").Disabled = True
                g_objIE.Document.All("Connect").Disabled = False
                
                g_objIE.Document.All("FindFiles").Disabled = True
                g_objIE.Document.All("CurrentDirectory").Disabled = True
                g_objIE.Document.All("Stop").Disabled = True

                ' Reset our button handler value...
                g_objIE.Document.All("ButtonHandler").Value = ""
                g_objIE.Document.All("SearchPattern").Focus


            Case "FindFiles"
                g_bContinue = True
                g_objIE.Document.All("FindFiles").Disabled = True
                g_objIE.Document.All("Stop").Disabled = False
                g_strSearchPattern = g_objIE.Document.All("SearchPattern").Value
                g_strDateStartValue = g_objIE.Document.All("DateStart").Value
                g_strDateEndValue = g_objIE.Document.All("DateEnd").Value
                
                SetIEText "Searching """ & objRemFSO.GetFolder(".").Path & _
                          """ for files matching pattern: """ & g_strSearchPattern & """..."
                
                Set re = New RegExp
                re.Pattern = g_strSearchPattern
                
                strCurrentFolder = objRemFSO.GetFolder(".").Path
                nFilesFound = 0
                bCompleted = True
                
                ProcessFolderTree strCurrentFolder, objRemFSO, re, nFilesFound, bCompleted
                
                strAction = "Search Complete"
                if bCompleted <> True then strAction = "Search Canceled"
                AppendToIEText "<br>" & strAction & ": " & nFilesFound & " files found."
                g_objIE.Document.All("Stop").Disabled = True
                g_objIE.Document.All("FindFiles").Disabled = False               
                
                ' Reset our button handler value.                
                g_objIE.Document.All("ButtonHandler").Value = ""
                g_objIE.Document.All("SearchPattern").Focus
            
            Case "Stop"
                g_bContinue = False
                AppendToIEText "<br>[User canceled search operation.]"
                g_objIE.Document.All("Stop").Disabled = True
                g_objIE.Document.All("FindFiles").Disabled = False
                
                ' Reset our button handler value.
                g_objIE.Document.All("ButtonHandler").Value = ""
                g_objIE.Document.All("SearchPattern").Focus
                 
        End Select

        ' Wait for user interaction with the dialog.
        WScript.Sleep 200
    Loop

End Function

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sub ProcessFolderTree(szCurrentFolder, objFSO, re, ByRef nFilesFound, ByRef bCompleted)
' Recursive routine that runs a regexp on all contents of the szCurrentFolder
    Dim objFolder
    Set objFolder = objFSO.GetFolder(szCurrentFolder)

    ' Uncomment the following line to display the current folder within the matches
    ' list as well as within the "CurrentDirectory" field above it.
    ' AppendToIEText vbcrlf & "Processing Folder: " & objFolder.Path

    ' Having this at the top to do a breadth-first search
    Dim objFile, colFiles
    On Error Resume Next
    Set colFiles = objFolder.Files
    if Err.Number = 0 then
        ' Resume normal error handling
        On Error Goto 0
        
        For Each objFile in objFolder.Files
            if g_objIE.Document.All("ButtonHandler").Value = "Stop" then
                bCompleted = False
                exit sub
            end if
            On Error Resume Next
            g_objIE.Document.All("CurrentFile").Value = objFile.Path
            if Err.Number <> 0 then WScript.Quit
            On Error Goto 0
            On Error Resume Next
            Set matches = re.Execute(objFile.Path)
            if Err.Number <> 0 then
                AppendToIEText "<br><i>Error in Regular Expression: " & Err.Description & "</i>"
                bCompleted = False
                exit Sub
            end if
            On Error Goto 0
            if matches.Count > 0 then
                ' Don't check date if both the start and end dates are empty (it
                ' would just waste time)
                if trim(g_strDateStartValue) & trim(g_strDateEndValue) <> "" then
                    ' Check the date to see if this file matches the date value
                    ' condition specified.
                    Set objInfo = objFile.Stat
                    strTimeDateValue = ""
                    if objInfo.CreateTimePresent then
                        strTimeDateValue = objInfo.CreateTime
                    elseif objInfo.ModifyTimePresent then
                        strTimeDateValue = objInfo.ModifyTime
                    elseif objInfo.ChangeTimePresent then
                        strTimeDateValue = objInfo.ChangeTime
                    elseif objInfo.AccessTimePresent then
                        strTimeDateValue = objInfo.AccesTime
                    end if

                    If strTimeDateValue = "" then
                        AppendToIEText "<br>&nbsp;&nbsp;&nbsp;&nbsp;Unable to retrieve time info for """ & objFile.Path & """"
                    else
                        ' Default the start and end dates if either one is empty
                        ' (if both are empty, we won't get in here anyway)
                        if g_strDateStartValue = "" then g_strDateStartValue = "01/01/1970"
                        if g_strDateEndValue   = "" then g_strDateEndValue = Date
                        if DateDiff("d", strTimeDateValue, g_strDateStartValue) <= 0 and _
                           DateDiff("d", strTimeDateValue, g_strDateEndValue) >= 0 then
                            AppendToIEText "<br>" & _
                                Replace(objFile.Path, matches(0).Value, "<font color='red'>" & matches(0).Value & "</font>") & _
                                vbtab & "(" & strTimeDateValue & ")"
                            nFilesFound = nFilesFound + 1
                        end if
                    end if
                else
                    AppendToIEText "<br>" & Replace(objFile.Path, matches(0).Value, "<font color='red'>" & matches(0).Value & "</font>")
                    nFilesFound = nFilesFound + 1
                end if
            end if
        Next
    else
        ' Display "access denied" and other errors that might have occurred during
        ' processing
        AppendToIEText "<br>&nbsp;&nbsp;&nbsp;&nbsp;Error processing files in """ & objFolder.Path & """: " & Err.Description
        
        ' Resume normal error handling
        On Error Goto 0
        strAdditionalInfo = "[No other information available]"
        Set objInfo = objFolder.Stat
        if objInfo.OwnerGroupPresent then
            strAdditionalInfo = " [Owner=" & objInfo.Owner & "; Group=" & objInfo.Group & "]"
        end if
        if objInfo.PermissionPresent then
            strAdditionalInfo = strAdditionalInfo & " [Permissions: " & objInfo.Permissions & "]"
        end if
        if strAdditionalInfo <> "" then
            AppendToIEText strAdditionalInfo
        end if

    end if
    
    ' Having this at the bottom allows for a breadth-first search
    Dim objSubFolder, colFolders
    On Error Resume Next
    Set colFolders = objFolder.SubFolders
    if Err.Number = 0 then
        ' Resume normal error handling
        On Error Goto 0
        For Each objSubFolder in objFolder.SubFolders
            if g_objIE.Document.All("ButtonHandler").Value = "Stop" then
                bCompleted = False
                exit sub
            end if
            ' Make sure we don't recurse into "." or ".."
            if objSubFolder.Name <> "." and objSubFolder.Name <> ".." then
                ProcessFolderTree objSubFolder.Path, objFSO, re, nFilesFound, bCompleted
            end if
        Next
    else
        ' Display "access denied" and other errors that might have occurred during
        ' processing
        
        AppendToIEText "<br>&nbsp;&nbsp;&nbsp;&nbsp;Error processing subfolders in """ & objFolder.Path & """: " & Err.Description
        strAdditionalInfo = ""
        Set objInfo = objFolder.Stat
        if objInfo.OwnerGroupPresent then
            strAdditionalInfo = strAdditionalInfo & " [Owner=" & objInfo.Owner & "; Group=" & objInfo.Group & "]"
        end if
        if objInfo.PermissionPresent then
            strAdditionalInfo = strAdditionalInfo & " [Permissions: " & objInfo.Permissions & "]"
        end if
        if strAdditionalInfo <> "" then
            AppendToIEText strAdditionalInfo
        end if

        ' Resume normal error handling
        On Error Goto 0

    end if

    g_objIE.Document.All("CurrentFile").Value = ""
        
    bCompleted = True

End Sub

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sub AppendToIEText(szText)
' Adds new text to the textarea created in InitIE()
    On Error Resume Next
    
    szCurrentText = GetCurrentIEText
    
    Err.Clear
    g_objIE.Document.All("TextArea").InnerHTML = szCurrentText & szText
    if Err.Number <> 0 then
        On Error Goto 0
        exit sub
    end if
    
    ' Make sure the text area always shows the information that has
    ' been added to the bottom of the text area.
    g_objIE.Document.All("TextArea").doScroll "pageDown"

    
    ' Make sure the IE text area always is scrolled to the bottom when
    ' new lines of text appear.
    'g_objIE.Document.All("TextArea").scrolltop = g_objIE.Document.All("TextArea").scrollHeight
    
    On Error Goto 0
End Sub

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Function GetCurrentIEText()
' Retrieves the text within the "TextArea" created in InitIE()
    On Error Resume Next
    Err.Clear
    szCurrentText = g_objIE.Document.All("TextArea").InnerHTML
    if Err.Number <> 0 then
        On Error Goto 0
        exit Function
    end if
    
    GetCurrentIEText = szCurrentText
    On Error Goto 0  
End Function

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sub ClearIEText()
' Clears the "TextArea" created in InitIE()
    On Error Resume Next
    g_objIE.Document.All("TextArea").InnerHTML = ""
    On Error Goto 0
End Sub

'~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sub SetIEText(strText)
    On Error Resume Next
    g_objIE.Document.All("TextArea").InnerHTML = strText
    On Error Goto 0
End Sub
