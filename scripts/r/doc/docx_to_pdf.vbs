Function DocToPdf( docInputFile, pdfOutputFile )
    Set fileSystemObject = CreateObject("Scripting.FileSystemObject")
    Set wordApplication = CreateObject("Word.Application")
    Set wordDocuments = wordApplication.Documents

    docInputFile = fileSystemObject.GetAbsolutePathName(docInputFile)
    baseFolder = fileSystemObject.GetParentFolderName(docInputFile)

    If Len(pdfOutputFile) = 0 Then
        pdfOutputFile = fileSystemObject.GetBaseName(docInputFile) + ".pdf"
    End If

    If Len(fileSystemObject.GetParentFolderName(pdfOutputFile)) = 0 Then
        pdfOutputFile = baseFolder + "\" + pdfOutputFile
    End If

    ' Disable any potential macros of the word document.
    wordApplication.WordBasic.DisableAutoMacros

    Set wordDocument = wordDocuments.Open(docInputFile)

    ' See http://msdn2.microsoft.com/en-us/library/bb221597.aspx
    wdFormatPDF = 17
    wordDocument.SaveAs2 pdfOutputFile, wdFormatPDF

    wdDoNotSaveChanges = 0
    wordDocument.Close wdDoNotSaveChanges
    wordApplication.Quit wdDoNotSaveChanges

    Set wordApplication = Nothing
    Set fileSystemObject = Nothing
End Function

Set files = WScript.Arguments.Unnamed
For i = 0 to files.count -1
    wscript.Echo "Convert to pdf: " & files.Item(i)
    DocToPdf files.Item(i), ""
Next
