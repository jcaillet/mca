import wx
import os
import time
import re
from loading import Loading
from mca.utils.utils import *
from mca.utils.parameters import *
from mca.centrality.straightness import *
from mca.ui.commonUI import *
# --- wxPython threadsafe  ---
from mca.utils.utils import GetTextTime
from wx.lib.pubsub import Publisher


class ComputeSC(centralityUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Straightness'
        self.helperFile = 'sc.pdf'

        centralityUI.__init__(self, parent, title)

        # --- rendering ---
        self.render()


    def action(self, event):
        fnBase = getFileNameBase(get_param_selectedProjectName(), self.sizerHNetNod.isNetwork(), fn_straightness)
        fileNames = getGeneratedFiles(fnBase)

        errorMsg = self.sizerHSave.check(fileNames)
        if errorMsg == '':
            if self.sizerHSave.isOverwritten():
                path = self.sizerHSave.getValue()
                Publisher().subscribe(self.catchError, 'catchError')
                normalized = self.sizerHNorm.isNormalized()

                self.Hide()
                self.load = Loading(self, "Computation")

                self.start = time.time()
                callback = "actionEnd"
                Publisher().subscribe(self.actionEnd, callback) # create a pubsub receiver

                # launch computation
                if self.sizerHNetNod.isNetwork():
                    EdgeStraightness(path, fnBase, callback, normalized)
                else:
                    NodeStraightness(path, fnBase, callback, normalized)
        else:
            dlg = wx.MessageDialog(self, errorMsg, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
