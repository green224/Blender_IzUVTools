
#
# 選択した頂点群を平面的に見るようにViewを移動する
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
		bl_idname = "view3d.izt_view_selected_flat"
		bl_label = "Iz Tools: View3D: View selected flat"
#		bl_options = {}

		def execute(self, context):

			# 選択中の頂点などの位置リストを構築する
			tgtPosLst=[]
			if bpy.context.mode == "EDIT_ARMATURE":
				for obj in bpy.context.selected_objects:
					for bone in obj.data.edit_bones:
						if bone.select_head: tgtPosLst.append(bone.head)
						if bone.select_tail: tgtPosLst.append(bone.tail)
			elif bpy.context.mode == "POSE":
				for bone in bpy.context.selected_pose_bones:
					obj = bone.id_data
					posW = obj.matrix_world @ bone.matrix @ bone.location
					tgtPosLst.append( posW )
			elif bpy.context.mode == "EDIT_MESH":
				bmList = getEditingBMeshList()
				for _,bm in bmList:
					for v in bm.verts:
						if v.select == False: continue
						tgtPosLst.append( v.co )

			# 選択頂点群から面方向を得る
			a = self.calcFace(tgtPosLst)
			if a == None: return {'CANCELLED'}
			front, center = a

			# 面方向を向くようにしたカメラ行列を得る
			theta = math.atan2( front.x, front.y )
			phi = math.atan2( math.sqrt(front.x*front.x + front.y*front.y), front.z )
			eul = Euler( (phi+math.radians(180),theta,0), "XYZ" )
			eul = Euler( (phi+math.radians(180),0,theta), "ZYX" )
			mtx = eul.to_matrix()
#			print(front)
#			print(phi)
#			print(theta)

			# 3DViewのカメラに対して処理を行う
			for area in bpy.context.screen.areas:
				if area.type != "VIEW_3D": continue
				rv3d = area.spaces[0].region_3d
				if rv3d is None: continue
				rv3d.view_perspective = "PERSP"
				
				# 姿勢を反映
				m = rv3d.view_matrix.copy()
				m[0][0] = mtx[0][0]
				m[0][1] = mtx[0][1]
				m[0][2] = mtx[0][2]
				m[1][0] = mtx[1][0]
				m[1][1] = mtx[1][1]
				m[1][2] = mtx[1][2]
				m[2][0] = mtx[2][0]
				m[2][1] = mtx[2][1]
				m[2][2] = mtx[2][2]
				rv3d.view_matrix = m

				# 選択頂点が画面に含まれるようにフォーカス(位置移動)
				ctx = bpy.context.copy()
				ctx['area'] = area
				ctx['region'] = area.regions[-1]
				bpy.ops.view3d.view_selected(ctx)

			return {'FINISHED'}

		# 位置リストから、面方向と中心位置を算出する
		def calcFace(self, tgtPosLst):

			tLen = len(tgtPosLst)
			if tLen < 3: return None

			# 中心位置
			centerPos = Vector((0,0,0))
			for i in tgtPosLst: centerPos += i
			centerPos /= tLen

			# 面方向
			ret = None
			for i in range( tLen ):
				a = tgtPosLst[i] - centerPos
				for j in range( i+1, tLen ):
					b = tgtPosLst[j] - centerPos
					t = a.normalized().cross(b.normalized())
					
					if t.length < 0.001: continue
					if ret == None:
						ret = t
					elif ret.dot(t)<0:
						ret -= t
					else:
						ret += t

			if ret == None: return None
						
			ret.normalize()
			return (ret, centerPos)

	def __init__(self, props):
		super().__init__()

		# 登録対象のクラスリストを定義
		self._classes = (
			OperatorSet.OpImpl,
		)

	# ショートカット登録処理
	def register_shortcut(self, kc):
		km = kc.keymaps.new(
			"3D View",
			space_type='VIEW_3D',
			region_type='WINDOW'
		)
		kmi = km.keymap_items.new(
			OperatorSet.OpImpl.bl_idname,
			'NUMPAD_PERIOD',
			'PRESS',
			shift=False,
			ctrl=True,
			alt=False
		)
		kmi.active = True
		return km, kmi

