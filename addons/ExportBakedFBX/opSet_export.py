
#
# FBX出力する機能を定義するモジュール
#

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


from . import bake_proc
from .opSet_base import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.bakebfbx_export"
		bl_label = "Export Baked Anim FBX"
		bl_options = {'UNDO', 'PRESET'}

		filename_ext = ".fbx"
		filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

		filepath: StringProperty(subtype="FILE_PATH")
		filename: StringProperty()
		directory: StringProperty(subtype="FILE_PATH")

		def execute(self, context):
#			if bpy.data.is_dirty : return {'CANCELLED'}
			
			# ここに来た時点で、ファイル選択ウィンドウでのプロパティ変更が掛かっている場合がある
			# invokeが呼ばれた時点でファイル変更は保存済みのはずなので、プロパティ変更がある場合
			# はそれも保存しておく
			if bpy.data.is_dirty :
				bpy.ops.wm.save_mainfile()

			param = context.scene.export_baked_fbx_property
			
			if not self.filepath.endswith(".fbx") :
				self.report({'WARNING'},'The extension must be .fbx')
				return {'CANCELLED'}
			if bake_proc.export( self, context, self.filepath, param.export_anim_type ):
				return {'FINISHED'}
			"""
			self.report(
				{'INFO'},
				"[FilePath] %s, [FileName] %s, [Directory] %s"
				% (self.filepath, self.filename, self.directory)
			)
			"""
			return {'CANCELLED'}

		def invoke(self, context, event):
			if bpy.data.is_dirty :
				self.report({'WARNING'},'Please save before export')
				return {'CANCELLED'}
			context.window_manager.fileselect_add(self)
			return {'RUNNING_MODAL'}
		
		def draw(self, context):
			layout = self.layout
			param = context.scene.export_baked_fbx_property

			col = layout.column()
			col.prop(param, "export_anim_type")


	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.OpImpl,
		)

		# Global保存パラメータを定義
		prm_anim_type = EnumProperty(
			name="Animation",
			description="Animation Export Target",
			items=[
				('ActiveNLA', "Active NLA", "Active NLA"),
				('AllNLA', "All NLA", "All NLA"),
				('AllActions', "All Actions", "All Actions")
			],
			default='ActiveNLA'
		)
		props.export_anim_type: prm_anim_type
		props.__annotations__["export_anim_type"] = prm_anim_type


	# プラグインをインストールしたときの処理
	def register(self):
		super().register()
		bpy.types.TOPBAR_MT_file_export.append(OperatorSet._menu_func)

	# プラグインをアンインストールしたときの処理
	def unregister(self):
		bpy.types.TOPBAR_MT_file_export.remove(OperatorSet._menu_func)
		super().unregister()

	# メニューを登録する関数
	def _menu_func(self, context):
		self.layout.operator( OperatorSet.OpImpl.bl_idname, text="Baked FBX (.fbx)" )

