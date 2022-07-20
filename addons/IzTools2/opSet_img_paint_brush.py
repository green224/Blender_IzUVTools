
#
# ImagePaintモードでのブラシの切り替え用ショートカット
#

import bpy
import bmesh
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


from .opSet_base import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_ip_brush_eraser"
		bl_label = "Iz Tools: ImagePaint: Eraser Brush"

		def execute(self, context):
			if context.object.mode != "TEXTURE_PAINT": return {'CANCELLED'}
			if context.area.type != 'IMAGE_EDITOR' and context.area.type != 'VIEW_3D': return {'CANCELLED'}

			brush = context.tool_settings.image_paint.brush
			if brush.blend == "MIX":
				brush.blend = "ERASE_ALPHA"
			elif brush.blend == "ERASE_ALPHA":
				brush.blend = "MIX"
			else:
				return {'CANCELLED'}

			return {'FINISHED'}

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.OpImpl,
		)

	# ショートカット登録処理
	def register_shortcut(self, kc):
		km = kc.keymaps.new(
			"Image Paint",
			space_type='EMPTY',
			region_type='WINDOW'
		)
		kmi = km.keymap_items.new(
			OperatorSet.OpImpl.bl_idname,
			'I',
			'PRESS',
			shift=False,
			ctrl=False,
			alt=False
		)
		kmi.active = True
		return km, kmi

