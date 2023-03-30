
import bpy
import math
import os


# ボーンの状態を更新する。
# そのままだと最終結果のL2W変換行列を使用するタイプのDriver等、反映が1フレ遅延するタイプの
# Driver/Constraintが反映されないままになってしまうので、これで強制的に再更新をかける。
def forceRefreshBones(armature):
	# view_layer.updateだけではL2W行列は更新されないが、なぜか選択をすると更新される。
	# 逆にこの方法以外で強制更新を行う方法が見つかっていない。
	for i in armature.data.bones: i.select = True
	bpy.context.view_layer.update()
	for i in armature.data.bones: i.select = False
	bpy.context.view_layer.update()

# ボーンのL2Wマトリクスを取得する。
# そのままだと初期位置や親ボーンなども含めた行列しか取れず、
# 直接回転などを取得できないため、これを使用する。
def getBoneMtx(amt, boneName):
	pBone = amt.pose.bones[boneName]
	dBone = amt.data.bones[boneName]
	pMtx = pBone.matrix.copy()
	dMtx = dBone.matrix_local.copy()

	if pBone.parent is not None:
		pMtxP = pBone.parent.matrix.copy()
		dMtxP = dBone.parent.matrix_local.copy()
		pMtxP.invert()
		dMtxP.invert()
		pMtx = pMtxP @ pMtx
		dMtx = dMtxP @ dMtx

	dMtx.invert()
	return dMtx @ pMtx

# 対象Armatureを取得する。1Armatureにだけ対応している。
# （そもそも複数ArmatureはUnityで再生できない）
def tgtArmature( operator ):
	ret = None
	for obj in bpy.data.objects:
		if not obj :continue
		if obj.type != 'ARMATURE':continue
		ret = obj
		break
	if not ret:
		operator.report({'WARNING'},'There is no armature')
		return None
	if not ret.animation_data:
		operator.report({'WARNING'},'There is no animation')
		return None
	if not ret.animation_data.nla_tracks:
		operator.report({'WARNING'},'There is no NLA tracks')
		return None
	return ret


# 各種数学用ユーティリティー
def clamp(x, smallest, largest): return max(smallest, min(x, largest))
def saturate(x): return clamp(x, 0, 1)
def frac(x):
	result = math.modf(x)[0]
	if result < 0: return saturate(1 + result)
	return result