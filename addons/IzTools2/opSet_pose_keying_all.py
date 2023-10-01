
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

# 指定のボーンのFCurve取得処理
def getFCurve( bone, data_path, data_index ):
	raw_data_path = 'pose.bones["' + bone.name + '"].' + data_path

	if bone.id_data.animation_data is None: return None

	fcurves = bone.id_data.animation_data.action.fcurves
	for i in fcurves:
		if i.data_path != raw_data_path or i.array_index != data_index: continue
		return i
	
	return None

# 指定のボーンにキーを打つ処理一式。is_removeがTrueの場合はキーを削除する
def keyingBone( bone, data_path, data_index, is_remove ):

	fcurve = getFCurve(bone, data_path, data_index)

	# 削除命令の場合は削除
	if is_remove:
		if fcurve is not None:
			bone.id_data.animation_data.action.fcurves.remove(fcurve)
		return

	# キーが無ければ追加
	if fcurve is None:
		bone.keyframe_insert(data_path=data_path, group=bone.name, index=data_index)
		fcurve = getFCurve(bone, data_path, data_index)

	# modifierが無ければ生成
	cyclesMod = None
	for mod in fcurve.modifiers:
		if mod.type != "CYCLES": continue
		cyclesMod = mod
		break
	if cyclesMod == None:
		fcurve.modifiers.new(type="CYCLES")

# is_remove_list配列にしたがって、keyingBoneを呼び出す処理
def keyingBoneByRemoveList( bone, data_path, is_remove_array ):
	for index, is_remove in enumerate(is_remove_array):
		keyingBone( bone, data_path, index, is_remove )

# 選択ボーンの固定されていないTransformにキーを打つ。
# 固定されているTransformについているキーは削除する
def keyingSelectBones():
	bones = bpy.context.selected_pose_bones
	if bones is None: return
	for bone in bones:
		for i in range(3):
			keyingBone(bone, "location", i, bone.lock_location[i])

		euler_remove_array = None
		qua_remove_array = None
		axis_remove_array = None
		if bone.rotation_mode == 'QUATERNION':
			euler_remove_array = [ True, True, True ]
			qua_remove_array = [
				bone.lock_rotation[0], bone.lock_rotation[1], bone.lock_rotation[2],
				bone.lock_rotation_w ]
			axis_remove_array = [ True, True, True, True ]
		elif bone.rotation_mode == 'AXIS_ANGLE':
			euler_remove_array = [ True, True, True ]
			qua_remove_array = [ True, True, True, True ]
			axis_remove_array = [
				bone.lock_rotation[0], bone.lock_rotation[1], bone.lock_rotation[2],
				bone.lock_rotation_w ]
		else:
			euler_remove_array = [
				bone.lock_rotation[0], bone.lock_rotation[1], bone.lock_rotation[2] ]
			qua_remove_array = [ True, True, True, True ]
			axis_remove_array = [ True, True, True, True ]
		keyingBoneByRemoveList(bone, "rotation_euler", euler_remove_array)
		keyingBoneByRemoveList(bone, "rotation_quaternion", qua_remove_array)
		keyingBoneByRemoveList(bone, "rotation_axis_angle", axis_remove_array)

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

		isAllAction: BoolProperty(name="isAllAction",
		   		default=False,
				options={'HIDDEN'})

		def execute(self, context):
			if self.isAllAction == True:
				bones = bpy.context.selected_pose_bones
				if bones is None: return {'CANCELLED'}
				animData = bones[0].id_data.animation_data

				lastAction = animData.action
				for action in bpy.data.actions:
					animData.action = action
					keyingSelectBones()
				animData.action = lastAction
				
			else:
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
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="Current Action")
			prop.isAllAction = False
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="All Actions")
			prop.isAllAction = True

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_Pose_Keying_All,
			OperatorSet.OpImpl,
		)

