"""
アニメーションを全BakeしてFBX出力をするアドオン。

そのままのFBX出力には複数の問題がある。
・一部のConstraintsやDriverなどで、姿勢の反映が1フレーム遅延するタイプのものが正常に出力できない。
・スケーリングしたボーンの子ボーンをConstraintsで回転させた場合に、正常なモーションを出力できない。

また組み込みのActionベイク処理は、諸々正常にベイクを行わないため、
この問題に対する解決法として使用することができない。
このアドオンでは、正しくBakeして、出力を行う。

使い方
１．File->Export Baked Anim FBX  を選択する
２．出力先ファイルを指定する
３．FBXが出力される。
    出力過程で作業状態に変更が加わってしまうので、最後にリバートが行われる。
	そのため、セーブ済みのファイルで無いと実行できないようにしている

注意
・出力対象のアニメーションは、NLAトラックのみ。
  Actionは出力されないので、出力したいアニメーションはNLAトラック化すること。
・ミュート状態のNLAトラックは出力されない仕様なので、
  出力したいNLAトラックのミュート状態はOFFにしておくこと。
・Bake範囲は、キーが打ってある範囲に限定される。
・名前に "[DONT_BAKE]" が含まれるボーンはベイク対象外となる。
  （ベイク処理を行わずにそのままFBX出力される）
・オブジェクトのVisibilityなど、そもそもBlenderではベイクできないものもある。
"""


# プラグインに関する情報
bl_info = {
	"name" : "Baked FBX Exporter",
	"author" : "Shu",
	"version" : (2,3),
    'blender': (3, 2, 0),
    "location": "File > Import-Export",
	"description" : "Export FBX with baked animation",
	"warning" : "",
	"wiki_url" : "",
	"tracker_url" : "",
	"category" : "Import-Export"
}



if "bpy" in locals():
	import imp
	imp.reload(common_arma)
	imp.reload(bake_proc)
	imp.reload(opSet_base)
	imp.reload(opSet_export)
from . import common_arma
from . import bake_proc
from . import opSet_base
from . import opSet_export


import bpy
from mathutils import *
import math


#-------------------------------------------------------

# Addon全体のGlobal保存パラメータ
class PR_ExpBFBX(bpy.types.PropertyGroup):
	pass
PR_ExpBFBX.__annotations__ = {}

classes = (
	PR_ExpBFBX,
)

# 機能モジュールのインスタンス一覧
opSet_Insts = [
	opSet_export.OperatorSet(PR_ExpBFBX),
]


#-------------------------------------------------------

#-------------------------------------------------------

# プラグインをインストールしたときの処理
def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	for ops in opSet_Insts: ops.register()
	bpy.types.Scene.export_baked_fbx_property = bpy.props.PointerProperty(type=PR_ExpBFBX)

# プラグインをアンインストールしたときの処理
def unregister():
	for ops in reversed(opSet_Insts): ops.unregister()
	for cls in reversed(classes):
		bpy.utils.unregister_class(cls)
	del bpy.types.Scene.export_baked_fbx_property

if __name__ == "__main__":
	register()
