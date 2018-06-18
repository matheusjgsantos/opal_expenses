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
        ###outfp.write("START PAGE %d\n" % i)
        if page is not None:
            ###print 'none'
            interpreter.process_page(page)
        ###outfp.write("END PAGE %d\n" % i)

    device.close()
    fp.close()

    return outfp.getvalue()

def opal_formater():
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO
    import re
    csv_raw_data = pdf_to_csv('OPAL_05-2018.pdf', separator, threshold)
    csv_data = StringIO(csv_raw_data)
    for csv_raw_line in csv_data.readlines():
        csv_line = csv_raw_line.rstrip()
        if len(csv_line) > 3 and csv_line[0].isdigit():
            # print csv_line #Worked!
            ###regex the lines that starts with digits
            date_regex = '^(3[01]|[12][0-9]|0?[1-9])/(1[0-2]|0?[1-9])/(?:[0-9]{2})?[0-9]{2}'
            if re.match (date_regex, csv_line):
                separated_csv_line = csv_line.split(',')
                complete_csv_line = ''
                for separated_item in separated_csv_line:
                    complete_csv_line = complete_csv_line+","+separated_item+","
                csv_line = complete_csv_line
            print csv_line
    #        ###if re.findall("i(?:[-/\s+](1[0-9]\d\d|20[0-2][0-5]))?", printable_line):
    #        if re.findall("[??\/??\/??]", csv_line):
    #            separated_line=csv_line.split(",")
    #            new_printable_line=''
    #            for item in separated_line:
    #                new_printable_line=new_printable_line+","+item+","
    #                print new_printable_line.rstrip('\n')
    #            else: 
    #                print csv_line.rstrip('\n')

if __name__ == '__main__':
    # the separator to use with the CSV
    separator = ','
    # the distance multiplier after which a character is considered part of a new word/column/block. Usually 1.5 works quite well
    threshold = 2
    #print pdf_to_csv('myLovelyFile.pdf', separator, threshold)
    #print pdf_to_csv('OPAL_05-2018.pdf', separator, threshold)
    opal_formater()