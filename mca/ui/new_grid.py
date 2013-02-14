import wx
import os
import time
import re
from mca.topology.topology import *
from loading import Loading
from mca.utils.parameters import *
from mca.utils.ogr2ogr import Populate, cleanTemporaryFiles
from mca.utils.utils import *
from mca.utils.db_utils import *
from mca.ui.commonUI import *
from mca.utils.grid_network import GridNetwork
# --- wxPython threadsafe  ---
from wx.lib.pubsub import Publisher

class NewGrid(newUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Create new grid project'
        self.helperFile = 'new_grid.pdf'

        newUI.__init__(self, parent, title)

        # --- polygon ---
        self.sizerHPolygon = uploadFileSizer(self.panel, 'Polygon', self.fit)
        self.sizerV.Add(self.sizerHPolygon, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- obstacles ---
        self.sizerHObstacles = uploadFileSizer(self.panel, 'Obstacles', self.fit, True)
        self.sizerV.Add(self.sizerHObstacles, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- resolution ---
        self.sizerHResolution = resolutionSizer(self.panel)
        self.sizerV.Add(self.sizerHResolution, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- rendering ---
        self.render()


    def action(self, event):
        self.wantObstacles = self.sizerHObstacles.isChecked()
        # check all inputs data and notify errors
        errorMsg = '' # reset error messages
        errorMsg += self.sizerHProject.check()
        errorMsg += self.sizerHAuthor.check()
        errorMsg += self.sizerHPolygon.check()
        errorMsg += self.sizerHResolution.check()
        errorMsg += self.sizerHProjectSrs.check()
        if self.wantObstacles:
            errorMsg += self.sizerHObstacles.check()

        if errorMsg == '':
            self.srsProject = self.sizerHProjectSrs.getValue()
            self.srsProject = re.search(r'\[(\d*)\].*', self.srsProject).group(1)
            unit = getUnit(int(self.srsProject))
            if unit == degreeUnit:
                warningMsg = 'You have chosen a projection with unit in degrees.\n'
                warningMsg += 'Would you like to contiue?'
                dlgWarning = wx.MessageDialog(self, warningMsg, 'Warning lon/lat projection system', wx.YES_NO|wx.ICON_EXCLAMATION)
                if dlgWarning.ShowModal() == wx.ID_YES:
                    self.computeNewGrid()
            	dlgWarning.Destroy()
            else:
                self.computeNewGrid()
        else:
            dlg = wx.MessageDialog(self, errorMsg, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def computeNewGrid(self):
        # get form values
        self.projectName = self.sizerHProject.getValue()
        self.authorName = self.sizerHAuthor.getValue()
        self.polygon = self.sizerHPolygon.getValue()
        self.obstacle = self.sizerHObstacles.getValue()
        self.srsObstacle = self.sizerHObstacles.getSRSValue()
        self.res = self.sizerHResolution.getValue()
        self.srsPolygon = self.sizerHPolygon.getSRSValue()
        self.srsPolygon = re.search(r'\[(\d*)\].*', self.srsPolygon).group(1)

        Publisher().subscribe(self.catchError, 'catchError') # create a pubsub receiver
        self.tmpP = None # path to temporary polygon files created during populate
        self.tmpO = None # path to temporary obstacles files created during populate
        self.gridCreated = False

        self.Hide()
        self.load = Loading(self, "Loading")
        self.start = time.time()

        callback = 'populatePolygonEnd'
        Publisher().subscribe(self.populatePolygonEnd, callback) # create a pubsub receiver
        Populate(self.polygon, self.srsPolygon, self.srsProject, 'polygon', callback)

    def cleanData(self):
        if self.gridCreated:
            cleanPublicSchema(self.projectName)
        if self.tmpP is not None:
            cleanPublicSchema('polygon')
            cleanTemporaryFiles(self.tmpP)
        if self.tmpO is not None:
            cleanPublicSchema('obstacles')
            cleanTemporaryFiles(self.tmpO)

    def populatePolygonEnd(self, msg):
        consoleAppend(' > Populate polygon in %s' % GetTextTime(time.time() - self.start))
        self.tmpP = msg.data

        self.ts = time.time()
        if self.wantObstacles:
            self.srsObstacle = re.search(r'\[(\d*)\].*', self.srsObstacle).group(1)

            callback = 'populateObstaclesEnd'
            Publisher().subscribe(self.populateObstaclesEnd, callback) # create a pubsub receiver
            Populate(self.obstacle, self.srsObstacle, self.srsProject, 'obstacles', callback)
        else:
            self.populateObstaclesEnd(None)

    def populateObstaclesEnd(self, msg):
        if self.wantObstacles:
            consoleAppend(' > Populate obstacles in %s' % GetTextTime(time.time() - self.ts))
            self.tmpO = msg.data

        self.ts = time.time()
        callback = "gridNetworkEnd"
        Publisher().subscribe(self.gridNetworkEnd, callback)
        pubDial = "publishDialog"
        Publisher().subscribe(self.publishDialog, pubDial)
        # the srs of the grid network is always the srs out of the polygon
        GridNetwork(callback, pubDial, self.res, self.srsProject, self.projectName, self.wantObstacles)

    def publishDialog(self, msg):
        txt = msg.data
        dlg = wx.MessageDialog(self, txt, 'Warning projection match', wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()
        # clean data
        self.cleanData()
        # enable main frame
        self.load.hide()
        self.parent.Enable()
        self.Destroy()

    def gridNetworkEnd(self, msg):
        consoleAppend(' > The grid network has been created in %s' % GetTextTime(time.time() - self.ts))
        self.gridCreated = True

        self.ts = time.time()
        callback = "topologyEnd"
        Publisher().subscribe(self.topologyEnd, callback) # create a pubsub receiver
        consoleAppend('Start creating the topology... This can take a while, please be patient...')
        Topology(self.projectName, self.srsProject, self.authorName, 0, 'grid', self.res, callback)

    def gridShpNetworkEnd(self, msg):
        # callback of GridNetwork.creatShp
        consoleAppend("New shapefile has been created in %s" % GetTextTime(time.time() - self.start))

        self.cleanData()
        self.parent.repaintTable()
        self.actionEnd(None)

    def topologyEnd(self, msg):
        consoleAppend('The topology has been created in %s...' % GetTextTime(time.time() - self.ts))

        self.cleanData()
        self.parent.repaintTable()
        self.actionEnd(None)
