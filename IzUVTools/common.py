
import bpy
from mathutils import *
import math



# 現在選択している(UV,頂点)の組のリストを得る
def getSelectedUVVerts():

	result = []

	# 選択中の全オブジェクトに対して行う
	objs = set(bpy.context.selected_objects)
	objDatas = set([i.data for i in objs])

	for mesh in objDatas:
		
		# UV番号と頂点番号の組み合わせを構築
		uvAndVertIdLst = []
		for face in mesh.polygons:
			for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
				uvAndVertIdLst.append( (vert_idx, loop_idx) )

		# UV番号から頂点へのマップを構築
		uv2vert = [0]*len(uvAndVertIdLst)
		for vert_idx, loop_idx in uvAndVertIdLst:
			uv2vert[ loop_idx ] = mesh.vertices[ vert_idx ]

		## UV情報と頂点情報のタプルを格納
		for idx, dat in enumerate(mesh.uv_layers.active.data):
			if (dat.select):
				result.append( (dat, uv2vert[idx]) )

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
def getMostScatteredDir(uvs, withDiag):
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

