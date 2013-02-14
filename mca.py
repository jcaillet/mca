# clean DB
from mca.utils.db_utils import clean_db
clean_db()

# run app
import wx
app = wx.App(False)
from mca.ui.main_frame import MainFrame
frame = MainFrame(None, 'Multiple Centrality Assessment')
app.MainLoop()