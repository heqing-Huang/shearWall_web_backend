"""
创建OCC模型
"""

import numpy as np
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge, \
    BRepBuilderAPI_MakeFace,BRepBuilderAPI_Transform
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism,BRepPrimAPI_MakeBox
from OCC.Core.gp import gp_Pnt, gp_Vec,gp_Dir,gp_Circ,gp_Ax2,gp_Trsf
from .tool import my_BRepAlgoAPI_Fuse,my_BRepAlgoAPI_Cut,my_BRepAlgoAPI_Common,addition_of_two_points
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut
from OCC.Core.BRepOffsetAPI import BRepOffsetAPI_MakePipe
from OCC.Core.GC import GC_MakeArcOfCircle
from typing import List,Tuple


class BuildOCCSolid(object):
    """
    建立OCC模型
    """
    def __init__(self,ifc_file,entity_type,object_name,occ_data):
        self.ifc_file = ifc_file
        self.entity_type = entity_type
        self.object_name = object_name
        self.occ_data = occ_data
        self.generate_basic_data()

    def generate_basic_data(self):
        """
        产生基础数据
        :return:
        """
        # 获取实体信息
        self.solid_result = self.occ_data.get_ifc_solid_element(self.entity_type[0])
        # 获取构造水平钢筋信息
        self.construct_horizon_result = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1], self.object_name[0])
        # 获取构造竖向钢筋信息
        self.construct_vertical_result = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1], self.object_name[0])
        # 获取桁架马镫筋信息
        self.truss_stirrup_result = self.occ_data.get_ifc_truss_stirrup_rebar(self.entity_type[2], self.object_name[1])
        # 获取桁架上弦纵筋信息
        self.truss_top_long_rebar_result = self.occ_data.get_ifc_truss_top_long_rebar(self.entity_type[2], self.object_name[1])
        # 获取桁架下弦纵筋信息
        self.truss_bottom_long_rebar_result = self.occ_data.get_ifc_truss_bottom_long_rebar(self.entity_type[2], self.object_name[1])


    def create_stretch_solid(self,position,height,profile,direction):
        """
        创建拉伸实体
        :return:
        """
        wall_profile = BRepBuilderAPI_MakeWire()  # 创建空的轮廓
        for num in range(len(profile)-1):
            start_point = addition_of_two_points(profile[num],position)
            end_point = addition_of_two_points(profile[num+1],position)
            edge = BRepBuilderAPI_MakeEdge(gp_Pnt(start_point[0], start_point[1], start_point[2]),
                                           gp_Pnt(end_point[0], end_point[1], end_point[2])).Edge()
            wall_profile.Add(edge)
        stretch_length = [direction[0]*height,direction[1]*height,direction[2]*height]
        stretch_length = gp_Vec(stretch_length[0], stretch_length[1], stretch_length[2])
        wall_face = BRepBuilderAPI_MakeFace(wall_profile.Wire())
        wall_solid = BRepPrimAPI_MakePrism(wall_face.Face(), stretch_length).Shape()
        return wall_solid

    def create_single_shear_wall_solid(self,single_wall):
        """
        创建双皮剪力墙单个实体
        :return:
        """
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Fuse(main_solid, cut_shape).Shape()  # 合并实体
        # 遍历每块双皮剪力墙
        curr_position = single_wall["position"]
        curr_height = single_wall["height"]
        curr_profile = single_wall["profile"]
        curr_direction = single_wall["direction"]
        curr_solid = self.create_stretch_solid(curr_position,curr_height,curr_profile,curr_direction)
        main_solid = my_BRepAlgoAPI_Fuse(main_solid, curr_solid).Shape()
        total_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()
        return total_solid

    def create_double_shear_wall_exterior_solid(self):
        """
        创建双皮剪力墙外层实体
        :return:
        """
        exterior_wall = self.solid_result[1]
        exterior_wall_solid = self.create_single_shear_wall_solid(exterior_wall)
        return exterior_wall_solid

    def create_double_shear_wall_interior_solid(self):
        """
        创建双皮剪力墙内层实体
        :return:
        """
        interior_wall = self.solid_result[0]
        interior_solid = self.create_single_shear_wall_solid(interior_wall)
        return interior_solid

    def create_make_pipe_shape(self,profile_points,radius):
        """
        创建扫掠形状
        :param profile_points: 轨迹[起点,终点]
        :param radius: 直径
        :return:
        """
        start_point = profile_points[0]
        end_point = profile_points[1]
        # 创建扫掠轨迹
        wire_profile = BRepBuilderAPI_MakeWire()
        for num in range(len(profile_points)-1):
            point_1 = profile_points[num]
            point_2 = profile_points[num+1]
            edge_ = BRepBuilderAPI_MakeEdge(gp_Pnt(point_1[0], point_1[1], point_1[2]),
                                               gp_Pnt(point_2[0], point_2[1], point_2[2])).Edge()
            wire_profile.Add(edge_)
        # 创建圆
        vec_1 = np.array(np.array(list(end_point))-np.array(list(start_point)))/np.linalg.norm(np.array(list(end_point))-np.array(list(start_point)))
        circle = gp_Circ(gp_Ax2(gp_Pnt(start_point[0], start_point[1], start_point[2]),
                                gp_Dir(vec_1[0], vec_1[1], vec_1[2])),
                         radius)
        edge = BRepBuilderAPI_MakeEdge(circle).Edge()  # 线
        wire = BRepBuilderAPI_MakeWire(edge).Wire()  # 多段线
        face = BRepBuilderAPI_MakeFace(wire).Face()  # 平面
        sweep_shape = BRepOffsetAPI_MakePipe(wire_profile.Wire(), face).Shape()

        return sweep_shape

    def create_make_pipe_shape_polygon(self,profile_points,radius):
        """
        创建多段线扫掠形状
        :param profile_points: 轨迹[起点,终点]
        :param radius: 直径
        :return:
        """
        start_point = profile_points[0][0]
        end_point = profile_points[0][1]
        # 创建扫掠轨迹
        wire_profile = BRepBuilderAPI_MakeWire()
        for num in range(len(profile_points)):
            seg = profile_points[num]
            if len(seg)==2:
                point_1 = seg[0]
                point_2 = seg[1]
                edge_ = BRepBuilderAPI_MakeEdge(gp_Pnt(point_1[0], point_1[1], point_1[2]),
                                                   gp_Pnt(point_2[0], point_2[1], point_2[2])).Edge()
            else:
                point_1 = seg[0]
                point_2 = seg[2]
                point_3 = seg[1]
                pnt_1 = gp_Pnt(point_1[0],point_1[1],point_1[2])
                pnt_2 = gp_Pnt(point_3[0],point_3[1],point_3[2])
                pnt_3 = gp_Pnt(point_2[0],point_2[1],point_2[2])
                arc_ = GC_MakeArcOfCircle(pnt_1,pnt_2,pnt_3)

                edge_ = BRepBuilderAPI_MakeEdge(arc_.Value()).Edge()
            wire_profile.Add(edge_)
        # 创建圆
        vec_1 = np.array(np.array(list(end_point))-np.array(list(start_point)))/np.linalg.norm(np.array(list(end_point))-np.array(list(start_point)))
        circle = gp_Circ(gp_Ax2(gp_Pnt(start_point[0], start_point[1], start_point[2]),
                                gp_Dir(vec_1[0], vec_1[1], vec_1[2])),radius)
        edge = BRepBuilderAPI_MakeEdge(circle).Edge()  # 线
        wire = BRepBuilderAPI_MakeWire(edge).Wire()  # 多段线
        face = BRepBuilderAPI_MakeFace(wire).Face()  # 平面
        sweep_shape = BRepOffsetAPI_MakePipe(wire_profile.Wire(), face).Shape()

        return sweep_shape

    def create_construct_rebar_model(self,construct_rebar_info):
        """
        创建构造钢筋模型
        :return:
        """
        rebar_radius = construct_rebar_info["Radius"] # 钢筋直径
        construct_profile = construct_rebar_info["profile"]  # 钢筋轮廓信息
        # 创建实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Fuse(main_solid, cut_shape).Shape()  # 合并实体
        for single_rebar in construct_profile:
            main_rebar = self.create_make_pipe_shape(single_rebar,rebar_radius)
            main_solid = my_BRepAlgoAPI_Fuse(main_solid, main_rebar).Shape()
        total_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()
        return total_solid

    @staticmethod
    def tool_occ_model_transform(translate_place,occ_model):
        """
        OCC模型的平移
        :param translate_place:
        :param occ_model:
        :return:
        """
        # 建立虚拟实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        for point in translate_place:
            move = gp_Vec(point[0], point[1], point[2])  # 平移点
            transform = gp_Trsf()  # 建立变换矩阵
            transform.SetTranslation(move)  # 对矩阵进行平移变换
            curr_solid = BRepBuilderAPI_Transform(occ_model, transform, False).Shape()  # 不复制该实体
            main_solid = BRepAlgoAPI_Fuse(main_solid, curr_solid).Shape()
        total_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()
        return total_solid

    def create_construct_horizon_rebar_model(self):
        """
        创建构造水平钢筋模型
        :return:
        """
        construct_horizon_rebar_info = self.construct_horizon_result
        horizon_rebar_model = self.create_construct_rebar_model(construct_horizon_rebar_info)
        return horizon_rebar_model

    def create_construct_vertical_rebar_model(self):
        """
        创建构造竖向钢筋模型
        :return:
        """
        construct_vertical_rebar_info = self.construct_vertical_result
        vertical_rebar_model = self.create_construct_rebar_model(construct_vertical_rebar_info)
        return vertical_rebar_model

    def create_truss_long_rebar_model(self,truss_rebar_info):
        """
        创建桁架钢筋模型
        :return:
        """
        rebar_radius = truss_rebar_info["Radius"] # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        translate_place = []
        start_loc = list(truss_profile[0][0][0]) # 起点
        # 平移量
        for single_truss in truss_profile:
            curr_loc = list(single_truss[0][0])
            move = [curr_loc[0]-start_loc[0],curr_loc[1]-start_loc[1],curr_loc[2]-start_loc[2]]
            translate_place.append(move)
        # 创建实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()  # 合并实体

        # 奖励第一个实体
        rebar_sequence = truss_profile[0]
        for single_rebar in rebar_sequence:
            main_rebar = self.create_make_pipe_shape(single_rebar, rebar_radius)
            main_solid = BRepAlgoAPI_Fuse(main_solid, main_rebar).Shape()
        fuse_solid = self.tool_occ_model_transform(translate_place,main_solid)
        return fuse_solid

    def create_truss_top_long_rebar_model(self):
        """
        创建桁架上弦纵筋模型
        :return:
        """
        truss_rebar_info = self.truss_top_long_rebar_result
        main_solid = self.create_construct_rebar_model(truss_rebar_info)
        return main_solid

    def create_truss_bottom_long_rebar_model(self):
        """
        创建桁架下弦纵筋模型
        :return:
        """
        truss_rebar_info = self.truss_bottom_long_rebar_result
        main_solid = self.create_construct_rebar_model(truss_rebar_info)
        return main_solid

    def create_multiplygon_rebar_model(self,rebar_info):
        """
        建立多段线钢筋信息
        :param rebar_info:
        :return:
        """
        rebar_radius = rebar_info["Radius"]  # 钢筋直径
        rebar_profile = rebar_info["profile"]  # 钢筋轮廓信息
        translate_place = []
        start_loc = list(rebar_profile[0][0])  # 起点
        # 平移量
        for single_truss in rebar_profile:
            curr_loc = list(single_truss[0])
            move = [curr_loc[0] - start_loc[0], curr_loc[1] - start_loc[1], curr_loc[2] - start_loc[2]]
            translate_place.append(move)
        # 创建实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()  # 合并实体

        # 建立第一个实体
        for single_rebar in rebar_profile:
            main_rebar = self.create_make_pipe_shape(single_rebar, rebar_radius)
            main_solid = BRepAlgoAPI_Fuse(main_solid, main_rebar).Shape()
        fuse_solid = self.tool_occ_model_transform(translate_place,main_solid)
        return fuse_solid

    def create_single_solid_and_move_model(self,translate_place:List[List[float]],rebar_profile:List[List[Tuple[float]]],
                                           radius:float):
        """
        建立单个扫略体并按需求平移
        :return:
        """
        # 创建实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()  # 合并实体
        # 建立虚拟实体
        special_move = gp_Vec(0, 0, 0)  # 平移点
        transform = gp_Trsf()  # 建立变换矩阵
        transform.SetTranslation(special_move)  # 对矩阵进行平移变换
        fuse_solid = BRepBuilderAPI_Transform(main_solid, transform, False).Shape()
        # 建立第一个实体
        for single_rebar in rebar_profile:
            main_rebar = self.create_make_pipe_shape(single_rebar, radius)
            main_solid = BRepAlgoAPI_Fuse(main_solid, main_rebar).Shape()
        for point in translate_place:
            move = gp_Vec(point[0], point[1], point[2])  # 平移点
            transform = gp_Trsf()  # 建立变换矩阵
            transform.SetTranslation(move)  # 对矩阵进行平移变换
            curr_solid = BRepBuilderAPI_Transform(main_solid, transform, False).Shape()  # 不复制该实体
            fuse_solid = BRepAlgoAPI_Fuse(fuse_solid, curr_solid).Shape()
        return fuse_solid

    def create_single_truss_stirrup_and_move_model(self,translate_place:List[List[float]],rebar_profile:List[List[Tuple[float]]],
                                           radius:float):
        """
        建立单个扫略体并按需求平移
        :return:
        """
        # 创建实体
        main_solid = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        cut_shape = BRepPrimAPI_MakeBox(gp_Pnt(-100, -100, -100), 1, 1, 1).Shape()
        main_solid = my_BRepAlgoAPI_Cut(main_solid, cut_shape).Shape()  # 合并实体
        # 建立虚拟实体
        special_move = gp_Vec(0, 0, 0)  # 平移点
        transform = gp_Trsf()  # 建立变换矩阵
        transform.SetTranslation(special_move)  # 对矩阵进行平移变换
        fuse_solid = BRepBuilderAPI_Transform(main_solid, transform, False).Shape()
        # 建立第一个实体
        for single_rebar in rebar_profile:
            main_rebar = self.create_make_pipe_shape_polygon(single_rebar, radius)
            main_solid = BRepAlgoAPI_Fuse(main_solid, main_rebar).Shape()
        for point in translate_place:
            move = gp_Vec(point[0], point[1], point[2])  # 平移点
            transform = gp_Trsf()  # 建立变换矩阵
            transform.SetTranslation(move)  # 对矩阵进行平移变换
            curr_solid = BRepBuilderAPI_Transform(main_solid, transform, False).Shape()  # 不复制该实体
            fuse_solid = BRepAlgoAPI_Fuse(fuse_solid, curr_solid).Shape()
        return fuse_solid

    def create_truss_stirrup_rebar_model(self):
        """
        创建桁架马镫筋模型
        :return:
        """
        truss_rebar_info = self.truss_stirrup_result
        rebar_radius = truss_rebar_info["Radius"]  # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        translate_place = []
        start_loc = list(truss_profile[0][0][0][0])  # 起点
        single_truss_rebar = truss_profile[0]
        # # 平移量
        for single_truss in truss_profile:
            curr_loc = list(single_truss[0][0][0])
            move = [curr_loc[0]-start_loc[0],curr_loc[1]-start_loc[1],curr_loc[2]-start_loc[2]]
            translate_place.append(move)
        fuse_solid = self.create_single_truss_stirrup_and_move_model(translate_place,single_truss_rebar,rebar_radius)
        return fuse_solid

    def create_truss_stirrup_rebar_rotated_model(self):
        """
        创建桁架马镫筋被旋转的实体模型：变换有限元处的数据
        :return:
        """
        from .tool import transform_truss_rebar_xy_plane_to_zx_plane,radian_bt_vectors,rotated_total_points_around_y_axis
        truss_rebar_info = self.truss_stirrup_result
        rebar_radius = truss_rebar_info["Radius"]  # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        translate_place = []
        start_loc = list(truss_profile[0][0][0][0])  # 起点
        single_truss_rebar = truss_profile[0]
        # 计算旋转角度
        _base_vector_z = np.asarray([0,0,1])
        _base_vector_y = np.array([0,1,0])
        _base_vector_x_ = np.array([-1,0,0])
        _base_vector_x = np.array([1,0,0])
        # 获取线段1
        seg_1 = single_truss_rebar[0][0]
        vector_1 = np.array([seg_1[1][0],seg_1[1][1],0]) - np.array([seg_1[0][0],seg_1[0][1],0])
        theta_ = radian_bt_vectors(_base_vector_x_,vector_1)
        profile_1 = rotated_total_points_around_y_axis(single_truss_rebar[0],theta_)
        # 桁架筋变换到yz平面
        profile_1 = transform_truss_rebar_xy_plane_to_zx_plane(profile_1)
        adjusted_single_truss_rebar = [profile_1]
        # 平移量
        for single_truss in truss_profile:
            curr_loc = list(single_truss[0][0][0])
            move = [curr_loc[0]-start_loc[0],curr_loc[1]-start_loc[1],curr_loc[2]-start_loc[2]]
            translate_place.append(move)
        translate_place = [[0,0,0]]
        fuse_solid = self.create_single_truss_stirrup_and_move_model(translate_place,adjusted_single_truss_rebar,rebar_radius)
        return fuse_solid

    def create_single_truss_stirrup_rebar_model(self):
        """
        创建单个桁架马镫筋模型
        :return:
        """
        truss_rebar_info = self.truss_stirrup_result
        rebar_radius = truss_rebar_info["Radius"]  # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        single_truss_rebar = truss_profile[0][0]
        # 建立第一个实体
        main_rebar = self.create_make_pipe_shape_polygon(single_truss_rebar, rebar_radius)
        return main_rebar

    def create_single_area_truss_stirrup_rebar_model(self):
        """
        创建单个部分区域的桁架马镫筋模型
        :return:
        """
        truss_rebar_info = self.truss_stirrup_result
        rebar_radius = truss_rebar_info["Radius"]  # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        single_truss_rebar = truss_profile[0][0][3:12]
        # 建立第一个实体
        main_rebar = self.create_make_pipe_shape_polygon(single_truss_rebar, rebar_radius)
        return main_rebar


    def create_truss_stirrup_straight_rebar_model(self):
        """
        创建桁架马镫筋直筋模型----平直钢筋
        :return:
        """
        truss_rebar_info = self.truss_stirrup_result
        rebar_radius = truss_rebar_info["Radius"]  # 钢筋直径
        truss_profile = truss_rebar_info["profile"]  # 钢筋轮廓信息
        translate_place = []
        start_loc = list(truss_profile[0][0][0][0]) # 起点
        single_truss_rebar = truss_profile[0]
        # # 平移量
        for single_truss in truss_profile:
            curr_loc = list(single_truss[0][0][0])
            move = [curr_loc[0]-start_loc[0],curr_loc[1]-start_loc[1],curr_loc[2]-start_loc[2]]
            translate_place.append(move)
        fuse_solid = self.create_single_truss_stirrup_and_move_model(translate_place,single_truss_rebar,rebar_radius)
        return fuse_solid

    def create_pvc_hole_solid_model(self):
        """
        创建pvc实体模型
        :return:
        """
        pvc_hole_info = self.occ_data.get_ifc_pvc_hole_info()
        hole_radius = pvc_hole_info["hole_diam"]/2
        hole_profile = pvc_hole_info["hole_profile"]
        hole_loc = pvc_hole_info["hole_loc"]
        fuse_solid = self.create_single_solid_and_move_model(hole_loc,hole_profile,hole_radius)
        return fuse_solid

    def create_special_hoist_embedded_part_model(self):
        """
        创建吊装预埋件模型
        :return:
        """
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        rebar_radius = hoist_embedded_info["diam"]/2
        hoist_loc = hoist_embedded_info["hoist_loc"]
        exterior_seg = hoist_embedded_info["exterior_seg"]
        horizon_seg_1 = hoist_embedded_info["horizon_seg_1"]
        horizon_seg_2 = hoist_embedded_info["horizon_seg_2"]
        hoist_profile = [exterior_seg,horizon_seg_1,horizon_seg_2]
        fuse_solid = self.create_single_solid_and_move_model(hoist_loc,hoist_profile,rebar_radius)
        return fuse_solid

    def create_hoist_embedded_part_model(self):
        """
        创建特殊吊装预埋件模型
        :return:
        """
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        rebar_radius = hoist_embedded_info["diam"]/2
        hoist_loc = hoist_embedded_info["hoist_loc"]
        total_profile = hoist_embedded_info["total_profile"]
        horizon_seg_1 = hoist_embedded_info["horizon_seg_1"]
        horizon_seg_2 = hoist_embedded_info["horizon_seg_2"]
        hoist_profile = [total_profile,[horizon_seg_1],[horizon_seg_2]]
        fuse_solid = self.create_single_truss_stirrup_and_move_model(hoist_loc,hoist_profile,rebar_radius)
        return fuse_solid

    def create_single_hoist_embedded_part_model(self):
        """
        创建单个吊装预埋件模型
        :return:
        """
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        rebar_radius = hoist_embedded_info["diam"]/2
        hoist_loc = hoist_embedded_info["hoist_loc"][:1]
        total_profile = hoist_embedded_info["total_profile"]
        horizon_seg_1 = hoist_embedded_info["horizon_seg_1"]
        horizon_seg_2 = hoist_embedded_info["horizon_seg_2"]
        hoist_profile = [total_profile,[horizon_seg_1],[horizon_seg_2]]
        fuse_solid = self.create_single_truss_stirrup_and_move_model(hoist_loc,hoist_profile,rebar_radius)
        return fuse_solid

    @staticmethod
    def tool_form_combine_solid_model(inner_radius:float,outer_radius:float,
                                      bolt_profile:List[Tuple[float,float,float]],plate_profile:List[Tuple[float,float,float]],
                                      plate_shape:List[Tuple[float,float,float]]):
        """
        形成组合体
        :param bolt_loc:
        :param inner_radius:
        :param outer_radius:
        :param bolt_profile:
        :param plate_profile:
        :param plate_shape:
        :return:
        """
        # 形成端板
        plate_p_s = plate_profile[0]
        plate_p_e = plate_profile[1]
        # 创建扫掠轨迹

        path_line = BRepBuilderAPI_MakeEdge(gp_Pnt(plate_p_s[0], plate_p_s[1], plate_p_s[2]),
                                        gp_Pnt(plate_p_e[0], plate_p_e[1], plate_p_e[2])).Edge()
        path_line_profile = BRepBuilderAPI_MakeWire(path_line).Wire()
        # 创建形状轮廓
        shape_profile = BRepBuilderAPI_MakeWire()
        for num in range(len(plate_shape)-1):
            point_1 = plate_shape[num]
            point_2 = plate_shape[num+1]
            edge_ = BRepBuilderAPI_MakeEdge(gp_Pnt(point_1[0], point_1[1], point_1[2]),
                                               gp_Pnt(point_2[0], point_2[1], point_2[2])).Edge()
            shape_profile.Add(edge_)
        rectangle_face = BRepBuilderAPI_MakeFace(shape_profile.Wire()).Face()
        rectangle_solid = BRepOffsetAPI_MakePipe(path_line_profile, rectangle_face).Shape()
        # 创建外圆
        circle_p_s = bolt_profile[0]
        circle_p_e = bolt_profile[1]

        circle_profile_line = BRepBuilderAPI_MakeEdge(gp_Pnt(circle_p_s[0], circle_p_s[1], circle_p_s[2]),
                                        gp_Pnt(circle_p_e[0], circle_p_e[1], circle_p_e[2])).Edge()
        circle_line_profile = BRepBuilderAPI_MakeWire(circle_profile_line).Wire()
        vec_1 = np.array(np.array(list(circle_p_e))-np.array(list(circle_p_s)))/np.linalg.norm(np.array(list(circle_p_e))-np.array(list(circle_p_s)))
        circle_1 = gp_Circ(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(vec_1[0], vec_1[1], vec_1[2])),outer_radius)
        # 创建内圆
        circle_2 = gp_Circ(gp_Ax2(gp_Pnt(0, 0, 0), gp_Dir(vec_1[0], vec_1[1], vec_1[2])),inner_radius)
        edge_1 = BRepBuilderAPI_MakeEdge(circle_1).Edge()  # 线
        wire_1 = BRepBuilderAPI_MakeWire(edge_1).Wire()  # 多段线
        face_1 = BRepBuilderAPI_MakeFace(wire_1).Face()  # 平面
        edge_2 = BRepBuilderAPI_MakeEdge(circle_2).Edge()  # 线
        wire_2 = BRepBuilderAPI_MakeWire(edge_2).Wire()  # 多段线
        face_2 = BRepBuilderAPI_MakeFace(wire_2).Face()  # 平面
        cylinder_1 = BRepOffsetAPI_MakePipe(circle_line_profile, face_1).Shape()  #　外圆柱
        cylinder_2 = BRepOffsetAPI_MakePipe(circle_line_profile, face_2).Shape()  # 内圆柱
        hole_cylinder = BRepAlgoAPI_Cut(cylinder_1,cylinder_2).Shape()
        fuse_solid = BRepAlgoAPI_Fuse(rectangle_solid,hole_cylinder).Shape()
        return fuse_solid

    def create_support_bolt_model(self):
        """
        创建斜撑螺栓模型
        :return:
        """
        support_bolt_info = self.occ_data.get_ifc_support_bolt_info()
        bolt_loc = support_bolt_info["bolt_loc"]
        bolt_inner_radius = support_bolt_info["bolt_inner_radius"]
        bolt_outer_radius = support_bolt_info["bolt_outer_radius"]
        bolt_profile = support_bolt_info["bolt_profile"]
        plate_profile = support_bolt_info["plate_profile"]
        plate_shape = support_bolt_info["plate_shape"]
        single_solid = self.tool_form_combine_solid_model(bolt_inner_radius,bolt_outer_radius,bolt_profile,plate_profile,
                                                          plate_shape)
        main_solid = self.tool_occ_model_transform(bolt_loc,single_solid)
        return main_solid




    def obtain_overall_construct_rebar_model(self):
        """
        获取完整的构造钢筋模型
        :return:
        """
        construct_horizon_rebar_model = self.create_construct_horizon_rebar_model()
        construct_vertical_rebar_model = self.create_construct_vertical_rebar_model()
        main_model = BRepAlgoAPI_Fuse(construct_horizon_rebar_model, construct_vertical_rebar_model).Shape()
        return main_model

    def obtain_overall_truss_top_bottom_long_rebar_model(self):
        """
        合并桁架上弦和下弦纵筋模型
        :return:
        """
        truss_bottom_long_rebar_model = self.create_truss_bottom_long_rebar_model()
        truss_top_long_rebar_model = self.create_truss_top_long_rebar_model()
        main_model = BRepAlgoAPI_Fuse(truss_bottom_long_rebar_model, truss_top_long_rebar_model).Shape()
        return main_model

    def obtain_overall_truss_rebar_model(self):
        """
        获取完整的桁架钢筋模型：桁架马镫筋、桁架上弦纵筋、桁架下弦纵筋
        :return:
        """
        truss_bottom_top_long_rebar_model = self.obtain_overall_truss_top_bottom_long_rebar_model()
        truss_stirrup_model = self.create_truss_stirrup_rebar_model()
        main_model = BRepAlgoAPI_Fuse(truss_bottom_top_long_rebar_model, truss_stirrup_model).Shape()
        return main_model

    def obtain_overall_rebar_model(self):
        """
        获取完整钢筋模型
        :return:
        """
        construct_rebar_model = self.obtain_overall_construct_rebar_model()
        truss_model = self.obtain_overall_truss_rebar_model()
        # 完整钢筋模型
        main_model = BRepAlgoAPI_Fuse(construct_rebar_model, truss_model).Shape()
        return main_model

    def obtain_double_shear_wall_solid(self):
        """
        获取双皮剪力墙实体
        :return:
        """
        exterior_solid_model = self.create_double_shear_wall_exterior_solid()
        interior_solid_model = self.create_double_shear_wall_interior_solid()
        main_model = BRepAlgoAPI_Fuse(exterior_solid_model, interior_solid_model).Shape()
        return main_model

    def obtain_overall_double_shear_wall_model(self):
        """
        获取完整双皮剪力墙模型
        :return:
        """
        wall_model = self.obtain_double_shear_wall_solid()
        construct_rebar_model = self.obtain_overall_construct_rebar_model()
        truss_model = self.obtain_overall_truss_rebar_model()
        # 完整钢筋模型
        main_model = BRepAlgoAPI_Fuse(construct_rebar_model, truss_model).Shape()
        # 完整实体和钢筋模型
        total_model = BRepAlgoAPI_Fuse(main_model,wall_model).Shape()
        return total_model

    def obtain_double_shear_wall_minus_pvc_hole_model(self):
        """
        获取双皮剪力墙减去pvc管孔洞模型：两片剪力墙实体、pvc管孔洞
        :return:
        """
        double_shear_wall_solid = self.obtain_double_shear_wall_solid()
        pvc_hole_solid = self.create_pvc_hole_solid_model()
        cut_solid = BRepAlgoAPI_Cut(double_shear_wall_solid,pvc_hole_solid).Shape()
        return cut_solid

    def obtain_double_shear_wall_and_pvc_hole_model(self):
        """
        获取双皮剪力墙加上pvc管孔洞模型：两片剪力墙实体、pvc管孔洞
        :return:
        """
        double_shear_wall_solid = self.obtain_double_shear_wall_solid()
        pvc_hole_solid = self.create_pvc_hole_solid_model()
        main_solid = BRepAlgoAPI_Fuse(double_shear_wall_solid,pvc_hole_solid).Shape()
        return main_solid

    def obtain_double_shear_wall_and_hoist_embedded_model(self):
        """
        将双皮剪力墙实体和吊装预埋件形成整体：双皮剪力墙实体、吊装预埋件
        :return:
        """
        double_shear_wall_model = self.obtain_double_shear_wall_solid()
        hoist_embedded_model = self.create_hoist_embedded_part_model()
        main_solid = BRepAlgoAPI_Fuse(double_shear_wall_model,hoist_embedded_model).Shape()
        return main_solid





