'''
Created on 26.08.2010

Copyright (C) 2010-2011 Kay Hannay

This file is part of efaLiveSetup.

efaLiveSetup is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
efaLiveSetup is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with efaLiveSetup.  If not, see <http://www.gnu.org/licenses/>.
'''
import pygtk
pygtk.require('2.0')
import gtk
import sys
import os
import subprocess
import traceback

import dialogs
from observable import Observable
from devicemanager import DeviceManagerController as DeviceManager
from screensetup import ScreenSetupController as ScreenSetup

import locale
import gettext
APP="efaLiveSetup"
LOCALEDIR=os.path.join(os.path.dirname(sys.argv[0]), "locale")
DIR=os.path.realpath(LOCALEDIR)
gettext.install(APP, DIR, unicode=True)

import logging


class SetupModel(object):
    def __init__(self, confPath):
        self._logger = logging.getLogger('efalivesetup.maingui.SetupModel')
        self._logger.setLevel(logging.DEBUG)
        self._checkPath(confPath)
        self._confPath=confPath
        self._settingsFileName = os.path.join(self._confPath, "settings.conf")
        self._backupFileName = os.path.join(self._confPath, "backup.conf")
        self.efaVersion=Observable()
        self.efaShutdownAction=Observable()
        self.autoUsbBackup=Observable()
        self.efaBackupPaths=None

    def initModel(self):
        self.efaVersion.updateData(1)
        self.efaShutdownAction.updateData("sudo /sbin/shutdown -h now")
        if os.path.isfile(self._settingsFileName):
            self.settingsFile=open(self._settingsFileName, "r")
            self.parseSettingsFile(self.settingsFile)
            self.settingsFile.close()

    def _checkPath(self, path):
        if not os.path.exists(path):
            self._logger.debug("Creating directory: %s" % path)
            os.makedirs(path, 0755)

    def parseSettingsFile(self, file):
        for line in file:
            if line.startswith("EFA_VERSION="):
                versionStr=line[(line.index('=') + 1):]
                self.setEfaVersion(int(versionStr))
                self._logger.debug("Parsed version: " + versionStr)
            elif line.startswith("EFA_SHUTDOWN_ACTION="):
                actionStr=line[(line.index('=') + 1):].rstrip()
                self.setEfaShutdownAction(actionStr)
                self._logger.debug("Parsed shutdown action: " + actionStr)
            elif line.startswith("AUTO_USB_BACKUP="):
                enableStr=line[(line.index('=') + 1):].rstrip()
                if enableStr == "\"TRUE\"":
                    self.enableAutoUsbBackup(True)
                else:
                    self.enableAutoUsbBackup(False)
                self._logger.debug("Parsed auto USB backup setting: " + enableStr)

    def save(self):
        self._logger.debug("Saving files: %s, %s" % (self._settingsFileName, self._backupFileName))
        try:
            settingsFile=open(self._settingsFileName, "w")
            settingsFile.write("EFA_VERSION=%d\n" % self.efaVersion._data)
            settingsFile.write("EFA_SHUTDOWN_ACTION=%s\n" % self.efaShutdownAction._data)
            if self.autoUsbBackup._data == True:
                settingsFile.write("AUTO_USB_BACKUP=\"TRUE\"\n")
            else:
                settingsFile.write("AUTO_USB_BACKUP=\"FALSE\"\n")
            settingsFile.close()
            backupFile=open(self._backupFileName, "w")
            backupFile.write("EFA_BACKUP_PATHS=\"%s\"\n" % self.efaBackupPaths)
            backupFile.close()
        except IOError, exception:
            self._logger.error("Could not save files: %s" % exception)
            raise Exception("Could not save files")

    def setEfaVersion(self, version):
        self.efaVersion.updateData(version)
        if version == 1:
            self.efaBackupPaths = "/opt/efa/daten /home/efa/efa"
        elif version == 2:
            self.efaBackupPaths = "/opt/efa2/data /home/efa/efa2"
        else:
            self._logger.error("Undefined version received: %d" % version)
        self._logger.debug("efa version: %d" % version)

    def setEfaShutdownAction(self, action):
        self.efaShutdownAction.updateData(action)
        self._logger.debug("efa shutdown action: %s" % action)

    def enableAutoUsbBackup(self, enable):
        self.autoUsbBackup.updateData(enable)
        self._logger.debug("auto USB backup: %s" % enable)

    def getConfigPath(self):
        return self._confPath


class SetupView(gtk.Window):
    def __init__(self, type):
        self._logger = logging.getLogger('efalivesetup.maingui.SetupView')
        gtk.Window.__init__(self, type)
        self.set_title(_("efaLive setup"))
        self.set_border_width(5)

        self.initComponents()

    def initComponents(self):
        self.mainBox=gtk.VBox(False, 2)
        self.add(self.mainBox)
        self.mainBox.show()

        # settings box
        self.settingsFrame=gtk.Frame(_("efaLive settings"))
        self.mainBox.pack_start(self.settingsFrame, True, True, 2)
        self.settingsFrame.show()

        self.settingsSpaceBox=gtk.HBox(False, 5)
        self.settingsFrame.add(self.settingsSpaceBox)
        self.settingsSpaceBox.show()

        self.settingsVBox=gtk.VBox(False, 5)
        self.settingsSpaceBox.pack_start(self.settingsVBox, True, True, 2)
        self.settingsVBox.show()

        # version box
        self.versionFrame=gtk.Frame(_("efa version"))
        self.settingsVBox.pack_start(self.versionFrame, True, True, 2)
        self.versionFrame.show()

        self.versionSpaceBox=gtk.HBox(False, 5)
        self.versionFrame.add(self.versionSpaceBox)
        self.versionSpaceBox.show()

        self.versionVBox=gtk.VBox(False, 5)
        self.versionSpaceBox.pack_start(self.versionVBox, True, True, 10)
        self.versionVBox.show()

        self.versionDesc=gtk.Label(_("Here you can choose the efa version that ")
            + _("you would like to use. Please note that efa 2 is a development ")
            + _("version, which might me unstable. If you need a stable version, ")
            + _("choose efa 1."))
        self.versionDesc.set_line_wrap(True)
        self.versionVBox.pack_start(self.versionDesc, True, True, 5)
        self.versionDesc.show()
        
        self.versionHBox=gtk.HBox(False, 5)
        self.versionVBox.pack_start(self.versionHBox, True, True, 10)
        self.versionHBox.show()

        self.versionLabel=gtk.Label(_("version"))
        self.versionHBox.pack_start(self.versionLabel, True, True, 2)
        self.versionLabel.show()

        self.versionCombo=gtk.combo_box_new_text()
        self.versionHBox.pack_start(self.versionCombo, True, True, 2)
        self.versionCombo.show()

        # shutdown box
        self.shutdownVBox=gtk.VBox(False, 5)
        self.settingsVBox.pack_start(self.shutdownVBox, True, True, 2)
        self.shutdownVBox.show()

        self.shutdownHBox=gtk.HBox(False, 5)
        self.shutdownVBox.pack_start(self.shutdownHBox, True, True, 2)
        self.shutdownHBox.show()

        self.shutdownLabel=gtk.Label(_("efa shutdown action"))
        self.shutdownHBox.pack_start(self.shutdownLabel, True, True, 2)
        self.shutdownLabel.show()

        self.shutdownCombo=gtk.combo_box_new_text()
        self.shutdownHBox.pack_start(self.shutdownCombo, True, True, 2)
        self.shutdownCombo.show()

        # automatic usb backup box
        self.autoUsbBackupVBox=gtk.VBox(False, 5)
        self.settingsVBox.pack_start(self.autoUsbBackupVBox, True, True, 2)
        self.autoUsbBackupVBox.show()

        self.autoUsbBackupHBox=gtk.HBox(False, 5)
        self.autoUsbBackupVBox.pack_start(self.autoUsbBackupHBox, True, True, 2)
        self.autoUsbBackupHBox.show()

        self.autoUsbBackupCbox = gtk.CheckButton(_("enable automatic USB backup"))
        self.autoUsbBackupHBox.pack_start(self.autoUsbBackupCbox, False, True, 2)
        self.autoUsbBackupCbox.show()

        # tools box
        self.toolsFrame=gtk.Frame(_("Tools"))
        self.mainBox.pack_start(self.toolsFrame, True, False, 2)
        self.toolsFrame.show()

        self.toolsSpaceVBox=gtk.VBox(False, 10)
        self.toolsFrame.add(self.toolsSpaceVBox)
        self.toolsSpaceVBox.show()
        
        self.toolsSpaceBox=gtk.HBox(False, 10)
        self.toolsSpaceVBox.pack_start(self.toolsSpaceBox, True, True, 5)
        self.toolsSpaceBox.show()
        
        self.toolsGrid=gtk.Table(2, 3, True)
        self.toolsSpaceBox.pack_start(self.toolsGrid, True, True, 5)
        self.toolsGrid.set_row_spacings(2)
        self.toolsGrid.set_col_spacings(2)
        self.toolsGrid.show()

        self.terminalButton=gtk.Button(_("Terminal"))
        self.toolsGrid.attach(self.terminalButton, 0, 1, 0, 1)
        self.terminalButton.show()
        
        self.fileManagerButton=gtk.Button(_("File manager"))
        self.toolsGrid.attach(self.fileManagerButton, 1, 2, 0, 1)
        self.fileManagerButton.show()
       
        self.deviceButton=gtk.Button(_("Devices"))
        self.toolsGrid.attach(self.deviceButton, 2, 3, 0, 1)
        self.deviceButton.show()
       
        self.screenButton=gtk.Button(_("Screen"))
        self.toolsGrid.attach(self.screenButton, 0, 1, 1, 2)
        self.screenButton.show()
        
        self.networkButton=gtk.Button(_("Network"))
        self.toolsGrid.attach(self.networkButton, 1, 2, 1, 2)
        self.networkButton.show()
       
        self.keyboardButton=gtk.Button(_("Keyboard"))
        self.toolsGrid.attach(self.keyboardButton, 2, 3, 1, 2)
        self.keyboardButton.show()
       

        # actions box
        self.actionsFrame=gtk.Frame(_("Actions"))
        self.mainBox.pack_start(self.actionsFrame, True, False, 2)
        self.actionsFrame.show()

        self.actionsSpaceVBox=gtk.VBox(False, 10)
        self.actionsFrame.add(self.actionsSpaceVBox)
        self.actionsSpaceVBox.show()
        
        self.actionsSpaceBox=gtk.HBox(False, 10)
        self.actionsSpaceVBox.pack_start(self.actionsSpaceBox, True, True, 5)
        self.actionsSpaceBox.show()
        
        self.actionsGrid=gtk.Table(1, 3, True)
        self.actionsSpaceBox.pack_start(self.actionsGrid, True, True, 5)
        self.actionsGrid.set_row_spacings(2)
        self.actionsGrid.set_col_spacings(2)
        self.actionsGrid.show()

        

        """
        self.actionsVBox=gtk.VBox(False, 5)
        self.actionsSpaceBox.pack_start(self.actionsVBox, False, False, 10)
        self.actionsVBox.show()

        self.actionsHBox=gtk.HBox(False, 0)
        self.actionsVBox.pack_start(self.actionsHBox, True, True, 10)
        self.actionsHBox.show()
        """

        self.shutdownButton=gtk.Button(_("Shutdown PC"))
        self.actionsGrid.attach(self.shutdownButton, 0, 1, 0, 1)
        self.shutdownButton.show()
        
        self.restartButton=gtk.Button(_("Restart PC"))
        self.actionsGrid.attach(self.restartButton, 1, 2, 0, 1)
        self.restartButton.show()
       
        self.actionsDummy=gtk.Label()
        self.actionsGrid.attach(self.actionsDummy, 2, 3, 0, 1)
        self.actionsDummy.show()
       

        # button box
        self.buttonBox=gtk.HBox(False, 0)
        self.mainBox.pack_start(self.buttonBox, False, False, 2)
        self.buttonBox.show()

        self.okButton=gtk.Button(_("Ok"))
        self.buttonBox.pack_end(self.okButton, False, False, 2)
        self.okButton.show()
        
        self.closeButton=gtk.Button(_("Cancel"))
        self.buttonBox.pack_end(self.closeButton, False, False, 2)
        self.closeButton.show()
        

class SetupController(object):
    def __init__(self, argv, model=None, view=None):
        self._logger = logging.getLogger('efalivesetup.maingui.SetupController')
        if(len(argv) < 2):
            raise(BaseException("No arguments given"))
        confPath=argv[1]
        if(model==None):
            self._model=SetupModel(confPath)
        else:
            self._model=model
        if(view==None):
            self._view=SetupView(gtk.WINDOW_TOPLEVEL)
        else:
            self._view=view

        self.initEvents()
        self._view.connect("destroy", self.destroy)
        self._view.show()

        self._view.versionCombo.append_text(_("1 (stable)"))
        self._view.versionCombo.append_text(_("2 (development)"))

        self._view.shutdownCombo.append_text(_("shutdown pc"))
        self._view.shutdownCombo.append_text(_("restart pc"))
        self._view.shutdownCombo.append_text(_("restart efa"))

        self._model.efaVersion.registerObserverCb(self.efaVersionChanged)
        self._model.efaShutdownAction.registerObserverCb(self.efaShutdownActionChanged)
        self._model.autoUsbBackup.registerObserverCb(self.autoUsbBackupChanged)
        self._model.initModel()

    def efaVersionChanged(self, version):
        index=0
        if(version==1):
            index=0
        elif(version==2):
            index=1
        self._view.versionCombo.set_active(index)

    def efaShutdownActionChanged(self, action):
        index=0
        if(action=="\"sudo /sbin/shutdown -h now\""):
            index=0
        elif(action=="\"sudo /sbin/shutdown -r now\""):
            index=1
        elif(action=="\"start_efa\""):
            index=2
        self._view.shutdownCombo.set_active(index)

    def autoUsbBackupChanged(self, enable):
        self._view.autoUsbBackupCbox.set_active(enable)

    def destroy(self, widget):
        gtk.main_quit()

    def initEvents(self):
        self._view.closeButton.connect("clicked", self.destroy)
        self._view.okButton.connect("clicked", self.save)
        self._view.versionCombo.connect("changed", self.setEfaVersion)
        self._view.shutdownCombo.connect("changed", self.setEfaShutdownAction)
        self._view.autoUsbBackupCbox.connect("toggled", self.setAutoUsbBackup)
        self._view.terminalButton.connect("clicked", self.runTerminal)
        self._view.screenButton.connect("clicked", self.runScreenSetup)
        self._view.deviceButton.connect("clicked", self.runDeviceManager)
        self._view.networkButton.connect("clicked", self.runNetworkSettings)
        self._view.fileManagerButton.connect("clicked", self.runFileManager)
        self._view.shutdownButton.connect("clicked", self.runShutdown)
        self._view.restartButton.connect("clicked", self.runRestart)
        self._view.keyboardButton.connect("clicked", self.runKeyboardSetup)

    def runTerminal(self, widget):
        try:
            subprocess.Popen(['xterm'])
        except OSError as error:
            message = "Could not open xterm program: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def runNetworkSettings(self, widget):
        try:
            subprocess.Popen(['nm-connection-editor'])
        except OSError as error:
            message = "Could not open nm-connection-editor program: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def runFileManager(self, widget):
        try:
            subprocess.Popen(['thunar'])
        except OSError as error:
            message = "Could not open thunar program: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def runShutdown(self, widget):
        do_shutdown = dialogs.show_confirm_dialog(self._view, _("Really shut down PC ?"))
        if do_shutdown == False:
            return
        try:
            subprocess.Popen(['sudo', '/sbin/shutdown', '-h', 'now'])
        except OSError as error:
            message = "Could not run /sbin/shutdown program: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def runRestart(self, widget):
        do_reboot = dialogs.show_confirm_dialog(self._view, _("Really reboot PC ?"))
        if do_reboot == False:
            return
        try:
            subprocess.Popen(['sudo', '/sbin/shutdown', '-r', 'now'])
        except OSError as error:
            message = "Could not run /sbin/shutdown program: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def runScreenSetup(self, widget):
        ScreenSetup(None, confPath=self._model.getConfigPath(), standalone=False)

    def runDeviceManager(self, widget):
        DeviceManager(None, standalone=False)
        
    def runKeyboardSetup(self, widget):
        try:
            subprocess.Popen(['sudo', 'dpkg-reconfigure', '-fgnome', 'keyboard-configuration'])
        except OSError as error:
            message = "Could not run keyboard setup: %s" % error
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

    def setEfaVersion(self, widget):
        self._model.setEfaVersion(widget.get_active() + 1)

    def setEfaShutdownAction(self, widget):
        action_string = ""
        action = widget.get_active()
        if action == 0:
            action_string = "\"sudo /sbin/shutdown -h now\""
        elif action == 1:
            action_string = "\"sudo /sbin/shutdown -r now\""
        elif action == 2:
            action_string = "\"start_efa\""
        self._model.setEfaShutdownAction(action_string)

    def setAutoUsbBackup(self, widget):
        self._model.enableAutoUsbBackup(widget.get_active())

    def save(self, widget):
        try:
            self._model.save()
            self.destroy(widget)
        except Error as error:
            message = _("Could not save files!\n\n") \
                    + _("Please check the path you provided for ") \
                    + _("user rights and existance.")
            dialogs.show_exception_dialog(self._view, message, traceback.format_exc())

if __name__ == '__main__':
    logging.basicConfig(filename='efaLiveSetup.log',level=logging.DEBUG)
    controller = SetupController(sys.argv)
    gtk.main();

