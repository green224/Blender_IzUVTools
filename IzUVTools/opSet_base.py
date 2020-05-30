
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
# Addonとしての1機能を定義するクラスの基底クラス
class OperatorSet_Base:

	# パネル定義クラスの基底クラス
	class Panel_Base(Panel):
		bl_label = " "
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		bl_category = "IzUVTools"

		def draw_header(self, _):
			layout = self.layout
			row = layout.row(align=True)
			row.label(text =self.header_name)
			

	# プラグインをインストールしたときの処理
	def register(self):
		for cls in self._classes:
			bpy.utils.register_class(cls)

	# プラグインをアンインストールしたときの処理
	def unregister(self):
		for cls in reversed(self._classes):
			bpy.utils.unregister_class(cls)


