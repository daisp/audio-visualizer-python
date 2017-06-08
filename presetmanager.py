from PyQt4 import QtGui
from collections import OrderedDict
import string
import os

import core


class PresetManager(QtGui.QDialog):
    def __init__(self, window, parent):
        super().__init__()
        self.parent = parent
        self.presetDir = os.path.join(self.parent.dataDir, 'presets')
        self.window = window
        self.findPresets()
        self.lastFilter = '*'

        # create filter box and preset list
        self.drawFilterList()
        self.window.comboBox_filter.currentIndexChanged.connect(
            lambda: self.drawPresetList(self.window.comboBox_filter.currentText())
        )
        self.drawPresetList('*')

        # make auto-completion for search bar
        self.autocomplete = QtGui.QStringListModel()
        completer = QtGui.QCompleter()
        completer.setModel(self.autocomplete)
        self.window.lineEdit_search.setCompleter(completer)

    def show(self):
        presetNames = []
        for presetList in self.presets.values():
            for preset in presetList:
                presetNames.append(preset[1])
        self.autocomplete.setStringList(presetNames)
        self.findPresets()
        self.drawFilterList()
        self.drawPresetList('*')
        self.window.show()

    def findPresets(self):
        parseList = []
        for dirpath, dirnames, filenames in os.walk(self.presetDir):
            # anything without a subdirectory must be a preset folder
            if dirnames:
                continue
            for preset in filenames:
                compName = os.path.basename(os.path.dirname(dirpath))
                compVers = os.path.basename(dirpath)
                try:
                    parseList.append((compName, int(compVers), preset))
                except ValueError:
                    continue
        self.presets =\
            {
            compName : \
                [
                (vers, preset) \
                    for name, vers, preset in parseList \
                    if name == compName \
                ] \
            for compName, _, __ in parseList \
            }

    def drawPresetList(self, filter=None):
        self.window.listWidget_presets.clear()
        if filter:
            self.lastFilter = str(filter)
        else:
            filter = str(self.lastFilter)
        for component, presets in self.presets.items():
            if filter != '*' and component != filter:
                continue
            for vers, preset in presets:
                self.window.listWidget_presets.addItem('%s: %s' % (component, preset))

    def drawFilterList(self):
        self.window.comboBox_filter.clear()
        self.window.comboBox_filter.addItem('*')
        for component in self.presets:
            self.window.comboBox_filter.addItem(component)

    def openSavePresetDialog(self):
        window = self.parent.window
        if window.listWidget_componentList.currentRow() == -1:
            return
        while True:
            dialog = QtGui.QInputDialog(
                QtGui.QWidget(), 'Audio Visualizer', 'New Preset Name:')
            dialog.setTextValue()
            newName, OK = dialog.getText()
            badName = False
            for letter in newName:
                if letter in string.punctuation:
                    badName = True
            if badName:
                # some filesystems don't like bizarre characters
                self.parent.showMessage(msg=\
'''Preset names must contain only letters, numbers, and spaces.''')
                continue
            if OK and newName:
                index = window.listWidget_componentList.currentRow()
                if index != -1:
                    saveValueStore = \
                        self.parent.selectedComponents[index].savePreset()
                    componentName = str(self.parent.selectedComponents[index]).strip()
                    vers = self.parent.selectedComponents[index].version()
                    self.createPresetFile(
                        componentName, vers, saveValueStore, newName)
            break

    def createPresetFile(self, compName, vers, saveValueStore, filename):
        dirname = os.path.join(self.presetDir, compName, str(vers))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filepath = os.path.join(dirname, filename)
        if os.path.exists(filepath):
            ch = self.parent.showMessage(
                msg="%s already exists! Overwrite it?" % filename,
                showCancel=True, icon=QtGui.QMessageBox.Warning)
            if not ch:
                return
        with open(filepath, 'w') as f:
            f.write(core.Core.stringOrderedDict(saveValueStore))
        self.drawPresetList()

    def openPreset(self, presetName):
        index = self.parent.window.listWidget_componentList.currentRow()
        if index == -1:
            return
        componentName = str(self.parent.selectedComponents[index]).strip()
        version = self.parent.selectedComponents[index].version()
        dirname = os.path.join(self.presetDir, componentName, str(version))
        filepath = os.path.join(dirname, presetName)
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r') as f:
            for line in f:
                saveValueStore = dict(eval(line.strip()))
                break
        self.parent.selectedComponents[index].loadPreset(saveValueStore)
        self.parent.drawPreview()

