# -*- coding: utf-8 -*-

import bpy
import bmesh
from mathutils import *
D = bpy.data
C = bpy.context

print(D)

objs = set(bpy.context.selected_objects)

bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
uv_layer = bm.loops.layers.uv.active

for face in bm.faces:
    print(f"UVs in face {face.index}")

    for loop in face.loops:
        uv = loop[uv_layer]
        print(f"    - uv coordinate: {uv.uv}, selection status: {uv.select}, corresponding vertex ID: {loop.vert.index}, loop ID: {loop.index}")


