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
# --- wxPython threadsafe  ---
from wx.lib.pubsub import Publisher


class NewProject(newUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Create new network project'
        self.helperFile = 'new_network.pdf'
        self.table = parent.projectGrid

        newUI.__init__(self, parent, title)

        # --- network ---
        self.sizerHNetwork = uploadFileSizer(self.panel, 'Network', self.fit)
        self.sizerV.Add(self.sizerHNetwork, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- tolerance ---
        self.sizerHTolerance = toleranceSizer(self.panel)
        self.sizerV.Add(self.sizerHTolerance, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- rendering ---
        self.render()

    def action(self, event):
        # check all inputs data and notify errors
        errorMsg = '' # reset error messages
        errorMsg += self.sizerHProject.check()
        errorMsg += self.sizerHAuthor.check()
        errorMsg += self.sizerHProjectSrs.check()
        errorMsg += self.sizerHNetwork.check()
        errorMsg += self.sizerHProjectSrs.check()
        errorMsg += self.sizerHTolerance.check()

        if errorMsg == '':
            self.srsO = self.sizerHProjectSrs.getValue()
            self.srsO= re.search(r'\[(\d*)\].*', self.srsO).group(1)
            unit = getUnit(int(self.srsO))
            if unit == degreeUnit:
                warningMsg = 'You have chosen a projection with unit in degrees.\n'
                warningMsg += 'Would you like to contiue?'
                dlgWarning = wx.MessageDialog(self, warningMsg, 'Warning lon/lat projection system', wx.YES_NO|wx.ICON_EXCLAMATION)
                if dlgWarning.ShowModal() == wx.ID_YES:
                    self.createNewProject()
                dlgWarning.Destroy()
            else:
                self.createNewProject()
        else:
            dlg = wx.MessageDialog(self, errorMsg, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def createNewProject(self):
       # get form values
        self.projectName = self.sizerHProject.getValue()
        self.authorName = self.sizerHAuthor.getValue()
        self.shape = self.sizerHNetwork.getValue()
        self.tol = self.sizerHTolerance.getValue()
        self.srsI = self.sizerHNetwork.getSRSValue() 
        self.srsI = re.search(r'\[(\d*)\].*', self.srsI).group(1)
 
        Publisher().subscribe(self.catchError, 'catchError') # create a pubsub receiver
        self.tmp = None
        self.topoCreated = False

        self.Hide()
        self.load = Loading(self, "Loading")

        self.start = time.time()

        cbPopEnd = "populateEnd"
        Publisher().subscribe(self.populateEnd, cbPopEnd) # create a pubsub receiver
        Populate(self.shape, self.srsI, self.srsO, self.projectName, cbPopEnd)

    def cleanData(self):
        if self.topoCreated:
            cleanPublicSchema(self.projectName)
        if self.tmp is not None:
            cleanTemporaryFiles(self.tmp)

    def populateEnd(self, msg):
        consoleAppend(' > Populate done in %s' % GetTextTime(time.time() - self.start))
        self.tmp = msg.data

        self.ts = time.time()
        callback = "topologyEnd"
        Publisher().subscribe(self.topologyEnd, callback) # create a pubsub receiver
        consoleAppend('Start creating the topology... This can take a while, please be patient...')
        Topology(self.projectName, self.srsO, self.authorName, self.tol, 'network', 0, callback)

    def topologyEnd(self, msg):
        consoleAppend(' > Topology created in %s' % GetTextTime(time.time() - self.ts))
        self.topoCreated = True

        self.ts = time.time()
        callback = "degree2End"
        Publisher().subscribe(self.degree2End, callback) # create a pubsub receiver
        consoleAppend('Start cleaning nodes degree 2...')
        CleanNodesDegree2(self.projectName, callback)

    def degree2End(self, msg):
        consoleAppend(' > Clean nodes with degree 2 in %s' % GetTextTime(time.time() - self.ts))

        self.cleanData()
        self.parent.repaintTable()
        self.actionEnd(None)
