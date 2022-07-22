
#
# ミップマップを考慮してバイリニアの隣接ピクセルの色吸い問題が起きないように
# エッジ拡張をすると、どれだけの広さになるかを可視化するモジュール。
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

	# 描画中か否か
	isRunning = False

	# オペレータ本体
	class OpImpl(Operator):
		bl_idname = "object.izt_island_preview_uv"
		bl_label = "Iz Tools: UV: Island Preview"

		def execute(self, context):
			if context.area.type == 'IMAGE_EDITOR':

				OperatorSet.isRunning = not OperatorSet.isRunning

				if context.area:
					context.area.tag_redraw()
				return {'FINISHED'}
			else:
				return {'CANCELLED'}
		
	# UIパネル描画部分
	class UI_PT_Izt_UV_Island_Preview(OperatorSet_Base.Panel_Base):
		bl_space_type = "IMAGE_EDITOR"
		bl_region_type = "UI"
		header_name = "Island Preview"

		def draw(self, context):
			layout = self.layout
			
			column = layout.column()

			row = column.row()
			param = context.scene.iz_uv_tool_property
			resoLevel = param.island_preview_reso_level
			row.label(text="resolution: " + str(2**resoLevel))

			row = column.row()
			row.prop(param, "island_preview_reso_level", slider=True)

			column.separator()

			row = column.row()
			row.prop(param, "island_preview_overlay_color")
			row = column.row()
			row.prop(param, "island_preview_fill_color_rate", slider=True)

			row = column.row()
			if OperatorSet.isRunning:
				row.operator(OperatorSet.OpImpl.bl_idname, text="Hide", icon="PAUSE")
			else:
				row.operator(OperatorSet.OpImpl.bl_idname, text="Show", icon="PLAY")

	# プラグインをインストールしたときの処理
	def register(self):
		cls = OperatorSet
		super().register()

		# 描画処理を登録
		cls.__hdl_drawOffsc = bpy.types.SpaceImageEditor.draw_handler_add(
			cls.__drawOffSc, (), 'WINDOW', 'PRE_VIEW' )
		cls.__hdl_drawImgEdt = bpy.types.SpaceImageEditor.draw_handler_add(
			cls.__drawImgEdt, (), 'WINDOW', 'POST_VIEW' )

	# プラグインをアンインストールしたときの処理
	def unregister(self):
		cls = OperatorSet

		# 描画処理の登録を解除
		bpy.types.SpaceImageEditor.draw_handler_remove(
			cls.__hdl_drawOffsc, 'WINDOW' )
		bpy.types.SpaceImageEditor.draw_handler_remove(
			cls.__hdl_drawImgEdt, 'WINDOW' )
		cls.__hdl_drawOffsc = None
		cls.__hdl_drawImgEdt = None

		super().unregister()


	# 描画ハンドラ
	__hdl_drawOffsc = None
	__hdl_drawImgEdt = None

	# 作業用オフスクリーンバッファ
	__offscreen0 = None
	__offscreen1 = None
	
	# シェーダおよび描画用バッチ
	__shader_Offsc = None
	__shader_ImgEdt = None
	__batch_ImgEdt = None


	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.UI_PT_Izt_UV_Island_Preview,
			OperatorSet.OpImpl,
		)

		# Global保存パラメータを定義
		prm_resoLv = IntProperty(
			name="reso level",
			description="Texture Resolution Level",
			default=8,
			min=4,
			max=12,
		)
		prm_overlayCol = FloatVectorProperty(
			name="overlay color",
			description="Island overlay Color",
			subtype="COLOR",
			default=[0,0.23,0.5],
            min=0, max=1,
		)
		prm_fillColRate = FloatProperty(
			name="fill color rate",
			description="Island fill Color Rate",
			default=0,
            min=0, max=1,
		)
		props.island_preview_reso_level: prm_resoLv
		props.island_preview_overlay_color: prm_overlayCol
		props.island_preview_fill_color_rate: prm_fillColRate
		props.__annotations__["island_preview_reso_level"] = prm_resoLv
		props.__annotations__["island_preview_overlay_color"] = prm_overlayCol
		props.__annotations__["island_preview_fill_color_rate"] = prm_fillColRate

	@classmethod
	def __drawOffSc(cls):
		if not cls.isRunning: return

		# シェーダおよび描画用バッチの初期化
		if cls.__shader_Offsc is None:
			vertex_shader = '''
				in vec2 uv;
				uniform float texSize;
				uniform vec2 pixelOffset;

				void main()
				{
					vec2 pos = uv + pixelOffset / texSize;
					gl_Position = vec4(pos*2-1, 0.0, 1.0);
				}
			'''
			fragment_shader = '''
				uniform vec4 color;

				out vec4 FragColor;

				void main()
				{
					FragColor = color;
				}
			'''
			cls.__shader_Offsc = gpu.types.GPUShader(vertex_shader, fragment_shader)

		# レンダリング先のテクスチャサイズ
		param = bpy.context.scene.iz_uv_tool_property
		texSize = 2 ** param.island_preview_reso_level
		overlayCol = param.island_preview_overlay_color

		# 作業用オフスクリーンバッファの作成
		if cls.__offscreen0 is None or cls.__offscreen0.width != texSize:
			if cls.__offscreen0 is not None:
				cls.__offscreen0.free()
				cls.__offscreen1.free()
			cls.__offscreen0 = gpu.types.GPUOffScreen(texSize, texSize)
			cls.__offscreen1 = gpu.types.GPUOffScreen(texSize, texSize)
		
		# バッチを作成
		bmList = getEditingBMeshList()
		bMeshes = [bm for _,bm in bmList]
		uvs = []
		indices_tri = []
		indices_line = []
		for bm in bMeshes:
			# 移動などの編集とかち合うと、bMeshのreadonly参照を行うだけで
			# bMesh自体が破壊されるという不具合が起きる（多分バグ?）ので
			# ここでは毎回bMesh丸ごとコピーしたものを参照するようにする。
			bm = bm.copy()

			uv_layer = bm.loops.layers.uv.active
			for face in bm.faces:
				i0 = len(uvs)
#					if len(face.loops) < 3: break	これは無くても一応大丈夫

				tris = [0,0,0]
				for loop in face.loops:
					uv = loop[uv_layer]

					i1 = len(uvs) - i0
					if i1 < 2:		# Triangleのシーケンスを格納
						tris[i1] = len(uvs)
					elif i1 == 2:
						tris[2] = len(uvs)
						indices_tri.append( tris )
					else:
						indices_tri.append( [i0, len(uvs)-1, len(uvs)] )
					if i1 != 0:		# Lineのシーケンスを格納
						indices_line.append( [len(uvs)-1, len(uvs)] )

					uvs.append( [ uv.uv.x, uv.uv.y ] )
#						if uv.select: result.append( (uv, loop.vert) )
				if len(uvs)-1 != i0:		# Lineのシーケンスが一つ足りてないので、最後の一つを格納
					indices_line.append( [len(uvs)-1, i0] )
			bm.free()
		batch_Tri = batch_for_shader(cls.__shader_Offsc, 'TRIS', {"uv": uvs}, indices=indices_tri)
		batch_Line = batch_for_shader(cls.__shader_Offsc, 'LINES', {"uv": uvs}, indices=indices_line)

		# オフスクリーンバッファへ描画
		ofsSize = 0.49
		pixelOffsets = [(-ofsSize,-ofsSize),(0,-ofsSize),(ofsSize,-ofsSize),(-ofsSize,0),(ofsSize,0),(-ofsSize,ofsSize),(0,ofsSize),(ofsSize,ofsSize)]
		with cls.__offscreen0.bind():
			fb = gpu.state.active_framebuffer_get()
			fb.clear(color=(0.0, 0.0, 0.0, 1.0), depth=1)

			gpu.state.face_culling_set("NONE")
			cls.__shader_Offsc.bind()
			cls.__shader_Offsc.uniform_float("texSize", texSize)
			cls.__shader_Offsc.uniform_float("color", (overlayCol[0],overlayCol[1],overlayCol[2],1))
			cls.__shader_Offsc.uniform_float("pixelOffset", (0,0))
			batch_Tri.draw(cls.__shader_Offsc)
			for pixelOfs in pixelOffsets:
				cls.__shader_Offsc.uniform_float("pixelOffset", pixelOfs)
				batch_Line.draw(cls.__shader_Offsc)


	@classmethod
	def __drawImgEdt(cls):
		if not cls.isRunning: return

		# シェーダおよび描画用バッチの初期化
		if cls.__shader_ImgEdt is None:
			vertex_shader = '''
				// ModelViewProjectionMatrix : source/blender/gpu/shaders/gpu_shader_2D_vert.glsl
				uniform mat4 ModelViewProjectionMatrix;

				in vec2 uv;
				out vec2 uvInterp;

				void main()
				{
					uvInterp = uv;
					gl_Position = ModelViewProjectionMatrix * vec4(uv, 0.0, 1.0);
				}
			'''
			fragment_shader = '''
				uniform sampler2D image;
				uniform float texSize;
				uniform float fillColRate;

				in vec2 uvInterp;
				out vec4 FragColor;

				vec4 fetchColor(vec2 offset) {
					// gpuモジュールにはフィルタリングの設定がないので
					// シェーダ側でポイントフィルタのように取得するように加工する
					return textureLod(
						image, (floor(uvInterp*texSize)+0.5+offset)/texSize, 0 );
				}
				bool isSame(vec4 c0, vec4 c1) {
					return c0.x==c1.x && c0.y==c1.y && c0.z==c1.z && c0.w==c1.w;
				}

				void main() {
					vec4 c0 = fetchColor(vec2(0,0));
					vec4 c1 = fetchColor(vec2(1,0));
					vec4 c2 = fetchColor(vec2(-1,0));
					vec4 c3 = fetchColor(vec2(0,1));
					vec4 c4 = fetchColor(vec2(0,-1));
					FragColor =
						isSame(c0,c1) && isSame(c0,c2) &&
						isSame(c0,c3) && isSame(c0,c4)
						? c0*fillColRate : c0;
				}
			'''
			cls.__shader_ImgEdt = gpu.types.GPUShader(vertex_shader, fragment_shader)
			cls.__batch_ImgEdt = batch_for_shader(
				cls.__shader_ImgEdt, 'TRI_FAN',
				{
					"uv": ((0, 0), (1, 0), (1, 1), (0, 1)),
				},
			)

		# レンダリング先のビューポートサイズ
		viewport = gpu.state.viewport_get()
		viewportW = viewport[2]-viewport[0]
		viewportH = viewport[3]-viewport[1]

		# レンダリング先のテクスチャサイズ
		param = bpy.context.scene.iz_uv_tool_property
		texSize = 2 ** param.island_preview_reso_level
		fillColRate = param.island_preview_fill_color_rate

		fb = gpu.state.active_framebuffer_get()
		gpu.state.blend_set("ADDITIVE")

		cls.__shader_ImgEdt.bind()
		cls.__shader_ImgEdt.uniform_sampler("image", cls.__offscreen0.texture_color)
# これが上手く適応できないので、とりあえずシェーダ側でむりやりポイントフィルタにする
#		bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)
#		bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
		cls.__shader_ImgEdt.uniform_float("texSize", texSize)
		cls.__shader_ImgEdt.uniform_float("fillColRate", fillColRate)
#		cls.__shader_ImgEdt.uniform_float("viewportSize", (viewportW, viewportH))
		cls.__batch_ImgEdt.draw(cls.__shader_ImgEdt)



