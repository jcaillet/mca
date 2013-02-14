import wx
import os
import time
import re
from loading import Loading
from mca.utils.utils import *
from mca.utils.parameters import *
from mca.centrality.closeness import *
from mca.ui.commonUI import *
from mca.utils.utils import GetTextTime
# --- wxPython threadsafe  ---
from wx.lib.pubsub import Publisher


class ComputeCC(centralityUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Closeness'
        self.helperFile = 'cc.pdf'
        self.isNetworkProject = get_param_selectedProjectKind() == 'network'

        centralityUI.__init__(self, parent, title)

        # --- weighted ---
        if self.isNetworkProject:
            self.sizerHWeighted = weightedSizer(self.panel)
            self.sizerV.Add(self.sizerHWeighted, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- radius ---
        self.sizerHRadius = radiusSizer(self.panel)
        self.sizerV.Add(self.sizerHRadius, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- rendering ---
        self.render()


    def action(self, event):
        wantLocal = self.sizerHRadius.isChecked()
        fnBase = getFileNameBase(get_param_selectedProjectName(), self.sizerHNetNod.isNetwork(), fn_closeness, local=wantLocal)
        fileNames = getGeneratedFiles(fnBase)

        errorMsg = '' # reset error messages
        errorMsg += self.sizerHSave.check(fileNames)
        if wantLocal: errorMsg += self.sizerHRadius.check()
        if errorMsg == '':
            if self.sizerHSave.isOverwritten():
                path = self.sizerHSave.getValue()
                if self.sizerHRadius.isChecked(): radius = self.sizerHRadius.getValue()
                Publisher().subscribe(self.catchError, 'catchError')
                normalized = self.sizerHNorm.isNormalized()
                if self.isNetworkProject:
                    weighted = self.sizerHWeighted.isWeighted()
                else:
                    weighted = True if wantLocal else False
                self.Hide()
                self.load = Loading(self, "Computation")

                self.start = time.time()
                callback = "actionEnd"
                Publisher().subscribe(self.actionEnd, callback) # create a pubsub receiver
                #launch computation
                if self.sizerHNetNod.isNetwork():
                    if wantLocal:
                        EdgeLocalCloseness(path, radius, fnBase, callback, weighted, normalized)
                    else:
                        EdgeCloseness(path, fnBase, callback, weighted, normalized)
                else:
                    if wantLocal:
                        NodeLocalCloseness(path, radius, fnBase, callback, weighted, normalized)
                    else:
                        NodeCloseness(path, fnBase, callback, weighted, normalized)

        else:
            dlg = wx.MessageDialog(self, errorMsg, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
