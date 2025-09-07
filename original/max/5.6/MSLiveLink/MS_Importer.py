import os, sys, json, pymxs

import MSVraySetup, MSLiveLinkHelpers, MSOctaneSetup, MSCoronaSetup, MSFStormSetup, MSArnoldSetup, MSRedshiftSetup
helper = MSLiveLinkHelpers.LiveLinkHelper()
VRayHelper = MSVraySetup.VraySetup()
OctaneHelper = MSOctaneSetup.OctaneSetup()
CoronaHelper = MSCoronaSetup.CoronaSetup()
FStormHelper = MSFStormSetup.FStormSetup()
ArnoldHelper = MSArnoldSetup.ArnoldSetup()
RedshiftHelper = MSRedshiftSetup.RedshiftSetup()

"""#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*
#####################################################################################

LiveLinkImporter is the class used to handle texture import, geometry import,
material setup, json structuring and other basic functionalities.
This class comes with a set of utility functions that give you access to the socket port,
shader setup, current renderer, all renderers, et...

If you're looking into building your own integration, this is the class you will be editing
for anything related to data handling within the current application.

In case you need to change the user interface, please check the MegascansLiveLink file,
which contains a LiveLinkUI class for the user interface

#####################################################################################
#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*#*"""


class LiveLinkImporter():
    Identifier = None
    isDebugMode = False

    """set_Asset_Data takes the json data we received from the thread and converts it into
       a friendly structure for all the other functions to use. """

    def __init__(self):
            self._path_ = os.path.dirname(__file__).replace("\\", "/")

            self.Settings = self.loadSettings()

            self.toSelRequest = self.Settings["Material_to_Sel"]
            LiveLinkImporter.Identifier = self

    def set_Asset_Data(self, json_data):
        
        self.SetRenderEngine()

        if(self.Renderer == "Not-Supported"):
            msg = 'Your current render engine is not supported by the Bridge Plugin so we are terminating the import process but the Plugin is still running!'
            helper.ShowMessageDialog("MS Plugin Error", msg)
            print (msg)
            return
        else:
            print("Your current render engine is " + self.Renderer)

        self.json_data = json_data
        
        # print("__________________________________")
        # print(self.json_data)
        # print("__________________________________")

        
        self.TexturesList = []
        self.Type = self.json_data["type"]
        self.mesh_transforms = []
        self.height = "1"
        self.activeLOD = self.json_data["activeLOD"]
        self.minLOD = self.json_data["minLOD"]
        self.ID = self.json_data["id"]
        self.Path = self.json_data["path"]
        self.isScatterAsset = self.CheckScatterAsset()
        self.isBillboard = self.CheckIsBillboard()
        self.isMetal = bool(self.json_data["category"] == "Metal" and self.Type == "surface")
        self.isBareMetal = bool("colorless" in [item.lower() for item in self.json_data["tags"]] and self.isMetal)
        self.isFruit = bool("fruits" in [item.lower() for item in self.json_data["tags"]] or "fruit" in [item.lower() for item in self.json_data["tags"]] or "fruits" in [item.lower() for item in self.json_data["categories"]] or "fruit" in [item.lower() for item in self.json_data["categories"]])
        self.useDisplacement = bool(((self.activeLOD != "high") and self.Settings["Enable_Displacement"]) or  self.Type != "3d")
        self.isSpecularWorkflow = bool(self.json_data["workflow"] == "specular")
        self.isAlembic = helper.GetMeshType(self.json_data["meshList"])
        self.isFabric = bool("fabric" in [item.lower() for item in self.json_data["tags"]] or "fabric" in [item.lower() for item in self.json_data["categories"]])
        self.isPlant = bool(self.Type == "3dplant")
        self.isSnow = bool("snow" in self.json_data["tags"] or "snow" in self.json_data["categories"])
        self.isSurfaceSSS =   self.Type == "surface" and (bool ("moss" in [item.lower() for item in self.json_data["categories"]]) or bool("skin" in [item.lower() for item in self.json_data["categories"]] ) or bool("snow" in [item.lower() for item in self.json_data["categories"]] ))#bool("moss" or "snow" or "skin" in [item.lower() for item in self.json_data["categories"]])#bool("moss" or "skin" in [item.lower() for item in self.json_data["categories"]]) and self.Type == "surface"

        texturesListName = "components"
        if self.isBillboard:
            texturesListName = "components"

        self.TexturesList = []
        self.textureTypes = [obj["type"] for obj in self.json_data[texturesListName]]
        
        for obj in self.json_data[texturesListName]:
            texFormat = obj["format"]
            texType = obj["type"]
            texPath = obj["path"]

            if texType == "displacement" and self.useDisplacement:
                dirn_ = os.path.dirname(texPath)
                filen_ = os.path.splitext(os.path.basename(texPath))[0]
                
                if os.path.exists(os.path.join(dirn_, filen_ + ".exr")):
                    texPath = os.path.join(dirn_, filen_ + ".exr")
                    texFormat = "exr"
            
            if texType == "diffuse" and "albedo" not in self.textureTypes:
                texType = "albedo"
                self.textureTypes.append("albedo")
                self.textureTypes.remove("diffuse")

            self.TexturesList.append((texFormat, texType, texPath))

        self.GeometryList = [(obj["format"], obj["path"]) for obj in self.json_data["meshList"]]

        if "name" in self.json_data.keys():
            self.Name = self.json_data["name"].replace(" ", "_")

        else:
            self.Name = os.path.basename(self.json_data["path"]).replace(" ", "_")

            if len(self.Name.split("_")) >= 2:
                self.Name = "_".join(self.Name.split("_")[:-1])
        
        self.materialName = self.ID + '_' + self.Name

        self.scanWidth = 1
        self.scanHeight = 1
        self.meta = None

        try:
            if 'meta' in self.json_data.keys():
                self.meta = self.json_data['meta']

                self.scanWidth = helper.GetScanWidth(self.meta)
                self.scanHeight = helper.GetScanHeight(self.meta)

                height_ = [item for item in self.meta if item["key"].lower() == "height"]
                if len(height_) >= 1:
                    self.height = str( height_[0]["value"].replace('m','') )
                    # Converting inches to meters
                    # dividing by 2 to use half as max and half as minimum
                    # managing displacement value according to the scan area
                    self.height = float(self.height) * (39.37 /2 * (self.scanWidth/2.1))
                    if(self.Type == "3d"):
                        self.height = 0.005 * 39.37 
        except:
            pass

        self.initAssetImport()

    def CheckScatterAsset(self):
        if(self.Type == "3d"):
            if('scatter' in self.json_data['categories'] or 'scatter' in self.json_data['tags'] or 'cmb_asset' in self.json_data['categories'] or 'cmb_asset' in self.json_data['tags']):
                # print("It is 3D scatter asset.")
                return True
        return False

    def CheckIsBillboard(self):
        # Use billboard textures if importing the Billboard LOD.
        if(self.Type == "3dplant"):
            if (self.activeLOD == self.minLOD):
                # print("It is billboard LOD.")
                return True
        return False

    # IMPORT FUNCTIONS

    def initAssetImport(self):
        self.Settings = self.loadSettings()
        self.toSelRequest = self.Settings["Material_to_Sel"]
        if len(self.GeometryList) > 0 and self.isAlembic and helper.GetMaxVersion() >= 2019:
            helper.SetAlembicImportSettings()

        assetData = RendererData(self.TexturesList, self.textureTypes, self.Type, self.materialName, self.useDisplacement, self.isMetal, self.isBareMetal, self.isFruit, self.isSnow, self.toSelRequest, self.isSpecularWorkflow, self.scanWidth, self.scanHeight, self.meta)
        render_setup = ("""""")
        
        if not assetData.applyToSel:
            render_setup += "clearSelection()"
            
        isMultiMatAsset = helper.HasMultipleMaterial(self.meta)
        if isMultiMatAsset and "obj" in self.json_data["meshFormat"].lower():
            render_setup += helper.OpenObjImpFile()
            render_setup += helper.GetObjSetting("Objects", "SingleMesh", "isSingleMesh")
            render_setup += helper.ChangeObjSetting("Objects", "SingleMesh", "1")

        render_setup += self.MeshSetup()
        if self.toSelRequest and self.Type.lower() not in ["3dplant", "3d"]:
            render_setup = render_setup.replace("SELOPTION", "Enabled")
        else:
            render_setup = render_setup.replace("SELOPTION", "Disabled")

        if self.Renderer in ["Arnold", "Corona", "Redshift", "Octane"]:
            render_setup += self.TextureSetup()
        
        if self.Renderer == "Arnold":
            render_setup += ArnoldHelper.GetMaterialSetup(assetData)
        elif self.Renderer == "Corona":
            render_setup += CoronaHelper.GetMaterialSetup(assetData)
        elif self.Renderer == "Vray":
            render_setup += VRayHelper.GetVRayRenderSetup(assetData)
        elif self.Renderer == "Redshift":
            render_setup += RedshiftHelper.GetMaterialSetup(assetData)
        elif self.Renderer == "FStorm":
            render_setup += FStormHelper.GetMaterialSetup(assetData)
        elif self.Renderer == "Octane":
            render_setup += OctaneHelper.GetMaterialSetup(assetData)

        # Creates Bugs
        # if self.Renderer in ["Arnold","Redshift"]:
        #     render_setup += self.assignMaterial()

        # Loop through all the assets in the json and import them one by one
        maplist_ = [(item["path"], item["format"], item["type"]) for item in self.json_data["components"]]
        
        # This loop constructs our texture maps to give them the appropriate color space, privilege exr for
        # displacement maps, etc...
        for map_ in maplist_:

            texture_ = map_[0]
            format_ = map_[1]
            # The following snippet of code basically tries to find if our displacement is available in exr
            # even if the user picked JPEG as the export option.

            if map_[2].lower() == "displacement":

                dirn_ = os.path.dirname(map_[0])
                filen_ = os.path.splitext(os.path.basename(map_[0]))[0]
                if os.path.exists(os.path.join(dirn_, filen_ + ".exr")):
                    texture_ = os.path.join(dirn_, filen_ + ".exr")
                    format_ = "exr"


            # c_space is used to set up the gamma of our bitMap nodes. Any EXR texture will be set to linear,
            # while the albedo, translucency and specular are set to sRGB when in JPEG mode. All other textures are
            # presumed to be linear.

            c_space = 1.0
            if format_.lower() in ["exr"]:
                c_space = 1.0
            if map_[2].lower() in ["albedo", "specular", "translucency"] and format_.lower() not in ["exr"]:
                c_space = 2.2

            render_setup = render_setup.replace(("TEX_" + map_[2].upper() + '"'), texture_.replace("\\", "/") + '"')
            render_setup = render_setup.replace(('"CS_' + map_[2].upper() + '"'), str(c_space))

        render_setup = render_setup.replace("MS_MATNAME", self.materialName)
        render_setup = render_setup.replace("MSTYPE", self.Type.lower() )

        pathlist_ = ", ".join([('"'+ item["path"].replace("\\", "/") +'"') for item in self.json_data["meshList"]])
        render_setup = render_setup.replace("FBXPATHLIST", pathlist_)

        

        render_setup = render_setup.replace("MSLOD", self.activeLOD )

        if "tags" in self.json_data.keys():
            if "fabric" in [item.lower() for item in self.json_data["tags"] ]:
                render_setup = render_setup.replace("MSFABRIC", "isFabric" )
            else:
                render_setup = render_setup.replace('"MSFABRIC"', "false" )

            if "metal" in self.json_data["tags"] or "metal" in self.json_data["categories"] :
                render_setup = render_setup.replace("MSMETAL", "isMetal" )
                
            if "colorless" in self.json_data["tags"] and "metal" in self.json_data["tags"] or "metal" in self.json_data["categories"] :
                render_setup = render_setup.replace("MSBAREMETAL", "isBareMetal" )
                
            if "fruits" in self.json_data["tags"]:
                render_setup = render_setup.replace("MSFRUIT", "isFruit" )

            if "isCustom" in self.json_data.keys():
                if self.json_data["isCustom"] == True:
                    render_setup = render_setup.replace("MSCUSTOM", "isCustom" )

        render_setup = render_setup.replace("MS_METAL", str(self.isMetal).lower())
        render_setup = render_setup.replace("MS_BAREMETAL", str(self.isBareMetal).lower())
        render_setup = render_setup.replace("MS_FABRIC", str(self.isFabric).lower())
        render_setup = render_setup.replace("MS_FRUIT", str(self.isFruit).lower())
        render_setup = render_setup.replace("MS_DISP", str(self.useDisplacement).lower())
        render_setup = render_setup.replace("MS_PLANT", str(self.isPlant).lower())
        render_setup = render_setup.replace("MS_SSS", str(self.isSurfaceSSS).lower())

        if self.Renderer.lower() == "corona":
            # Used by Corona render
            render_setup = render_setup.replace( "SPECULARTOIOR", os.path.join(self._path_, "SpecularToIOR.CUBE").replace("\\", "/") )
            render_setup = render_setup.replace( "MS_HEIGHT", str(self.height) )

        if self.Renderer.lower() == "redshift":
            # Used by Redshift render
            render_setup = render_setup.replace( "MS_HEIGHT", str(self.height) )

        if self.isScatterAsset:
            render_setup += self.ScatterSetup()
            render_setup = render_setup.replace("SCATTERPARENTNAME", self.materialName)

        if isMultiMatAsset and "obj" in self.json_data["meshFormat"].lower():
            render_setup += helper.ResetObjIniValue("Objects", "SingleMesh", "isSingleMesh")
            
        if self.Renderer == "Octane":
            updated_line = ""
            for script_line in render_setup.splitlines():
                if "TEX_" in script_line:
                    updated_line = "--" + script_line
                    render_setup =render_setup.replace(script_line, updated_line)

        print(render_setup)

        # If debug mode is active, we print the maxscript code without executing it
        if not LiveLinkImporter.isDebugMode:
            pymxs.runtime.execute(render_setup)
        
    # Auto detect render engine.
    def SetRenderEngine(self):
        selectedRenderer = str(pymxs.runtime.execute("renderers.current")) #MaxPlus.RenderSettings_GetCurrent().GetClassName() --- pymxs returns v_ray instead of v-ray unlike maxplus
        selectedRenderer = selectedRenderer.lower()
        self.Renderer = "Not-Supported"
        if("corona" in selectedRenderer):
            self.Renderer = "Corona"
        elif("redshift" in selectedRenderer):
            self.Renderer = "Redshift"
        elif("v_ray" in selectedRenderer):
            self.Renderer = "Vray"
        elif("octane" in selectedRenderer):
            self.Renderer = "Octane"
        elif("fstorm" in selectedRenderer):
            self.Renderer = "FStorm"
        elif("arnold" in selectedRenderer):
            self.Renderer = "Arnold"

    # Shader setup / Mesh import functions.

    def MeshSetup(self):
        return ("""
        FBXImporterSetParam "ScaleFactor" 1
        selToMat = "SELOPTION"
        old_sel = for s in selection collect s

        assetType = "MSTYPE"
        assetLOD = "MSLOD"
        isFabric = "MSFABRIC"
        isMetal = "MSMETAL"
        isBareMetal = "MSBAREMETAL"
        isCustom = "MSCUSTOM"
        isFruit = "MSFRUIT"

        
        MSFabric = MS_FABRIC
        MSMetal = MS_METAL
        MSBareMetal = MS_BAREMETAL
        MSFruit = MS_FRUIT
        Disp = MS_DISP
        MSPlant = MS_PLANT
        SSSSurface = MS_SSS

        meshes_ = #(FBXPATHLIST)

        oldObj = objects as array

        for geo in meshes_ do (
        ImportFile geo #noprompt
        )

        newObj = for o in objects where findItem oldObj o == 0 collect o

        select newObj
        if (selToMat == "Enabled") do
        (
        selectMore old_sel
        )

        CurOBJs = for s in selection collect s

        if sme.IsOpen() == false do(
        
            sme.Open()
            sme.Close()
            MatEditor.mode = #advanced
            ActiveSMEView = sme.GetView (sme.activeView)
            )

        """)

    def TextureSetup(self):

        if self.Renderer == "Octane":
            return ("""

            --Bitmaptextures

            albedoBitmap = undefined
            diffuseBitmap = undefined
            roughnessBitmap = undefined
            opacityBitmap = undefined
            normalBitmap = undefined
            metallicBitmap = undefined
            translucencyBitmap = undefined
            transmissionBitmap = undefined
            displacementBitmap = undefined
            specularBitmap = undefined
            glossBitmap = undefined
            FuzzBitmap = undefined
            aoBitmap = undefined
            cavityBitmap = undefined
            bumpBitmap = undefined
            normalbumpBitmap = undefined

            albedoBitmap = Bitmaptexture fileName: "TEX_ALBEDO" gamma: "CS_ALBEDO"
            diffuseBitmap = Bitmaptexture fileName: "TEX_ALBEDO" gamma: "CS_ALBEDO"
            roughnessBitmap = Bitmaptexture fileName: "TEX_ROUGHNESS" gamma: "CS_ROUGHNESS"
            opacityBitmap = Bitmaptexture fileName: "TEX_OPACITY" gamma: "CS_OPACITY"
            normalBitmap = Bitmaptexture fileName: "TEX_NORMAL" gamma: "CS_NORMAL"
            metallicBitmap = Bitmaptexture fileName: "TEX_METALNESS" gamma: "CS_METALNESS"
            translucencyBitmap = Bitmaptexture fileName: "TEX_TRANSLUCENCY" gamma: "CS_TRANSLUCENCY"
            transmissionBitmap = Bitmaptexture fileName: "TEX_TRANSMISSION" gamma: "CS_TRANSMISSION"
            displacementBitmap = Bitmaptexture fileName: "TEX_DISPLACEMENT" gamma: "CS_DISPLACEMENT"
            specularBitmap = Bitmaptexture fileName: "TEX_SPECULAR" gamma: "CS_SPECULAR"
            glossBitmap = Bitmaptexture fileName: "TEX_GLOSS" gamma: "CS_GLOSS"
            FuzzBitmap = Bitmaptexture fileName: "TEX_FUZZ" gamma: "CS_FUZZ"
            aoBitmap = Bitmaptexture fileName: "TEX_AO" gamma: "CS_AO"
            cavityBitmap = Bitmaptexture fileName: "TEX_CAVITY" gamma: "CS_CAVITY"
            bumpBitmap = Bitmaptexture fileName: "TEX_BUMP" gamma: "CS_BUMP"
            normalbumpBitmap = Bitmaptexture fileName: "TEX_NORMALBUMP" gamma: "CS_NORMALBUMP"

            """)
        else:
            return ("""

            --Bitmaps

            albedoBitmap = openBitmap "TEX_ALBEDO" gamma: "CS_ALBEDO"
            diffuseBitmap = openBitmap "TEX_ALBEDO" gamma: "CS_ALBEDO"
            roughnessBitmap = openBitmap "TEX_ROUGHNESS" gamma: "CS_ROUGHNESS"
            opacityBitmap = openBitmap "TEX_OPACITY" gamma: "CS_OPACITY"
            normalBitmap = openBitmap "TEX_NORMAL" gamma: "CS_NORMAL"
            metallicBitmap = openBitmap "TEX_METALNESS" gamma: "CS_METALNESS"
            translucencyBitmap = openBitmap "TEX_TRANSLUCENCY" gamma: "CS_TRANSLUCENCY"
            transmissionBitmap = openBitmap "TEX_TRANSMISSION" gamma: "CS_TRANSMISSION"
            displacementBitmap = openBitmap "TEX_DISPLACEMENT" gamma: "CS_DISPLACEMENT"
            specularBitmap = openBitmap "TEX_SPECULAR" gamma: "CS_SPECULAR"
            glossBitmap = openBitmap "TEX_GLOSS" gamma: "CS_GLOSS"
            FuzzBitmap = openBitmap "TEX_FUZZ" gamma: "CS_FUZZ"
            aoBitmap = openBitmap "TEX_AO" gamma: "CS_AO"
            cavityBitmap = openBitmap "TEX_CAVITY" gamma: "CS_CAVITY"
            bumpBitmap = openBitmap "TEX_BUMP" gamma: "CS_BUMP"
            normalbumpBitmap = openBitmap "TEX_NORMALBUMP" gamma: "CS_NORMALBUMP"

            """)

    def assignMaterial(self):
        return ("""

        mat.showInViewport = true

        """)

    def ScatterSetup(self):
        return (
            """
            actionMan.executeAction 0 "40043"  -- Selection: Select None

            parentObject = Point pos:[0,0,0] name:"SCATTERPARENTNAME"

            select CurOBJs
            for o in selection do o.parent = parentObject
            actionMan.executeAction 0 "40043"  -- Selection: Select None
            """
        )
        

    # UTILITY FUNCTIONS 
    # Returns the json structure sent by Bridge
    def getExportStructure(self):
        return self.json_data

    # Returns an array of settings : [current renderer, current
    def defaultSettings(self): 
        self.Settings = ({
            "Material_to_Sel" : True,
            "WinGeometry": [0, 0, 0, 0]
        })
        return self.Settings

    # Creates the Settings file.
    def createSettings(self):
        self.Settings = self.defaultSettings()
        output_ = json.dumps(self.Settings, sort_keys=True, ensure_ascii=False, indent=2)
        with open(os.path.join(self._path_, "Settings.json"), 'w') as outfile:
            json.dump(self.Settings, outfile)

    # Loads the Settings file. Will create it if it doesn't exist by using the createSettings function
    def loadSettings(self):
        if os.path.exists(os.path.join(self._path_, "Settings.json")):
            with open(os.path.join(self._path_, "Settings.json"), 'r') as fl_:
                self.Settings =  json.load(fl_)
        else:
            self.createSettings()
        return self.Settings

    # Update the current settings with the input settings.
    def updateSettings(self, settings):
        if os.path.exists(os.path.join(self._path_, "Settings.json")):
            with open(os.path.join(self._path_, "Settings.json"), 'w') as outfile:
                json.dump(settings, outfile)
        else:
            self.Settings = settings
            output_ = json.dumps(self.Settings, sort_keys=True, ensure_ascii=False, indent=2)
            with open(os.path.join(self._path_, "Settings.json"), 'w') as outfile:
                json.dump(self.Settings, outfile)

    # Update the current settings with the input settings.
    def getPref(self, request):
        return self.Settings[request]


class RendererData():
    def __init__(self, textureList, textureTypes, assetType, materialName, useDisplacement, isMetal, isBareMetal, isFruit, isSnow, applyToSel, isSpecular, width, height, meta):
        self.textureList = textureList
        self.textureTypes = textureTypes
        self.assetType = assetType
        self.materialName = materialName
        self.useDisplacement = useDisplacement
        self.isMetal = isMetal
        self.isBareMetal = isBareMetal
        self.isFruit = isFruit
        self.isSnow = isSnow
        self.applyToSel = applyToSel
        self.isSpecular = isSpecular
        self.width = width
        self.height = height
        self.meta = meta
