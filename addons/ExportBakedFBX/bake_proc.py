
import bpy
import math
import os

from .common_arma import *

from bpy.props import (
		BoolProperty,
		PointerProperty,
		StringProperty, 
		CollectionProperty,
		FloatProperty,
		EnumProperty,
		IntProperty,
		)

# ベイク対象から外すボーンの名前に追加する文字列
DONT_BAKE_KEYWORD = "[DONT_BAKE]"

# ベイク処理本体
def bakeAnim( operator ):
	# 対象Armatureを取得
	tgt_armature = tgtArmature(operator)
	if tgt_armature is None: return False

	# オリジナルArmatureのモードおよび、NLAトラックのミュート状態を記憶しておく
	bpy.context.view_layer.objects.active = tgt_armature
	old_mode = bpy.context.object.mode
	bpy.ops.object.mode_set(mode='POSE')
	old_tracks_mute = []
	for track in tgt_armature.animation_data.nla_tracks:
		old_tracks_mute.append(track.mute)
		track.mute = True

	# ベイクする必要のあるボーン名を収集
	deformBoneKeys = []
	for key in tgt_armature.data.bones.keys():
		if tgt_armature.data.bones[key].use_deform : 
			deformBoneKeys.append(key)

	# アニメーションの再生のために、Armatureの状態をクリーンにする
	def cleanArmaturePose(action):
		# 目標Armatureのみを選択
		bpy.context.view_layer.objects.active = tgt_armature
		bpy.ops.object.mode_set(mode='OBJECT')
		bpy.ops.object.select_all(action='DESELECT')
		bpy.context.view_layer.objects.active = tgt_armature
		tgt_armature.select_set( True )
		tgt_armature.animation_data.action = action
		bpy.ops.object.mode_set(mode='POSE')

		# キーのないボーンのTransformをデフォルト状態にしておく
		bpy.ops.pose.select_all(action='SELECT')
		bpy.ops.pose.transforms_clear()

	# アクションのキーフレーム長を計算
	def getActionFrameLength(action):
		firstFrame =  9999999
		lastFrame  = -9999999
		for fcu in action.fcurves:
			for keyframe in fcu.keyframe_points:
				x, y = keyframe.co
				k = math.ceil(x)
				if k < firstFrame : firstFrame = k
				if k > lastFrame  : lastFrame  = k
		return firstFrame, lastFrame

	# 全アクションを列挙
	#actions = [ a for a in bpy.data.actions if bool(a) & a.use_fake_user ]
	actions = [ a for a in bpy.data.actions if bool(a) ]
	transCaches = []
	for action in actions:
		cleanArmaturePose(action)
		firstFrame, lastFrame  = getActionFrameLength(action)

		# アクションの全フレームにわたって、Transform情報を収集する
		transCache = []
		for i in range(firstFrame, lastFrame+1):
			bpy.context.scene.frame_set(i)
			forceRefreshBones(tgt_armature)
			transCache_1bone = [getBoneMtx(tgt_armature,j) for j in deformBoneKeys]
			transCache.append(transCache_1bone)
		transCaches.append(transCache)

	for action_idx, action in enumerate(actions):
		cleanArmaturePose(action)
		firstFrame, lastFrame  = getActionFrameLength(action)

		# 既存のキーを全削除する
		fcCache = []
		for fcu in action.fcurves:
			if not DONT_BAKE_KEYWORD in fcu.data_path: fcCache.append(fcu)		# ベイク対象外オブジェクトは除く
		for fcu in fcCache: action.fcurves.remove(fcu)

		# Deformボーンについて、全フレームにTransform情報をベイク
		def makeFC(boneName, path, idx):
			ret = action.fcurves.find('pose.bones["'+boneName+'"].'+path, index=idx)
			if ret is None:
				ret = action.fcurves.new('pose.bones["'+boneName+'"].'+path, index=idx)
#			ret.auto_smoothing = 'CONT_ACCEL'
			ret.keyframe_points.add(lastFrame-firstFrame+1)
			return ret
		def makeFCs(boneName, path, len):
			return [makeFC(boneName, path, i) for i in range(len)]
		def setKeyFramePoints(fcs, frameIdx, frameT, vals):
			for idx, fc in enumerate(fcs):
				pnt = fc.keyframe_points[frameIdx]
				pnt.co = frameT, vals[idx]
				pnt.interpolation = 'BEZIER'
				pnt.handle_left_type = 'AUTO_CLAMPED'
				pnt.handle_right_type = 'AUTO_CLAMPED'
		for boneIdx, boneName in enumerate(deformBoneKeys):
			fc_l = makeFCs(boneName ,"location", 3)
			fc_r = makeFCs(boneName ,"rotation_quaternion", 4)
			fc_s = makeFCs(boneName ,"scale", 3)
			for frameIdx, frameT in enumerate(range(firstFrame, lastFrame+1)):
				mtx = transCaches[action_idx][frameIdx][boneIdx]
				t = mtx.to_translation()
				r = mtx.to_quaternion()
				s = mtx.to_scale()
				setKeyFramePoints(fc_l, frameIdx, frameT, [t.x, t.y, t.z])
				setKeyFramePoints(fc_r, frameIdx, frameT, [r.w, r.x, r.y, r.z])
				setKeyFramePoints(fc_s, frameIdx, frameT, [s.x, s.y, s.z])
			for fc in fc_l: fc.update()
			for fc in fc_r: fc.update()
			for fc in fc_s: fc.update()

		print("Action: {}, First frame: {}, Second frame: {}".format(action.name, firstFrame, lastFrame))

	# 表示アクションを非選択にする
	cleanArmaturePose(None)

	# Constraintsを全削除
	for bone in tgt_armature.pose.bones:
		if not DONT_BAKE_KEYWORD in bone.name:				# ベイク対象外オブジェクトは除く
			cstrCache = [i for i in bone.constraints]
			for i in cstrCache: bone.constraints.remove(i)

	# Driverを全削除
	drvCache = [i for i in tgt_armature.animation_data.drivers]
	for i in drvCache: tgt_armature.animation_data.drivers.remove(i)

	# 全ボーンの回転モードを四元数に変更
	for bone in tgt_armature.pose.bones: bone.rotation_mode = "QUATERNION"
	
	# Deformボーン以外を削除する
	bpy.ops.object.mode_set(mode='EDIT')
	for key in tgt_armature.data.bones.keys():
		if not tgt_armature.data.edit_bones[key].use_deform \
			and not DONT_BAKE_KEYWORD in tgt_armature.data.bones[key].name: 		# ベイク対象外オブジェクトは除く
			tgt_armature.data.edit_bones.remove(tgt_armature.data.edit_bones[key])
	bpy.ops.object.mode_set(mode='OBJECT')

	# オリジナルArmatureのモードおよびNLAトラックのミュート状態を復元する
	bpy.context.view_layer.objects.active = tgt_armature
	bpy.ops.object.mode_set(mode=old_mode)
	for i,track in enumerate(tgt_armature.animation_data.nla_tracks):
		track.mute = old_tracks_mute[i]
		
#	#すべてのボーンの姿勢を初期状態にする
#	bpy.ops.object.mode_set(mode='POSE')
#	bpy.ops.pose.select_all(action='SELECT')
#	bpy.ops.pose.transforms_clear()
#	forceRefreshBones(tgt_armature)
	return True

# FBX出力する処理
def exportFBX(operator, file_name: StringProperty, anim_type: EnumProperty):
	
	# 出力アニメーションが全NLAの場合、NLAトラックを全アクティブにする。
	# どうせリバートするので、これは元の状態に復元する必要はない
	if anim_type == 'AllNLA':
		tgt_armature = tgtArmature(operator)
		for track in tgt_armature.animation_data.nla_tracks:
			if track.name.startswith('[Action Stash]'): continue
			track.mute = False

	mdl_filepath = bpy.data.filepath
	mdl_directory = os.path.dirname( mdl_filepath )
	fbx_filepath = os.path.join( mdl_directory, file_name )
	
	use_nla: bool = False
	if (anim_type == 'ActiveNLA') or (anim_type == 'AllNLA'):
		use_nla = True
	elif anim_type == 'AllActions':
		use_nla = False
	
	bpy.ops.export_scene.fbx(
		filepath=fbx_filepath,
		check_existing=False,
		filter_glob="*.fbx",
		use_selection=False,
		use_active_collection=True,
		global_scale=1.0,
		apply_unit_scale=True,
		apply_scale_options='FBX_SCALE_NONE',
		bake_space_transform=True,
		object_types={'MESH', 'ARMATURE'},
		use_mesh_modifiers=True,
		use_mesh_modifiers_render=True,
		mesh_smooth_type='OFF',
		use_subsurf=False,
		use_mesh_edges=False,
		use_tspace=False,
		use_custom_props=False,
		add_leaf_bones=True,
		primary_bone_axis='Y',
		secondary_bone_axis='X',
		use_armature_deform_only=True,
		armature_nodetype='NULL',
		bake_anim=True,
		bake_anim_use_all_bones=True,
		bake_anim_use_nla_strips= use_nla,
		bake_anim_use_all_actions= not use_nla,
		bake_anim_force_startend_keying=True,
		bake_anim_step=1.0,
		bake_anim_simplify_factor=1.0,
		path_mode='AUTO',
		embed_textures=False,
		batch_mode='OFF',
		use_batch_own_dir=True,
		use_metadata=True,
		axis_forward='-Z',
		axis_up='Y'
	)

# 出力処理本体
def export(operator, context, file_name: StringProperty, anim_type: EnumProperty):
	print("[ExportFBX] Begin")
	if not bakeAnim(operator): return False

	exportFBX(operator, file_name, anim_type)
	print("[ExportFBX] Complete")

	# 色々ぶっ壊れるのでリバートする
	bpy.ops.wm.revert_mainfile()
	print("[ExportFBX] Reverted")
	return True
