
#
# 選択ボーン全てのTransformのLock状態を一括変更するための機能。
# および回転モードの一括変更機能を定義するモジュール
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

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体:ロック状態設定
	class OpImpl_Lock(Operator):
		bl_idname = "object.izt_pose_tans_lock_all_lock"
		bl_label = "Iz Tools: Pose: Transform Lock All [Lock]"
		bl_options = {'REGISTER', 'UNDO'}

		tgt: EnumProperty(name="tgt",
				default="LocX",
				items=[
				('LocX','LocX',''),
				('LocY','LocY',''),
				('LocZ','LocZ',''),
				('RotX','RotX',''),
				('RotY','RotY',''),
				('RotZ','RotZ',''),
				('RotW','RotW',''),
				('Rot4D','Rot4D',''),
				('SclX','SclX',''),
				('SclY','SclY',''),
				('SclZ','SclZ',''),
				],
				options={'HIDDEN'})
		is_lock: BoolProperty(name="is lock", default=True, options={'HIDDEN'})

		def execute(self, context):
			bones = bpy.context.selected_pose_bones
			if self.tgt == 'LocX':
				for bone in bones:
					bone.lock_location[0] = self.is_lock
			elif self.tgt == 'LocY':
				for bone in bones:
					bone.lock_location[1] = self.is_lock
			elif self.tgt == 'LocZ':
				for bone in bones:
					bone.lock_location[2] = self.is_lock
			elif self.tgt == 'RotX':
				for bone in bones:
					bone.lock_rotation[0] = self.is_lock
			elif self.tgt == 'RotY':
				for bone in bones:
					bone.lock_rotation[1] = self.is_lock
			elif self.tgt == 'RotZ':
				for bone in bones:
					bone.lock_rotation[2] = self.is_lock
			elif self.tgt == 'RotW':
				for bone in bones:
					bone.lock_rotation_w = self.is_lock
			elif self.tgt == 'Rot4D':
				for bone in bones:
					bone.lock_rotations_4d = self.is_lock
			elif self.tgt == 'SclX':
				for bone in bones:
					bone.lock_scale[0] = self.is_lock
			elif self.tgt == 'SclY':
				for bone in bones:
					bone.lock_scale[1] = self.is_lock
			elif self.tgt == 'SclZ':
				for bone in bones:
					bone.lock_scale[2] = self.is_lock
			else:
				raise SystemError		#ここには来ないはず
			return {'FINISHED'}

	# オペレータ本体:回転モード設定
	class OpImpl_RotMode(Operator):
		bl_idname = "object.izt_pose_tans_lock_all_rotmode"
		bl_label = "Iz Tools: Pose: Transform Lock All [RotMode]"
		bl_options = {'REGISTER', 'UNDO'}

		def execute(self, context):
			param = context.scene.iz_uv_tool_property
			bones = bpy.context.selected_pose_bones
			for bone in bones:
				bone.rotation_mode = param.trans_rot_mode
			return {'FINISHED'}

	# UIパネル描画部分
	class UI_PT_Izt_Pose_Trans_Lock_All(OperatorSet_Base.Panel_Base):
		bl_space_type = "VIEW_3D"
		bl_region_type = "UI"
		header_name = "Transform Lock All"

		def draw(self, context):

			layout = self.layout
			column = layout.column()

			# 現在の選択状態を得るためのボーンを取得
			bones = bpy.context.selected_pose_bones
			if bones==None or len(bones)==0:
				row = column.row()
				row.label(text="No bone selected")
				return
			tgtBone = bones[0]

			# アイコン識別子を得るための処理
			def iconLock( isLock ):
				if isLock: return "LOCKED"
				return "UNLOCKED"
			
			# ロック状態変更用のボタンを表示する処理
			def drawLockModeBtn(layout, label, tgtMode, curValue):
				prop = layout.operator(OperatorSet.OpImpl_Lock.bl_idname, text=label, icon= iconLock(curValue))
				prop.tgt = tgtMode
				prop.is_lock = not curValue

			row = column.row()
			row.label(text="Location:")
			row = column.row()
			drawLockModeBtn(row, "X", "LocX", tgtBone.lock_location[0])
			drawLockModeBtn(row, "Y", "LocY", tgtBone.lock_location[1])
			drawLockModeBtn(row, "Z", "LocZ", tgtBone.lock_location[2])

			column.separator()

			row = column.row()
			row.label(text="Rotation:")
			row = column.row()
			drawLockModeBtn(row, "X", "RotX", tgtBone.lock_rotation[0])
			drawLockModeBtn(row, "Y", "RotY", tgtBone.lock_rotation[1])
			drawLockModeBtn(row, "Z", "RotZ", tgtBone.lock_rotation[2])
			row = column.row()
			drawLockModeBtn(row, "W", "RotW", tgtBone.lock_rotation_w)
			drawLockModeBtn(row, "4D", "Rot4D", tgtBone.lock_rotations_4d)

			column.separator()

			param = context.scene.iz_uv_tool_property
#			param.trans_rot_mode = tgtBone.rotation_mode
			row = column.row()
			row.prop(param, "trans_rot_mode")
			prop = row.operator(OperatorSet.OpImpl_RotMode.bl_idname, text="Set")

			column.separator()

			row = column.row()
			row.label(text="Scale:")
			row = column.row()
			drawLockModeBtn(row, "X", "SclX", tgtBone.lock_scale[0])
			drawLockModeBtn(row, "Y", "SclY", tgtBone.lock_scale[1])
			drawLockModeBtn(row, "Z", "SclZ", tgtBone.lock_scale[2])

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_Pose_Trans_Lock_All,
			OperatorSet.OpImpl_Lock,
			OperatorSet.OpImpl_RotMode,
		)

		# Global保存パラメータを定義
		a = EnumProperty(
			name="",
			description="tansform rotation mode for setting",
			default="YXZ",
			items=[
			('QUATERNION','QUATERNION',''),
			('XYZ','XYZ Euler',''),
			('XZY','XZY Euler',''),
			('YXZ','YXZ Euler',''),
			('YZX','YZX Euler',''),
			('ZXY','ZXY Euler',''),
			('ZYX','ZYX Euler',''),
			('AXIS_ANGLE','AXIS_ANGLE',''),
			]
		)
		props.trans_rot_mode: a
		props.__annotations__["trans_rot_mode"] = a
