import os, sys, json,pymxs
import MSLiveLinkHelpers
helper = MSLiveLinkHelpers.LiveLinkHelper()

class VraySetup():

    def GetVRayRenderSetup(self, assetData):
        self.roughnessUsed = False
        self.assetData = assetData
        self.VrayRenderSetup = ""
        self.VrayRenderSetup += helper.SetWidthAndHeight(self.assetData.width * 100, self.assetData.height * 100)
        materialScript = helper.GetActiveSMEView()
        if helper.HasMultipleMaterial(assetData.meta):
            multiNodeName = "MutliMaterial"
            materialScript += helper.CreateMultiSubMaterial(multiNodeName, assetData.materialName, helper.GetNumberOfUniqueMaterial(assetData.meta))
            index = 1
            matsData = helper.ExtractMatData(assetData.meta)
            for matData in matsData:
                matName = assetData.materialName + "_" + str(index)
                nodeName = "MatNode_" + str(index)
                if matData.matType == "glass":
                    materialScript += self.GetGlassMultiMaterial(nodeName, matName)
                elif self.assetData.isBareMetal:
                    self.CreateBareMetalMaterial()
                else:
                    materialScript += self.GetOpaqueMultiMaterial(nodeName, matName)

                materialScript += helper.AssignMaterialToMultiSlots(multiNodeName, nodeName, matData.matIDs)
                index += 1
            materialScript += helper.CreateNodeInSME(multiNodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(multiNodeName)
            materialScript += helper.ShowInViewport(multiNodeName)
        else:
            if self.assetData.isBareMetal:
                self.CreateBareMetalMaterial()
            else:
                self.CreateOpaqueMaterial()

        if self.roughnessUsed:
            self.UseRoughness()
        #self.VrayRenderSetup += helper.ShowInViewport()
        self.VrayRenderSetup += helper.DeselectEverything()
        self.VrayRenderSetup += materialScript
        return self.VrayRenderSetup
  
    def GetGlassMultiMaterial(self,nodeName, matName):
        assetType = self.assetData.assetType.lower()
        script = ''
        script += self.CreateMatNode()
         
        if "specular" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_reflection", True, "specular", 2, -300, 612)
        if "gloss" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_reflectionGlossiness", True, "gloss", 1, -300, 780)
        elif "roughness" in self.assetData.textureTypes:
            script+= self.CreateHDRINode("texmap_reflectionGlossiness", True, "roughness", 1, -300, 780)
            self.roughnessUsed = True

        script += helper.AddNormalProperties(self.assetData.textureTypes, assetType == "3d")
        if "normal" in self.assetData.textureTypes or "bump" in self.assetData.textureTypes:
            script += self.CreateNormalNode("texmap_bump", True, "Nrm + Bump", "normal", "bump", 1, 1, -300, 680, -600, 670, -600, 690)
        
        if "opacity" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_opacity", True, "opacity", 1, -300, 830)
        
        script += 'mat.Refraction = color 225 225 225'
        
        return script.replace('mat', nodeName)
    
    
    def GetOpaqueMultiMaterial(self,nodeName, matName):
        assetType = self.assetData.assetType.lower()
        script = ''
        script += self.CreateMatNode()
        
        if "albedo" in self.assetData.textureTypes:
            if "ao" in self.assetData.textureTypes:
                script += self.CreateComplexNode("texmap_diffuse", True, "Albedo + AO", "albedo", "ao", 2, 1, -300, 512, -600, 500, -600, 540)
            else:
                script += self.CreateHDRINode("texmap_diffuse", True, "albedo", 2, -300, 540)
        
        if "specular" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_reflection", True, "specular", 2, -300, 612)
        if "gloss" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_reflectionGlossiness", True, "gloss", 1, -300, 780)
        elif "roughness" in self.assetData.textureTypes:
            script+= self.CreateHDRINode("texmap_reflectionGlossiness", True, "roughness", 1, -300, 780)
            self.roughnessUsed = True
        
        script += helper.AddNormalProperties(self.assetData.textureTypes, assetType == "3d")
        if "normal" in self.assetData.textureTypes or "bump" in self.assetData.textureTypes:
            script += self.CreateNormalNode("texmap_bump", True, "Nrm + Bump", "normal", "bump", 1, 1, -300, 680, -600, 670, -600, 690)
        
        if "cavity" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_cavity", False, "cavity", 1, -300, 1050)
            
        if "fuzz" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_fuzz", False, "fuzz", 1, -300, 1150)

        if "opacity" in self.assetData.textureTypes:
            script += self.CreateHDRINode("texmap_opacity", True, "opacity", 1, -300, 830)

        if "translucency" in self.assetData.textureTypes:
            script += self.CreateHDRINode("", False, "translucency", 2, 0, 950)
            self.ConnectTranslucencyTexture()
        
        elif "transmission" in self.assetData.textureTypes:
            script += self.CreateHDRINode("", False, "transmission", 1, 0, 950)
            self.ConnectTranslucencyTexture()

        if "displacement" in self.assetData.textureTypes and self.assetData.useDisplacement and assetType not in ["3dplant"]:
            script += helper.SelectObjects()
            script += self.CreateHDRINode("", False, "displacement", 1, -300, 830)
            if(assetType == "3d"):
                self.SetupDisplacement(2)
            else:
                self.SetupDisplacement(8)                
        return script.replace('mat', nodeName)
    
    def CreateOpaqueMaterial(self):

        assetType = self.assetData.assetType.lower()
        isPlant = assetType == "3dplant"

        if isPlant:
            self.CreateTwoSidedMatNode()
        elif "transmission" in self.assetData.textureTypes or "translucency" in self.assetData.textureTypes:
            self.CreateSSSMatNode()
        else:
            self.VrayRenderSetup += self.CreateMatNode()

        self.StandardIORSetup()

        if "albedo" in self.assetData.textureTypes:
            if "ao" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateComplexNode("texmap_diffuse", True, "Albedo + AO", "albedo", "ao", 2, 1, -300, 512, -600, 500, -600, 540)
                if isPlant:
                    self.AlbedoFor3DPlant()
            else:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_diffuse", True, "albedo", 2, -300, 540)
        
        if self.assetData.isSpecular:
            if "specular" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_reflection", True, "specular", 2, -300, 612)
            if "gloss" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "gloss", 1, -300, 780)
            elif "roughness" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "roughness", 1, -300, 780)
                self.roughnessUsed = True

        else:
            if "metalness" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_metalness", True, "metalness", 1, -300, 612)
            if "roughness" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "roughness", 1, -300, 780)
                self.roughnessUsed = True

            elif "gloss" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "gloss", 1, -300, 780)

        self.VrayRenderSetup += helper.AddNormalProperties(self.assetData.textureTypes)
        if "normal" in self.assetData.textureTypes or "bump" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateNormalNode("texmap_bump", True, "Nrm + Bump", "normal", "bump", 1, 1, -300, 680, -600, 670, -600, 690)

        if "opacity" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_opacity", True, "opacity", 1, -300, 830)

        if "cavity" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_cavity", False, "cavity", 1, -300, 1050)
        
        if "fuzz" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_fuzz", False, "fuzz", 1, -300, 1150)

        if "translucency" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("", False, "translucency", 2, 0, 950)
            self.ConnectTranslucencyTexture()
        
        elif "transmission" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("", False, "transmission", 1, 0, 950)
            self.ConnectTranslucencyTexture()

        if "displacement" in self.assetData.textureTypes and self.assetData.useDisplacement and assetType not in ["3dplant"]:
            self.VrayRenderSetup += helper.SelectObjects()
            self.VrayRenderSetup += self.CreateHDRINode("", False, "displacement", 1, -300, 830)
            if(assetType == "3d"):
                self.SetupDisplacement(2)
            else:
                self.SetupDisplacement(8)
        
        if (assetType not in ["3d", "3dplant"])or assetType in ["3d", "3dplant"]: #If asset is a surface or 3d/3dplant
            self.VrayRenderSetup += helper.AssignMaterialToObjects("mat_2sided" if isPlant else "mat")

    def CreateBareMetalMaterial(self):
        self.VrayRenderSetup += self.CreateMatNode()
        self.MetalIORSetup()
        
        if "specular" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_reflection", True, "specular", 2, -300, 612)
        else:
            if "albedo" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_diffuse", True, "albedo", 2, -300, 540)
        
            if "metalness" in self.assetData.textureTypes:
                self.VrayRenderSetup += self.CreateHDRINode("texmap_metalness", True, "metalness", 1, -300, 612)

        self.VrayRenderSetup += helper.AddNormalProperties(self.assetData.textureTypes)
        if "normal" in self.assetData.textureTypes or "bump" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateNormalNode("texmap_bump", True, "Nrm + Bump", "normal", "bump", 1, 1, -300, 680, -600, 670, -600, 690)
        
        if "gloss" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "gloss", 1, -300, 780)
        elif "roughness" in self.assetData.textureTypes:
            self.VrayRenderSetup += self.CreateHDRINode("texmap_reflectionGlossiness", True, "roughness", 1, -300, 780)
            self.roughnessUsed = True

        
        #if self.assetData.applyToSel:
        self.VrayRenderSetup += helper.AssignMaterialToObjects()

    def CreateMatNode(self, MatXLoc = 0, MatYLoc = 512, defaultRefl = 128):
        matScript = ("""
        
        mat = VRayMtl()
        ActiveSMEView = sme.GetView (sme.activeView)
        ActiveSMEView.CreateNode mat [MatXLoc, MatYLoc]
        mat.name = "MS_MATNAME"
        mat.brdf_type = 4

        isPlant = False
        useRealWorldScale = False

        -- Sets the reflection color to a 0.5 grayscale value.
        mat.Reflection = color defaultRefl defaultRefl defaultRefl
        
        """).replace("MS_MATNAME", self.assetData.materialName).replace("MatXLoc", str(MatXLoc)).replace("MatYLoc", str(MatYLoc)).replace("defaultRefl", str(defaultRefl))
        return matScript    
    def CreateTwoSidedMatNode(self, MatXLoc = 0, MatYLoc = 512, defaultRefl = 128):
        matScript = ("""
        
        mat = VRayMtl()
        ActiveSMEView = sme.GetView (sme.activeView)
        mat.name = "MS_MATNAME"

        mat_2sided = VRay2SidedMtl()
        mat_2sided.name = "MS_MATNAME"
        mat_2sided.frontMtl = mat
        mat_2sided.backMtl = mat

        ActiveSMEView.CreateNode mat_2sided [150,650]
        ActiveSMEView.CreateNode mat [MatXLoc, MatYLoc]

        mat.brdf_type = 4

        mat.showInViewport = true

        isPlant = True
        useRealWorldScale = False

        -- Sets the reflection color to a 0.5 grayscale value.
        mat.Reflection = color defaultRefl defaultRefl defaultRefl
        
        """).replace("MS_MATNAME", self.assetData.materialName).replace("MatXLoc", str(MatXLoc)).replace("MatYLoc", str(MatYLoc)).replace("defaultRefl", str(defaultRefl))
        self.VrayRenderSetup += matScript
    
    def CreateSSSMatNode(self, MatXLoc = 0, MatYLoc = 512, defaultRefl = 128):
        matScript = ("""
        
        mat = VRayMtl()
        ActiveSMEView = sme.GetView (sme.activeView)
        mat.name = "MS_MATNAME"

        mat_2sided = VRay2SidedMtl()
        mat_2sided.name = "MS_MATNAME"
        mat_2sided.frontMtl = mat

        ActiveSMEView.CreateNode mat_2sided [150,650]
        ActiveSMEView.CreateNode mat [MatXLoc, MatYLoc]

        mat.brdf_type = 4

        mat.showInViewport = true

        mat.translucency_on = 3

        isPlant = False
        useRealWorldScale = False

        -- Sets the reflection color to a 0.5 grayscale value.
        mat.Reflection = color defaultRefl defaultRefl defaultRefl
        
        """).replace("MS_MATNAME", self.assetData.materialName).replace("MatXLoc", str(MatXLoc)).replace("MatYLoc", str(MatYLoc)).replace("defaultRefl", str(defaultRefl))
        self.VrayRenderSetup += matScript

    def CreateHDRINode(self, connectionName, connectToMat, texType, colorspace, nodeXLoc, nodeYLoc):
        hdriScript = ("""

        -- NodeName setup
        hdriMapNode = VRayHDRI()
        hdriMapNode.name = "NodeName"
        hdriMapNode.HDRIMapName =   "TexPath"
        hdriMapNode.color_space = colorspace
        
        if useRealWorldScale do (
            hdriMapNode.coords.realWorldScale = on 
            hdriMapNode.coords.U_Tiling = scanWidth
            hdriMapNode.coords.V_Tiling = scanHeight
        )

        hdriMapNode.coords.blur = 0.01

        ActiveSMEView.CreateNode hdriMapNode [nodeXLoc, nodeYLoc]


        """).replace("NodeName", texType.capitalize()).replace("TexPath", helper.GetTexturePath(self.assetData.textureList, texType))
        hdriScript = hdriScript.replace("colorspace", str(colorspace)).replace("nodeXLoc", str(nodeXLoc)).replace("nodeYLoc", str(nodeYLoc))

        if connectToMat:
            hdriScript += helper.ConnectNodeToMaterial(connectionName, "hdriMapNode")
            
        return hdriScript

    def CreateComplexNode(self, connectionName, connectToMat, nodeName, texAType, texBType, aColorspace, bColorspace, NodeXLoc, NodeYLoc, aNodeXLoc, aNodeYLoc, bNodeXLoc, bNodeYLoc):
        complexNodeScript = ("""

        -- NodeName setup
        complexNode = VRayCompTex ()
        complexNode.name = "NodeName"
        complexNode.operator = 3

        complexNode.sourceA  = VRayHDRI()
        complexNode.sourceA.name = "NodeAName"
        complexNode.sourceA.HDRIMapName =   "aTexPath"
        complexNode.sourceA.color_space = aColorspace

        complexNode.sourceB  = VRayHDRI()
        complexNode.sourceB.name = "NodeBName"
        complexNode.sourceB.HDRIMapName =   "bTexPath"
        complexNode.sourceB.color_space = bColorspace

        if useRealWorldScale do (
            complexNode.sourceA.coords.realWorldScale = on 
            complexNode.sourceA.coords.U_Tiling = scanWidth
            complexNode.sourceA.coords.V_Tiling = scanHeight

            complexNode.sourceB.coords.realWorldScale = on 
            complexNode.sourceB.coords.U_Tiling = scanWidth
            complexNode.sourceB.coords.V_Tiling = scanHeight
        )

        complexNode.sourceA.coords.blur = 0.01
        complexNode.sourceB.coords.blur = 0.01

        ActiveSMEView.CreateNode complexNode [PosX, PosY]
        ActiveSMEView.CreateNode complexNode.sourceA [aPosX, aPosY]
        ActiveSMEView.CreateNode complexNode.sourceB [bPosX, bPosY]

        """).replace("NodeName", nodeName).replace("NodeAName", texAType).replace("aTexPath", helper.GetTexturePath(self.assetData.textureList, texAType))
        complexNodeScript = complexNodeScript.replace("aColorspace", str(aColorspace)).replace("NodeBName", texBType).replace("bTexPath", helper.GetTexturePath(self.assetData.textureList, texBType))
        complexNodeScript = complexNodeScript.replace("bColorspace", str(bColorspace))
        complexNodeScript = complexNodeScript.replace("aPosX", str(aNodeXLoc)).replace("aPosY", str(aNodeYLoc)).replace("bPosX", str(bNodeXLoc))
        complexNodeScript = complexNodeScript.replace("bPosY", str(bNodeYLoc)).replace("PosX", str(NodeXLoc)).replace("PosY", str(NodeYLoc))

        if connectToMat:
            complexNodeScript += helper.ConnectNodeToMaterial(connectionName, "complexNode")

        return complexNodeScript
    
    def CreateNormalNode(self, connectionName, connectToMat, nodeName, texAType, texBType, aColorspace, bColorspace, NodeXLoc, NodeYLoc, aNodeXLoc, aNodeYLoc, bNodeXLoc, bNodeYLoc):
        normalNodeScript = ("""

        -- NodeName setup
        normalNode = VRayNormalMap ()
        normalNode.name = "NodeName"

        if hasNormal do (
            normalNode.normal_map  = VRayHDRI()
            normalNode.normal_map.name = "NodeAName"
            normalNode.normal_map.HDRIMapName =   "aTexPath"
            normalNode.normal_map.color_space = aColorspace
            normalNode.normal_map.coords.blur = 0.01
            ActiveSMEView.CreateNode normalNode.normal_map [aPosX, aPosY]
        )

        if hasBump do (
            normalNode.bump_map  = VRayHDRI()
            normalNode.bump_map.name = "NodeBName"
            normalNode.bump_map.HDRIMapName =   "bTexPath"
            normalNode.bump_map.color_space = bColorspace
            normalNode.bump_map.coords.blur = 0.01
            ActiveSMEView.CreateNode normalNode.bump_map [bPosX, bPosY]
        )

        if useRealWorldScale do (
            if hasNormal do (
            normalNode.normal_map.coords.realWorldScale = on 
            normalNode.normal_map.coords.U_Tiling = scanWidth
            normalNode.normal_map.coords.V_Tiling = scanHeight
            )

            if hasBump do (
                normalNode.bump_map.coords.realWorldScale = on 
                normalNode.bump_map.coords.U_Tiling = scanWidth
                normalNode.bump_map.coords.V_Tiling = scanHeight
            )
        )

        ActiveSMEView.CreateNode normalNode [PosX, PosY]

        """).replace("NodeName", nodeName).replace("NodeAName", texAType.capitalize()).replace("aTexPath", helper.GetTexturePath(self.assetData.textureList, texAType))
        normalNodeScript = normalNodeScript.replace("aColorspace", str(aColorspace)).replace("NodeBName", texBType.capitalize()).replace("bTexPath", helper.GetTexturePath(self.assetData.textureList, texBType))
        normalNodeScript = normalNodeScript.replace("bColorspace", str(bColorspace))
        normalNodeScript = normalNodeScript.replace("aPosX", str(aNodeXLoc)).replace("aPosY", str(aNodeYLoc)).replace("bPosX", str(bNodeXLoc))
        normalNodeScript = normalNodeScript.replace("bPosY", str(bNodeYLoc)).replace("PosX", str(NodeXLoc)).replace("PosY", str(NodeYLoc))

        if connectToMat:
            normalNodeScript += helper.ConnectNodeToMaterial(connectionName, "normalNode")

        return normalNodeScript

    def StandardIORSetup(self):
        IORScript = ("""
        mat.reflection_lockIOR = off
        mat.reflection_ior = 1.5
        """)
        self.VrayRenderSetup += IORScript

    def MetalIORSetup(self):
        IORScript = ("""
        mat.Diffuse = color 0 0 0
        mat.reflection_lockIOR = off
        mat.reflection_ior = 100
        """)
        self.VrayRenderSetup += IORScript

    def UseRoughness(self):
        useRoughnessScript = ("""
        mat.brdf_useRoughness = on
        """)
        self.VrayRenderSetup += useRoughnessScript
    
    def UseRealWorldScale(self):
        useRealWorldScaleScript = ("""
        useRealWorldScale = True
        """)
        self.VrayRenderSetup += useRealWorldScaleScript

    def SetupDisplacement(self, displacementValue):
        dispScript = ("""
        max modify mode
        dispMod = VRayDisplacementMod ()
        dispMod.type = 1
        dispMod.amount = displacementValue
        dispMod.texmap = hdriMapNode
        modPanel.addModToSelection (dispMod)
        max create mode
        """).replace("displacementValue", str(displacementValue))
        self.VrayRenderSetup += dispScript

    def AlbedoFor3DPlant(self):
        twoSidedMatScript = ("""
        mat.texmap_diffuse = complexNode.SourceA
        """)
        self.VrayRenderSetup += twoSidedMatScript

    def ConnectTranslucencyTexture(self):
        translucencyScript = ("""
        mat_2sided.texmap_translucency = hdriMapNode
        """)
        self.VrayRenderSetup += translucencyScript