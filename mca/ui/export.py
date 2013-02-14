import wx
import os
import time
from mca.utils.parameters import *
from mca.ui.commonUI import *
from mca.utils.ogr2ogr import Postgresql_2_shp
from loading import Loading
from mca.utils.utils import GetTextTime
from collections import namedtuple


class ExportProject(commonUI):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):
        # --- variables ---
        self.ActionName = 'Export'
        self.helperFile = 'export.pdf'
        self.actionButton = 'Export'
        # --- files will be created ---
        self.proj = get_param_selectedProjectName()
        fnBaseNet = getFileNameBase(self.proj, True)
        self.network_file_name = getGeneratedFiles(fnBaseNet)
        fnBaseNod = getFileNameBase(self.proj, False)
        self.nodes_file_name = getGeneratedFiles(fnBaseNod)
        self.fileNames = self.network_file_name + self.nodes_file_name

        commonUI.__init__(self, parent, title)

        # --- title ---
        self.sizerHTitle = titleSizer(self.panel, self.ActionName, get_param_selectedProjectName())
        self.sizerV.Add(self.sizerHTitle, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- save file ---
        self.sizerHSave = filesSaveSizer(self.panel, self)
        self.sizerV.Add(self.sizerHSave, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        # --- render ---
        commonUI.render(self)

    def action(self, event):
        error = self.sizerHSave.check(self.fileNames)
        if error == '':
            if self.sizerHSave.isOverwritten():
                self.path = self.sizerHSave.getValue()
                self.path_2_network = os.path.join(self.path, self.proj + fn_edges)
                self.path_2_nodes = os.path.join(self.path, self.proj + fn_nodes)

                Publisher().subscribe(self.catchError, 'catchError') # create a pubsub receiver

                self.Hide()
                self.load = Loading(self, "Loading")

                self.start = time.time()
                self.callback = "postgresql_2_shpEnd"
                Publisher().subscribe(self.postgresql_2_shpEnd, self.callback) # create a pubsub receiver
                Postgresql_2_shp(self.path_2_network, self.proj, 'edge_data', self.callback)
        else:
            dlg = wx.MessageDialog(self, error, 'Errors', wx.CANCEL|wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

    def postgresql_2_shpEnd(self, msg):
        if msg.data == 'edge_data':
            Postgresql_2_shp(self.path_2_nodes, self.proj, 'node', self.callback)
        else:
            logFile = self.proj + fn_export + '.log'
            path_2_log = os.path.join(self.path, logFile)
            msg = 'The following files have been created in %s:\n' % self.path
            msg += '   - %s     - %s\n   - %s     - %s\n   - %s     - %s\n   - %s     - %s\n   - %s'
            consoleAppend(msg % tuple(self.fileNames + [logFile]))

            msg=namedtuple('literal', 'data')(**{'data':path_2_log})
            self.actionEnd(msg)
