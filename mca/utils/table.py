import wx
import wx.grid as Grid
from mca.utils.parameters import *


class Table(Grid.Grid):

    def __init__(self, window, data, colNames):

        self.window = window

        # add blank row if no data
        if len(data) == 0:
            data = [[''] * len(colNames)]

        # --- styles ---
        tableMinSize = wx.Size(-1, -1)
        tableMaxSize = wx.Size(-1, 225)
        goodSize = tableMaxSize if len(data) > 10 else tableMinSize
        gridLabelFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        rowHeight = 25 # pixels
        gridRowAttr = Grid.GridCellAttr() # to color row
        gridRowAttr.SetBackgroundColour('#ffffff')
        self.arrowSpace = '   '

        # --- init ---
        Grid.Grid.__init__(self, window, size=goodSize)
        self.CreateGrid(len(data), len(colNames))
        self.matrix = [['' for y in xrange(len(colNames))] for x in xrange(len(data))]
        self.columnLabel = colNames
        self.sortedColumn = 0
        self.sortedDescending = False
        self.selectedRow = -1

        # --- bind events ---
        self.Bind(Grid.EVT_GRID_SELECT_CELL, self.selectedCell)
        self.Bind(Grid.EVT_GRID_LABEL_LEFT_CLICK, self.columnClicked)

        # --- set column names ---
        idx = 0
        for col in colNames:
            self.SetColLabelValue(idx, col + self.arrowSpace)
            idx += 1

        # --- feed matrix ---
        row = 0
        for r in data:
            col = 0
            for c in r:
                self.matrix[row][col] = c
                col += 1
            # by the way set style
            self.SetRowSize(row, rowHeight)
            if row % 2 == 0: self.SetRowAttr(row, gridRowAttr) # color odd row
            row += 1

        # --- layout ---
        self.SetLabelFont(gridLabelFont)
        self.SetRowLabelSize(0) # hide row label width (-1 to fit)
        self.SetColLabelSize(1.5 * rowHeight) # fit column label height
        self.AutoSize()
        self.SetDefaultCellBackgroundColour(self.GetBackgroundColour())
        self.SetMargins(0, 0)
        self.EnableEditing(False) # whole grid read-only

        self.sortColumn(0)
        self.repaint()



    def repaint(self):
        row = 0
        for r in self.matrix:
            col = 0
            for c in r:
                self.SetCellValue(row, col, str(c))
                col += 1
            row += 1

    def sortColumn(self, col):
        # reset previous sorted label
        self.SetColLabelValue(self.sortedColumn, self.columnLabel[self.sortedColumn] + self.arrowSpace)

        if self.sortedColumn != col:
            self.sortedDescending = True
        else:
            self.sortedDescending = not(self.sortedDescending)

        self.sortedColumn = col

        if self.sortedDescending:
            label = self.columnLabel[self.sortedColumn] + u' \u25bc'
            self.matrix.sort(key=lambda a: a[self.sortedColumn])
        else:
            label = self.columnLabel[self.sortedColumn] + u' \u25b2'
            self.matrix.sort(key=lambda a: a[self.sortedColumn], reverse=True)

        self.SetColLabelValue(self.sortedColumn, label)

        self.repaint()
        self.AutoSizeColumns(True)

    def printMatrix(self):
        for r in self.matrix:
            row = '|'
            for c in r:
                row += ' '+str(c)+' |'
            row += '\n'
            print row

    def selectedCell(self, event):
        row = event.GetRow()
        proj = self.GetCellValue(row, 1)
        kind = self.GetCellValue(row, 0)
        srs = self.GetCellValue(row, 2)
        res = self.GetCellValue(row, 6)
        nbobj = self.GetCellValue(row, 4)
        set_param_selectedProject(proj, kind, srs, res, nbobj)
        self.selectedRow = row
        self.SelectRow(row)
        event.Skip()

    def columnClicked(self, event):
        self.sortColumn(int(event.GetCol()))
        if self.selectedRow != -1: self.SelectRow(self.selectedRow)

