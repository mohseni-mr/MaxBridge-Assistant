import os, sys, json
import MSLiveLinkHelpers
helper = MSLiveLinkHelpers.LiveLinkHelper()

class FStormSetup():

    def GetMaterialSetup(self, assetData):
        materialScript = helper.GetActiveSMEView()
        materialScript += self.AddGamma()

        if helper.HasMultipleMaterial(assetData.meta):
            multiNodeName = "MutliMaterial"
            materialScript += helper.CreateMultiSubMaterial(multiNodeName, assetData.materialName, helper.GetNumberOfUniqueMaterial(assetData.meta))
            index = 1
            matsData = helper.ExtractMatData(assetData.meta)
            for matData in matsData:
                matName = assetData.materialName + "_" + str(index)
                nodeName = "MatNode_" + str(index)
                if matData.matType == "glass":
                    materialScript += self.GetGlassMaterial(nodeName, matName)
                else:
                    materialScript += self.GetOpaqueMaterial(nodeName, matName, assetData.useDisplacement)
                materialScript += helper.AssignMaterialToMultiSlots(multiNodeName, nodeName, matData.matIDs)
                index += 1
            materialScript += helper.CreateNodeInSME(multiNodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(multiNodeName)
            materialScript += helper.ShowInViewport(multiNodeName)
        else:
            nodeName = "MatNode"
            materialScript += self.GetOpaqueMaterial(nodeName, assetData.materialName, assetData.useDisplacement)
            materialScript += helper.CreateNodeInSME(nodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(nodeName)
            materialScript += helper.ShowInViewport(nodeName)
        
        helper.DeselectEverything()
        return materialScript

    def GetOpaqueMaterial(self, nodeName, matName, useDisplacement):
                
        DisplacementNode = "--Displacement"
        
        if(useDisplacement):
            DisplacementNode = """ 
        --Displacement
        if doesFileExist "TEX_DISPLACEMENT" do (
            mymod_ = FStormDisplacement ()
            modPanel.addModToSelection (mymod_)
            mymod_.power = 1.9685
            dispBitmap = FStormBitmap()
            dispBitmap.filename = "TEX_DISPLACEMENT"
            dispBitmap.gamma = linearGamma
            mymod_.texture = dispBitmap
        )
        
        """
        return ("""

        --Displacement

        MAT_NODE_NAME = FStorm()
        MAT_NODE_NAME.name = "MS_MATNAME"

        MAT_NODE_NAME.diffuse_velvet = 0
        MAT_NODE_NAME.diffuse_rough = 0.5

        if doesFileExist "TEX_ALBEDO" do (
            MAT_NODE_NAME.diffuse_tex = FStormBitmap()
            MAT_NODE_NAME.diffuse_tex.name = ("Diffuse")
            MAT_NODE_NAME.diffuse_tex.filename = "TEX_ALBEDO"
            MAT_NODE_NAME.diffuse_tex.gamma = colorGamma
        )

        --Reflection/Specular
        MAT_NODE_NAME.Reflection = color 255 255 255
          if doesFileExist "TEX_SPECULAR" then (
            MAT_NODE_NAME.reflection_tex = FStormBitmap()
            MAT_NODE_NAME.reflection_tex.name = ("Specular")
            MAT_NODE_NAME.reflection_tex.filename = "TEX_SPECULAR"
            MAT_NODE_NAME.reflection_tex.gamma = linearGamma
            MAT_NODE_NAME.reflection_tex.type = 1
        )
        else (
            MAT_NODE_NAME.refl_level = 1
        )
        
        
        

        if doesFileExist "TEX_ROUGHNESS" then (
            MAT_NODE_NAME.reflection_glossy_tex = FStormBitmap()
            MAT_NODE_NAME.reflection_glossy_tex.name = ("Glossiness")
            MAT_NODE_NAME.reflection_glossy_tex.filename = "TEX_ROUGHNESS"
            MAT_NODE_NAME.reflection_glossy_tex.gamma = linearGamma
            MAT_NODE_NAME.reflection_glossy_tex.type = 1
            MAT_NODE_NAME.reflection_glossy_tex.inverted = on
        )
        else (
            if doesFileExist "TEX_GLOSS" then (
                MAT_NODE_NAME.reflection_glossy_tex = FStormBitmap()
                MAT_NODE_NAME.reflection_glossy_tex.name = ("Glossiness")
                MAT_NODE_NAME.reflection_glossy_tex.filename = "TEX_GLOSS"
                MAT_NODE_NAME.reflection_glossy_tex.gamma = linearGamma
                MAT_NODE_NAME.reflection_glossy_tex.type = 1
            )
        )
        
        if doesFileExist "TEX_METALNESS" do (
            MAT_NODE_NAME.ior_tex = FStormBitmap()
            MAT_NODE_NAME.ior_tex.name = ("Metalness")
            MAT_NODE_NAME.ior_tex.filename = "TEX_METALNESS"
            MAT_NODE_NAME.ior_tex.gamma = linearGamma
            MAT_NODE_NAME.refl_glossy_angle = 1
        )

        if doesFileExist "TEX_OPACITY" do (
            MAT_NODE_NAME.opacity_tex = FStormBitmap()
            MAT_NODE_NAME.opacity_tex.name = ("Opacity")
            MAT_NODE_NAME.opacity_tex.filename = "TEX_OPACITY"
            MAT_NODE_NAME.opacity_tex.gamma = linearGamma
            MAT_NODE_NAME.opacity_tex.type = 1
        )
        
        if doesFileExist "TEX_TRANSLUCENCY" then
        (
            MAT_NODE_NAME.translucence_tex = FStormBitmap()
            MAT_NODE_NAME.translucence_tex.name = ("Translucency")
            MAT_NODE_NAME.translucence_tex.filename = "TEX_TRANSLUCENCY"
            MAT_NODE_NAME.translucence_tex.gamma = colorGamma
            MAT_NODE_NAME.traslucence_level = 0.45
            MAT_NODE_NAME.double_sided = on
        )
        else if doesFileExist "TEX_TRANSMISSION" then
        (
            MAT_NODE_NAME.translucence_tex = FStormBitmap()
            MAT_NODE_NAME.translucence_tex.name = ("Transmission")
            MAT_NODE_NAME.translucence_tex.filename = "TEX_TRANSMISSION"
            MAT_NODE_NAME.translucence_tex.gamma = linearGamma
        )

        --Index of Refraction
        MAT_NODE_NAME.ior = 1.5

        if doesFileExist "TEX_NORMAL" do (
            MAT_NODE_NAME.bump_texture = FStormBitmap()
            MAT_NODE_NAME.bump_texture.name = ("Normal")
            MAT_NODE_NAME.bump_texture.filename = "TEX_NORMAL"
            MAT_NODE_NAME.bump_texture.gamma = linearGamma
            MAT_NODE_NAME.bump_texture.normal_map = on
            MAT_NODE_NAME.bump_texture_amount = 10
        )
        
        --Bump
        if doesFileExist "TEX_BUMP" do
        (
            BumpNode = FStormBitmap ()
            BumpNode.gamma = linearGamma
            BumpNode.filename =("TEX_BUMP")
            BumpNode.name = ("Bump")
            ActiveSMEView.CreateNode BumpNode [-300, 700]
        )
        
        --Cavity
        if doesFileExist "TEX_CAVITY" do
        (
            CavityNode = FStormBitmap ()
            CavityNode.gamma = linearGamma
            CavityNode.filename =("TEX_CAVITY")
            CavityNode.name = ("CAVITY")
            ActiveSMEView.CreateNode CavityNode [-300, 800]
        )
        --Fuzz
        if doesFileExist "TEX_FUZZ" do
        (
            FuzzNode = FStormBitmap ()
            FuzzNode.gamma = linearGamma
            FuzzNode.filename =("TEX_FUZZ")
            FuzzNode.name = ("Fuzz")
            ActiveSMEView.CreateNode FuzzNode [-300, 900]
        )

        """).replace("--Displacement", DisplacementNode).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName)

    def GetGlassMaterial(self, nodeName, matName):
        return ("""

        MAT_NODE_NAME = FStorm()
        MAT_NODE_NAME.name = "MS_MATNAME"

        if doesFileExist "TEX_ROUGHNESS" then (
            MAT_NODE_NAME.reflection_glossy_tex = FStormBitmap()
            MAT_NODE_NAME.reflection_glossy_tex.name = ("Glossiness")
            MAT_NODE_NAME.reflection_glossy_tex.filename = "TEX_ROUGHNESS"
            MAT_NODE_NAME.reflection_glossy_tex.gamma = linearGamma
            MAT_NODE_NAME.reflection_glossy_tex.type = 1
            MAT_NODE_NAME.reflection_glossy_tex.inverted = on
        )
        else (
            if doesFileExist "TEX_GLOSS" then (
                MAT_NODE_NAME.reflection_glossy_tex = FStormBitmap()
                MAT_NODE_NAME.reflection_glossy_tex.name = ("Glossiness")
                MAT_NODE_NAME.reflection_glossy_tex.filename = "TEX_GLOSS"
                MAT_NODE_NAME.reflection_glossy_tex.gamma = linearGamma
                MAT_NODE_NAME.reflection_glossy_tex.type = 1
            )
        )

        if doesFileExist "TEX_NORMAL" do (
            MAT_NODE_NAME.bump_texture = FStormBitmap()
            MAT_NODE_NAME.bump_texture.name = ("Normal")
            MAT_NODE_NAME.bump_texture.filename = "TEX_NORMAL"
            MAT_NODE_NAME.bump_texture.gamma = linearGamma
            MAT_NODE_NAME.bump_texture.normal_map = on
            MAT_NODE_NAME.bump_texture_amount = 10
        )

        MAT_NODE_NAME.Diffuse = color 0 0 0
        MAT_NODE_NAME.opacity = 0
        MAT_NODE_NAME.refl_glossiness = 0.96

        """).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName)
    
    def AddGamma(self):
        return ("""

        colorGamma = 1.0
        linearGamma = 2.2

        """)