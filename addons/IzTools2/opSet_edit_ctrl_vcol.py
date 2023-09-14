
#
# 選択頂点の頂点カラーを単純に編集するパネル
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
		FloatVectorProperty,
		EnumProperty,
		IntProperty,
		)


from .opSet_base import *
from .common_uv import *

#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl_SetColor(Operator):
		bl_idname = "object.izt_edit_ctrl_vcol_set"
		bl_label = "Iz Tools: Edit: Control VCol: Set"
		bl_options = {'REGISTER', 'UNDO'}

		ch: EnumProperty(name="channel",
		   		default="R",
				items=[
				('R','R','R'),
				('G','G','G'),
				('B','B','B'),
				('A','A','A'),
				('All','All','All'),
				],
				options={'HIDDEN'})
		
		valR: FloatProperty(name="valueR",
		    	default=1.0,
				options={'HIDDEN'})
		valG: FloatProperty(name="valueG",
		    	default=1.0,
				options={'HIDDEN'})
		valB: FloatProperty(name="valueB",
		    	default=1.0,
				options={'HIDDEN'})
		valA: FloatProperty(name="valueA",
		    	default=1.0,
				options={'HIDDEN'})

		def execute(self, context):
			bmList = getEditingBMeshList()
			
			# 編集中のオブジェクトのBMeshごとに処理
			for _,bm in bmList:
				col_layer = bm.loops.layers.color.active

				# 頂点カラーが無い場合は何もしない
				if col_layer is None: return {'CANCELLED'}

				# 選択中頂点のカラーを設定
				for face in bm.faces:
					for loop in face.loops:
						if not loop.vert.select: continue
						col = loop[col_layer]

						if self.ch is "R": col.x = self.valR
						elif self.ch is "G": col.y = self.valG
						elif self.ch is "B": col.z = self.valB
						elif self.ch is "A": col.w = self.valA
						else:
							col.x = self.valR
							col.y = self.valG
							col.z = self.valB
							col.w = self.valA
						loop[col_layer] = col
			
			# BMeshを反映
			for mesh,_ in bmList:
				bmesh.update_edit_mesh(mesh)

			return {'FINISHED'}

	class OpImpl_SpoitColor(Operator):
		bl_idname = "object.izt_edit_ctrl_vcol_spoit"
		bl_label = "Iz Tools: Edit: Control VCol: Spoit"
		bl_options = {'REGISTER'}

		ch: EnumProperty(name="channel",
		   		default="R",
				items=[
				('R','R','R'),
				('G','G','G'),
				('B','B','B'),
				('A','A','A'),
				],
				options={'HIDDEN'})
		
		chVal: FloatProperty(name="value",
		    	default=1.0,
				options={'HIDDEN'})

		def execute(self, context):
			param = context.scene.iz_uv_tool_property

			if self.ch is "R":
				param.edit_ctrl_vcol_colR = self.chVal
			elif self.ch is "G":
				param.edit_ctrl_vcol_colG = self.chVal
			elif self.ch is "B":
				param.edit_ctrl_vcol_colB = self.chVal
			else:
				param.edit_ctrl_vcol_colA = self.chVal

			return {'FINISHED'}

	# UIパネル描画部分
	class UI_PT_Izt_Edit_Ctrl_VCol(OperatorSet_Base.Panel_Base):
		bl_space_type = "VIEW_3D"
		bl_region_type = "UI"
		bl_context = "mesh_edit"
		header_name = "Vertex Color"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()
			
			param = context.scene.iz_uv_tool_property

			# 編集中のオブジェクトのBMesh
			bm = bmesh.from_edit_mesh(bpy.context.active_object.data)

			# 移動などの編集とかち合うと、bMeshのreadonly参照を行うだけで
			# bMesh自体が破壊されるという不具合が起きる（多分バグ?）ので
			# ここでは毎回bMesh丸ごとコピーしたものを参照するようにする。
			bm = bm.copy()

			# 頂点カラーが無い場合は非表示
			col_layer = bm.loops.layers.color.active
			if col_layer is None: return

			# 選択中のカラーを取得
			isSelected = False
			col = None
			for face in bm.faces:
				for loop in face.loops:
					if not loop.vert.select: continue
					col = loop[col_layer]
					isSelected = True
					break
				if isSelected: break

			# 一つも頂点を選択していない場合は非表示
			if not isSelected: return


			# 選択頂点カラーのUI表示
			column.label(text = "Current:")
			row = column.row(align=True)
			op = row.operator(
				OperatorSet.OpImpl_SpoitColor.bl_idname,
				text = f"{col.x}")
			op.ch = "R"
			op.chVal = col.x
			op = row.operator(
				OperatorSet.OpImpl_SpoitColor.bl_idname,
				text = f"{col.y}")
			op.ch = "G"
			op.chVal = col.y
			op = row.operator(
				OperatorSet.OpImpl_SpoitColor.bl_idname,
				text = f"{col.z}")
			op.ch = "B"
			op.chVal = col.z
			op = row.operator(
				OperatorSet.OpImpl_SpoitColor.bl_idname,
				text = f"{col.w}")
			op.ch = "A"
			op.chVal = col.w

			layout.separator()

			# チャンネルごとの設定値と設定ボタンのUI表示
			column = layout.column(align=True)
			column.label(text = "Edit:")
			for ch in ["R","G","B","A"]:
				split = column.split(factor=0.7, align=True)
				split.prop(param, f"edit_ctrl_vcol_col{ch}", slider=True)
				split = split.split(factor=1.0, align=True)
				op = split.operator(
					OperatorSet.OpImpl_SetColor.bl_idname,
					text="Set")
				op.ch = ch
				op.valR = param.edit_ctrl_vcol_colR
				op.valG = param.edit_ctrl_vcol_colG
				op.valB = param.edit_ctrl_vcol_colB
				op.valA = param.edit_ctrl_vcol_colA

			# 全チャンネル設定ボタン
			column = layout.column()
			row = column.row()
			op = row.operator(
				OperatorSet.OpImpl_SetColor.bl_idname,
				text="Set RGBA")
			op.ch = "All"
			op.valR = param.edit_ctrl_vcol_colR
			op.valG = param.edit_ctrl_vcol_colG
			op.valB = param.edit_ctrl_vcol_colB
			op.valA = param.edit_ctrl_vcol_colA

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_Edit_Ctrl_VCol,
			OperatorSet.OpImpl_SetColor,
			OperatorSet.OpImpl_SpoitColor,
		)

		# Global保存パラメータを定義
		prm_colR = FloatProperty(
			name="R",
			default=1,
			min=0, max=1,
		)
		prm_colG = FloatProperty(
			name="G",
			default=1,
			min=0, max=1,
		)
		prm_colB = FloatProperty(
			name="B",
			default=1,
			min=0, max=1,
		)
		prm_colA = FloatProperty(
			name="A",
			default=1,
			min=0, max=1,
		)
		props.edit_ctrl_vcol_colR: prm_colR
		props.edit_ctrl_vcol_colG: prm_colG
		props.edit_ctrl_vcol_colB: prm_colB
		props.edit_ctrl_vcol_colA: prm_colA
		props.__annotations__["edit_ctrl_vcol_colR"] = prm_colR
		props.__annotations__["edit_ctrl_vcol_colG"] = prm_colG
		props.__annotations__["edit_ctrl_vcol_colB"] = prm_colB
		props.__annotations__["edit_ctrl_vcol_colA"] = prm_colA

