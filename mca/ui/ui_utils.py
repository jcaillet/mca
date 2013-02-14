import wx
import wx.lib.filebrowsebutton as fbb
from help import Information
import shapefile
from mca.utils.parameters import *
from mca.utils.utils import *
from mca.utils.db_utils import *


class projectSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.projectLabel = wx.StaticText(panel, label="Project name", size=labelSize)
        self.Add(self.projectLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.project = wx.TextCtrl(panel, value="", size=labelSize)
        self.Add(self.project)

    # Checks :
    #  - non-empty field
    #  - must be unique
    def check(self):
        name = str(self.project.GetValue())
        toReturn = ''
        if name == '':
            toReturn += '- Project name is empty\n'
        if re.match(r'^.*[A-Z]+.*\Z', name) is not None:
            toReturn += '- Use lowercase characters in the given project name\n'
        if re.match(r'^[0-9].*\Z', name) is not None:
            toReturn += '- First project name character must be a letter\n'
        if re.match(r'^[a-zA-Z0-9_]*\Z', name) is None:
            toReturn += "- Invalid characters in the given project name, only '_' is permitted\n"
        if topologyExists(name):
            toReturn += '- Project name already exists\n'

        if toReturn != '': toReturn += '\n'
        return toReturn

    def getValue(self):
        return str(self.project.GetValue())



class authorSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.authorLabel = wx.StaticText(panel, label="Author", size=labelSize)
        self.Add(self.authorLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.author = wx.TextCtrl(panel, value="", size=labelSize)
        self.Add(self.author)

    def check(self):
        auth = str(self.author.GetValue())
        toReturn = '- Author field is empty\n\n'
        if auth != '':
            toReturn = ''
        return toReturn

    def getValue(self):
        return str(self.author.GetValue())



class projectSRSSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.projectSrsLabel = wx.StaticText(panel, label="Project SRS", size=labelSize)
        self.Add(self.projectSrsLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.projectSrs = wx.ComboBox(panel, style=wx.CB_DROPDOWN, size=labelSize, value="")
        self.projectSrs.Bind(wx.EVT_TEXT, self.srsProjectAutoComplete)
        self.Add(self.projectSrs)
        self.img = wx.Image(clearImgPath, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(panel, -1, self.img)
        self.bitmap.Bind(wx.EVT_LEFT_UP, self.clearValue)
        self.Add(self.bitmap, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=2*margin)

    def clearValue(self, event):
        self.projectSrs.SetValue('')

    def srsProjectAutoComplete(self, event):
        self.srsAutoComplete(event, self.projectSrs)

    def srsAutoComplete(self, event, field):
        elected = []
        key = event.GetString()
        if len(key) >= 3:
            for s in getAllSrs():
                if re.search(r'(?i).*%s.*' %re.escape(key), s):
                    elected.append(s)
            field.Clear()
            field.AppendItems(elected)
            if len(elected) == 1: field.SetValue(elected[0])

    # Checks :
    #  - list contains
    def check(self):
        srs = str(self.projectSrs.GetValue())
        toReturn = '- Project SRS field is empty\n\n'
        if srs != '':
            if srs in getAllSrs():
                toReturn = ''
            else:
                toReturn = '- Project SRS unknown, select a value in the autocompleted list\n\n'
        return toReturn

    def getValue(self):
        return str(self.projectSrs.GetValue())



class uploadFileSizer(wx.BoxSizer):
    def __init__(self, panel, name, fit, hideable=False, fieldsActivation=None):
        wx.BoxSizer.__init__(self, wx.VERTICAL)

        self.name = name
        self.fit = fit
        self.hideable = hideable
        self.fieldsActivation = fieldsActivation
        self.config = get_param_config()
        self.initDir = self.config.getLoadDir()

        self.sizerHFile = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerHSRS = wx.BoxSizer(wx.HORIZONTAL)

        if hideable == True:
            self.checkBox = wx.CheckBox(panel, -1, name)
            self.checkBox.SetFont(blockFont)
            self.checkBox.Bind(wx.EVT_CHECKBOX, self.checked)
            self.Add(self.checkBox)

        self.uploadLabel = wx.StaticText(panel, label=('Upload %s' %name), size=fbbTitleSize)
        self.sizerHFile.Add(self.uploadLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.filePath = fbb.FileBrowseButton(panel, labelText="",  initialValue="", size=fbbSize, startDirectory=self.initDir, fileMask="*.shp", fileMode=wx.OPEN)
        self.filePath.textControl.Bind(wx.EVT_TEXT, self.getEPSG)
        self.sizerHFile.Add(self.filePath)
        self.Add(self.sizerHFile)

        self.uploadSRSLabel = wx.StaticText(panel, label=('%s SRS' %name), size=labelSize)
        self.sizerHSRS.Add(self.uploadSRSLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.fileSRS = wx.ComboBox(panel, style=wx.CB_DROPDOWN, size=labelSize)
        self.fileSRS.Bind(wx.EVT_TEXT, self.autoCompleteSRS)
        self.sizerHSRS.Add(self.fileSRS, flag=wx.ALIGN_CENTER_VERTICAL)
        self.img = wx.Image(clearImgPath, wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        self.bitmap = wx.StaticBitmap(panel, -1, self.img)
        self.bitmap.Bind(wx.EVT_LEFT_UP, self.clearValue)
        self.sizerHSRS.Add(self.bitmap, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=2*margin)
        self.Add(self.sizerHSRS)

        self.show()

    def clearValue(self, event):
        self.fileSRS.SetValue('')

    def isChecked(self):
        return self.checkBox.GetValue()

    def checked(self, event):
        if self.fieldsActivation:
            self.fieldsActivation(None)
        self.show()

    def show(self):
        if self.hideable == True:
            self.Show(self.sizerHFile, self.checkBox.GetValue())
            self.Show(self.sizerHSRS, self.checkBox.GetValue())
            self.fit()

    def autoCompleteSRS(self, event):
        self.srsAutoComplete(event, self.fileSRS)

    def getEPSG(self, event):
        key = event.GetString()
        key = key.replace('.shp','.prj')
        espg_key = esriprj2standards(key)
        if espg_key is not None:
            self.fileSRS.SetValue(espg_key)
            self.srsAutoComplete(espg_key, self.fileSRS)
        else:
            self.fileSRS.SetValue('')

    def srsAutoComplete(self, event, field):
        elected = []
        key = event if isinstance(event, str) else event.GetString()
        if len(key) >= 3:
            for s in getAllSrs():
                if re.search(r'(?i).*%s.*' %re.escape(key), s):
                    elected.append(s)
            field.Clear()
            field.AppendItems(elected)
            if len(elected) == 1: field.SetValue(elected[0])

    def activate(self, toActivate):
        if toActivate:
            self.checkBox.Enable()
        else:
            self.checkBox.SetValue(False)
            self.checkBox.Disable()


    def check(self):
        val = os.path.dirname(self.filePath.GetValue())
        self.config.setLoadDir(val)
        self.config.save()

        return self.checkSRS() + self.checkFile()

    def checkAccessType(self, pathAccess):
        sf = shapefile.Reader(pathAccess)
        shType = sf.shapeType
        if shType != 5:
            toReturn = 'Invalid shapefile access type, please provide a shapefile containing Polygon(s)'
            return toReturn
        else:
            toReturn = ''
            return toReturn

    # Checks :
    #  - list contains
    def checkSRS(self):
        srs = str(self.fileSRS.GetValue())
        toReturn = '- %s SRS field is empty\n\n' %self.name
        if srs != '':
            if srs in getAllSrs():
                toReturn = ''
            else:
                toReturn = '- %s SRS unknown, select a value in the autocompleted list\n\n' %self.name
        return toReturn

    # Checks :
    #  - non-empty field
    #  - must reach a shape file
    def checkFile(self):
        path = str(self.filePath.GetValue())
        toReturn = '- %s file path is empty\n\n' %self.name
        if path != '':
            if path.endswith('.shp'):
                if os.path.isfile(path):
                    toReturn = ''
                else:
                    toReturn = '- %s file not found\n\n' %self.name
            else:
                toReturn = '- %s file type is invalid, must be shape (.shp)\n\n' %self.name
        return toReturn

    def getValue(self):
        return str(self.filePath.GetValue())

    def getSRSValue(self):
        return str(self.fileSRS.GetValue())



class resolutionSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.resolutionLabel = wx.StaticText(panel, label="Grid resolution", size=labelSize)
        self.Add(self.resolutionLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.resolution = wx.TextCtrl(panel, value="0", size=radioSize)
        self.Add(self.resolution)
        self.resolutionUnityTxt = wx.StaticText(panel, label="(unit according to project SRS)")
        self.resolutionUnityTxt.SetFont(smallFont)
        self.Add(self.resolutionUnityTxt, flag=wx.ALIGN_CENTER_VERTICAL)

    # Checks :
    #  - non-empty field
    #  - must be a positive double value
    def check(self):
        res = str(self.resolution.GetValue())
        toReturn = '- Resolution is empty\n\n'
        if res != '':
            if isInt(res) | isFloat(res):
                if float(res) > 0.0:
                    toReturn = ''
                else:
                    toReturn = '- Resolustion must be greater than 0\n\n'
            else:
                toReturn = '- Resolution must be positive\n\n'
        return toReturn

    def getValue(self):
        return float(self.resolution.GetValue())



class toleranceSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.toleranceLabel = wx.StaticText(panel, label="Snapping tolerance", size=labelSize)
        self.Add(self.toleranceLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.tolerance = wx.TextCtrl(panel, value="0", size=radioSize)
        self.Add(self.tolerance)
        self.toleranceUnityTxt = wx.StaticText(panel, label="(unit according to project SRS)")
        self.Add(self.toleranceUnityTxt, flag=wx.ALIGN_CENTER_VERTICAL)

    # Checks :
    #  - non-empty field
    #  - must be a positive double value (postgresql type)
    #    (don't check python long type, no sense to represent meters in choosed projection)
    def check(self):
        tol = str(self.tolerance.GetValue())
        toReturn = '- Tolerance is empty, use 0 for no snapping\n\n'
        if tol != '':
            if isInt(tol) | isFloat(tol):
                if float(tol) >= 0.0:
                    toReturn = ''
                else:
                    toReturn = '- Tolerance must be equal or greater than 0\n\n'
            else:
                toReturn = '- Tolerance must be positive or null\n\n'
        return toReturn

    def getValue(self):
        return float(self.tolerance.GetValue())



class titleSizer(wx.BoxSizer):
    def __init__(self, panel, actionName, selectedProj=None):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.labelSize = labelSize if selectedProj else allSize
        self.title = wx.StaticText(panel, label=actionName, size=self.labelSize)
        self.title.SetFont(titleFont)
        self.Add(self.title, flag=wx.ALIGN_CENTER_VERTICAL)
        if selectedProj:
            self.projName = wx.StaticText(panel, label=selectedProj, size=labelSize)
            self.projName.SetFont(projectFont)
            self.Add(self.projName, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL, border=margin)

    def getValue(self):
        return str(self.title.GetValue())



class netNodSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.netNodLabel = wx.StaticText(panel, label="Centrality on", size=labelSize)
        self.Add(self.netNodLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.netRadio = wx.RadioButton(panel, label='Network', style=wx.RB_GROUP, size=radioSize)
        self.Add(self.netRadio)
        self.nodRadio = wx.RadioButton(panel, label='Nodes', size=radioSize)
        self.Add(self.nodRadio)

    def isNetwork(self):
        return self.netRadio.GetValue()

    def isNodes(self):
        return self.nodRadio.GetValue()



class implementationSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.implementationTitle = wx.StaticText(panel, label="Implementation method", size=labelSize)
        self.Add(self.implementationTitle, flag=wx.ALIGN_CENTER_VERTICAL)
        self.normRadio = wx.RadioButton(panel, label='Normal', style=wx.RB_GROUP, size=radioSize)
        self.Add(self.normRadio)
        self.meanRadio = wx.RadioButton(panel, label='Mean', size=radioSize)
        self.Add(self.meanRadio)

    def activate(self, toActivate):
        if toActivate:
            self.implementationTitle.Enable()
            self.normRadio.Enable()
            self.meanRadio.Enable()
        else:
            self.implementationTitle.Disable()
            self.normRadio.Disable()
            self.meanRadio.Disable()

    def isNormal(self):
        return self.normRadio.GetValue()

    def isMean(self):
        return self.meanRadio.GetValue()



class normalizationSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.normalizationLabel = wx.StaticText(panel, label="Normalization of the results", size=labelSize)
        self.Add(self.normalizationLabel, flag=wx.ALIGN_CENTER_VERTICAL)
        self.normalizationYesRadio = wx.RadioButton(panel, label='Yes', style=wx.RB_GROUP, size=radioSize)
        self.Add(self.normalizationYesRadio)
        self.normalizationNoRadio = wx.RadioButton(panel, label='No', size=radioSize)
        self.Add(self.normalizationNoRadio)

    def isNormalized(self):
        return self.normalizationYesRadio.GetValue()



class approximationSizer(wx.BoxSizer):
    def __init__(self, panel, fit, fieldsActivation=None):
        wx.BoxSizer.__init__(self, wx.VERTICAL)

        self.fit = fit
        self.fieldsActivation = fieldsActivation
        # block recursion on text control event
        self.blockApprox = False
        self.blockPercent = False

        self.sizerHNbObj = wx.BoxSizer(wx.HORIZONTAL)
        self.sizerHPercent = wx.BoxSizer(wx.HORIZONTAL)

        self.checkBox = wx.CheckBox(panel, -1, 'Approximation')
        self.checkBox.SetFont(blockFont)
        self.checkBox.Bind(wx.EVT_CHECKBOX, self.checked)
        self.Add(self.checkBox)

        self.approxNbObjects = wx.StaticText(panel, label="Number of nodes", size=labelSize)
        self.sizerHNbObj.Add(self.approxNbObjects)
        self.approximation = wx.TextCtrl(panel, value="")
        self.approximation.Bind(wx.EVT_TEXT, self.approxSet)
        self.sizerHNbObj.Add(self.approximation)
        self.Add(self.sizerHNbObj, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        self.approxCorrespond = wx.StaticText(panel, label="Percentage", size=labelSize)
        self.sizerHPercent.Add(self.approxCorrespond)
        self.approxPercent = wx.TextCtrl(panel, value="")
        self.approxPercent.Bind(wx.EVT_TEXT, self.percentSet)
        self.sizerHPercent.Add(self.approxPercent)
        self.approxPercentSign = wx.StaticText(panel, label="%")
        self.sizerHPercent.Add(self.approxPercentSign)
        self.Add(self.sizerHPercent, flag=wx.ALIGN_LEFT|wx.ALL, border=margin)

        self.show()

    def approxSet(self, event):
        if self.blockApprox:
            self.blockApprox = False
        else:
            percent = ''
            try:
                tot = get_param_selectedProjectNbObjects()
                approx = int(self.approximation.GetValue())
                percent = '%s' % int(round(approx*100.0/tot, 2))
            except:
                pass

            self.blockPercent = True
            self.approxPercent.SetValue(percent)

    def percentSet(self, event):
        if self.blockPercent:
            self.blockPercent = False
        else:
            approx = ''
            try:
                tot = get_param_selectedProjectNbObjects()
                percent = float(self.approxPercent.GetValue())
                approx = '%s' % int(round(percent*tot/100.0, 0))
            except:
                pass

            self.blockApprox = True
            self.approximation.SetValue(approx)

    def isChecked(self):
        return self.checkBox.GetValue()

    def checked(self, event):
        if self.fieldsActivation:
            self.fieldsActivation(None)
        self.show()

    def show(self):
        self.Show(self.sizerHNbObj, self.checkBox.GetValue())
        self.Show(self.sizerHPercent, self.checkBox.GetValue())
        self.fit()

    def activate(self, toActivate):
        if toActivate:
            self.checkBox.Enable()
        else:
            self.checkBox.SetValue(False)
            self.checkBox.Disable()

    def check(self):
        approx = str(self.approximation.GetValue())
        error = 'No number of objects specified for approximation'
        if approx != '':
            if isInt(approx) & (int(approx) > 0) & (int(approx) < get_param_selectedProjectNbObjects()):
                error = ''
            else:
                error = 'Approximation must be a positive integer number, less than the total of objects'
        return error

    def getValue(self):
        return int(self.approximation.GetValue())



class weightedSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.weightedTitle = wx.StaticText(panel, label="Weighted", size=labelSize)
        self.Add(self.weightedTitle, flag=wx.ALIGN_CENTER_VERTICAL)
        self.weightedYesRadio = wx.RadioButton(panel, label='Yes', style=wx.RB_GROUP, size=radioSize)
        self.Add(self.weightedYesRadio)
        self.weightedNoRadio = wx.RadioButton(panel, label='No', size=radioSize)
        self.Add(self.weightedNoRadio)

    def isWeighted(self):
        return self.weightedYesRadio.GetValue()



class radiusSizer(wx.BoxSizer):
    def __init__(self, panel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.radiusTitle = wx.StaticText(panel, label="Radius", size=labelSize)
        self.Add(self.radiusTitle, flag=wx.ALIGN_CENTER_VERTICAL)
        self.radiusCheck = wx.CheckBox(panel, label='Yes', size=radioSize)
        self.radiusCheck.Bind(wx.EVT_CHECKBOX, self.radiusSelect)
        self.Add(self.radiusCheck)
        self.radiusInput = wx.TextCtrl(panel, value="Define radius", size=radioSize)
        self.radiusInput.Disable()
        self.Add(self.radiusInput)

    def radiusSelect(self, event):
        if self.isChecked():
            self.radiusInput.SetValue('')
            self.radiusInput.Enable()
        else:
            self.radiusInput.SetValue('Define radius')
            self.radiusInput.Disable()

    def check(self):
        rad = str(self.radiusInput.GetValue())
        error = 'No number specified for radius'
        if rad != '':
            if isInt(rad) & (int(rad) > 0) | isFloat(rad) & (float(rad) > 0):
                error = ''
            else:
                error = 'Value for radius must be a positive number'
        return error

    def isChecked(self):
        return self.radiusCheck.GetValue()

    def getValue(self):
        return float(self.radiusInput.GetValue())



class filesSaveSizer(wx.BoxSizer):
    def __init__(self, panel, parent):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)

        self.parent = parent
        self.config = get_param_config()
        self.initDir = self.config.getComputeDir()

        self.saveTitle = wx.StaticText(panel, label="Choose folder to save files", size=fbbTitleSize)
        self.Add(self.saveTitle, flag=wx.ALIGN_CENTER_VERTICAL)
        self.savePath = fbb.DirBrowseButton(panel, labelText="", size=fbbSize, startDirectory=self.initDir)
        self.Add(self.savePath)

    def isOverwritten(self):
        return self.overwritten

    def check(self, fileNames):
        val = self.savePath.GetValue()
        self.config.setComputeDir(val)
        self.config.save()

        self.overwritten = True
        path = str(self.savePath.GetValue())
        error = 'No directory selected'
        if path != '':
            if os.path.isdir(path):
                error = ''
                for f in fileNames:
                    if os.path.isfile(os.path.join(path, f)):
                        msg = 'The directory already contains some files with the same name as those will be created.\n\n' \
                            'If you decide to continue the operation, they will be overwritten.\n\n' \
                            'Are you sure you want continue ?'
                        dlg = wx.MessageDialog(self.parent, msg, 'Warning', wx.YES_NO|wx.ICON_EXCLAMATION)
                        if dlg.ShowModal() == wx.ID_NO:
                            self.overwritten = False
                        dlg.Destroy()
                        break
            else:
                error = 'Selected directory is invalid'
        return error

    def getValue(self):
        return str(self.savePath.GetValue())



class actionButtonsSizer(wx.BoxSizer):
    def __init__(self, panel, helperFile, actionButton, action, cancel):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.helper = Information(panel, helperFile)
        self.Add(self.helper)
        self.createButton = wx.Button(panel, label=actionButton)
        self.createButton.Bind(wx.EVT_BUTTON, action)
        self.Add(self.createButton, flag=wx.LEFT, border=helperMargin)
        self.cancelButton = wx.Button(panel, label="Cancel")
        self.cancelButton.Bind(wx.EVT_BUTTON, cancel)
        self.Add(self.cancelButton, flag=wx.LEFT, border=margin)
