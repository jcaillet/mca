import wx
from mca.utils.parameters import helpImgPath, helpFilesPath
import subprocess


class Information(wx.StaticBitmap):

    def __init__(self, parent, pdf):
        self.path = helpFilesPath + '/' + pdf
        helpImage = wx.Image(helpImgPath, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        wx.StaticBitmap.__init__(self, parent, -1, helpImage)
        self.Bind(wx.EVT_LEFT_UP, self.showInfo)

    def showInfo(self, event):
        subprocess.call(["xdg-open", self.path])