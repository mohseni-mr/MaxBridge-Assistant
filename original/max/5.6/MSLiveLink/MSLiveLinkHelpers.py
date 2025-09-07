import os, sys, json, pymxs

class LiveLinkHelper():

    def DeselectEverything(self):
        return ("""
        actionMan.executeAction 0 "40043"  -- Selection: Select None
        """)

    def ShowInViewport(self, nodeName = "mat" ):
        return ("""
        NODE_NAME.showInViewport = true
        """).replace("NODE_NAME", nodeName)
    
    def GetActiveSMEView(self):
        return ("""
        ActiveSMEView = sme.GetView (sme.activeView)
        """)
    
    def CreateNodeInSME(self, nodeName, x, y):
        return ("""
        ActiveSMEView.CreateNode NODE_NAME [posX, posY]
        """).replace("NODE_NAME", nodeName).replace("posX", str(x)).replace("posY", str(y))

    def AssignMaterialToObjects(self, materialName = "mat"):
        return ("""
        select CurOBJs
        for o in selection do o.material = MATERIALTOAPPLY
        """).replace("MATERIALTOAPPLY", materialName)

    # Obj import settings modification
    # Ref: https://help.autodesk.com/view/MAXDEV/2021/ENU/?guid=GUID-639CF6E0-1B9F-4B05-9CE8-D6418162E0CE
    def OpenObjImpFile(self):
        return ("""
        objIniFile =objimp.getIniName()
        getIniSetting objIniFile
        """)
    
    def GetObjSetting(self, parent, child, varName):
        return ("""
        VAR_NAME = getIniSetting objIniFile "PARENT_NAME""CHILD_NAME"
        """).replace("VAR_NAME", varName).replace("PARENT_NAME", parent).replace("CHILD_NAME", child)

    def ChangeObjSetting(self, parent, child, varValue):
        return ("""
        setIniSetting objIniFile "PARENT_NAME""CHILD_NAME" "VAR_VALUE"
        """).replace("VAR_VALUE", varValue).replace("PARENT_NAME", parent).replace("CHILD_NAME", child)

    def ResetObjIniValue(self, parent, child, varName):
        return ("""
        setIniSetting objIniFile "PARENT_NAME""CHILD_NAME" VAR_NAME
        """).replace("VAR_NAME", varName).replace("PARENT_NAME", parent).replace("CHILD_NAME", child)

    def SelectObjects(self):
        return ("""
        select CurOBJs
        """)

    def GetScanWidth(self, meta):
        width = 1
        try:
            scanArea = [item for item in meta if item["key"].lower() == "scanarea"]
            if len(scanArea) >= 1:
                scanValue = str(scanArea[0]["value"])
                scanValue = scanValue.split(" ")[0]
                width = int(scanValue.split("x")[0])
        except:
            pass
        return width

    def GetScanHeight(self, meta):
        height = 1
        try:
            scanArea = [item for item in meta if item["key"].lower() == "scanarea"]
            if len(scanArea) >= 1:
                scanValue = str(scanArea[0]["value"])
                scanValue = scanValue.split(" ")[0]
                height = int(scanValue.split("x")[1])
        except:
            pass
        return height
    
    def GetAssetHeight(self, meta):
        height = 0
        try:
            heightValue = [item for item in meta if item["key"].lower() == "height"]
            if len(height) >= 1:
                height = str( heightValue[0]["value"].replace('m','') )
                #converting inches (default 3ds Max unit) into meters
                height = float(height) * 39.37
        except:
            pass
        return str(height)

    def SetWidthAndHeight(self, scanWidth, scanHeight):
        widthHeightScript = ("""
        scanWidth = WIDTH_VALUE
        scanHeight = HEIGHT_VALUE
        """).replace("WIDTH_VALUE", str(scanWidth)).replace("HEIGHT_VALUE", str(scanHeight))
        return widthHeightScript

    def GetTexturePath(self, textureList, textureType):
        for item in textureList:
            if item[1] == textureType.lower():
                return item[2].replace("\\", "/")
        return ""

    def ConnectNodeToMaterial(self, connectionName, nodeName):
        nodeConnectionScript = ("""
        mat.CONNECTION_NAME = NODE_NAME
        """).replace("CONNECTION_NAME", connectionName).replace("NODE_NAME", nodeName)
        return nodeConnectionScript

    def AddNormalProperties (self, textureTypes, is3DAsset = False):
        normalScript = ("""
        hasNormal = False
        hasBump = False
        """)
        if "normal" in textureTypes:
            normalScript = normalScript.replace("hasNormal = False", "hasNormal = True")
        
        if "bump" in textureTypes and not is3DAsset:
            normalScript = normalScript.replace("hasBump = False", "hasBump = True")

        return normalScript

    def ShowMessageDialog(self, title, message):
        messageBoxScript = ("""
        messagebox "DIALOG_MESSAGE" title: "DIALOG_TITLE"
        """).replace("DIALOG_TITLE", title).replace("DIALOG_MESSAGE", message)
        pymxs.runtime.execute(messageBoxScript)

    def GetMeshType(self, meshList):
        if len(meshList) > 0:
            if meshList[0]["format"] == "abc":
                return True
        return False

    def SetAlembicImportSettings(self):
        alembicImportScript = ("""
        AlembicImport.Visibility = True
        AlembicImport.UVs = True
        AlembicImport.Normals = True
        AlembicImport.VertexColors = True
        AlembicImport.ImportToRoot = True
        AlembicImport.CoordinateSystem = #YUp

        AlembicImport.FitTimeRange = False
        AlembicImport.SetStartTime = False
        AlembicImport.ExtraChannels = False
        AlembicImport.Velocity = False
        AlembicImport.MaterialIDs = False
        AlembicImport.ShapeSuffix = False
        """)
        self.RunMaxScript(alembicImportScript)

    def RunMaxScript(self, whatsToRunss):
    	pymxs.runtime.execute(whatsToRunss)

    def GetMaxVersion(self):
        try:
            return pymxs.runtime.maxVersion()[7]
        except:
            return 0

    def CreateMultiSubMaterial(self, multiNodeName, matName, matsAmount):
        multi_node_script = ("""
        MS_NODE_NAME = multiSubMaterial()
        MS_NODE_NAME.name = "MS_MAT_NAME"
        MS_NODE_NAME.numsubs = NUM_OF_MATS
        """).replace("NUM_OF_MATS", str(matsAmount))

        # Removing default PBR materials. Also we add 1 to index because material list starts from index number 1.
        for x in range(matsAmount):
            multi_node_script += ("""
            MS_NODE_NAME.materialList[MAT_INDEX] = undefined
            """).replace("MAT_INDEX", str(x + 1))

        return multi_node_script.replace("MS_NODE_NAME", multiNodeName).replace("MS_MAT_NAME", matName)

    def AssignMaterialToMultiSlots(self, multiNodeName, matName, slotsToAssignTo):
        multi_node_script = ("""""")

        for x in slotsToAssignTo:
            multi_node_script += ("""
            MS_NODE_NAME.materialList[MAT_INDEX] = MS_MAT_NAME
            """).replace("MAT_INDEX", str(x))

        return multi_node_script.replace("MS_NODE_NAME", multiNodeName).replace("MS_MAT_NAME", matName)

    def HasMultipleMaterial(self, meta):
        try:
            for item in meta:
                if item["key"].lower() == "materialids":
                    return True
        except:
            pass
        return False
    
    def ExtractMatData(self, meta):
        matsToMake = []
        try:
            for item in meta:
                if item["key"].lower() == "materialids":
                    for vals in item["value"]:
                        matData = MaterialData(vals["material"], vals["ids"])
                        matsToMake.append(matData)
        except:
            pass
        return matsToMake
    
    def GetNumberOfUniqueMaterial(self, meta):
        numOfMats = 0
        try:
            for item in meta:
                if item["key"].lower() == "materialids":
                    for vals in item["value"]:
                        numOfMats += len(vals["ids"])
        except:
            pass
        return numOfMats
    
    def RearrangeMaterialGraph(self):
        return ("""
        actionMan.executeAction 369891408 "40060"
        """)

class MaterialData():
    def __init__(self, matType, matIDs):
        self.matType = matType
        self.matIDs = matIDs