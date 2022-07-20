
#
# UVの接続エッジ部分を、テクスチャが完全につながるように補正する機能。
# 接続エッジの可視化も行う。
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
		FloatVectorProperty,
		)

import gpu
import bgl
from gpu_extras.batch import batch_for_shader
from gpu_extras.presets import draw_circle_2d


from .opSet_base import *
from .common_uv import *


#-------------------------------------------------------

# 機能本体
class OperatorSet(OperatorSet_Base):

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_edge_sync_uv"
		bl_label = "Iz Tools: UV: Edge Sync"
		bl_options = {'REGISTER', 'UNDO'}

		def execute(self, context):
			if context.area.type != 'IMAGE_EDITOR': return {'CANCELLED'}

			# 選択エッジ一覧を取得
			bmList = getEditingBMeshList()
			bMeshes = [bm for _,bm in bmList]
			selUVs = OperatorSet._getSelectedUVs(bMeshes)

			# 選択中エッジに対応する非選択エッジがない場合は、何もしない
			if len(selUVs) == 0: return {'CANCELLED'}

			# PixelCenterFitの場合は、この操作でもそれを適応するために、
			# 表示画像から解像度を取得しておく
			imgSize = None
			imgEditor = context.area.spaces[0]
			if imgEditor.uv_editor and imgEditor.uv_editor.pixel_snap_mode == "CENTER":
				if imgEditor.image:
					imgSize = Vector((
						imgEditor.image.size[0],
						imgEditor.image.size[1]
					))

			# まず、操作対象エッジの中心位置と、
			# 操作対象エッジが参照元エッジをどれだけ回転させたものに一致
			# させる必要があるかを求める。
			srcCenter = Vector((0, 0))
			dstCenter = Vector((0, 0))
			aglCnt = [0, 0, 0, 0]
			for (srcUV0, srcUV1, dstUV0, dstUV1) in selUVs:
				sUV0 = srcUV0.uv
				sUV1 = srcUV1.uv
				dUV0 = dstUV0.uv
				dUV1 = dstUV1.uv

				srcDUV = sUV1 - sUV0
				dstDUV = dUV1 - dUV0
				srcDir = srcDUV.normalized()
				dstDir = dstDUV.normalized()

				# 90度ごとに回転したときの方向と内積をとる
				d0 = dstDir.dot( srcDir )
				d90 = dstDir.dot( Vector(( -srcDir.y, srcDir.x )) )
				d180 = dstDir.dot( Vector(( -srcDir.x, -srcDir.y )) )
				d270 = dstDir.dot( Vector(( srcDir.y, -srcDir.x )) )

				# 尤もらしい方向をカウント
				agl = 0
				if d0 < d90:
					if d90 < d180:
						agl = 3 if d180 < d270 else 2
					else:
						agl = 3 if d90 < d270 else 1
				else:
					if d0 < d180:
						agl = 3 if d180 < d270 else 2
					else:
						agl = 3 if d0 < d270 else 0

				aglCnt[agl] = aglCnt[agl] + 1

				# 中央位置計算
				srcCenter += sUV0 + sUV1
				dstCenter += dUV0 + dUV1

			# 最も数の多い角度を、回転角度とする
			agl = 0
			if aglCnt[0] < aglCnt[1]:
				if aglCnt[1] < aglCnt[2]:
					agl = 3 if aglCnt[2] < aglCnt[3] else 2
				else:
					agl = 3 if aglCnt[1] < aglCnt[3] else 1
			else:
				if aglCnt[0] < aglCnt[2]:
					agl = 3 if aglCnt[2] < aglCnt[3] else 2
				else:
					agl = 3 if aglCnt[0] < aglCnt[3] else 0
				
			# ここで得られた角度で回転を行う処理
			def rotDstPos(pos):
				if agl == 1:
					return Vector(( -pos.y, pos.x ))
				elif agl == 2:
					return Vector(( -pos.x, -pos.y ))
				elif agl == 3:
					return Vector(( pos.y, -pos.x ))
				return pos

			# 中央位置を算出
			srcCenter /= (aglCnt[0] + aglCnt[1] + aglCnt[2] + aglCnt[3]) * 2
			dstCenter /= (aglCnt[0] + aglCnt[1] + aglCnt[2] + aglCnt[3]) * 2

			# ピクセル内位置を考慮した、操作先中央位置を計算
			resultDstCenter = dstCenter
			if imgSize:
				# 参照元中央位置のテクセル内座標を得る
				srcCenterInTexel = Vector((
					frac( srcCenter.x * imgSize.x ),
					frac( srcCenter.y * imgSize.y )
				))

				# 操作対象の処理結果の中央位置テクセル内座標を得る
				dstCenterInTexel = rotDstPos(srcCenterInTexel - Vector((0.5, 0.5)))
				dstCenterInTexel = Vector((
					frac( saturate(dstCenterInTexel.x + 0.5) ),
					frac( saturate(dstCenterInTexel.y + 0.5) )
				))
				resultDstCenter = Vector((
					(math.floor(dstCenter.x * imgSize.x) + dstCenterInTexel.x) / imgSize.x,
					(math.floor(dstCenter.y * imgSize.y) + dstCenterInTexel.y) / imgSize.y
				))

			# UVの変換テーブルを作成
			uvConvMap = []
			def findConvMap( uv ):		# UV変換テーブルからの取得処理
				for i in uvConvMap:
					if uv == i[0]: return i
				return None
			def addConvMap( src, dst ):	# UV変換テーブルへの追加処理
				if not findConvMap(src): uvConvMap.append( [src, dst] )

			for (srcUV0, srcUV1, dstUV0, dstUV1) in selUVs:
				sUV0 = srcUV0.uv
				sUV1 = srcUV1.uv
				dUV0 = dstUV0.uv
				dUV1 = dstUV1.uv

				# 中央位置からの差分位置
				c2s0 = sUV0 - srcCenter
				c2s1 = sUV1 - srcCenter
				c2d0 = rotDstPos(c2s0)
				c2d1 = rotDstPos(c2s1)

				# 操作対象UVの変換先を決定
				resultUV0 = resultDstCenter + c2d0
				resultUV1 = resultDstCenter + c2d1

				# UV変換テーブルへ追加
				addConvMap( dUV0, resultUV0 )
				addConvMap( dUV1, resultUV1 )

			# UV変換テーブルにしたがって、UVを更新
			convLst = []
			for bm in bMeshes:
				uv_layer = bm.loops.layers.uv.active
				for face in bm.faces:
					for loop in face.loops:
						uv = loop[uv_layer]

						a = findConvMap(uv.uv)
						if a: convLst.append((uv, a[1]))
			for i in convLst: i[0].uv = i[1]

			# BMeshを反映
			for mesh,_ in bmList:
				bmesh.update_edit_mesh(mesh)
			
			return {'FINISHED'}
		
	# UIパネル描画部分
	class UI_PT_Izt_UV_Edge_Sync(OperatorSet_Base.Panel_Base):
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		header_name = "Edge Sync"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()

			row = column.row()
			param = context.scene.iz_uv_tool_property
			row.prop(param, "edge_sync_color")

# ライン描画ではなぜかブレンドモードを変更できず、α合成もできないので、このプロパティは非表示
#			row = column.row()
#			row.prop(param, "edge_sync_alpha", slider=True)

			row = column.row()
			row.operator(OperatorSet.OpImpl.bl_idname, text="Sync")

	# プラグインをインストールしたときの処理
	def register(self):
		cls = OperatorSet
		super().register()

		# 描画処理を登録
		cls.__drawHdl = bpy.types.SpaceImageEditor.draw_handler_add(
			cls.__draw, (), 'WINDOW', 'POST_VIEW' )

	# プラグインをアンインストールしたときの処理
	def unregister(self):
		cls = OperatorSet

		# 描画処理の登録を解除
		bpy.types.SpaceImageEditor.draw_handler_remove(
			cls.__drawHdl, 'WINDOW' )
		cls.__drawHdl = None

		super().unregister()

	# ショートカット登録処理
	def register_shortcut(self, kc):
		km = kc.keymaps.new(
			"Image Generic",
			space_type='IMAGE_EDITOR',
			region_type='WINDOW'
		)
		kmi = km.keymap_items.new(
			OperatorSet.OpImpl.bl_idname,
			'K',
			'PRESS',
			shift=False,
			ctrl=False,
			alt=False
		)
		kmi.active = True
		return km, kmi



	# 描画ハンドラ
	__drawHdl = None

	# シェーダおよび描画用バッチ
	__shader = None

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_UV_Edge_Sync,
			OperatorSet.OpImpl,
		)

		# Global保存パラメータを定義
		prm_color = FloatVectorProperty(
			name="color",
			description="Edge Color",
			subtype="COLOR",
			default=[1,0.7,0],
            min=0, max=1,
		)
		prm_alpha = FloatProperty(
			name="alpha",
			description="Edge Alpha",
			default=0.7,
            min=0, max=1,
		)
		props.edge_sync_color: prm_color
		props.edge_sync_alpha: prm_alpha
		props.__annotations__["edge_sync_color"] = prm_color
		props.__annotations__["edge_sync_alpha"] = prm_alpha

	# 描画処理本体
	@classmethod
	def __draw(cls):
		context = bpy.context

		# シェーダおよび描画用バッチの初期化
		if cls.__shader is None:
			vertex_shader = '''
				// ModelViewProjectionMatrix : source/blender/gpu/shaders/gpu_shader_2D_vert.glsl
				uniform mat4 ModelViewProjectionMatrix;
				in vec2 uv;

				void main() {
					gl_Position = ModelViewProjectionMatrix * vec4(uv, 0.0, 1.0);
				}
			'''
			fragment_shader = '''
				uniform vec3 color;
				uniform float alpha;
				out vec4 FragColor;

				void main() {
					FragColor = vec4(color, alpha);
				}
			'''
			cls.__shader = gpu.types.GPUShader(vertex_shader, fragment_shader)

		bmList = getEditingBMeshList()

		# 移動などの編集とかち合うと、bMeshのreadonly参照を行うだけで
		# bMesh自体が破壊されるという不具合が起きる（多分バグ?）ので
		# ここでは毎回bMesh丸ごとコピーしたものを参照するようにする。
		bmList = [bm.copy() for _,bm in bmList]

		selUVs = cls._getSelectedUVs(bmList)

		# 選択中エッジに対応する非選択エッジがない場合は、何もしない
		if len(selUVs) != 0:

# ライン描画だとなぜかブレンドモードが利かない
#			fb = gpu.state.active_framebuffer_get()
#			gpu.state.blend_set("ADDITIVE")

			# レンダリング時のカラー
			param = context.scene.iz_uv_tool_property
			color = param.edge_sync_color
			alpha = param.edge_sync_alpha

			cls.__shader.bind()
			cls.__shader.uniform_float("color", color)
			cls.__shader.uniform_float("alpha", alpha)

			# バッチの生成
			uvs = []
			for (_, _, uv0, uv1) in selUVs:
				uvs.append([uv0.uv.x, uv0.uv.y])
				uvs.append([uv1.uv.x, uv1.uv.y])
			batch = batch_for_shader(
				cls.__shader, 'LINES',
				{"uv": uvs},
			)

			bgl.glLineWidth(3)
			batch.draw(cls.__shader)

		# バグるのを回避するためにコピーしたBMeshを開放
		for bm in bmList: bm.free()

	# 指定のBMeshリストから、選択中エッジLoopと、同じエッジを参照したLoopの組をリストアップする処理
	@staticmethod
	def _getSelectedUVs(bmList):
		result = []
		for bm in bmList:
			uv_layer = bm.loops.layers.uv.active

			# 現在選択中のエッジを得る
			for edge in bm.edges:
				isSelect = False
				selLoop = None
				srcUV0 = None
				srcUV1 = None
				for loop in edge.link_loops:
					srcUV0 = loop[uv_layer]
					srcUV1 = loop.link_loop_next[uv_layer]
					if srcUV0.select and srcUV1.select:
						isSelect = True
						selLoop = loop
						break

				if isSelect:
					#それぞれのエッジに対して、対応するエッジを抽出する
					for loop in edge.link_loops:
						dstUV1 = loop[uv_layer]
						dstUV0 = loop.link_loop_next[uv_layer]
						if not dstUV0.select or not dstUV1.select:
							result.append( (srcUV0, srcUV1, dstUV0, dstUV1) )

		return result


