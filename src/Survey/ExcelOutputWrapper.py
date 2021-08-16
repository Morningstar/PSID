import xlsxwriter
import random
import warnings
import pandas as pd
import numpy as np


class ExcelOutputWrapper:

    spaceBetweenTables = 2
    startColForTables = 1

    def __init__(self):
        self.curWorksheet = None
        self.curWorksheetName = None
        self.writer = None
        self.resetPosition()

    def resetPosition(self):
        self.lastStartRow = 0
        self.lastEndRow = 0
        self.lastEndCol = 0

    def addWorksheet(self, label):
        if len(label)>31:
            label = label[0:28] + str(random.randint(0, 999))
        try:
            self.curWorksheet = self.workbook.add_worksheet(label)
            self.curWorksheetName = label
            self.writer.sheets[label] = self.curWorksheet
            self.resetPosition()
        except Exception as e:
            print(e)
            print("Overwriting previous worksheet: " + label)
            self.curWorksheet = self.workbook.get_worksheet_by_name(label)
            self.curWorksheetName = label
            self.resetPosition()

    def createFormats(self):
        self.noFormat = None
        self.boldFormat = self.workbook.add_format({'bold': True})
        self.commentFormat = self.workbook.add_format({'italic': True, 'font_color': 'grey'})
        self.percentFormat = self.workbook.add_format({'num_format': "0.0%"})
        self.numberFormat = self.workbook.add_format({'num_format': '#,##0.0'})
        self.wholeNumberFormat = self.workbook.add_format({'num_format': '#,##0'})

        # https: // pbpython.com / improve - pandas - excel - output.html
        # worksheet.write_formula(cell_location, formula, total_fmt)
        # worksheet.set_column('B:D', 20)

    def addTable(self, dta, tableName, description=None, columnFormats=None, direction="down"):
        '''
        Add a new table in the current excel sheet, below or next to anything currently in the sheet.
        Optionally add a description and format the columns

        :param dta:
        :type dta:
        :param priorEndRow:
        :type priorEndRow:
        :param priorEndCol:
        :type priorEndCol:
        :param tableName:
        :type tableName:
        :param description:
        :type description:
        :param columnFormats:
        :type columnFormats:
        :param direction:
        :type direction:
        :return:
        :rtype:
        '''

        if (dta is None) or (len(dta.columns)==0):
            return

        if direction == "down":
            if self.lastEndRow > 0: # on a new page start=end=0
                startRow = self.lastEndRow + 1 + self.spaceBetweenTables
            else:
                startRow = 0
            startCol = 0  # Reset to first Col
        else: # Go to the left
            startRow = self.lastStartRow
            startCol = self.lastEndCol + self.spaceBetweenTables

        curRow = startRow
        curCol = startCol

        self.curWorksheet.write_string(curRow, curCol, tableName, self.boldFormat)
        curRow += 1
        if description is not None:
            self.curWorksheet.write_string(curRow, curCol, description, self.commentFormat)
            curRow += 1
        curCol += self.startColForTables
        dta.to_excel(self.writer, sheet_name=self.curWorksheetName, startrow=curRow, startcol=curCol)
        curRow += (len(dta.index))
        curCol = curCol + dta.index.nlevels + len(dta.columns.to_list())

        # In XLSWriter, it's  not possible to CHANGE a cell format after it's set.
        # Either you set it for the whole column (a problem when there are multiple tables)
        # Or you manually write each cell in the table - deconstructing "to_excel"
        # OR you use this hack -- a conditional format, in which the format is always on
        if columnFormats is not None:
            for columnToFormat in columnFormats.keys():
                lastDataRow = curRow
                firstDataRow = lastDataRow - (len(dta.index) - 1)

                if columnToFormat == "ALL":
                    lastDataCol = curCol
                    firstDataCol = lastDataCol - len(dta.columns.to_list())
                    # firstDataCol = startCol + dta.index.nlevels
                    # lastDataCol = startCol + dta.index.nlevels + len(dta.columns.to_list())
                else:
                    if columnToFormat in dta.columns.to_list():
                        firstDataCol = curCol - len(dta.columns.to_list())
                        firstDataCol = firstDataCol + dta.columns.get_loc(columnToFormat)
                        lastDataCol = firstDataCol
                    else:
                        warnings.warn("Problem applying format for " + columnToFormat + ". Column doesn't exist")
                        firstDataCol = None
                # range = (first_row, first_col, last_row, last_col)
                # https: // stackoverflow.com / questions / 22352907 / apply - format - to - a - cell - after - being - written - in -xlsxwriter
                if firstDataCol is not None:
                    self.curWorksheet.conditional_format(firstDataRow, firstDataCol, lastDataRow, lastDataCol, {'type': 'no_errors','format': columnFormats[columnToFormat]})

        self.lastStartRow = startRow
        self.lastEndRow = curRow
        self.lastEndCol = curCol

        return True

    def addImage(self, imageData, imageName, direction="down"):

        if direction == "down":
            if self.lastEndRow > 0: # on a new page start=end=0
                startRow = self.lastEndRow + 1 + self.spaceBetweenTables
            else:
                startRow = 0
            startCol = 0  # Reset to first Col
        else: # Go to the left
            startRow = self.lastStartRow
            startCol = self.lastEndCol + self.spaceBetweenTables

        curRow = startRow
        curCol = startCol

        self.curWorksheet.write_string(curRow, curCol, imageName, self.boldFormat)
        curRow += 1
        curCol += self.startColForTables

        self.curWorksheet.insert_image(curRow, curCol, "", {'image_data': imageData})

        # The big challenge with images, is that we dont know how large they are!
        # So, just take a guess..
        self.lastStartRow = startRow
        self.lastEndRow = curRow + 5
        self.lastEndCol = curCol


    def startFile(self, destinationFile):
        self.writer = pd.ExcelWriter(destinationFile, engine='xlsxwriter')
        self.workbook = self.writer.book
        self.createFormats()

    def endFile(self):
        self.workbook.close()

