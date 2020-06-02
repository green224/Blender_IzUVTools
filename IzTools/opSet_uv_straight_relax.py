
#
# 直線的にUVリラックスを掛ける機能を定義するモジュール
#
# 複数頂点を選択して、その端にある2頂点を固定して
# 間の頂点を直線的に並べた状態でUVリラックスを行うという機能。
# 腕や足などのドラム缶状に展開したいUVに対して、決められた直線上にリラックスできるので便利。
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
from .common_uv import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_straight_relax_uv"
		bl_label = "Iz Tools: UV: Straight Relax"
		bl_options = {'REGISTER', 'UNDO'}

		def execute(self, context):
			bpy.ops.object.mode_set(mode='OBJECT')
			self.proc()
			bpy.ops.object.mode_set(mode='EDIT')
			return {'FINISHED'}

		# UV座標リストから、それらのUVがなんとなく並んでいる方向を計算する
		def calcLineupDir(self, uvs):

			# 2頂点に外接し、その中間点を中心とし、他の全ての頂点を内包するという円が
			# ある場合に、それが方向を定義する2頂点とする。
			# 無い場合は方向を定義できない。
			for i in range(len(uvs)):
				for j in range(i+1,len(uvs)):
					a = uvs[i]
					b = uvs[j]
					ctr = (a+b)/2
					rSqr = (a-ctr).length_squared

					isOk = True
					for k in range(len(uvs)):
						if k==i or k==j: continue

						if rSqr < ( uvs[k] - ctr ).length_squared:
							isOk = False
							break

					if isOk: return (a-b).normalized()

			# 方向が定義できない
			return None

		def proc(self):

			uvVerts = getSelectedUVVerts()

			# UV座標と頂点座標のみの処理用配列を生成
			uvLst = [(i.uv, j.co) for i,j in uvVerts]
			dctUVs = []			# 重複を除いたリスト
			for i in uvLst:
				if (not i in dctUVs): dctUVs.append((i[0].copy(), i[1].copy()))

			# 対象頂点が1以下の場合は何もしない
			if len(dctUVs) <= 1: return

			# 方向を決定する
			dir = self.calcLineupDir([i[0] for i in uvLst])
			if dir is None: return		#方向が定義できない

			# 整列方向に沿って、dctUVsをソートする
			dctUVs.sort(key=lambda i: i[0].dot(dir))

			# 元UVリストから、dctUVsのインデックスへのマップを構築
			src2dctMap = []
			for i in uvLst:
				src2dctMap.append( next(idx for idx,j in enumerate(dctUVs) if (j==i)) )

			# 頂点間距離を維持した形を計算する
			kpdUVs = [dctUVs[0][0]]
			for i in range( 1, len(dctUVs) ):
				a = dctUVs[i-1]
				b = dctUVs[i]
				l = (b[1]-a[1]).length
				c = kpdUVs[i-1]
				kpdUVs.append( c + dir*l )
			scl = (dctUVs[-1][0]-dctUVs[0][0]).length / (kpdUVs[-1]-kpdUVs[0]).length
			kpdUVs = [kpdUVs[0]+(i-kpdUVs[0])*scl for i in kpdUVs]

			# 元のUVに反映
			for idx,i in enumerate(uvVerts):
				i[0].uv = kpdUVs[src2dctMap[idx]]
		
	# UIパネル描画部分
	class UI_PT_Iz_UV_Straight_Relax(OperatorSet_Base.Panel_Base):
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		header_name = "Straight Relax UV"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()
			row = column.row()
			row.operator(OperatorSet.OpImpl.bl_idname, text="Execute")

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Iz_UV_Straight_Relax,
			OperatorSet.OpImpl,
		)

	# ショートカット登録処理
	def register_shortcut(self, keymap):
		kmi = keymap.keymap_items.new(
			OperatorSet.OpImpl.bl_idname,
			'J',
			'PRESS',
			shift=False,
			ctrl=False,
			alt=False
		)
		kmi.active = True
		return kmi

