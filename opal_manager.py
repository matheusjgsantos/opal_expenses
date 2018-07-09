#!/usr/local/bin/python -vvv
from Tkinter import Tk
import Tkinter, Tkconstants, tkFileDialog
from Tkinter import Entry, Button, Label, StringVar
window = Tk()
window.title("OPAL Expenses PDF importer")
window.geometry('765x400')
window.minsize(width=756, height=400)
textField=Label(window,width=13,anchor="w",borderwidth=1,text="OPAL expense file:")
textField.grid(column=1,row=0)
filenameFieldText=StringVar()
filenameField=Entry(window,width=60,textvariable=filenameFieldText)
filenameFieldText.set("No file selected")
filenameField.grid(column=2,row=0)
def pdfFileBrowse_func():
    global opalFileName
    opalFileName = tkFileDialog.askopenfilename(initialdir = "root", title = "Select Opal PDF report file",filetypes = (("PDF Files", "*.pdf"),("All files", "*.*")))
    filenameFieldText.set(opalFileName)
filenameBrowseButton=Button(window, text="Open PDF", command=pdfFileBrowse_func)
filenameBrowseButton.grid(column=3,row=0)
def processFileName_func():
    try:
        opal_formater(opalFileName)
    except:
        filenameFieldText.set("Select a file to process")
processFileButton=Button(window,text="Process",command=processFileName_func)
processFileButton.grid(column=3,row=1)
window.mainloop()
