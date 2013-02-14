import wx
import wx.animate
from mca.utils.parameters import *

import thread
from time import sleep
import sys


class Loading(wx.Dialog):

    def __init__(self, parent, title):
        wx.Dialog.__init__(self, parent, title=title, size=wx.Size(200, 120))

        self.Bind(wx.EVT_CLOSE, self.onClose)

        panel = wx.Panel(self)

        sizerV = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizerV)

        txt = wx.StaticText(panel, label="In progress...")
        sizerV.Add(txt, flag=wx.ALIGN_LEFT|wx.ALL, border=20)

        gif = wx.animate.GIFAnimationCtrl(panel, -1, waitingImgPath)
        sizerV.Add(gif, flag=wx.ALIGN_CENTER)
        gif.Play() # continuously loop

        # --- rendering ---
        self.Centre()
        self.Show(True)

    def hide(self):
        self.Destroy()

    def onClose(self, event):
        pass