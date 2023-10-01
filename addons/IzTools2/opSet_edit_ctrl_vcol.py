
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

# BMeshから選択中のカラーを取得する処理
def _getSelectedColorFromBMesh(bm):
	# 頂点カラーが無い場合は無効
	col_layer = bm.loops.layers.color.active
	if col_layer is None: return None

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
	if not isSelected: return None

	return col.copy()

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
		
		def execute(self, context):
			bmList = getEditingBMeshList()
			
			param = context.scene.iz_uv_tool_property
			valR = param.edit_ctrl_vcol_colR
			valG = param.edit_ctrl_vcol_colG
			valB = param.edit_ctrl_vcol_colB
			valA = param.edit_ctrl_vcol_colA
			strength = param.edit_ctrl_vcol_strength

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

						if self.ch == "R":
							col.x = lerp( col.x, valR, strength )
						elif self.ch == "G":
							col.y = lerp( col.y, valG, strength )
						elif self.ch == "B":
							col.z = lerp( col.z, valB, strength )
						elif self.ch == "A":
							col.w = lerp( col.w, valA, strength )
						else:
							col.x = lerp( col.x, valR, strength )
							col.y = lerp( col.y, valG, strength )
							col.z = lerp( col.z, valB, strength )
							col.w = lerp( col.w, valA, strength )
						loop[col_layer] = col
			
			# BMeshを反映
			for obj,_ in bmList:
				bmesh.update_edit_mesh(obj.data)

			return {'FINISHED'}

	class OpImpl_BakeLight(Operator):
		bl_idname = "object.izt_edit_ctrl_vcol_light"
		bl_label = "Iz Tools: Edit: Control VCol: Bake Light"
		bl_options = {'REGISTER', 'UNDO'}

		def execute(self, context):
			bmList = getEditingBMeshList()

			param = context.scene.iz_uv_tool_property
			strength = param.edit_ctrl_vcol_strength
			light = param.edit_ctrl_vcol_light
			lightScale = param.edit_ctrl_vcol_lightScale
			lightShadingMode = param.edit_ctrl_vcol_lightShadingMode

			# ライトが未選択の場合は何もしない
			if light is None: return {'CANCELLED'}

			# 陰影計算処理を定義
			calcLight = None
			def calcLightByDir(lightDir, nml):
				ret = -lightDir.dot(nml)	# 通常のランバート計算
				ret = lightScale * ret		# 任意の強度にスケールする
				ret = ret / 2 + 0.5			# ハーフランバートにする
				return saturate( ret )
			if light.data.type == "POINT":
				def calcLight(pos, nml):
					lightPos = light.matrix_world @ Vector()
					lightDir = (pos - lightPos).normalized()
					return calcLightByDir(lightDir, nml)
			elif light.data.type == "SUN":
				lightDir = light.matrix_world.to_3x3() @ Vector((0,0,-1))
				lightDir = lightDir.normalized()
				def calcLight(pos, nml):
					return calcLightByDir(lightDir, nml)
			else:
				return {'CANCELLED'}

			# 編集中のオブジェクトのBMeshごとに処理
			for obj,bm in bmList:
				col_layer = bm.loops.layers.color.active
				#normal_layer = bm.loops.layers.normal

				# 頂点カラーが無い場合は何もしない
				if col_layer is None: return {'CANCELLED'}

				# 法線変換用行列。L2Wの回転部分の逆転置行列
				l2w = obj.matrix_world
				nmlL2W = l2w.to_3x3().inverted_safe().transposed()

				# 選択中頂点のカラーを設定
				for face in bm.faces:
					for loop in face.loops:
						if not loop.vert.select: continue
						col = loop[col_layer]

						# 法線の取得。
						# 表示されている法線の取得はBlenderの仕様上とても大変で
						# 現状スマートに取得する方法が不明なので、とりあえずFlatとSmoothのみ
						if lightShadingMode == "SMOOTH":
							nml = loop.vert.normal
						else:
							nml = loop.face.normal
						#nml = loop[normal_layer]

						posW = l2w @ loop.vert.co
						nmlW = nmlL2W @ nml
						newCol = calcLight( posW, nmlW )

						col.x = lerp( col.x, newCol, strength )
						col.y = lerp( col.y, newCol, strength )
						col.z = lerp( col.z, newCol, strength )
						loop[col_layer] = col
			
			# BMeshを反映
			for obj,_ in bmList:
				bmesh.update_edit_mesh(obj.data)

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

			if self.ch == "R":
				param.edit_ctrl_vcol_colR = self.chVal
			elif self.ch == "G":
				param.edit_ctrl_vcol_colG = self.chVal
			elif self.ch == "B":
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

			# 選択中のカラーを取得
			col = _getSelectedColorFromBMesh(bm)

			# バグるのを回避するためにコピーしたBMeshを開放
			bm.free()
			bm = None

			# 選択中の頂点・頂点カラーが存在しない場合は何もしない
			if col is None: return


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

			# 強度スライダー
			column.prop(param, "edit_ctrl_vcol_strength", slider=True)

			# 全チャンネル設定ボタン
			column = layout.column()
			row = column.row()
			op = row.operator(
				OperatorSet.OpImpl_SetColor.bl_idname,
				text="Set RGBA")
			op.ch = "All"


			layout.separator()

			# ライトベイク
			column = layout.column(align=True)
			column.label(text = "Bake Light:")
			column.prop_search(param, "edit_ctrl_vcol_light", context.scene, "objects")
			column.prop(param, "edit_ctrl_vcol_lightShadingMode")

			# 強度スライダー
			column.prop(param, "edit_ctrl_vcol_lightScale")
			column.prop(param, "edit_ctrl_vcol_strength", slider=True)

			# ライトベイク実行ボタン
			column = layout.column()
			row = column.row()
			op = row.operator(
				OperatorSet.OpImpl_BakeLight.bl_idname,
				text="Bake")

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_Edit_Ctrl_VCol,
			OperatorSet.OpImpl_SetColor,
			OperatorSet.OpImpl_BakeLight,
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
		prm_strength = FloatProperty(
			name="Strength",
			default=1,
			min=0, max=1,
		)
		def lightPoll(self, object): return object.type == 'LIGHT'
		prm_light = PointerProperty(
			name="Light",
			type=bpy.types.Object,
			poll=lightPoll,
		)
		prm_lightScale = FloatProperty(
			name="Scale",
			default=1,
		)
		prm_lightShadingMode = EnumProperty(
			name="ShadingMode",
			default="SMOOTH",
			items=[
			('SMOOTH','Smooth','Smooth'),
			('FLAT','Flat','Flat'),
			],
		)
		props.edit_ctrl_vcol_colR: prm_colR
		props.edit_ctrl_vcol_colG: prm_colG
		props.edit_ctrl_vcol_colB: prm_colB
		props.edit_ctrl_vcol_colA: prm_colA
		props.edit_ctrl_vcol_strength: prm_strength
		props.edit_ctrl_vcol_light: prm_light
		props.edit_ctrl_vcol_lightScale: prm_lightScale
		props.edit_ctrl_vcol_lightShadingMode: prm_lightShadingMode
		props.__annotations__["edit_ctrl_vcol_colR"] = prm_colR
		props.__annotations__["edit_ctrl_vcol_colG"] = prm_colG
		props.__annotations__["edit_ctrl_vcol_colB"] = prm_colB
		props.__annotations__["edit_ctrl_vcol_colA"] = prm_colA
		props.__annotations__["edit_ctrl_vcol_strength"] = prm_strength
		props.__annotations__["edit_ctrl_vcol_light"] = prm_light
		props.__annotations__["edit_ctrl_vcol_lightScale"] = prm_lightScale
		props.__annotations__["edit_ctrl_vcol_lightShadingMode"] = prm_lightShadingMode

