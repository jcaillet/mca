import wx
import os
import time
import re
from loading import Loading
from mca.utils.utils import *
from mca.utils.ogr_utils import *
from mca.utils.parameters import *
from mca.centrality.betweenness import *
from mca.ui.commonUI import *
# --- wxPython threadsafe  ---
from wx.lib.pubsub import Publisher



class ComputeBC(centralityUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Betweenness'
        self.helperFile = 'bc.pdf'
        self.isNetworkProject = get_param_selectedProjectKind() == 'network'
        self.isGridProject = get_param_selectedProjectKind() == 'grid'

        centralityUI.__init__(self, parent, title)

        # --- weighted ---
        if self.isNetworkProject:
            self.sizerHWeighted = weightedSizer(self.panel)
            self.sizerV.Add(self.sizerHWeighted, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- implementation ---
        self.sizerHImplementation = implementationSizer(self.panel)
        self.sizerV.Add(self.sizerHImplementation, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- approximation ---
        self.sizerHApproximation = approximationSizer(self.panel, self.fit, self.fieldsActivation)
        self.sizerV.Add(self.sizerHApproximation, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- access ---
        self.sizerHAccess = uploadFileSizer(self.panel, 'Access', self.fit, True, self.fieldsActivation)
        self.sizerV.Add(self.sizerHAccess, flag=wx.ALIGN_LEFT|wx.LEFT, border=margin)

        # --- rendering ---
        self.render()

        # --- special binding ---
        self.sizerHNetNod.netRadio.Bind(wx.EVT_RADIOBUTTON, self.fieldsActivation)
        self.sizerHNetNod.nodRadio.Bind(wx.EVT_RADIOBUTTON, self.fieldsActivation)
        self.sizerHImplementation.normRadio.Bind(wx.EVT_RADIOBUTTON, self.fieldsActivation)
        self.sizerHImplementation.meanRadio.Bind(wx.EVT_RADIOBUTTON, self.fieldsActivation)

        # --- initialize activation ---
        self.fieldsActivation(None)


    def fieldsActivation(self, event):
        # conditions
        condImpl = self.sizerHNetNod.isNetwork()
        condApprox = not(self.sizerHAccess.isChecked())
        condAccess = not(self.sizerHApproximation.isChecked())
        # enable / disable
        self.sizerHImplementation.activate(condImpl)
        self.sizerHApproximation.activate(condApprox)
        self.sizerHAccess.activate(condAccess)

    def action(self, event):
        wantApprox = self.sizerHApproximation.isChecked()
        wantAccess = self.sizerHAccess.isChecked()
        isMean = False if self.sizerHNetNod.isNodes() else self.sizerHImplementation.isMean()
        self.fnBase = getFileNameBase(get_param_selectedProjectName(), self.sizerHNetNod.isNetwork(), fn_betweenness, isMean, False, wantAccess, wantApprox)
        fileNames = getGeneratedFiles(self.fnBase)

        pathAccess = self.sizerHAccess.getValue() if wantAccess else ''
        errorMsg = '' # reset error messages
        errorMsg += self.sizerHSave.check(fileNames)
        if wantApprox: errorMsg += self.sizerHApproximation.check()
        if wantAccess: errorMsg += self.sizerHAccess.check()
        if wantAccess & self.isNetworkProject: errorMsg += self.sizerHAccess.checkAccessType(pathAccess)

        if errorMsg == '':
            if self.sizerHSave.isOverwritten():
                self.path = self.sizerHSave.getValue()
                approx = self.sizerHApproximation.getValue() if wantApprox else ''
                srsAccess = self.sizerHAccess.getSRSValue() if wantAccess else ''

                self.normalized = self.sizerHNorm.isNormalized()
                self.weighted = self.sizerHWeighted.isWeighted() if self.isNetworkProject else False
                self.k = approx if wantApprox else None
                if wantAccess:
                    srsAcc = int(re.search(r'\[(\d*)\].*', srsAccess).group(1))
                    self.k = intersectNodes(pathAccess, srsAcc, get_param_selectedProjectName(), get_param_selectedProjectSrs(), self.isGridProject, get_param_selectedGridProjectResolution())
                    if self.k is None:
                        warningMsg = 'You have chosen access that do not intersect with the network.\n\n'
                        warningMsg += 'Do you want to carry on anyway ?'
                        dlgWarning = wx.MessageDialog(self, warningMsg, 'Warning access not intersect', wx.YES_NO|wx.ICON_EXCLAMATION)
                        if dlgWarning.ShowModal() == wx.ID_YES:
                            self.computeBC()
                        dlgWarning.Destroy()
                    else:
                        self.computeBC()
                else:
                    self.computeBC()

        else:
            dlg = wx.MessageDialog(self, errorMsg, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def computeBC(self):
        self.Hide()
        self.load = Loading(self, "Computation")

        Publisher().subscribe(self.catchError, 'catchError')

        self.start = time.time()
        callback = "actionEnd"
        Publisher().subscribe(self.actionEnd, callback) # create a pubsub receiver

        # launch computation
        if self.sizerHNetNod.isNetwork():
            if self.sizerHImplementation.isNormal():
                EdgeBetweenness(self.path, self.fnBase, callback, self.k, self.weighted, self.normalized)
            else:
                EdgeMeanBetweenness(self.path, self.fnBase, callback, self.k, self.weighted, self.normalized)
        else:
            NodeBetweenness(self.path, self.fnBase, callback, self.k, self.weighted, self.normalized)

