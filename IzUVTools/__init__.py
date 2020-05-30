"""
UV展開用のこまごました機能集

ショートカットキー
	i: 選択頂点を整列
	j: 選択頂点を直線状にリラックス
"""


# プラグインに関する情報
bl_info = {
	"name" : "Iz UV tools",
	"author" : "Shu",
	"version" : (0,2),
    'blender': (2, 80, 0),
    "location": "UV Image Editor > Tools",
	"description" : "Add some tools of uv",
	"warning" : "",
	"wiki_url" : "",
	"tracker_url" : "",
	"category" : "UV"
}



if "bpy" in locals():
	import imp
	imp.reload(opSet_align)
	imp.reload(opSet_straight_relax)
from . import opSet_align
from . import opSet_straight_relax


import bpy
from mathutils import *
import math

from bpy.types import (
		Operator,
		Panel,
		PropertyGroup,
		OperatorFileListElement,
		)

from bpy.props import (
		BoolProperty,
		PointerProperty,
		StringProperty, 
		CollectionProperty,
		FloatProperty,
		EnumProperty,
		IntProperty,
		)


#-------------------------------------------------------

# Addon全体のGlobal保存パラメータ
class PR_IzUV(bpy.types.PropertyGroup):
	pass
PR_IzUV.__annotations__ = {}

classes = (
	PR_IzUV,
)

# 機能モジュールのインスタンス一覧
opSet_Insts = [
	opSet_align.OperatorSet(PR_IzUV),
	opSet_straight_relax.OperatorSet(PR_IzUV),
]


#-------------------------------------------------------

# ショートカットキー登録
addon_keymaps = []
def register_shortcut():
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		km = kc.keymaps.new(
			"Image Generic",
			space_type='IMAGE_EDITOR',
			region_type='WINDOW'
		)
		for ops in opSet_Insts:
			kmi = ops.register_shortcut(km)
			addon_keymaps.append((km, kmi))

# ショートカットキー登録解除
def unregister_shortcut():
    for km, kmi in addon_keymaps: km.keymap_items.remove(kmi)
    addon_keymaps.clear()


#-------------------------------------------------------

# プラグインをインストールしたときの処理
def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	for ops in opSet_Insts: ops.register()
	bpy.types.Scene.iz_uv_tool_property = bpy.props.PointerProperty(type=PR_IzUV)
	register_shortcut()

# プラグインをアンインストールしたときの処理
def unregister():
	unregister_shortcut()
	for ops in reversed(opSet_Insts): ops.unregister()
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.iz_uv_tool_property

if __name__ == "__main__":
	register()
