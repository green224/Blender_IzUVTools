"""
こまごました便利機能集

ショートカットキー
	UV展開用
		i: 選択頂点を整列
		j: 選択頂点を直線状にリラックス
"""


# プラグインに関する情報
bl_info = {
	"name" : "Iz Tools",
	"author" : "Shu",
	"version" : (0,10),
    'blender': (3, 2, 0),
    "location": "UV Image Editor > Tools, 3D View > Toolbox",
	"description" : "Add some tools of uv and bone and etc.",
	"warning" : "",
	"wiki_url" : "",
	"tracker_url" : "",
	"category" : "Object"
}



if "bpy" in locals():
	import imp
	imp.reload(common_uv)
	imp.reload(opSet_base)
	imp.reload(opSet_pose_keying_all)
	imp.reload(opSet_pose_trans_lock_all)
	imp.reload(opSet_edit_ctrl_vcol)
	imp.reload(opSet_uv_pixel_center_fit)
	imp.reload(opSet_uv_align)
	imp.reload(opSet_uv_straight_relax)
	imp.reload(opSet_uv_island_preview)
	imp.reload(opSet_uv_edge_sync)
	imp.reload(opSet_img_paint_brush)
	imp.reload(opSet_view3d_viewsel_flat)
from . import common_uv
from . import opSet_base
from . import opSet_pose_keying_all
from . import opSet_pose_trans_lock_all
from . import opSet_edit_ctrl_vcol
from . import opSet_uv_pixel_center_fit
from . import opSet_uv_align
from . import opSet_uv_straight_relax
from . import opSet_uv_island_preview
from . import opSet_uv_edge_sync
from . import opSet_img_paint_brush
from . import opSet_view3d_viewsel_flat


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
class PR_IzTools(bpy.types.PropertyGroup):
	pass
PR_IzTools.__annotations__ = {}

classes = (
	PR_IzTools,
)

# 機能モジュールのインスタンス一覧
opSet_Insts = [
	opSet_pose_keying_all.OperatorSet(PR_IzTools),
	opSet_pose_trans_lock_all.OperatorSet(PR_IzTools),
	opSet_edit_ctrl_vcol.OperatorSet(PR_IzTools),
	opSet_uv_pixel_center_fit.OperatorSet(PR_IzTools),
	opSet_uv_align.OperatorSet(PR_IzTools),
	opSet_uv_straight_relax.OperatorSet(PR_IzTools),
	opSet_uv_island_preview.OperatorSet(PR_IzTools),
	opSet_uv_edge_sync.OperatorSet(PR_IzTools),
	opSet_img_paint_brush.OperatorSet(PR_IzTools),
	opSet_view3d_viewsel_flat.OperatorSet(PR_IzTools),
]


#-------------------------------------------------------

# ショートカットキー登録
addon_keymaps = []
def register_shortcut():
	wm = bpy.context.window_manager
	kc = wm.keyconfigs.addon
	if kc:
		for ops in opSet_Insts:
			km, kmi = ops.register_shortcut(kc)
			if km != None: addon_keymaps.append((km, kmi))

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
	bpy.types.Scene.iz_uv_tool_property = bpy.props.PointerProperty(type=PR_IzTools)
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
