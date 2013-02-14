import shapefile
from osgeo import ogr
from shapely.wkb import loads
from shapely.geometry import LineString, Polygon
import wx
import os
import time
import re
from loading import Loading
from mca.utils.utils import *
from mca.utils.db_utils import *
from mca.utils.parameters import *
from mca.centrality.betweenness import *
from mca.utils.utils import GetTextTime
# --- wxPython threadsafe  ---
from wx.lib.pubsub import Publisher
from ui_utils import *


class commonUI(wx.Frame):

    def __init__(self, parent, title):
        # check requirements
        try:
            self.ActionName
            self.helperFile
            self.actionButton
        except:
            raise Exception('Unimplemented values')

        parent.Disable()
        wx.Frame.__init__(self, parent, title=title)
        self.SetIcon(ico)
        self.Bind(wx.EVT_CLOSE, self.onClose)

        # --- variables ---
        self.parent = parent
        self.load = None
        self.start = time.time()

        # --- layout ---
        self.panel = wx.Panel(self) # main
        self.sizerV = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizerV)

    def render(self):
        # --- buttons ---
        self.sizerHButtons = actionButtonsSizer(self.panel, self.helperFile, self.actionButton, self.action, self.cancel)
        self.sizerV.Add(self.sizerHButtons, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- rendering ---
        self.sizerV.Fit(self) # tell to the main window to fit the size of self.sizerV
        self.Centre()
        self.Show()

    def fit(self):
        self.sizerV.Fit(self)

    def action(self, event):
        raise Exception('commonUI action not overriden')

    def actionEnd(self, msg):
        if self.load: self.load.hide()
        consoleAppend('%s done in %s' %(self.ActionName, GetTextTime(time.time() - self.start)))
        if msg:
            if msg.data:
                createFile(msg.data, consoleGetContent())
        self.parent.Enable()
        self.Destroy()

    def catchError(self, msg):
        consoleAppend(msg.data, console_red)
        self.load.hide()
        self.parent.Enable()
        self.Destroy()

    def cancel(self, event):
        self.Close()

    def onClose(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to cancel ?', 'Cancel', wx.YES_NO|wx.ICON_QUESTION)
        ret = dlg.ShowModal()
        dlg.Destroy()
        if ret == wx.ID_YES:
            consoleAppend('%s aborted' %self.ActionName)
            self.parent.Enable()
            event.Skip()



class centralityUI(commonUI):

    def __init__(self, parent, title):
        # --- variables ---
        self.actionButton = 'Compute'
        self.overwritten = True

        commonUI.__init__(self, parent, title)

        # --- title ---
        self.sizerHTitle = titleSizer(self.panel, self.ActionName, get_param_selectedProjectName())
        self.sizerV.Add(self.sizerHTitle, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- network vs nodes ---
        self.sizerHNetNod = netNodSizer(self.panel)
        self.sizerV.Add(self.sizerHNetNod, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- normalization ---
        self.sizerHNorm = normalizationSizer(self.panel)
        self.sizerV.Add(self.sizerHNorm, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

    def render(self):
        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- save file ---
        self.sizerHSave = filesSaveSizer(self.panel, self)
        self.sizerV.Add(self.sizerHSave, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        commonUI.render(self)



class newUI(commonUI):

    def __init__(self, parent, title):
        # --- variables ---
        self.actionButton = 'Create'

        commonUI.__init__(self, parent, title)

        # --- title ---
        self.sizerHTitle = titleSizer(self.panel, self.ActionName)
        self.sizerV.Add(self.sizerHTitle, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- project ---
        self.sizerHProject = projectSizer(self.panel)
        self.sizerV.Add(self.sizerHProject, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- author ---
        self.sizerHAuthor = authorSizer(self.panel)
        self.sizerV.Add(self.sizerHAuthor, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

    def render(self):
        # --- separator ---
        self.separator = wx.StaticLine(self.panel, style=wx.LI_HORIZONTAL, size=separatorSize)
        self.sizerV.Add(self.separator, flag=wx.ALIGN_CENTER)

        # --- project srs ---
        self.sizerHProjectSrs = projectSRSSizer(self.panel)
        self.sizerV.Add(self.sizerHProjectSrs, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        commonUI.render(self)

    def cleanData(self):
        raise Exception('newUI cleanData not overriden')

    def catchError(self, msg):
        self.cleanData()
        commonUI.catchError(self, msg)
