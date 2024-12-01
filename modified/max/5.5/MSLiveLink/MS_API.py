import os, json, sys, socket, time, re
from pymxs import runtime as rt

#import QThread

_path_ = os.path.dirname(__file__).replace("\\", "/")
if _path_ not in sys.path:
  sys.path.append( _path_ )



import MS_Importer
from Logging import Logger
_importerSetup_ = MS_Importer.LiveLinkImporter()

MSLIVELINK_VERSION = "5.5"

try:
    from PySide6.QtGui import *
    from PySide6.QtCore import *
    from PySide6.QtWidgets import *
except ImportError:
    try:
        from PySide2.QtGui import *
        from PySide2.QtCore import *
        from PySide2.QtWidgets import *
    except ImportError:
        try:
            from PySide.QtGui import *
            from PySide.QtCore import *
        except ImportError:
            try:
                from PyQt5.QtGui import *
                from PyQt5.QtCore import *
                from PyQt5.QtWidgets import *
            except ImportError:
                try:
                    from PyQt4.QtGui import *
                    from PyQt4.QtCore import *
                except ImportError:
                    raise ImportError("No suitable PyQt or PySide version found")





"""#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*
#####################################################################################

MegascansLiveLinkAPI is the core component of the Megascans Plugin plugins.
This API relies on a QThread to monitor any incoming data from Bridge by communicating
via a socket port.

This module has a bunch of classes and functions that are standardized as much as possible
to make sure you don't have to modify them too much for them to work in any python-compatible
software.
If you're looking into extending the user interface then you can modify the MegascansLiveLinkUI
class to suit your needs.

#####################################################################################
#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*"""




def GetHostApp():
    try:
        try:
            import qtmax
            mainWindow = qtmax.GetQMaxMainWindow()
        except:
            try:
                mainWindow = QWidget.find(rt.windows.getMAXHWND())
            except:
                mainWindow = QApplication.activeWindow()

        while True:
            lastWin = mainWindow.parent()
            if lastWin:
                mainWindow = lastWin
            else:
                break
        return mainWindow
    except:
        pass

""" QLiveLinkMonitor is a QThread-based thread that monitors a specific port for import.
Simply put, this class is responsible for communication between your software and Bridge."""

class QLiveLinkMonitor(QThread):
    Bridge_Call = Signal()
    Instance = []

    def __init__(self):
        super(QLiveLinkMonitor, self).__init__()
        self.TotalData = b""
        QLiveLinkMonitor.Instance.append(self)

    def __del__(self):
        self.quit()
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):
        time.sleep(0.025)
        try:
            host, port = 'localhost', 13292
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_.bind((host, port))
            while True:
                socket_.listen(5)
                client, address = socket_.accept()
                data = b""
                data = client.recv(4096*2)
                if data:
                    self.TotalData = b""
                    self.TotalData += data
                    while True:
                        data = client.recv(4096*2)
                        if data:
                            self.TotalData += data
                        else:
                            break
                    time.sleep(0.05)
                    self.Bridge_Call.emit()
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error in QLiveLinkMonitor: {e}")

    def InitializeImporter(self):
        import pymxs
        json_array = json.loads(self.TotalData)
        for asset_ in json_array:
            importer = _importerSetup_.Identifier
            importer.set_Asset_Data(asset_)
            try:
                guid = asset_['guid']
                assetID = asset_['id']
            except KeyError:
                guid = ""
                assetID = ""
            bridge_event = "BRIDGE_BULK_EXPORT_ASSET" if len(json_array) > 1 else "BRIDGE_EXPORT_ASSET"
            try:
                Logger(pymxs.runtime.execute("classof renderers.current"), pymxs.runtime.maxversion()[7], guid, assetID, bridge_event)
            except Exception as e:
                Logger(pymxs.runtime.execute("classof renderers.current"), "2019 or lower", guid, assetID, bridge_event)
                print(f"Error in InitializeImporter Logger: {e}")




"""
#################################################################################################
#################################################################################################
"""

stylesheet_ = ("""

QCheckBox { background: transparent; color: #E6E6E6; font-family: Source Sans Pro; font-size: 14px; }
QCheckBox::indicator:hover { border: 2px solid #2B98F0; background-color: transparent; }
QCheckBox::indicator:checked:hover { background-color: #2B98F0; border: 2px solid #73a5ce; }
QCheckBox:indicator{ color: #67696a; background-color: transparent; border: 2px solid #67696a;
width: 14px; height: 14px; border-radius: 2px; }
QCheckBox::indicator:checked { border: 2px solid #18191b;
background-color: #2B98F0; color: #ffffff; }
QCheckBox::hover { spacing: 12px; background: transparent; color: #ffffff; }
QCheckBox::checked { color: #ffffff; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { border: 1px solid #444; }
QCheckBox:disabled { background: transparent; color: #414141; font-family: Source Sans Pro;
font-size: 14px; margin: 0px; text-align: center; }

QComboBox { color: #FFFFFF; font-size: 14px; font-family: Source Sans Pro;
selection-background-color: #1d1e1f; background-color: #1d1e1f; }
QComboBox:hover { color: #c9c9c9; font-size: 14px; font-family: Source Sans Pro;
selection-background-color: #232426; background-color: #232426; } """)


"""
#################################################################################################
#################################################################################################
"""

class LiveLinkUI(QWidget):

    Instance = []
    Settings = [0, 0, 0]


    # UI Widgets

    def __init__(self, _importerSetup_, parent=GetHostApp()):
        super(LiveLinkUI, self).__init__(parent)

        LiveLinkUI.Instance = self
        self.Importer = _importerSetup_

        self._path_ = _path_
        self.setObjectName("LiveLinkUI")
        img_ = QPixmap( os.path.join(self._path_, "MS_Logo.png") )
        self.setWindowIcon(QIcon(img_))
        self.setMinimumWidth(250)
        self.setWindowTitle("MS Plugin " + MSLIVELINK_VERSION + " - 3ds Max")
        self.setWindowFlags(Qt.Window)

        self.style_ = ("""  QWidget#LiveLinkUI { background-color: #262729; } """)
        self.setStyleSheet(self.style_)

        # style_ = ("QLabel {background-color: #232325; font-size: 14px;font-family: Source Sans Pro; color: #afafaf;}")

        # Set the main layout
        self.MainLayout = QVBoxLayout()
        self.setLayout(self.MainLayout)
        self.MainLayout.setSpacing(5)
        self.MainLayout.setContentsMargins(5, 2, 5, 2)


        # Set the checkbox options

        self.checks_l = QVBoxLayout()
        self.checks_l.setSpacing(2)
        self.MainLayout.addLayout(self.checks_l)

        self.applytoSel = QCheckBox("Apply Material to Selection")
        self.applytoSel.setToolTip("Applies the imported material(s) to your selection.")
        self.applytoSel.setChecked( self.Importer.getPref("Material_to_Sel") )
        self.applytoSel.setFixedHeight(30)
        self.applytoSel.setStyleSheet(stylesheet_)
        self.checks_l.addWidget(self.applytoSel)
        
        
        # Enable Displacement Check Box
        # Set the checkbox options

        self.checks_l = QVBoxLayout()
        self.checks_l.setSpacing(2)
        self.MainLayout.addLayout(self.checks_l)

        self.enableDisplacement = QCheckBox("Import 3D Assets with Displacement")
        self.enableDisplacement.setToolTip("Enables displacement for 3D Assets")
        self.enableDisplacement.setChecked( self.Importer.getPref("Enable_Displacement") )
        self.enableDisplacement.setFixedHeight(30)
        self.enableDisplacement.setStyleSheet(stylesheet_)
        self.checks_l.addWidget(self.enableDisplacement)
        
        
        # Save current import settings
        self.applytoSel.stateChanged.connect(self.settingsChanged)
        self.enableDisplacement.stateChanged.connect(self.settingsChanged)

    # UI Callbacks
    def settingsChanged(self):
        settings_data = self.Importer.loadSettings()
        settings_data["Material_to_Sel"] = self.applytoSel.isChecked()
        settings_data["Enable_Displacement"] = self.enableDisplacement.isChecked()
        self.Importer.updateSettings(settings_data)

# LIVELINK INITIALIZER

def initLiveLink():

    if LiveLinkUI.Instance != None:
        try: LiveLinkUI.Instance.close()
        except: pass

    LiveLinkUI.Instance = LiveLinkUI(_importerSetup_)
    LiveLinkUI.Instance.show()
    pref_geo = QRect(500, 300, 460, 30)
    LiveLinkUI.Instance.setGeometry(pref_geo)
    return LiveLinkUI.Instance
    
    
#LIVELINK MENU INSTALLER
def createToolbarMenuPymxs():
    import pymxs
    pymxs.runtime.execute(" global mxsInit = 0 ")
    pymxs.runtime.mxsInit = initLiveLink
    pymxs.runtime.execute("""
    -- Sample menu extension script
    -- If this script is placed in the "stdplugs\stdscripts"
    -- folder, then this will add the new items to MAX's menu bar
    -- when MAX starts.
    -- A sample macroScript that we will attach to a menu item
    macroScript Megascans
    category: "Quixel"
    tooltip: "MS Plugin"
    (
    on execute do mxsInit()
    )


    -- This example adds a new sub-menu to MAX's main menu bar.
    -- It adds the menu just before the "Help" menu.
    if ((menuMan.findMenu "Megascans") == undefined) then
    --if menuMan.registerMenuContext 0x1ee76d8f then
    (
    -- Get the main menu bar
    local mainMenuBar = menuMan.getMainMenuBar()
    -- Create a new menu
    local subMenu = menuMan.createMenu "Megascans"
    -- create a menu item that calls the sample macroScript
    local subItem = menuMan.createActionItem "Megascans" "Quixel"
    -- Add the item to the menu
    subMenu.addItem subItem -1
    -- Create a new menu item with the menu as it's sub-menu
    local subMenuItem = menuMan.createSubMenuItem "Megascans" subMenu
    -- compute the index of the next-to-last menu item in the main menu bar
    local subMenuIndex = mainMenuBar.numItems() - 1
    -- Add the sub-menu just at the second to last slot
    mainMenuBar.addItem subMenuItem subMenuIndex
    -- redraw the menu bar with the new item
    menuMan.updateMenuBar()
    )"""
    )

def createNewMenu():
    # This is the new menu creation method for 3ds Max 2025
    try:
        import pymxs
        pymxs.runtime.execute(" global mxsInit = 0 ")
        pymxs.runtime.mxsInit = initLiveLink
        
        # Define the macro script action details
        macroCategory = "Quixel"
        macroName = "Megascans"

        # Create the macroscript that will be triggered by the menu item
        rt.macros.new(
            macroCategory,          # Category for the macro script
            macroName,              # Name of the macro script
            "MS Plugin",  # Tooltip text
            "Megascans",  # Menu text
            "on execute do mxsInit()"             # Function to execute when the action is triggered
        )

        # Define the menu callback function
        def menuCallback():
            # Get the menu manager from the notification parameter
            menuMgr = rt.callbacks.notificationParam()
            mainMenuBar = menuMgr.mainMenuBar

            # Use unique GUIDs for the menu and menu item
            submenuGUID = "4810d984-1235-40b4-8648-75de85d473a5"
            menuItemGUID = "5da4fbde-0f56-4e31-9b82-ade5aa0e7ec1"

            submenuName = "Megascans"
            submenu = mainMenuBar.createSubMenu(submenuGUID, submenuName)

            macroScriptTableId = 647394
            submenu.createAction(menuItemGUID, macroScriptTableId, "Megascans`Quixel")

        # Register the menu callback on the cuiRegisterMenus event
        MENU_SCRIPT_ID = rt.name("Megascans")
        rt.callbacks.removeScripts(id=MENU_SCRIPT_ID)
        rt.callbacks.addScript(rt.name("cuiRegisterMenus"), menuCallback, id=MENU_SCRIPT_ID)

        rt.maxOps.getICuiMenuMgr().loadConfiguration(rt.maxOps.getICuiMenuMgr().getCurrentConfiguration())

    except Exception as e:
        print(f"{e}")
        

# Start the LiveLink server here.
def StartSocketServer():
    try:
        if len(QLiveLinkMonitor.Instance) == 0:
            bridge_monitor = QLiveLinkMonitor()
            bridge_monitor.Bridge_Call.connect(bridge_monitor.InitializeImporter)
            bridge_monitor.start()
        print("Quixel Bridge Plugin v" + MSLIVELINK_VERSION + " started successfully.")
        
    except:
        print("Quixel Bridge Plugin v" + MSLIVELINK_VERSION + " failed to start.")
        pass
    
    

# The file named builtins calls ours MS_API file from 3ds Max startup - afterwards MS_API is the __main__ file that is run directly with bridge exports
# Start our socket server and setup Megascans menu in the Max Menu bar
if __name__ == "builtins" or __name__ == "__builtin__":
    # Calculate the major version of 3ds Max
    max_version = int((rt.maxVersion()[0] / 1000.0) - 2.0)

    if max_version >= 25:
        # Use the new menu creation method for 3ds Max 2025 and above
        try:
            createNewMenu()
            print("New menu created successfully for 3ds Max 2025 or later.")
        except Exception as e:
            print(f"Failed to create menu for 3ds Max 2025 or later: {e}")
    else:
        # Use the old menu creation method for 3ds Max versions prior to 2025
        try:
            createToolbarMenuPymxs()
            print("Toolbar menu created successfully for older versions of 3ds Max.")
        except Exception as e:
            print(f"Failed to create menu for older versions of 3ds Max: {e}")

    StartSocketServer()

