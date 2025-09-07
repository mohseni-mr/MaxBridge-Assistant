import os, sys, json
import MSLiveLinkHelpers
helper = MSLiveLinkHelpers.LiveLinkHelper()

class ArnoldSetup():

    def GetMaterialSetup(self, assetData):
        #materialScript = helper.GetActiveSMEView()
        materialScript = ""
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
                    materialScript += self.GetOpaqueMaterial(nodeName, matName, assetData.useDisplacement, str(assetData.isSnow))
                materialScript += helper.AssignMaterialToMultiSlots(multiNodeName, nodeName, matData.matIDs)
                index += 1
            materialScript += helper.CreateNodeInSME(multiNodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(multiNodeName)
            materialScript += helper.ShowInViewport(multiNodeName)
        else:
            nodeName = "MatNode"
            materialScript += self.GetOpaqueMaterial(nodeName, assetData.materialName, assetData.useDisplacement, str(assetData.isSnow))
            materialScript += helper.CreateNodeInSME(nodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(nodeName)
            materialScript += helper.ShowInViewport(nodeName)
        
        helper.DeselectEverything()
        return materialScript

    def GetOpaqueMaterial(self, nodeName, matName, useDisplacement, snowCheck):
        
        DisplacementNode = "--Displacement"
        
        if(useDisplacement):
            DisplacementNode = """ 
        --Displacement
        if doesFileExist "TEX_DISPLACEMENT" do
        (
            mymod_.displacement_map = Bitmaptexture bitmap:displacementBitmap

            mymod_.displacement_map_on = on
            mymod_.enable_displacement_options = on
            mymod_.enable_subdivision_options = on
            mymod_.subdivision_iterations = 3
            mymod_.displacement_zero = 0.5
            mymod_.displacement_height = 5
            mymod_.displacement_enable_autobump = off
        )
        """
        
        return ("""
        --#########################################################################
        -- MATERIAL CREATION : Creates and sets up the material's base parameters. MS_MATNAME is replaced by the material's name.
        --#########################################################################

        MAT_NODE_NAME = ai_Standard_Surface()
        MAT_NODE_NAME.name = "MS_MATNAME"
        ActiveSMEView = sme.GetView (sme.activeView)
        ActiveSMEView.CreateNode mat [0, 0]
        
        if not getCommandPanelTaskMode() == "#modify" do
            SetCommandPanelTaskMode #modify
        
        
        mymod_ = ArnoldGeometryPropertiesModifier ()
        modPanel.addModToSelection (mymod_)
        
        --###########################################################
        -- TEXTURE ASSIGNMENT : Assigns all the existing textures to the corresponding slot in the material.
        --###########################################################

        --Albedo
        if doesFileExist "TEX_ALBEDO" do
        (
            MAT_NODE_NAME.base_color_shader = Bitmaptexture bitmap:albedoBitmap name:"Albedo"
        )

        --Roughness
        if doesFileExist "TEX_ROUGHNESS" then
        (
            MAT_NODE_NAME.specular_roughness_shader = Bitmaptexture bitmap:roughnessBitmap name:"Roughness"
        )
        else if doesFileExist "TEX_GLOSS" then
        (
            MAT_NODE_NAME.specular_roughness_shader = Bitmaptexture bitmap:glossBitmap name:"Gloss"
            MAT_NODE_NAME.specular_roughness_shader.output.invert = true
        )
        
        --Specular
        if doesFileExist "TEX_SPECULAR" do
        (
            MAT_NODE_NAME.specular_shader = Bitmaptexture bitmap:specularBitmap name:"Specular"
        )
        
        --Metalness
        if doesFileExist "TEX_METALNESS" do
        (
            MAT_NODE_NAME.metalness_shader = Bitmaptexture bitmap:metallicBitmap name:"Metalness"
        )

        --Normal
        if doesFileExist "TEX_NORMAL" do
        (
            normal_node = ai_normal_map()
            normal_node.input_shader = Bitmaptexture bitmap:normalBitmap name:"Normal"
            MAT_NODE_NAME.normal_shader = normal_node
        )
        
        --For Snow
        if SNOW_CHECK then
        (
            
            MAT_NODE_NAME.subsurface_scale = 0.1
            MAT_NODE_NAME.subsurface_type = 1
            MAT_NODE_NAME.subsurface_radius = color 102 127.5 153
            
            --if Transmission
            if doesFileExist "TEX_TRANSMISSION" do
            (
                -- MAT_NODE_NAME.subsurface = 0.5
                -- MAT_NODE_NAME.subsurface_color_shader = Bitmaptexture bitmap:transmissionBitmap name:"Transmission"
                MAT_NODE_NAME.subsurface_shader = Bitmaptexture bitmap:transmissionBitmap name:"Transmission"
                MAT_NODE_NAME.subsurface_color = color 255 255 255
                
                multiplyNode = RGB_Multiply()
                multiplyNode.map1 = Bitmaptexture bitmap:transmissionBitmap name:"Transmission"
                multiplyNode.color2 = color 64 64 64
                MAT_NODE_NAME.transmission_shader = multiplyNode
            )
            
            --if Translucency
            if doesFileExist "TEX_TRANSLUCENCY" do
            (
                -- MAT_NODE_NAME.subsurface = 0.5
                -- MAT_NODE_NAME.subsurface_color_shader = Bitmaptexture bitmap:translucencyBitmap name:"Translucency"
                MAT_NODE_NAME.subsurface_shader = Bitmaptexture bitmap:translucencyBitmap name:"Translucency"
                MAT_NODE_NAME.subsurface_color = color 255 255 255
                
                multiplyNode = RGB_Multiply()
                multiplyNode.map1 = Bitmaptexture bitmap:translucencyBitmap name:"Translucency"
                multiplyNode.color2 = color 64 64 64
                MAT_NODE_NAME.transmission_shader = multiplyNode
            )
            
            
        )
        else
        (
            --Translucency
            if doesFileExist "TEX_TRANSLUCENCY" do
            (
                MAT_NODE_NAME.subsurface_color_shader = Bitmaptexture bitmap:translucencyBitmap name:"Translucency"
                MAT_NODE_NAME.subsurface = 0.55
                MAT_NODE_NAME.exit_to_background = on
                MAT_NODE_NAME.thin_walled = on
            )

            --Transmission
            if doesFileExist "TEX_TRANSMISSION" do
            (
                MAT_NODE_NAME.transmission_shader = Bitmaptexture bitmap:transmissionBitmap name:"Transmission"
            )
        )
        

        --Opacity
        if doesFileExist "TEX_OPACITY" do
        (
            MAT_NODE_NAME.opacity_shader = Bitmaptexture bitmap:opacityBitmap name:"Opacity"

            mymod_.enable_general_options = on
            mymod_.opaque = off
            mymod_.double_sided = on
        )

        --Displacement 
        
        select CurOBJs
        for o in selection do o.material = MAT_NODE_NAME

        --Bump
        if doesFileExist "TEX_BUMP" do
        (
            myBmp = bitmaptexture filename:"TEX_BUMP"
            myBmp.name = ("Bump")
            ActiveSMEView.CreateNode myBmp [-300, 700]

        )
        
        --Cavity
        if doesFileExist "TEX_CAVITY" do
        (
            myBmp = bitmaptexture filename:"TEX_CAVITY"
            myBmp.name = ("Cavity") 
            ActiveSMEView.CreateNode myBmp [-300, 800]
     
        )
        --Fuzz
        if doesFileExist "TEX_FUZZ" do
        (
            myBmp = bitmaptexture filename:"TEX_FUZZ" 
            myBmp.name = ("Fuzz") 
            ActiveSMEView.CreateNode myBmp [-300, 900]
   
        )
        
        """).replace("--Displacement", DisplacementNode).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName).replace("SNOW_CHECK", snowCheck)

    def GetGlassMaterial(self, nodeName, matName):
        return ("""

        MAT_NODE_NAME = ai_Standard_Surface()
        MAT_NODE_NAME.name = "MS_MATNAME"
        MAT_NODE_NAME.transmission = 1
        
        --Roughness/Gloss
        if doesFileExist "TEX_ROUGHNESS" then
        (
            MAT_NODE_NAME.specular_roughness_shader = Bitmaptexture bitmap:roughnessBitmap name:"Roughness"
        )
        else if doesFileExist "TEX_GLOSS" then
        (
            MAT_NODE_NAME.specular_roughness_shader = Bitmaptexture bitmap:glossBitmap name:"Gloss"
            MAT_NODE_NAME.specular_roughness_shader.output.invert = true
        )

        --Normal
        if doesFileExist "TEX_NORMAL" do (
            normal_node = ai_normal_map()
            normal_node.input_shader = Bitmaptexture bitmap:normalBitmap name:"Normal"
            MAT_NODE_NAME.normal_shader = normal_node
        )


        """).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName)