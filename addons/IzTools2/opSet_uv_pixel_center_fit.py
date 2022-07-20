
#
# UVのピクセル中央合わせオプションを
# ショートカットキーでON/OFFするための機能。
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
		FloatVectorProperty,
		)


from .opSet_base import *
from .common_uv import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_pixel_center_fit_uv"
		bl_label = "Iz Tools: UV: Pixel Center Fit"

		def execute(self, context):
			if context.area.type != 'IMAGE_EDITOR': return {'CANCELLED'}

			imgEditor = context.area.spaces[0]
			isCFit = OperatorSet._isCurrentCenterFit(context)
			if isCFit is not None:
				# SnapModeをCenterとDisableで切り替える
				if isCFit:	imgEditor.uv_editor.pixel_snap_mode = "DISABLED"
				else:		imgEditor.uv_editor.pixel_snap_mode = "CENTER"
				return {'FINISHED'}

			# UVEditorで画像読み込み済みでない場合は操作無効
			return {'CANCELLED'}
		
	# UIパネル描画部分
	class UI_PT_Izt_UV_Pixel_Center_Fit(OperatorSet_Base.Panel_Base):
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		header_name = "UV Snap Mode"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()

			isCFit = OperatorSet._isCurrentCenterFit(context)
			row = column.row()
			row.operator(
				OperatorSet.OpImpl.bl_idname,
				text = "Enabled" if isCFit else "Disabled",
				icon = "SNAP_ON" if isCFit else "SNAP_OFF" )
			row.enabled = isCFit is not None


	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_UV_Pixel_Center_Fit,
			OperatorSet.OpImpl,
		)

	# 現在PixelCenterFit状態か否かを取得する
	@staticmethod
	def _isCurrentCenterFit(context):
		imgEditor = context.area.spaces[0]
		if imgEditor.uv_editor and imgEditor.image:
			if imgEditor.uv_editor.pixel_snap_mode == "CENTER":
				return True
			else:
				return False
		return None


