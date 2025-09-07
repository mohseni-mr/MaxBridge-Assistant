import os, sys, json
import MSLiveLinkHelpers
helper = MSLiveLinkHelpers.LiveLinkHelper()

class OctaneSetup():

    def GetMaterialSetup(self, assetData):
        materialScript = helper.GetActiveSMEView()
        materialScript += self.createTransformNode(assetData.assetType)

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
                    materialScript += self.GetOpaqueMaterial(nodeName, matName, assetData.useDisplacement, assetData.assetType)
                materialScript += helper.AssignMaterialToMultiSlots(multiNodeName, nodeName, matData.matIDs)
                index += 1
            materialScript += helper.CreateNodeInSME(multiNodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(multiNodeName)
            materialScript += helper.ShowInViewport(multiNodeName)
        else:
            nodeName = "MatNode"
            materialScript += self.GetOpaqueMaterial(nodeName, assetData.materialName, assetData.useDisplacement, assetData.assetType)
            materialScript += helper.CreateNodeInSME(nodeName, 0, 0)
            materialScript += helper.AssignMaterialToObjects(nodeName)
            materialScript += helper.ShowInViewport(nodeName)
        
        materialScript += helper.RearrangeMaterialGraph()
        helper.DeselectEverything()
        return materialScript

    def GetOpaqueMaterial(self, nodeName, matName, useDisplacement, assetType):
        DisplacementNode = "--Displacement"
        
        if(useDisplacement and assetType not in ["3dplant"]):
            DisplacementNode = """ 
            --Displacement
            nodecheck = Displacement
            if displacementBitmap != undefined then (
                if doesFileExist displacementBitmap.fileName do
                (
                    if nodecheck != undefined do(
                        MAT_NODE_NAME.Displacement = Displacement()
                    )
                    
                    if nodecheck == undefined do(
                        MAT_NODE_NAME.Displacement =  Texture_displacement ()
                    )
                    
                    MAT_NODE_NAME.displacement.texture_input_type = 2
                    MAT_NODE_NAME.displacement.amount = 0.1
                    MAT_NODE_NAME.displacement.black_level = 0.5
                    MAT_NODE_NAME.displacement.texture_tex = Greyscale_image ()
                    MAT_NODE_NAME.displacement.texture_tex.gamma = 1.0
                    MAT_NODE_NAME.displacement.texture_tex.name = ("Displacement")
                    showTextureMap MAT_NODE_NAME MAT_NODE_NAME.displacement.texture_tex true
                    MAT_NODE_NAME.displacement.texture_tex.filename_bitmaptex = displacementBitmap
                    if useTransformNode do (
                        MAT_NODE_NAME.displacement.texture_tex.transform = TransformNode
                    )
                )
            )
            """
        
        return ("""

        MAT_NODE_NAME = universal_material()
        MAT_NODE_NAME.name = "MS_MATNAME"
        
        if albedoBitmap != undefined then (
            if doesFileExist albedoBitmap.fileName do
            (
                MAT_NODE_NAME.albedo_tex = RGB_image ()
                MAT_NODE_NAME.albedo_tex.gamma = 2.2
                MAT_NODE_NAME.albedo_tex.name = ("Albedo")
                MAT_NODE_NAME.albedo_input_type = 2
                MAT_NODE_NAME.albedo_tex.filename_bitmaptex = albedoBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.albedo_tex.transform = TransformNode
                )
            )
        )
        
        if metallicBitmap != undefined then (
            if doesFileExist metallicBitmap.fileName do
            (
                MAT_NODE_NAME.metallic_tex = Greyscale_image ()
                MAT_NODE_NAME.metallic_tex.gamma = 1.0
                MAT_NODE_NAME.metallic_tex.name = ("Metalness")
                MAT_NODE_NAME.metallic_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.metallic_tex true
                MAT_NODE_NAME.metallic_tex.filename_bitmaptex = metallicBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.metallic_tex.transform = TransformNode
                )
            )
        )
        
        if roughnessBitmap != undefined then (
            if doesFileExist roughnessBitmap.fileName then
            (
                MAT_NODE_NAME.roughness_tex = Greyscale_image ()
                MAT_NODE_NAME.roughness_tex.gamma = 1.0
                MAT_NODE_NAME.roughness_tex.name = ("Roughness")
                MAT_NODE_NAME.roughness_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.roughness_tex true
                MAT_NODE_NAME.roughness_tex.filename_bitmaptex = roughnessBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.roughness_tex.transform = TransformNode
                )
            )
        )
        else if glossBitmap != undefined then 
        (
            if doesFileExist glossBitmap.fileName then (
                MAT_NODE_NAME.roughness_tex = Greyscale_image ()
                MAT_NODE_NAME.roughness_tex.gamma = 1.0
                MAT_NODE_NAME.roughness_tex.name = ("Gloss")
                MAT_NODE_NAME.roughness_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.roughness_tex true
                MAT_NODE_NAME.roughness_tex.filename_bitmaptex = glossBitmap
                glossBitmap.output.invert = true
                if useTransformNode do (
                    MAT_NODE_NAME.roughness_tex.transform = TransformNode
                )
            )
        )
        
        if specularBitmap != undefined then (
            if doesFileExist specularBitmap.fileName then
            (
                MAT_NODE_NAME.specular_tex = RGB_image ()
                MAT_NODE_NAME.specular_tex.gamma = 2.2
                MAT_NODE_NAME.specular_tex.name = ("Specular")
                MAT_NODE_NAME.specular_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.specular_tex true
                MAT_NODE_NAME.specular_tex.filename_bitmaptex = specularBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.specular_tex.transform = TransformNode
                )
            )
        )
        
        if normalBitmap != undefined then (
            if doesFileExist normalBitmap.fileName do
            (
                MAT_NODE_NAME.normal_tex = RGB_image ()
                MAT_NODE_NAME.normal_tex.gamma = 1.0
                MAT_NODE_NAME.normal_tex.name = ("Normal")
                MAT_NODE_NAME.normal_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.normal_tex true
                MAT_NODE_NAME.normal_tex.filename_bitmaptex = normalBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.normal_tex.transform = TransformNode
                )
            )
        )

        --Displacement
        
        
        if opacityBitmap != undefined then (
            if doesFileExist opacityBitmap.fileName do
            (
                MAT_NODE_NAME.opacity_tex = Greyscale_image ()
                MAT_NODE_NAME.opacity_tex.gamma = 1.0
                MAT_NODE_NAME.opacity_tex.name = ("Opacity")
                MAT_NODE_NAME.opacity_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.opacity_tex true
                MAT_NODE_NAME.opacity_tex.filename_bitmaptex = opacityBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.opacity_tex.transform = TransformNode
                )
            )
        )

        if translucencyBitmap != undefined then (
            if doesFileExist translucencyBitmap.fileName then
            (
                MAT_NODE_NAME.transmission_tex = RGB_image ()
                MAT_NODE_NAME.transmission_tex.gamma = 2.2
                MAT_NODE_NAME.transmission_tex.name = ("Translucency")
                MAT_NODE_NAME.transmission_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.transmission_tex true
                MAT_NODE_NAME.transmission_tex.filename_bitmaptex = translucencyBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.transmission_tex.transform = TransformNode
                )
            )
        )
        
        
        else if transmissionBitmap != undefined then 
        (
            if doesFileExist transmissionBitmap.fileName then (
                MAT_NODE_NAME.transmission_tex = Greyscale_image ()
                MAT_NODE_NAME.transmission_tex.gamma = 1.0
                MAT_NODE_NAME.transmission_tex.name = ("Transmission")
                MAT_NODE_NAME.transmission_input_type = 2
                MAT_NODE_NAME.transmissionType = 1
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.transmission_tex true
                MAT_NODE_NAME.transmission_tex.filename_bitmaptex = transmissionBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.transmission_tex.transform = TransformNode
                )
            )
        )
         
          --Bump
        if bumpBitmap != undefined then (
            if doesFileExist bumpBitmap.fileName then
            (
                BumpNode = Greyscale_image ()
                BumpNode.gamma = 1.0
                BumpNode.filename_bitmaptex = bumpBitmap
                BumpNode.name = ("Bump")
                ActiveSMEView.CreateNode BumpNode [-300, 700]
            )
        )
        
         --Cavity
        if cavityBitmap != undefined then (
            if doesFileExist cavityBitmap.fileName then
            (
                CavityNode = Greyscale_image ()
                CavityNode.gamma = 1.0
                CavityNode.filename_bitmaptex = cavityBitmap
                CavityNode.name = ("Cavity")
                ActiveSMEView.CreateNode CavityNode [-300, 800]
            )
        )
        --Fuzz
        if fuzzBitmap != undefined then (
            if doesFileExist FuzzBitmap.fileName then
            (
                FuzzNode = Greyscale_image ()
                FuzzNode.gamma = 1.0
                FuzzNode.filename_bitmaptex = FuzzBitmap
                FuzzNode.name = ("Fuzz")
                ActiveSMEView.CreateNode FuzzNode [-300, 900]
            )
        )

        """).replace("--Displacement", DisplacementNode).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName)

    def GetGlassMaterial(self, nodeName, matName):
        return ("""

        MAT_NODE_NAME = specular_material()
        MAT_NODE_NAME.name = "MS_MATNAME"
        ActiveSMEView.CreateNode MAT_NODE_NAME [0, 600]

        if roughnessBitmap != undefined then (
            if doesFileExist roughnessBitmap.fileName then
            (
                MAT_NODE_NAME.roughness_tex = Greyscale_image ()
                MAT_NODE_NAME.roughness_tex.gamma = 1.0
                MAT_NODE_NAME.roughness_tex.name = ("Roughness")
                MAT_NODE_NAME.roughness_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.roughness_tex true
                MAT_NODE_NAME.roughness_tex.filename_bitmaptex = roughnessBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.roughness_tex.transform = TransformNode
                )
            )
        )
        else if glossBitmap != undefined then 
        (
            if doesFileExist glossBitmap.fileName then (
                MAT_NODE_NAME.roughness_tex = Greyscale_image ()
                MAT_NODE_NAME.roughness_tex.gamma = 1.0
                MAT_NODE_NAME.roughness_tex.name = ("Gloss")
                MAT_NODE_NAME.roughness_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.roughness_tex true
                MAT_NODE_NAME.roughness_tex.filename_bitmaptex = glossBitmap
                glossBitmap.output.invert = true
                if useTransformNode do (
                    MAT_NODE_NAME.roughness_tex.transform = TransformNode
                )
            )
        )

        if normalBitmap != undefined then (
            if doesFileExist normalBitmap.fileName do
            (
                MAT_NODE_NAME.normal_tex = RGB_image ()
                MAT_NODE_NAME.normal_tex.gamma = 1.0
                MAT_NODE_NAME.normal_tex.name = ("Normal")
                MAT_NODE_NAME.normal_input_type = 2
                showTextureMap MAT_NODE_NAME MAT_NODE_NAME.normal_tex true
                MAT_NODE_NAME.normal_tex.filename_bitmaptex = normalBitmap
                if useTransformNode do (
                    MAT_NODE_NAME.normal_tex.transform = TransformNode
                )
            )
        )

        MAT_NODE_NAME.index = 1.5
        MAT_NODE_NAME.fake_shadows = on
        MAT_NODE_NAME.thinWall = on


        """).replace("MAT_NODE_NAME", nodeName).replace("MS_MATNAME", matName)

    def createTransformNode(self, assetType):
        if assetType.lower() not in ["3dplant", "3d"] and False:
            return ("""
            for c in textureMap.classes do
            (
                if (c.category == #Octane)    then
                (
                    str = c as string
                    if (str == "2D_transformation") then class_2dTransform = c
                )
            )

            TransformNode = class_2dTransform()
            useTransformNode = True

            """)
        else:
            return ("""

            useTransformNode = False

            """)