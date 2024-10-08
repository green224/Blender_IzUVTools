
import bpy
import bmesh
from mathutils import *
import math


# 現在PixelCenterFit状態か否かを取得する
def isPixelCenterFit(context):
	imgEditor = context.area.spaces[0]
	if imgEditor.uv_editor and imgEditor.image:
		if imgEditor.uv_editor.pixel_round_mode == "CENTER":
			return True
		else:
			return False
	return None

# ImageEditorの表示画像から解像度を取得する処理
def getTexSizeOfImageEditor(context):
	imgEditor = context.area.spaces[0]
	if imgEditor.uv_editor:
		if imgEditor.image:
			return Vector((
				imgEditor.image.size[0],
				imgEditor.image.size[1]
			))
	return None

# 現在編集しているオブジェクトとBMeshリストを得る
def getEditingBMeshList():
	result = []

	# 選択中の全オブジェクトに対して行う
	objs = set(bpy.context.selected_objects)

	for obj in objs:

		# メッシュ以外は除外
		if not hasattr(obj.data,"polygons"): continue

		# Editモード外のメッシュは除外
		if not obj.data.is_editmode: continue
		
		# BMeshから、UV番号ごとの選択状態を得る
		bm = bmesh.from_edit_mesh(obj.data)
		result.append((obj, bm))
	
	return result

# bMeshリストを引数に受け取り、現在選択している(UV,頂点)の組のリストを得る。
def getSelectedUVVerts(bMeshes):

	result = []

	for bm in bMeshes:
		uv_layer = bm.loops.layers.uv.active
		for face in bm.faces:
			for loop in face.loops:
				## 選択されているUVに対して、UV情報と頂点情報のタプルを格納
				uv = loop[uv_layer]
				if uv.select: result.append( (uv, loop.vert) )

	return result

# UV頂点リストから、座標の最小値、最大値、サイズ、中央値を求める
def getMinMaxUV(uvs):
	minUV = Vector((math.inf, math.inf))
	maxUV = Vector((-math.inf, -math.inf))
	for i in uvs:
		minUV.x = min(i.x, minUV.x)
		minUV.y = min(i.y, minUV.y)
		maxUV.x = max(i.x, maxUV.x)
		maxUV.y = max(i.y, maxUV.y)
	return (minUV, maxUV, maxUV-minUV, (minUV+maxUV)/2)

# UV頂点リストから、座標が最も散らばっている方向を8方向から算出する
def getMostScatteredUVDir(uvs, withDiag):
	minmaxPara = getMinMaxUV(uvs);
	if withDiag:
		minmaxDiag = getMinMaxUV([Vector((i.x+i.y,i.y-i.x)) for i in uvs]);

	dir0 = minmaxPara[2].x / (minmaxPara[2].y+0.00000001)
	dir1 = minmaxPara[2].y / (minmaxPara[2].x+0.00000001)
	if withDiag:
		dir2 = minmaxDiag[2].x / (minmaxDiag[2].y+0.00000001)
		dir3 = minmaxDiag[2].y / (minmaxDiag[2].x+0.00000001)
		if dir0<dir3 and dir1<dir3 and dir2<dir3: return "\\"
		if dir0<dir2 and dir1<dir2: return "/"
	if dir0<dir1: return "|"
	return "-"



# 各種数学用ユーティリティー
def clamp(x, smallest, largest): return max(smallest, min(x, largest))
def saturate(x): return clamp(x, 0, 1)
def frac(x):
	result = math.modf(x)[0]
	if result < 0: return saturate(1 + result)
	return result
def lerp(a, b, t): return t*b + (1 - t)*a

