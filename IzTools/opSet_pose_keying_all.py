
#
# 選択ボーンのアニメ可能なプロパティに
# 自動でキーを打つする機能を定義するモジュール
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


from .opSet_base import *

#-------------------------------------------------------

# 指定のボーンにキーを打つ処理一式。is_removeがTrueの場合はキーを削除する
def keyingBone( bone, data_path, data_index, is_remove ):

	# 削除命令の場合は削除
	if is_remove:
		bone.keyframe_delete(data_path=data_path, group=bone.name, index=data_index)
		return

	# キーを追加
	bone.keyframe_insert(data_path=data_path, group=bone.name, index=data_index)

	# Fcurveを取得
	fcurves = bone.id_data.animation_data.action.fcurves
	fcurve = None
	raw_data_path = 'pose.bones["' + bone.name + '"].' + data_path
	for i in fcurves:
		if i.data_path != raw_data_path or i.array_index != data_index: continue
		fcurve = i
		break
	if fcurve == None: raise SystemError		# Fcurveが見つからないのは変

	# modifierが無ければ生成
	cyclesMod = None
	for mod in fcurve.modifiers:
		if mod.type != "CYCLES": continue
		cyclesMod = mod
		break
	if cyclesMod == None:
		fcurve.modifiers.new(type="CYCLES")


# 選択ボーンの固定されていないTransformにキーを打つ。
# 固定されているTransformについているキーは削除する
def keyingSelectBones():
	bones = bpy.context.selected_pose_bones
	for bone in bones:
		for i in range(3):
			keyingBone(bone, "location", i, bone.lock_location[i])
		if bone.rotation_mode != 'QUATERNION' and bone.rotation_mode != 'AXIS_ANGLE':
			for i in range(3):
				keyingBone(bone, "rotation_euler", i, bone.lock_rotation[i])
		for i in range(3):
			keyingBone(bone, "scale", i, bone.lock_scale[i])


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_pose_keying_all"
		bl_label = "Iz Tools: Pose: Keying all"
		bl_options = {'REGISTER', 'UNDO'}

		def execute(self, context):
			keyingSelectBones()
			return {'FINISHED'}

	# UIパネル描画部分
	class UI_PT_Izt_Pose_Keying_All(OperatorSet_Base.Panel_Base):
		bl_space_type = "VIEW_3D"
		bl_region_type = "UI"
		header_name = "Keying All"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()
			
			row = column.row()
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="Execute")

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_Pose_Keying_All,
			OperatorSet.OpImpl,
		)

