#!/usr/local/bin/python
# opal_expenses.py
#
# Subject: This script aims to import a Opal expense report and transform into a table format
#
# Authors:
#   Matheus Jose Geraldini dos Santos (matheusjgsantos@gmail.com)
#   Andrea Bucci
#
# Dependencies:
#   Python 2.6/2.7
#   pip: PDFMiner
#   pip: xlwt
#
# Additional info:
#	The CsvConverterClass was excerpted from https://stackoverflow.com/questions/36902496/python-pdfminer-pdf-to-csv, which was originaly developed by https://stackoverflow.com/users/64206/tgray. The class was mostly maintained as the original version, with minor changes.
#
# Version: 1
#

WEEK_DAYS = ['Sun ', 'Mon ', 'Tue ', 'Wed ', 'Thu ', 'Fri ', 'Sat ']
SHIFTER = {'sun': WEEK_DAYS[0:5],
           'mon': WEEK_DAYS[1:6],
           'tue': WEEK_DAYS[2:7]}

def sanitize():
    '''
    Sanitize the input

    @param None
    @return lst of arguments
    '''
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", help="apply manual/automatic filter",
                        default="auto", choices=['auto', 'manual', 'both'])
    parser.add_argument("--shift", help="day when shift starts",
                        default="mon", choices=['sun', 'mon', 'tue'])
    parser.add_argument("--input", help="OPAL .pdf file", required=True)
    args = parser.parse_args()
    return args

def openFileBrowser():
    from Tkinter import Tk
    import Tkinter, Tkconstants, tkFileDialog
    from Tkinter import Entry, Button, Label, StringVar
    # Create the TK window
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

def pdf_to_csv(filename, separator, threshold):
    from cStringIO import StringIO
    from pdfminer.converter import LTChar, TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfpage import PDFPage

    class CsvConverter(TextConverter):
        def __init__(self, *args, **kwargs):
            TextConverter.__init__(self, *args, **kwargs)
            self.separator = separator
            self.threshold = threshold

        def end_page(self, i):
            from collections import defaultdict
            lines = defaultdict(lambda: {})
            for child in self.cur_item._objs:  # <-- changed
                if isinstance(child, LTChar):
                    (_, _, x, y) = child.bbox
                    line = lines[int(-y)]
                    line[x] = child._text.encode(self.codec)  # <-- changed
            for y in sorted(lines.keys()):
                line = lines[y]
                if self.line_creator(line) != None:
                     self.outfp.write(self.line_creator(line))
                     self.outfp.write("\n")

        def line_creator(self, line):
            keys = sorted(line.keys())
            # calculate the average distange between each character on this row
            average_distance = sum([keys[i] - keys[i - 1] for i in range(1, len(keys))]) / len(keys)
            # append the first character to the result
            result = [line[keys[0]]]
            for i in range(1, len(keys)):
                # if the distance between this character and the last character is greater than the average*threshold
                if (keys[i] - keys[i - 1]) > average_distance * self.threshold:
                    # append the separator into that position
                    result.append(self.separator)
                # append the character
                result.append(line[keys[i]])
            printable_line = ''.join(result)
            return printable_line

    # ... the following part of the code is a remix of the
    # convert() function in the pdfminer/tools/pdf2text module
    rsrc = PDFResourceManager()
    outfp = StringIO()
    device = CsvConverter(rsrc, outfp, codec="utf-8", laparams=LAParams())
    # becuase my test documents are utf-8 (note: utf-8 is the default codec)

    fp = open(filename, 'rb')

    interpreter = PDFPageInterpreter(rsrc, device)
    for i, page in enumerate(PDFPage.get_pages(fp)):
        if page is not None:
            interpreter.process_page(page)

    device.close()
    fp.close()

    return outfp.getvalue()

# This function receives data from pdf_to_csv fuction, parsers the relevant lines and formats the output
def opal_formater(input_file):
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
    import re
    date_regex = '^(3[01]|[12][0-9]|0?[1-9])/(1[0-2]|0?[1-9])/(?:[0-9]{2})?[0-9]{2}'
    transactionId = '([0-9]{3,5})'
    transactionWeekDay = '([Mm]on|[Tt]ue|[[Ww]ed|[Tt]hu|[Ff]ri|[Ss]at|[Ss]un)'
    transactionTime = '([0-1][0-9]:[0-5][0-9])'
    transactionLocation = '\D[A-Za-z]+\s*'
    transactionJourneyNumber = '[1-99]{2}'
    transactionFareApplied = 'Travel Reward|Off-peak'
    transactionFareApplied_value=False
    transactionFullFare = '[0-9]{1,3}\.[0-9]{2}'
    transactionFullFare_value=False
    transactionDiscount = '[0-9]{1,3}\.[0-9]{2}'
    transactionDiscount_value=False
    transactionAmount = '[0-9]{1,3}\.[0-9]{2}'
    transactionAmount_value=False
    # Calls the pdf_to_csv function and receives the opal report data. Separator is ',', threshold is the size of each column
    csv_raw_data = pdf_to_csv(input_file, separator, threshold)
    # StringIO reads the long string from the pdf_to_csv and allow read lines from it as if it was a file
    csv_data = StringIO(csv_raw_data)
    for csv_raw_line in csv_data.readlines():
        # readlines is stupid and adds unnecessary new-line escapes (\n), so we'll rstrip it to avoid blank lines
        csv_line = csv_raw_line.rstrip()
        if len(csv_line) > 3 and csv_line[0].isdigit() and csv_line[1].isdigit():
            # print csv_line #Worked!
            ###regex the lines that starts with any date format, I guess(??)
            if re.match(transactionId, csv_line):
                separated_csv_line = csv_line.split(',')
                for separated_item in separated_csv_line:
                    if re.match(transactionId, separated_item):
                        transactionId_value = separated_item
                        #print transactionId_value
                    if re.match(transactionWeekDay, separated_item):
                        transactionWeekDay_value = separated_item
                        #print transactionWeekDay_value
                    if re.match(transactionTime, separated_item):
                        transactionTime_value = separated_item
                    if re.match(transactionLocation, separated_item):
                        transactionOrigin_value = separated_item
                    if re.match(transactionJourneyNumber, separated_item):
                        transactionJourneyNumber_value = separated_item
                    if re.match(transactionFareApplied, separated_item):
                        transactionFareApplied_value = separated_item
                    if re.match(transactionFullFare, separated_item) and not transactionFullFare_value and not transactionDiscount_value and not transactionAmount_value:
                        transactionFullFare_value = separated_item
                    else:
                        if transactionFullFare_value and not transactionDiscount_value and re.match(transactionDiscount, separated_item) and not transactionAmount_value:
                             transactionDiscount_value = separated_item
                        else:
                            if transactionFullFare_value and transactionDiscount_value and re.match(transactionAmount, separated_item) and not transactionAmount_value:
                                transactionAmount_value = separated_item

            if re.match (date_regex, csv_line):
                # if matches, we'll split the lines and add two "," in order do shift the line two rows to de right on excel
                separated_csv_line = csv_line.split(',')
                complete_csv_line = ''
                for separated_item in separated_csv_line:
                    if re.match(date_regex, separated_item):
                        transactionDate_value = separated_item
                        #print transactionDate_value
                    if re.match(transactionLocation, separated_item):
                        transactionDestination_value = separated_item
                    #complete_csv_line = complete_csv_line+","+separated_item+","
                #csv_line = complete_csv_line
                #print csv_line
                    #print separated_item
            # Print the lines that doesn't starts with a date
            #else:
                #print csv_line
                if not transactionFareApplied_value:
                    transactionFareApplied_value = "N/A"
                print "%s %s %s %s %s %s %s %s %s %s" % (transactionId_value, transactionWeekDay_value, transactionDate_value, transactionTime_value, transactionOrigin_value, transactionDestination_value, transactionFareApplied_value, transactionFullFare_value, transactionDiscount_value, transactionAmount_value)

if __name__ == '__main__':
    # the separator to use with the CSV
    separator = ','
    # the distance multiplier after which a character is considered part of a new word/column/block. Usually 1.5 works quite well
    threshold = 2
    # Sanitize args, from Andrea
    #args = sanitize()
    #mode = args.mode.lower()
    #shift = SHIFTER[args.shift.lower()]
    #src_file = args.input
    opal_filename="/Users/gmatheus/Documents/Personal/Expenses/OPAL_05-2018.pdf"
    opal_formater(opal_filename)
    #openFileBrowser()
