'*** This file will be overwritten when the ClientPack is upgraded.      ***
'*** If you wish to modify the file, please make your changes in a copy. ***
'
' Description:
'   This script connects to an SSH2 server, runs the
'   Unix/Linux command uptime, and writes the current
'   date and the results of the uptime command into the
'   first blank row in the specified Excel spreadsheet.
'
' Notes:
' - Fill in the connection information prior to running
'   this script.
' - The Excel spreadsheet must exist prior to running
'   this script.
' - This script does not contain any error checking.

Set License = CreateObject("vralib.License")
License.AcceptEvaluationLicense

' Create an SSH2 connection object
Set g_objConnection = CreateObject("VRALIB.Connection")

' Set up the connection information
g_objConnection.Hostname = "myhost"
g_objConnection.Port = 22
g_objConnection.Username = "myusername"
g_objConnection.AuthenticationMethods = "password"
g_objConnection.Password = "mypassword"
g_objConnection.Connect

Set objExcel = CreateObject("Excel.Application")

' The Excel file must exist prior to running this script
Set objWorkbook = objExcel.Workbooks.Open ("C:\temp\test.xls") 

' Find the first empty row in the spreadsheet.
intRow = 1
strDN = ""
Do Until objExcel.Cells(intRow,1).Value = "" 
      intRow = intRow + 1
Loop

' Put the current date in the first column in the spreadsheet.
objExcel.Cells(intRow,1).Value = Date

' Put the output from the uptime command in the second column
' in the spreadsheet.
Set g_objExec = g_objConnection.Exec("uptime")
objExcel.Cells(intRow,2).Value = g_objExec.StdOut.ReadLine

' Save the spreadsheet
objExcel.Workbooks(1).Save
objExcel.Workbooks(1).Close
objExcel.Quit

' Disconnect from the SSH2 server
g_objConnection.Disconnect

wscript.echo "Uptime information was added to the Excel spreadsheet." 
