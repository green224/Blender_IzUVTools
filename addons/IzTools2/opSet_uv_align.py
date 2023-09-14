
#
# UV頂点を整列する機能を定義するモジュール
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
from .common_uv import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_align_uv"
		bl_label = "Iz Tools: UV: Align"
		bl_options = {'REGISTER', 'UNDO'}

		dir: EnumProperty(name="dirType",
				default="Auto",
				items=[
				('Auto','Auto','Auto'),
				('AutoWithDiag','AutoWithDiag','AutoWithDiag'),
				('-','-','-'),
				('|','|','|'),
				('/','/','/'),
				('\\','\\','\\'),
				],
				options={'HIDDEN'})

		def execute(self, context):
#			bpy.ops.object.mode_set(mode='OBJECT')
			self.proc( context.scene.iz_uv_tool_property )
#			bpy.ops.object.mode_set(mode='EDIT')
			return {'FINISHED'}

		def proc(self, param):
			bmList = getEditingBMeshList()
			uvVerts = getSelectedUVVerts( [bm for _,bm in bmList] )

			# PixelCenterFitか否か
			isPCFit = isPixelCenterFit(bpy.context)
			imgSize = getTexSizeOfImageEditor(bpy.context)

			# UV座標のみの処理用配列を生成
			uvLst = [i.uv.copy() for i,_ in uvVerts]

			# 画像読み込み済みの場合は、UVをピクセル座標に変換しておく
			if imgSize:
				uvLst = [Vector((i.x*imgSize.x, i.y*imgSize.y)) for i in uvLst]

			# 重複を除いたUV座標リスト
			dctUVs = []
			for i in uvLst:
				if (not i in dctUVs): dctUVs.append(i.copy())

			# 対象頂点が1以下の場合は何もしない
			if len(dctUVs) <= 1: return

			# 整列方向の自動算出の場合は、方向を決定する
			procDir = self.dir
			if (procDir == "Auto" or procDir == "AutoWithDiag"):
				procDir = getMostScatteredUVDir(dctUVs, procDir == "AutoWithDiag")

			# 斜め整列の場合は斜めに座標変換しておく
			if (procDir=="/" or procDir=="\\"):
				uvLst  = [Vector((i.x+i.y, i.y-i.x)) for i in uvLst]
				dctUVs = [Vector((i.x+i.y, i.y-i.x)) for i in dctUVs]

			# 整列方向に沿って、dctUVsをソートする
			procDirX = procDir=="-" or procDir=="/"
			if procDirX	: dctUVs.sort(key=lambda i: i.x)
			else		: dctUVs.sort(key=lambda i: i.y)

			# 元UVリストから、dctUVsのインデックスへのマップを構築
			src2dctMap = []
			for i in uvLst:
				src2dctMap.append( next(idx for idx,j in enumerate(dctUVs) if (j==i)) )

			# ここで中央を計算しておく
			center = getMinMaxUV(dctUVs)[3]

			# PixelCenterFitの場合は、予め整列垂直方向にCenterFitしておく
			if isPCFit:
				if procDir=="/":
					center.y = math.floor(center.y)
				elif procDir=="\\":
					center.x = math.floor(center.x)
				elif procDirX:
					center.y = math.floor(center.y) +0.5
				else:
					center.x = math.floor(center.x) +0.5

			# 頂点間距離を維持した形を計算する
			kpdUVs = [dctUVs[0].copy()]
			for i in range( 1, len(dctUVs) ):
				a = dctUVs[i-1]
				b = dctUVs[i]
				l = (b-a).length
				c = kpdUVs[i-1]
				if procDirX:	kpdUVs.append( Vector((c.x+l, a.y)) )
				else:			kpdUVs.append( Vector((a.x, c.y+l)) )
			delta = ( (kpdUVs[-1]-kpdUVs[0]) - (dctUVs[-1]-dctUVs[0]) ) / 2
			kpdUVs = [i-delta for i in kpdUVs]

			# パラメータに応じて頂点間を保つ形とそうでない形の間をとる
			kdRate = param.align_keep_dist_rate
			for i in range(len(dctUVs)):
				dctUVs[i] = dctUVs[i].lerp(kpdUVs[i], kdRate)

			# XもしくはYに整列処理
			if procDirX:
				for i in dctUVs: i.y = center.y
			else:
				for i in dctUVs: i.x = center.x

			# 斜め整列の場合は元の座標に座標変換して戻す
			if (procDir == "/" or procDir == "\\"):
				for i in dctUVs:
					x1 = (i.x - i.y)/2
					y1 = (i.x + i.y)/2
					i.x = x1
					i.y = y1
					
			# 元のUVに反映
			for idx,i in enumerate(uvVerts):
				uv = dctUVs[src2dctMap[idx]].copy()
				if imgSize:
					uv.x /= imgSize.x
					uv.y /= imgSize.y
				if isPCFit:
					uv.x = (math.floor(uv.x*imgSize.x) +0.5) /imgSize.x
					uv.y = (math.floor(uv.y*imgSize.y) +0.5) /imgSize.y
				i[0].uv = uv

			# BMeshを反映
			for obj,_ in bmList:
				bmesh.update_edit_mesh(obj.data)
		
	# UIパネル描画部分
	class UI_PT_Izt_UV_Align(OperatorSet_Base.Panel_Base):
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		header_name = "Align UV"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()
			
			row = column.row()
			param = context.scene.iz_uv_tool_property
			prop = row.prop(param, "align_keep_dist_rate", slider=True)

			column.separator()

			row = column.row()
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="|")
			prop.dir = "|"
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="---")
			prop.dir = "-"
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="/")
			prop.dir = "/"
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="\\")
			prop.dir = "\\"

			row = column.row()
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="Auto")
			prop.dir = "Auto"
			prop = row.operator(OperatorSet.OpImpl.bl_idname, text="Auto With Diag")
			prop.dir = "AutoWithDiag"

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_UV_Align,
			OperatorSet.OpImpl,
		)

		# Global保存パラメータを定義
		a = FloatProperty(
			name="keep uv distance",
			description="Keep the distance of uv location between vertices",
			default=1,
			min=0,
			max=1,
		)
		props.align_keep_dist_rate: a
		props.__annotations__["align_keep_dist_rate"] = a

	# ショートカット登録処理
	def register_shortcut(self, kc):
		km = kc.keymaps.new(
			"Image Generic",
			space_type='IMAGE_EDITOR',
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
		kmi.properties.dir = "Auto"
		kmi.active = True
		return km, kmi

