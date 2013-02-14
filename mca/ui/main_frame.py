import wx
import wx.grid
from mca.utils.parameters import *
from mca.utils.config import Config
from mca.utils.db_utils import getAllProjects, deleteTopology
from new_project import NewProject
from new_grid import NewGrid
from export import ExportProject
from mca.utils.table import Table
from compute_bc import ComputeBC
from compute_cc import ComputeCC
from compute_sc import ComputeSC


class MainFrame(wx.Frame):

    # Create a new _init_ within the SuperClass MainFrame
    def __init__(self, parent, title):

        #print ComputeBC.__mro__

        wx.Frame.__init__(self, parent, title=title)
        self.SetIcon(ico)

        set_param_config(Config())

        # --- styles ---
        self.margin = 20 # pixels
        self.padding = 10 # pixels
        self.rowHeight = 25 # pixels
        self.scrollHeight = 10 * self.rowHeight

        # --- constants ---
        self.managTool = ' Project Management Tools '
        self.centralTool = ' Multiple Centrality Assessment Tools '

        # --- layout ---
        self.panel = wx.Panel(self) # main
        self.sizerV = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizerV)

        # --- online data ---
        sizerH1 = wx.BoxSizer(wx.HORIZONTAL)
        self.dataTitle = wx.StaticText(self.panel, label="Get online data :")
        sizerH1.Add(self.dataTitle, flag=wx.ALIGN_CENTER_VERTICAL)
        self.planetOSMLink = wx.HyperlinkCtrl(self.panel, id=1, label="Planet OSM", url='http://wiki.openstreetmap.org/wiki/Planet.osm')
        sizerH1.Add(self.planetOSMLink, flag=wx.LEFT|wx.RIGHT, border=self.padding)
        self.seprator1 = wx.StaticText(self.panel, label="|")
        sizerH1.Add(self.seprator1, flag=wx.ALIGN_CENTER_VERTICAL)
        self.bbBikeLink = wx.HyperlinkCtrl(self.panel, id=2, label="BBbike", url='http://download.bbbike.org/osm/')
        sizerH1.Add(self.bbBikeLink, flag=wx.LEFT|wx.RIGHT, border=self.padding)
        self.seprator2 = wx.StaticText(self.panel, label="|")
        sizerH1.Add(self.seprator2, flag=wx.ALIGN_CENTER_VERTICAL)
        self.clouderMadeLink = wx.HyperlinkCtrl(self.panel, id=3, label="CloudMade", url='http://datamarket.cloudmade.com/')
        sizerH1.Add(self.clouderMadeLink, flag=wx.LEFT|wx.RIGHT, border=self.padding)
        self.seprator3 = wx.StaticText(self.panel, label="|")
        sizerH1.Add(self.seprator3, flag=wx.ALIGN_CENTER_VERTICAL)
        self.geofabrikLink = wx.HyperlinkCtrl(self.panel, id=3, label="Geofabrik", url='http://download.geofabrik.de/')
        sizerH1.Add(self.geofabrikLink, flag=wx.LEFT|wx.RIGHT, border=self.padding)

        self.sizerV.Add(sizerH1, flag=wx.LEFT|wx.TOP, border=self.margin)

        # --- projects ---
        self.sizerH2 = wx.BoxSizer(wx.HORIZONTAL)
        self.projectPan = wx.Panel(self.panel)

        self.projectWin = wx.ScrolledWindow(self.projectPan)

        self.paintTable()

        self.sizerV.Add(self.projectPan, flag=wx.ALIGN_CENTER|wx.ALL, border=self.margin)

        # --- buttons ---
        staticButtons = wx.StaticBox(self.panel, -1, self.managTool)
        sizerH3 = wx.StaticBoxSizer(staticButtons, wx.HORIZONTAL)
        self.newButton = wx.Button(self.panel, label="New", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.newAction, self.newButton)
        sizerH3.Add(self.newButton, flag=wx.ALL, border=self.padding)
        self.deleteButton = wx.Button(self.panel, label="Delete", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.deleteAction, self.deleteButton)
        sizerH3.Add(self.deleteButton, flag=wx.ALL, border=self.padding)
        self.exportButton = wx.Button(self.panel, label="Export", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.exportAction, self.exportButton)
        sizerH3.Add(self.exportButton, flag=wx.ALL, border=self.padding)

        self.sizerV.Add(sizerH3, flag=wx.ALIGN_CENTER)

        # --- actions ---
        staticActions = wx.StaticBox(self.panel, -1, self.centralTool)
        sizerH4 = wx.StaticBoxSizer(staticActions, wx.HORIZONTAL)
        self.betweennessButton = wx.Button(self.panel, label="Betweenness", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.betweennessAction, self.betweennessButton)
        sizerH4.Add(self.betweennessButton, flag=wx.ALL, border=self.padding)
        self.closenessButton = wx.Button(self.panel, label="Closeness", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.closenessAction, self.closenessButton)
        sizerH4.Add(self.closenessButton, flag=wx.ALL, border=self.padding)
        self.straightnessButton = wx.Button(self.panel, label="Straightness", size=buttonSize)
        self.Bind(wx.EVT_BUTTON, self.straightnessAction, self.straightnessButton)
        sizerH4.Add(self.straightnessButton, flag=wx.ALL, border=self.padding)

        self.sizerV.Add(sizerH4, flag=wx.ALIGN_CENTER|wx.ALL, border=self.margin)

        # --- console ---
        sizerH5 = wx.BoxSizer(wx.HORIZONTAL)

        self.consoleIsDisplay = True
        self.consoleDetail = wx.StaticText(self.panel, label="- hide console details")
        self.consoleDetail.SetFont(wx.Font(8, wx.NORMAL, wx.ITALIC, wx.NORMAL))
        self.consoleDetail.SetForegroundColour('#666666')
        self.consoleDetail.Bind(wx.EVT_LEFT_UP, self.toggleConsole)
        sizerH5.Add(self.consoleDetail, flag=wx.ALIGN_CENTER_VERTICAL)

        sizerH5.Add((-1, -1), 1, flag=wx.EXPAND) # add space to spread clear console to the right

        self.consoleClear = wx.StaticText(self.panel, label="clear console")
        self.consoleClear.SetFont(wx.Font(8, wx.NORMAL, wx.ITALIC, wx.NORMAL))
        self.consoleClear.SetForegroundColour('#666666')
        self.consoleClear.Bind(wx.EVT_LEFT_UP, self.clearConsole)
        sizerH5.Add(self.consoleClear, flag=wx.ALIGN_CENTER_VERTICAL)

        self.sizerV.Add(sizerH5, flag=wx.ALIGN_CENTER|wx.EXPAND)

        self.console = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE|wx.TE_CHARWRAP|wx.SIMPLE_BORDER|wx.TE_READONLY, size=wx.Size(-1, 150))
        self.console.SetBackgroundColour('#000000')
        self.console.SetDefaultStyle(wx.TextAttr(console_default))

        self.sizerV.Add(self.console, 1, flag=wx.EXPAND)

        set_console(self.console)

        # --- status bar ---
        self.sb = self.CreateStatusBar()
        self.sb.SetStatusText(' - no project selected - ')
        set_statusBar(self.sb)

        # --- rendering ---
        self.sizerV.Fit(self) # tell to the main window to fit the size of sizerV
        self.Centre()
        self.Show()


    def clearConsole(self, event):
        self.console.Clear()

    def toggleConsole(self, event):
        if self.consoleIsDisplay:
            self.console.Hide()
            self.consoleDetail.SetLabel('+ show console details')
            self.consoleIsDisplay = False
        else:
            self.console.Show()
            self.consoleDetail.SetLabel('- hide console details')
            self.consoleIsDisplay = True
        self.sizerV.Fit(self)

    def showHelp(self, event):
        consoleAppend('help')

    def newAction(self, event):
        self.newDialog = wx.Dialog(self, title='Choose new project type')
        newSizerV = wx.BoxSizer(wx.VERTICAL)
        self.newText = wx.StaticText(self.newDialog, label="Which type of project do you want to create ?")
        newSizerV.Add(self.newText, flag=wx.ALL, border=self.margin)
        newSizerH = wx.BoxSizer(wx.HORIZONTAL)
        self.networkButton = wx.Button(self.newDialog, label="Network")
        newSizerH.Add(self.networkButton)
        self.newDialog.Bind(wx.EVT_BUTTON, self.newNetworkProject, self.networkButton)
        self.gridButton = wx.Button(self.newDialog, label="Grid")
        newSizerH.Add(self.gridButton)
        self.newDialog.Bind(wx.EVT_BUTTON, self.newGridProject, self.gridButton)
        newSizerV.Add(newSizerH, flag=wx.ALIGN_CENTER)
        self.newDialog.SetSizer(newSizerV)
        newSizerV.Fit(self.newDialog)
        self.newDialog.ShowModal()

    def newNetworkProject(self, event):
        self.newDialog.Destroy()
        wx.Dialog(NewProject(self, self.managTool))

    def newGridProject(self, event):
        self.newDialog.Destroy()
        wx.Dialog(NewGrid(self, self.managTool))

    def deleteAction(self, event):
        proj = get_param_selectedProjectName()
        if proj is not None:
            dlg = wx.MessageDialog(self, 'Do you really want to delete the project "%s" ?' %proj, 'Delete project', wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                deleteTopology(proj)
                self.repaintTable()
                set_param_selectedProject(None, None, None, None, None)
                consoleAppend('Project "%s" deleted' %proj)
            dlg.Destroy()
        else:
            dlg = wx.MessageDialog(self, 'No project selected', 'Project name', wx.CANCEL|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def exportAction(self, event):
        proj = get_param_selectedProjectName()
        if proj is not None:
            wx.Dialog(ExportProject(self, self.managTool))
        else:
            dlg = wx.MessageDialog(self, 'No project selected', 'Project name', wx.CANCEL|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def betweennessAction(self, event):
        proj = get_param_selectedProjectName()
        if proj is not None:
            wx.Dialog(ComputeBC(self, self.centralTool))
        else:
            dlg = wx.MessageDialog(self, 'No project selected', 'Project name', wx.CANCEL|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def closenessAction(self, event):
        proj = get_param_selectedProjectName()
        if proj is not None:
            wx.Dialog(ComputeCC(self, self.centralTool))
        else:
            dlg = wx.MessageDialog(self, 'No project selected', 'Project name', wx.CANCEL|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def straightnessAction(self, event):
        proj = get_param_selectedProjectName()
        if proj is not None:
            wx.Dialog(ComputeSC(self, self.centralTool))
        else:
            dlg = wx.MessageDialog(self, 'No project selected', 'Project name', wx.CANCEL|wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def repaintTable(self):
        self.projectGrid.Hide()
        self.sizerH2.Remove(self.projectGrid)
        self.paintTable()
        self.sizerV.Fit(self)

    def paintTable(self):
        colNames = ["Kind", "Project name", "SRS id", "Edges", "Nodes", "Snapping", "Grid\nresolution", "Author", "Creation date"]
        data = list(getAllProjects())
        self.projectGrid = Table(self.projectWin, data, colNames)
        self.sizerH2.Add(self.projectGrid)
        self.projectWin.SetSizer(self.sizerH2)
        self.sizerH2.Fit(self.projectWin)

        #wid = self.projectGrid.GetSize().GetWidth() + wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        #self.projectWin.SetSize(wx.Size(wid, self.scrollHeight))
        #self.projectPan.SetSize(wx.Size(wid, self.scrollHeight))
