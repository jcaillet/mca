import os
from mca import basedir
import wx
from wx.lib.pubsub import Publisher


# --------------
# --- CONFIG ---
# --------------
config = None

def set_param_config(cfg):
    global config
    config = cfg

def get_param_config():
    return config



# -------------
# --- PATHS ---
# -------------
helpFilesPath = os.path.join(basedir, 'ui', 'resources', 'help')
imgPath = os.path.join(basedir, 'ui', 'resources', 'images')
waitingImgPath = os.path.join(imgPath, 'waiting.gif') # http://ajaxload.info/ => background-color: D0CBC9, foreground-color: 447FAD
helpImgPath = os.path.join(imgPath, 'help-32.png')
clearImgPath = os.path.join(imgPath, 'clear-14.png')
iconImgPath = os.path.join(imgPath, 'mca.png')
ico = wx.Icon(iconImgPath, wx.BITMAP_TYPE_PNG)



# --------------
# --- STYLES ---
# --------------
margin = 5
helperMargin = 284
separatorSize = wx.Size(500,20)
fbbSize = wx.Size(302,-1)
fbbTitleSize = wx.Size(191, -1)
allSize = wx.Size(-1, -1)
labelSize = wx.Size(200, -1)
radioSize = wx.Size(100, -1)
buttonSize = wx.Size(120, -1)
titleFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
projectFont = wx.Font(12, wx.DEFAULT, wx.ITALIC, wx.NORMAL)
blockFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.BOLD)
smallFont = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL)



# -------------------
# --- FILES NAMES ---
# -------------------
fn_extensions = ['.dbf', '.prj', '.shp', '.shx']
fn_betweenness = '_betweenness'
fn_closeness = '_closeness'
fn_straightness = '_straightness'
fn_export = '_export'
fn_edges = '_edges'
fn_nodes = '_nodes'

def getFileNameBase(proj, isEdges, centrality='', mean=False, local=False, access=False, approx=False):
    fn = proj
    fn += fn_edges if isEdges else fn_nodes
    if mean: fn += '_mean'
    if local: fn += '_local'
    if access: fn += '_access'
    if approx: fn += '_approx'
    if centrality: fn += centrality
    return fn

def getGeneratedFiles(fileNameBase):
    return [fileNameBase + elem for elem in fn_extensions]


# ------------------------
# --- SELECTED PROJECT ---
# ------------------------

selectedProjectName = None
selectedProjectKind = None
selectedProjectSrs = None
selectedGridProjectResolution = None

def set_param_selectedProject(name, kind, srs, res, nbobj):
    global selectedProjectName
    global selectedProjectKind
    global selectedProjectSrs
    global selectedGridProjectResolution
    global selectedProjectNbObjects
    selectedProjectName = name
    selectedProjectKind = kind
    selectedProjectSrs = int(srs) if srs else None
    selectedGridProjectResolution = float(res) if res else None
    selectedProjectNbObjects = int(nbobj) if nbobj else None
    if name: setStatusText(" selected project : %s " %name)
    else: setStatusText(' - no project selected - ')

def get_param_selectedProjectName():
    return selectedProjectName

def get_param_selectedProjectKind():
    return selectedProjectKind

def get_param_selectedProjectSrs():
    return selectedProjectSrs

def get_param_selectedGridProjectResolution():
    return selectedGridProjectResolution

def get_param_selectedProjectNbObjects():
    return selectedProjectNbObjects


# ------------------
# --- STATUS BAR ---
# ------------------

statusBar = None

def set_statusBar(newVal):
    global statusBar
    statusBar = newVal

def setStatusText(txt):
    if statusBar is not None:
        statusBar.SetStatusText(txt)
    else:
        print 'NO STATUS BAR   ' + txt


# ---------------
# --- CONSOLE ---
# ---------------

console_default = '#CCCCCC'
console_red = '#DE3A3A'
console_green = '#35BD35'
console_blue = '#5252E3'
console = None

def set_console(cons):
    global console
    console = cons
    Publisher().subscribe(consoleAppendFromPublisher, "consoleAppend")

# @see: http://wiki.wxwidgets.org/WxTextCtrl
# Fatal IO error 11 (Resource temporarily unavailable) on X server :0
# https://lists.ubuntu.com/archives/foundations-bugs/2012-March/071180.html
def consoleAppend(txt, colour=''):
    if console is not None:
        console.Freeze()
        if colour: console.SetDefaultStyle(wx.TextAttr(colour))
        console.AppendText(txt + '\n')
        if colour: console.SetDefaultStyle(wx.TextAttr(console_default))
        console.LineDown()
        console.ShowPosition(console.GetLastPosition())
        console.Thaw()
    else:
        print 'NO CONSOLE   ' + txt

def consoleAppendFromPublisher(msg):
    consoleAppend(msg.data)

def consoleGetContent():
    return str(console.GetValue()) if console is not None else ''
