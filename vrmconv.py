# Licnese under NYSL

import bpy
import sys
import os
import argparse

def mtoon_to_bsdf():
    materials = bpy.data.materials
    for material in materials:
        if not material.use_nodes :
            continue
        
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        main_texture = None
        normalmap_texture = None
        emission_texture = None
        material_output = None
        mtoon = None
        
        for node in nodes:
            if node.label == 'MainTexture':
                main_texture = node
            if node.label == 'NormalmapTexture':
                normalmap_texture = node
            if node.label == 'Emission_Texture':
                emission_texture = node
            if node.name == 'Material Output':
                material_output = node
            if node.name == 'Group' or 'グループ':
                mtoon = node

        if (not main_texture == None and
            not material_output == None and
            not mtoon == None):

            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.location = mtoon.location
            nodes.remove(mtoon)

            links.new(main_texture.outputs['Color'], bsdf.inputs['Base Color'])
            links.new(main_texture.outputs['Alpha'], bsdf.inputs['Alpha'])
            links.new(bsdf.outputs['BSDF'], material_output.inputs['Surface'])

            if(not normalmap_texture == None):
                links.new(normalmap_texture.outputs['Color'], bsdf.inputs['Normal'])
            if(not emission_texture == None):
                links.new(emission_texture.outputs['Color'], bsdf.inputs['Emission'])

def remove_trashes():
    if 'Colliders' in bpy.data.collections:
        colliders_collection = bpy.data.collections['Colliders']
        objects = colliders_collection.objects
        for object in objects:
            objects.unlink(object)
        bpy.data.collections.remove(colliders_collection)

    if 'secondary' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['secondary'])

def remove_root_bone():
    bpy.context.view_layer.objects.active = bpy.data.objects[bpy.data.armatures[0].name]
    bpy.ops.object.mode_set(mode='EDIT')
    armature = bpy.data.armatures[0]
    if 'Root' not in armature.bones:
        return
    root = armature.bones['Root']
    if root.parent != None:
        return
    if armature.edit_bones[0].name == 'Root':
        for child in root.children:
            print(child.name)
            armature.edit_bones[child.name].parent = None
    armature.edit_bones.remove(armature.edit_bones['Root'])
    bpy.ops.object.mode_set(mode='OBJECT')

def rename_bones():
    prefixes = ['J_Adj_', 'J_Bip_C_', 'J_Bip_', 'J_Sec_C_', 'J_Sec_']
    bones = bpy.data.armatures[0].bones
    
    chest = None
    upper_chest = None
    
    for bone in bones:
        for prefix in prefixes:
            if bone.name.startswith(prefix):
                bone.name = bone.name.replace(prefix, '')
        
        if bone.name == 'Chest':
            chest = bone
        if bone.name == 'UpperChest':
            upper_chest = bone
    
    if not chest == None and not upper_chest == None:
        upper_chest.name = '<NoIK>' + upper_chest.name

def cecil_rename_bones():
    bones = bpy.data.armatures[0].bones

    for bone in bones:
        # セシル変身
        if bone.name == 'MeRoot':
            bone.name = '<NoIK>MeRoot'
        if bone.name == 'Me_L':
            bone.name = '<NoIK>Me_L'
        if bone.name == 'Me_R':
            bone.name = '<NoIK>Me_R'
        if bone.name == 'LeftEyeRoot':
            bone.name = '<NoIK>LeftEyeRoot'
        if bone.name == 'RightEyeRoot':
            bone.name = '<NoIK>RightEyeRoot'
        if bone.name == 'LeftEye':
            bone.name = 'EyeL'
        if bone.name == 'RightEye':
            bone.name = 'EyeR'
            
def get_avatar_type():
    bones = bpy.data.armatures[0].bones
    for bone in bones:
        if(bone.name == "MeRoot"):
            return 'CECIL_HENSHIN'
    return 'VROID'

if '__main__' == __name__:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--fbx', required=False)
    parser.add_argument('--addonfile', required=False)
    
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    
    input = args.input
    output = args.output
    fbx = args.fbx
    addonfile = args.addonfile

    bpy.ops.preferences.addon_install(filepath=addonfile, overwrite = True)
    bpy.ops.preferences.addon_enable(module="VRM_Addon_for_Blender-release")
    bpy.ops.import_scene.vrm(filepath=input, extract_textures_into_folder=True)

    match(get_avatar_type()):
        case 'VROID':
            print('Running in VROID mode')
            remove_trashes()
            rename_bones()
            remove_root_bone()
            mtoon_to_bsdf()
        case 'CECIL_HENSHIN':
            print('Running in Cecil Henshin mode')
            cecil_rename_bones()
            mtoon_to_bsdf()

    if fbx:
        bpy.ops.export_scene.fbx(filepath=output, embed_textures=True, path_mode='COPY', object_types={'ARMATURE', 'MESH'}, global_scale=0.01)
    else:
        bpy.ops.export_scene.gltf(filepath=output)
