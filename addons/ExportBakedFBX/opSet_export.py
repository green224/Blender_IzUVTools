
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
		bl_idname = "object.ebfbx_export"
		bl_label = "Export Baked Anim FBX"
		bl_options = {'UNDO', 'PRESET'}

		filename_ext = ".fbx"
		filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

		filepath: StringProperty(subtype="FILE_PATH")
		filename: StringProperty()
		directory: StringProperty(subtype="FILE_PATH")

		def execute(self, context):
			if bpy.data.is_dirty : return {'CANCELLED'}
			if not self.filepath.endswith(".fbx") :
				self.report({'WARNING'},'The extension must be .fbx')
				return {'CANCELLED'}
			if bake_proc.export( self, context, self.filepath ): return {'FINISHED'}
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

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.OpImpl,
		)

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

