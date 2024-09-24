"""
模型数据：为图形绘制和标注提供基础数据
"""
import copy
import math

from GenerateDrawing.occ_model import BuildOCCSolid
from GenerateDrawing.special_function import compute_project_shape_axis,get_polygon_bounding_box_points,\
    get_point_sequence_bounding_box_points,point_sets_sort,transform_point_set_to_segment,rotation_3d,\
    compute_solid_cut_profile_shape,get_rectangle_rebar_shape_center_position,get_polygon_points_y_to_positive_value,\
    choose_specific_value_from_polygon_points,choose_specific_value_from_polygon_points_to_specific_polygon,\
    form_total_straight_rebar_rectangle,transform_point_from_xy_plane_to_yx_plane
from GenerateDrawing.generate_occ_data import OCCData
from DoubleWallDesign.geometry import DoubleSideWall
import numpy as np
from typing import List


# 双皮剪力墙3D图数据
class DoubleShearWallViewData(object):
    """
    双皮剪力墙视图数据:所有xyz皆参考全局坐标系，x---双皮剪力墙宽度，y---双皮剪力墙厚度，z---双皮剪力墙高度
    Input: occ_model--OCC模型，occ_data---OCC数据
    """
    def __init__(self,double_wall_geo:DoubleSideWall,entity_type:List[str],object_name:List[str],occ_model:BuildOCCSolid,\
                 occ_data:OCCData):
        self.double_wall_geo = double_wall_geo
        self.entity_type = entity_type
        self.object_name = object_name
        self.occ_model = occ_model
        self.occ_data = occ_data

    def generate_double_shear_wall_XOZ_projection_data(self):
        """
        产生双皮剪力墙XOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成
        :return:
        """
        double_shear_wall_model = self.occ_model.obtain_double_shear_wall_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,-1,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(double_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_hoist_embedded_part_XOZ_projection_data(self):
        """
        产生吊装预埋件XOZ平面投影数据
        :return:
        """
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        rebar_diam = hoist_embedded_info["diam"]
        left_projection_length = hoist_embedded_info["left_project_length"]
        local_rebar = [[-rebar_diam/2,0,0],[-rebar_diam/2,-left_projection_length,0],[rebar_diam/2,-left_projection_length,0],\
                       [rebar_diam/2,0,0],[-rebar_diam/2,0,0]]
        hoist_loc = hoist_embedded_info["hoist_loc"]
        # 平移所有钢筋
        total_hoist_rebar = []
        for i in range(len(hoist_loc)):
            curr_move = hoist_loc[i]
            curr_rebar = []
            for j in range(len(local_rebar)):
                curr_point = np.array(local_rebar[j])+np.array([curr_move[0],curr_move[2],0])
                curr_rebar.append(curr_point.tolist())
            total_hoist_rebar.append(curr_rebar)
        # 将所有钢筋制成线段
        total_profile_points = []
        for single_rebar in total_hoist_rebar:
            single_seg = []
            for num in range(len(single_rebar)-1):
                single_seg.append([tuple(single_rebar[num]),tuple(single_rebar[num+1])])
            total_profile_points.append(single_seg)
        return total_profile_points

    def generate_truss_top_long_rebar_XOZ_projection_data(self):
        """
        获取桁架顶部纵向钢筋XOZ平面投影数据
        :return:
        """
        projection_info = self.occ_data.get_ifc_truss_top_long_rebar(self.entity_type[2],self.object_name[1])
        projection_points = projection_info["profile"]
        return projection_points

    def generate_pvc_hole_XOZ_projection_data(self):
        """
        产生PVC孔洞XOZ投影数据：字典
        :return:
        """
        pvc_hole_info = self.occ_data.get_ifc_pvc_hole_info()
        return pvc_hole_info

    def generate_support_bolt_XOZ_projection_data(self):
        """
        产生斜撑螺栓XOZ平面投影数据
        :return:
        """
        support_bolt_info = self.occ_data.get_ifc_support_bolt_info()
        return support_bolt_info

    def generate_form_front_view_bottom_dimension_points(self):
        """
        获取模板主视图底部标注数据：模板轮廓数据、pvc管数据、斜撑螺栓数据
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_bottom_loc = [[form_bbox.min_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.min_y,0]]
        second_floor_dimension = [[(form_bbox.min_x,form_bbox.min_y,0),(form_bbox.max_x,form_bbox.min_y,0)]]
        # 获取PVC管的坐标
        pvc_hole_info = self.generate_pvc_hole_XOZ_projection_data()
        hole_loc = pvc_hole_info["hole_loc"]  # 孔洞位置，在xyz三维空间的定位
        pvc_hole_bbox = get_point_sequence_bounding_box_points(hole_loc)
        bottom_hole_loc = [[pvc_hole_bbox.min_x,form_bbox.min_y,0],[pvc_hole_bbox.max_x,form_bbox.min_y,0]]
        # 获取斜撑螺栓的坐标
        support_bolt_info = self.generate_support_bolt_XOZ_projection_data()
        bolt_loc = support_bolt_info["bolt_loc"]
        bolt_bbox = get_point_sequence_bounding_box_points(bolt_loc)
        bottom_bolt_loc = [[bolt_bbox.min_x, form_bbox.min_y, 0], [bolt_bbox.max_x, form_bbox.min_y, 0]]

        # 所有待标注点
        total_dimension_points = []
        total_dimension_points.extend(form_bottom_loc)
        total_dimension_points.extend(bottom_bolt_loc)
        total_dimension_points.extend(bottom_hole_loc)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(total_dimension_points,index)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_form_front_view_top_dimension_points(self):
        """
        产生模板主视图顶部标注点：模板轮廓点、吊装预埋件点、pvc管点、斜撑螺栓点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_top_loc = [[form_bbox.min_x, form_bbox.max_y, 0], [form_bbox.max_x, form_bbox.max_y, 0]]
        # 获取
        # 获取PVC管的坐标
        pvc_hole_info = self.generate_pvc_hole_XOZ_projection_data()
        hole_loc = pvc_hole_info["hole_loc"]  # 孔洞位置，在xyz三维空间的定位
        pvc_hole_bbox = get_point_sequence_bounding_box_points(hole_loc)
        top_hole_loc = [[pvc_hole_bbox.min_x, form_bbox.max_y, 0], [pvc_hole_bbox.max_x, form_bbox.max_y, 0]]
        # 获取斜撑螺栓的坐标
        support_bolt_info = self.generate_support_bolt_XOZ_projection_data()
        bolt_loc = support_bolt_info["bolt_loc"]
        bolt_bbox = get_point_sequence_bounding_box_points(bolt_loc)
        top_bolt_loc = [[bolt_bbox.min_x, form_bbox.max_y, 0], [bolt_bbox.max_x, form_bbox.max_y, 0]]
        # 吊装预埋件点
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        hoist_loc = hoist_embedded_info["hoist_loc"]
        top_hoist_loc = [[hoist_loc[0][0],form_bbox.max_y, 0],[hoist_loc[1][0],form_bbox.max_y, 0]]
        # 获取桁架上弦钢筋的x坐标
        truss_top_rebar_profile = self.generate_truss_top_long_rebar_XOZ_projection_data()
        truss_top_rebar_loc = [[seg[0][0],form_bbox.max_y, 0] for seg in truss_top_rebar_profile]
        # 形成第一层标注点
        first_sequence_point = []
        first_sequence_point.extend(form_top_loc)
        first_sequence_point.extend(top_hole_loc)
        first_sequence_point.extend(top_bolt_loc)
        first_sequence_point.extend(top_hoist_loc)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(first_sequence_point,index,reverse=True)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 形成第二层标注点
        second_sequence_point = []
        second_sequence_point.extend(form_top_loc)
        second_sequence_point.extend(truss_top_rebar_loc)
        total_sort_point = point_sets_sort(second_sequence_point,index,reverse=True)
        second_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_interior_construct_horizon_rebar_info(self):
        """
        产生内层构造水平钢筋信息
        :return:
        """
        construct_horizon_rebar_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],self.object_name[0])
        construct_horizon_rebar = construct_horizon_rebar_info["profile"]
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        mean_y = (form_bbox.min_y+form_bbox.max_y)/2
        index = 1
        interior_construct_horizon_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_horizon_rebar,index,mean_y,flag=True)
        rebar_info = {}
        rebar_info["diam"] = 2*construct_horizon_rebar_info["Radius"]
        rebar_info["profile"] = interior_construct_horizon_rebar
        return rebar_info

    def generate_exterior_construct_horizon_rebar_info(self):
        """
        产生外层构造水平钢筋信息
        :return:
        """
        construct_horizon_rebar_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],self.object_name[0])
        construct_horizon_rebar = construct_horizon_rebar_info["profile"]
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        mean_y = (form_bbox.min_y+form_bbox.max_y)/2
        index = 1
        exterior_construct_horizon_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_horizon_rebar,index,mean_y,flag=False)
        rebar_info = {}
        rebar_info["diam"] = 2*construct_horizon_rebar_info["Radius"]
        rebar_info["profile"] = exterior_construct_horizon_rebar
        return rebar_info

    def generate_interior_construct_vertical_rebar_info(self):
        """
        产生内层构造竖向钢筋信息
        :return:
        """
        construct_vertical_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                                 self.object_name[0])
        construct_vertical_rebar = construct_vertical_info["profile"]
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        mean_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        interior_construct_vertical_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_vertical_rebar, index, mean_y, flag=True)
        rebar_info = {}
        rebar_info["diam"] = 2 * construct_vertical_info["Radius"]
        rebar_info["profile"] = interior_construct_vertical_rebar
        return rebar_info

    def generate_exterior_construct_vertical_rebar_info(self):
        """
        产生外层构造竖向钢筋信息
        :return:
        """
        construct_vertical_rebar_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                                     self.object_name[0])
        construct_vertical_rebar = construct_vertical_rebar_info["profile"]
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        mean_y = (form_bbox.min_y+form_bbox.max_y)/2
        index = 1
        exterior_construct_vertical_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_vertical_rebar,index,mean_y,flag=False)
        rebar_info = {}
        rebar_info["diam"] = 2*construct_vertical_rebar_info["Radius"]
        rebar_info["profile"] = exterior_construct_vertical_rebar
        return rebar_info


    def generate_form_front_view_left_dimension_points(self):
        """
        产生模板主视图左侧标注点：模板轮廓点、pvc管数据
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_left_loc = [[form_bbox.min_x, form_bbox.min_y, 0], [form_bbox.min_x, form_bbox.max_y, 0]]
        # 去掉重复的元素
        # 获取斜撑螺栓的坐标
        support_bolt_info = self.generate_support_bolt_XOZ_projection_data()
        bolt_loc = support_bolt_info["bolt_loc"]
        # 获取PVC管的坐标
        pvc_hole_info = self.generate_pvc_hole_XOZ_projection_data()
        hole_loc = pvc_hole_info["hole_loc"]  # 孔洞位置，在xyz三维空间的定位
        loc_y = []
        for point in bolt_loc:
            loc_y.append(point[2])
        for point in hole_loc:
            loc_y.append(point[2])
        loc_y = list(set(loc_y))
        first_floor_loc = []
        for index in loc_y:
            first_floor_loc.append([form_bbox.min_x,index,0])
        first_floor_loc.extend(form_left_loc)
        index = 1  # 按照y坐标进行排序
        total_sort_point = point_sets_sort(first_floor_loc,index,reverse=True)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 获取第二层
        total_sort_point = point_sets_sort(form_left_loc,index,reverse=True)
        second_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_form_front_view_right_dimension_points(self):
        """
        产生模板主视图右侧标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_right_loc = [[form_bbox.max_x, form_bbox.min_y, 0], [form_bbox.max_x, form_bbox.max_y, 0]]
        # 去掉重复的元素
        # 获取斜撑螺栓的坐标
        support_bolt_info = self.generate_support_bolt_XOZ_projection_data()
        bolt_loc = support_bolt_info["bolt_loc"]
        # 获取PVC管的坐标
        pvc_hole_info = self.generate_pvc_hole_XOZ_projection_data()
        hole_loc = pvc_hole_info["hole_loc"]  # 孔洞位置，在xyz三维空间的定位
        loc_y = []
        for point in bolt_loc:
            loc_y.append(point[2])
        for point in hole_loc:
            loc_y.append(point[2])
        loc_y = list(set(loc_y))
        first_floor_loc = []
        for index in loc_y:
            first_floor_loc.append([form_bbox.max_x,index,0])
        first_floor_loc.extend(form_right_loc)
        index = 1  # 按照y坐标进行排序
        total_sort_point = point_sets_sort(first_floor_loc,index)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info

    # 双皮剪力墙
    def generate_double_shear_wall_YOZ_projection_data(self):
        """
        产生双皮剪力墙YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成---右视图
        :return:
        """
        double_shear_wall_model = self.occ_model.obtain_double_shear_wall_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(double_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    # 双皮剪力墙
    def generate_exterior_shear_wall_YOZ_projection_data(self):
        """
        产生外皮剪力墙YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成---右视图
        :return:
        """
        exterior_shear_wall_model = self.occ_model.create_double_shear_wall_exterior_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(exterior_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    # 双皮剪力墙
    def generate_interior_shear_wall_YOZ_projection_data(self):
        """
        产生内皮剪力墙YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成---右视图
        :return:
        """
        interior_shear_wall_model = self.occ_model.create_double_shear_wall_interior_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(interior_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_pvc_hole_YOZ_projection_data(self):
        """
        产生PVC管YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成----pvc管
        :return:
        """
        pvc_hole_model = self.occ_model.create_pvc_hole_solid_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(pvc_hole_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_hoist_embedded_YOZ_projection_data(self):
        """
        产生吊装预埋件YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成----吊装预埋件
        :return:
        """
        hoist_embedded_model = self.occ_model.create_single_hoist_embedded_part_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(hoist_embedded_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_support_embedded_YOZ_projection_data(self):
        """
        产生斜撑螺栓YOZ平面投影数据:投影平面y轴是由视线方向与投影坐标系的x轴通过叉乘形成----吊装预埋件
        :return:
        """
        support_embedded_model = self.occ_model.create_support_bolt_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(support_embedded_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_form_right_view_bottom_dimension_points(self):
        """
        获取模板右视图底部标注数据：模板轮廓数据、pvc管数据、斜撑螺栓数据、吊装埋件数据
        :return:
        """
        # 获取外层模板数据
        form_projection_data_e = self.generate_exterior_shear_wall_YOZ_projection_data()
        form_bbox_e = get_polygon_bounding_box_points(form_projection_data_e)
        form_bottom_loc_e = [[form_bbox_e.min_x,form_bbox_e.min_y,0],[form_bbox_e.max_x,form_bbox_e.min_y,0]]
        # 获取内层模板数据
        form_projection_data_i = self.generate_interior_shear_wall_YOZ_projection_data()
        form_bbox_i = get_polygon_bounding_box_points(form_projection_data_i)
        form_bottom_loc_i = [[form_bbox_i.min_x,form_bbox_i.min_y,0],[form_bbox_i.max_x,form_bbox_i.min_y,0]]
        # 所有待标注点
        total_dimension_points = []
        total_dimension_points.extend(form_bottom_loc_e)
        total_dimension_points.extend(form_bottom_loc_i)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(total_dimension_points,index)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        form_projection_data = self.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_bottom_loc = [[[form_bbox.min_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.min_y,0]]]
        # 形成完整标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = form_bottom_loc
        return total_dimension_info

    def generate_form_right_view_left_dimension_points(self):
        """
        获取模板右视图底部标注数据：模板轮廓数据、pvc管数据、斜撑螺栓数据、吊装埋件数据
        :return:
        """
        # 所有标注信息
        form_projection_data = self.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_bottom_loc = [[[form_bbox.min_x, form_bbox.max_y, 0], [form_bbox.min_x, form_bbox.min_y, 0]]]
        # 形成完整标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = form_bottom_loc
        return total_dimension_info

    def generate_double_shear_wall_XOY_projection_data(self):
        """
        产生双皮剪力墙XOY平面的投影数据
        :return:
        """
        double_shear_wall_model = self.occ_model.obtain_double_shear_wall_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(double_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_exterior_shear_wall_XOY_projection_data(self):
        """
        产生外皮剪力墙XOY平面的投影数据
        :return:
        """
        exterior_shear_wall_model = self.occ_model.create_double_shear_wall_exterior_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(exterior_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_interior_shear_wall_XOY_projection_data(self):
        """
        产生内皮剪力墙XOY平面的投影数据
        :return:
        """
        interior_shear_wall_model = self.occ_model.create_double_shear_wall_interior_solid()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(interior_shear_wall_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    # 模板俯视图
    def generate_support_bolt_XOY_projection_data(self):
        """
        产生斜撑螺栓XOY平面的投影数据
        :return:
        """
        support_bolt_model = self.occ_model.create_support_bolt_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(support_bolt_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_pvc_hole_XOY_projection_data(self):
        """
        产生PVC管XOY平面的投影数据
        :return:
        """
        pvc_hole_model = self.occ_model.create_pvc_hole_solid_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(pvc_hole_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_truss_bottom_and_top_long_rebar_XOY_projection_data(self):
        """
        产生所有桁架下弦和上弦钢筋XOY平面的投影数据
        :return:
        """
        truss_top_bottom_long_model = self.occ_model.obtain_overall_truss_top_bottom_long_rebar_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(truss_top_bottom_long_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data


    def generate_truss_construct_rebar_XOY_projection_data(self):
        """
        产生所有桁架构造钢筋XOY平面的投影数据
        :return:
        """
        total_construct_rebar_model = self.occ_model.obtain_overall_construct_rebar_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(total_construct_rebar_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_truss_stirrup_rebar_XOY_projection_data(self):
        """
        产生所有桁架马镫筋XOY平面的投影数据
        :return:
        """
        truss_stirrup_rebar_model = self.occ_model.create_truss_stirrup_rebar_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [1,0,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [0,0,1]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(truss_stirrup_rebar_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_truss_stirrup_straight_rebar_XOY_projection_data(self):
        """
        产生桁架马镫筋直筋XOY平面投影数据
        :return:
        """
        truss_stirrup_points = self.occ_data.get_ifc_truss_stirrup_rebar(self.entity_type[2], self.object_name[1])
        rebar_profiles = truss_stirrup_points["profile"]
        total_seg = [[rebar_seg[0][0],rebar_seg[1][0]] for rebar_seg in rebar_profiles]
        rebar_radius = truss_stirrup_points["Radius"]
        total_rebar_rec = form_total_straight_rebar_rectangle(total_seg,rebar_radius)
        return total_rebar_rec

    def generate_form_top_view_bottom_dimension_points(self):
        """
        产生模板俯视图底部标注点
        :return:
        """
        # 获取外层模板数据
        form_projection_data_e = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data_e)
        form_bottom_loc = [[[form_bbox.min_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.min_y,0]]]
        # 形成完整标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = form_bottom_loc
        return total_dimension_info

    def generate_form_top_view_left_dimension_points(self):
        """
        产生模板俯视图左侧标注点
        :return:
        """
        # 获取外层模板数据
        form_projection_data_e = self.generate_exterior_shear_wall_XOY_projection_data()
        form_bbox_e = get_polygon_bounding_box_points(form_projection_data_e)
        form_left_loc_e = [[form_bbox_e.min_x,form_bbox_e.max_y,0],[form_bbox_e.min_x,form_bbox_e.min_y,0]]
        # 获取内层模板数据
        form_projection_data_i = self.generate_interior_shear_wall_XOY_projection_data()
        form_bbox_i = get_polygon_bounding_box_points(form_projection_data_i)
        form_left_loc_i = [[form_bbox_i.min_x,form_bbox_i.min_y,0],[form_bbox_i.min_x,form_bbox_i.max_y,0]]
        # 所有待标注点
        total_dimension_points = []
        total_dimension_points.extend(form_left_loc_e)
        total_dimension_points.extend(form_left_loc_i)
        index = 1  # 按照y坐标进行排序
        total_sort_point = point_sets_sort(total_dimension_points,index,reverse=True)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_left_loc = [[[form_bbox.min_x,form_bbox.max_y,0],[form_bbox.min_x,form_bbox.min_y,0]]]
        # 形成完整标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = form_left_loc
        return total_dimension_info

    def generate_double_wall_three_dim_XOZ_projection_data(self):
        """
        产生双皮剪力墙XOZ平面的投影数据
        :return:
        """
        # project_coord_origin = [0,0,0]  # 投影坐标系原点
        # project_coord_dir_x = [math.sqrt(3)/2,1/2,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        # gazing_direction = [1/2,-math.sqrt(3)/2,0]  # 视线方向
        origin = [0, 0, 0]
        normal_direction = np.asarray([1, 0, 0])  # 轴方向
        normal_x_direction = np.asarray([0, 1, 0])  # Nx方向
        _BASE_X_AXIS = np.asarray([0,0,1])
        # 变换一次
        angle_1 = math.pi / 10
        angle_x_1 = angle_1 / 6
        change_normal_direction_1 = rotation_3d(normal_direction, _BASE_X_AXIS, -angle_1)
        change_normal_x_direction_1 = rotation_3d(normal_x_direction, change_normal_direction_1, 0)
        # 变换两次
        angle_2 = -math.pi/7
        change_normal_direction_2 = rotation_3d(change_normal_direction_1,change_normal_x_direction_1,angle_2)
        change_normal_x_direction_2 = rotation_3d(change_normal_x_direction_1,change_normal_direction_2,angle_2)
        # 投影平面为通过normal_x与(normal_direction与normal_x_direction叉乘形成的新方向)组成的平面
        base_normal_dir = [change_normal_direction_1[0],change_normal_direction_1[1],change_normal_direction_1[2]]
        base_normal_x_dir = [change_normal_x_direction_1[0],change_normal_x_direction_1[1],change_normal_x_direction_1[2]]
        # 获取双皮剪力墙投影数据
        double_wall_model = self.occ_model.obtain_double_shear_wall_solid()
        # 获取实体投影数据
        double_wall_projection_data = compute_project_shape_axis(double_wall_model,origin,
                                                     base_normal_dir,base_normal_x_dir)
        # double_wall_projection_data = compute_project_shape_axis(double_wall_model,project_coord_origin,
        #                                              gazing_direction,project_coord_dir_x)
        # 获取吊装预埋件模型投影数据
        hoist_embedded_model = self.occ_model.create_hoist_embedded_part_model()
        # 获取实体投影数据
        hoist_embedded_projection_data = compute_project_shape_axis(hoist_embedded_model,origin,
                                                     base_normal_dir,base_normal_x_dir)
        # 获取pvc管孔洞模型投影数据
        pvc_hole_model = self.occ_model.create_pvc_hole_solid_model()
        # 获取实体投影数据
        pvc_hole_projection_data = compute_project_shape_axis(pvc_hole_model,origin,
                                                     base_normal_dir,base_normal_x_dir)
        # 获取pvc管孔洞模型投影数据
        pvc_hole_model = self.occ_model.create_pvc_hole_solid_model()
        # 获取实体投影数据
        pvc_hole_projection_data = compute_project_shape_axis(pvc_hole_model,origin,
                                                     base_normal_dir,base_normal_x_dir)
        # 获取斜撑螺栓模型投影数据
        support_bolt_model = self.occ_model.create_support_bolt_model()
        # 获取实体投影数据
        support_bolt_projection_data = compute_project_shape_axis(support_bolt_model,origin,
                                                     base_normal_dir,base_normal_x_dir)
        return double_wall_projection_data,hoist_embedded_projection_data,pvc_hole_projection_data,\
               support_bolt_projection_data


    def generate_construct_horizon_rebar_XOZ_cut_data(self):
        """
        产生所有构造横向钢筋XOZ平面的投影数据
        :return:
        """
        construct_horizon_rebar_model = self.occ_model.create_construct_horizon_rebar_model()
        # 获取构造横向钢筋坐标点
        construct_horizon_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],
                                                                                      self.object_name[0])
        profile_points = construct_horizon_info["profile"]
        plane_point = list(profile_points[0][0])
        direction = [0,1,0]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_horizon_rebar_model,plane_point,direction)
        return cut_profile

    def generate_construct_vertical_rebar_XOZ_cut_data(self):
        """
        产生构造竖向钢筋XOZ平面剖切数据
        :return:
        """
        construct_vertical_rebar_model = self.occ_model.create_construct_vertical_rebar_model()
        # 获取构造横向钢筋坐标点
        construct_vertical_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                                      self.object_name[0])
        profile_points = construct_vertical_info["profile"]
        plane_point = list(profile_points[0][0])
        direction = [0,1,0]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_vertical_rebar_model,plane_point,direction)
        return cut_profile

    def generate_rebar_reinforcement_view_bottom_dimension_points(self):
        """
        获取配筋图底部标注数据：模板轮廓数据、横向构造钢筋数据
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_bottom_loc = [[form_bbox.min_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.min_y,0]]
        second_floor_dimension = [[(form_bbox.min_x,form_bbox.min_y,0),(form_bbox.max_x,form_bbox.min_y,0)]]
        # 获取横向构造钢筋坐标点
        construct_horizon_rebar = self.generate_construct_horizon_rebar_XOZ_cut_data()
        rebar_bbox = get_polygon_bounding_box_points(construct_horizon_rebar)
        bottom_rebar_loc = [[rebar_bbox.min_x,form_bbox.min_y,0],[rebar_bbox.max_x,form_bbox.min_y,0]]

        # 所有待标注点
        total_dimension_points = []
        total_dimension_points.extend(form_bottom_loc)
        total_dimension_points.extend(bottom_rebar_loc)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(total_dimension_points,index)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_rebar_reinforcement_view_top_dimension_points(self):
        """
        获取配筋图顶部标注数据：模板轮廓数据、横向构造钢筋数据
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_top_loc = [[form_bbox.min_x,form_bbox.max_y,0],[form_bbox.max_x,form_bbox.max_y,0]]
        # 获取横向构造钢筋坐标点
        construct_horizon_rebar = self.generate_construct_horizon_rebar_XOZ_cut_data()
        horizon_rebar_bbox = get_polygon_bounding_box_points(construct_horizon_rebar)
        top_horizon_rebar_loc = [[horizon_rebar_bbox.min_x,form_bbox.max_y,0],[horizon_rebar_bbox.max_x,form_bbox.max_y,0]]
        # 获取桁架上弦钢筋的x坐标
        truss_top_rebar_profile = self.generate_truss_top_long_rebar_XOZ_projection_data()
        truss_top_rebar_loc = [[seg[0][0],form_bbox.max_y, 0] for seg in truss_top_rebar_profile]
        # 获取竖向构造钢筋坐标点
        construct_vertical_rebar = self.generate_construct_vertical_rebar_XOZ_cut_data()
        construct_vertical_rebar_loc = get_rectangle_rebar_shape_center_position(construct_vertical_rebar)
        top_vertical_rebar_loc = [[point[0],form_bbox.max_y,0] for point in construct_vertical_rebar_loc]
        # 第一层待标注点
        first_dimension_points = []
        first_dimension_points.extend(form_top_loc)
        first_dimension_points.extend(top_horizon_rebar_loc)
        first_dimension_points.extend(top_vertical_rebar_loc)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(first_dimension_points,index,reverse=True)  # 从大到小排序
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 第二层待标注点
        second_dimension_points = []
        second_dimension_points.extend(form_top_loc)
        second_dimension_points.extend(truss_top_rebar_loc)
        index = 0 # 按照x坐标进行排序
        total_sort_point = point_sets_sort(second_dimension_points,index,reverse=True)
        second_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_rebar_reinforcement_view_left_dimension_points(self):
        """
        获取配筋图左侧标注数据：模板轮廓数据、竖向构造钢筋数据
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_left_loc = [[form_bbox.min_x,form_bbox.max_y,0],[form_bbox.min_x,form_bbox.min_y,0]]
        # 获取竖向构造钢筋坐标点
        construct_vertical_rebar = self.generate_construct_vertical_rebar_XOZ_cut_data() # 剖切数据
        rebar_bbox = get_polygon_bounding_box_points(construct_vertical_rebar)
        left_vertical_rebar_loc = [[form_bbox.min_x,rebar_bbox.min_z,0],[form_bbox.min_x,rebar_bbox.max_z,0]]
        # 第一层待标注点
        first_dimension_points = []
        first_dimension_points.extend(form_left_loc)
        first_dimension_points.extend(left_vertical_rebar_loc)
        index = 1  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(first_dimension_points,index,reverse=True)  # 从大到小排序
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 第二层待标注点
        second_floor_dimension = [form_left_loc]
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = second_floor_dimension
        return total_dimension_info

    def generate_rebar_reinforcement_view_right_dimension_points(self):
        """
        获取配筋图右侧标注数据：模板轮廓数据、横向构造钢筋数据、竖向构造钢筋
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_right_loc = [[form_bbox.max_x,form_bbox.max_y,0],[form_bbox.max_x,form_bbox.min_y,0]]
        # 获取竖向构造钢筋坐标点
        construct_vertical_rebar = self.generate_construct_vertical_rebar_XOZ_cut_data() # 剖切数据
        rebar_bbox = get_polygon_bounding_box_points(construct_vertical_rebar)
        right_vertical_rebar_loc = [[form_bbox.max_x,rebar_bbox.min_z,0],[form_bbox.max_x,rebar_bbox.max_z,0]]
        # 获取横向构造钢筋轴心坐标点
        construct_horizon_rebar = self.generate_construct_horizon_rebar_XOZ_cut_data()
        construct_horizon_rebar_loc = get_rectangle_rebar_shape_center_position(construct_horizon_rebar)
        right_horizon_rebar_loc = [[form_bbox.max_x,point[2],0] for point in construct_horizon_rebar_loc]
        # 第一层待标注点
        first_dimension_points = []
        first_dimension_points.extend(form_right_loc)
        first_dimension_points.extend(right_vertical_rebar_loc)
        first_dimension_points.extend(right_horizon_rebar_loc)
        index = 1  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(first_dimension_points,index)  # 从大到小排序
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info

    def generate_rebar_reinforcement_view_cut_line_points(self):
        """
        产生配筋图剖切线点：表示方法：点、方向、文本
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        # 获取1-1剖切线
        point_left_1 = [form_bbox.min_x,(form_bbox.min_y+form_bbox.max_y)/2,0]
        direction_left_1 = np.asarray([-1,0,0])
        point_right_2 = [form_bbox.max_x,(form_bbox.min_y+form_bbox.max_y)/2,0]
        direction_right_2 = np.asarray([1,0,0])
        text_left_right = "1"
        text_align_loc_1 = 1
        # 获取2-2剖切线
        point_bottom_1 = [(form_bbox.min_x+form_bbox.max_x)/2,form_bbox.min_y,0]
        direction_bottom_1 = np.asarray([0,-1,0])
        point_top_2 = [(form_bbox.min_x+form_bbox.max_x)/2,form_bbox.max_y,0]
        direction_top_2 = np.asarray([0,1,0])
        text_bottom_top = "2"
        text_align_loc_2 = 2
        # 获取总体剖切信息
        total_info = [[point_left_1,direction_left_1,text_left_right,text_align_loc_1],[point_right_2,direction_right_2,text_left_right,text_align_loc_1],\
                      [point_bottom_1,direction_bottom_1,text_bottom_top,text_align_loc_2],[point_top_2,direction_top_2,text_bottom_top,text_align_loc_2]]
        return total_info

    def generate_rebar_reinforcement_view_outline_shape_points(self):
        """
        产生配筋图引出线形状点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        # 获取竖向构造钢筋坐标点
        construct_vertical_rebar = self.generate_construct_vertical_rebar_XOZ_cut_data()  # 剖切数据
        vertical_rebar_bbox = get_polygon_bounding_box_points(construct_vertical_rebar)

        # 获取横向构造钢筋轴心坐标点
        construct_horizon_rebar = self.generate_construct_horizon_rebar_XOZ_cut_data()
        horizon_rebar_bbox = get_polygon_bounding_box_points(construct_horizon_rebar)
        # 横向钢筋引出线
        horizon_rebar_point_s = [(2*horizon_rebar_bbox.min_x/5+3*horizon_rebar_bbox.max_x/5),\
                                 horizon_rebar_bbox.max_z,0]
        length_1 = abs(form_bbox.max_y-horizon_rebar_bbox.max_z)
        direction_1 = np.asarray([0,1,0])
        text_1 = "1"
        # 纵向钢筋引出线
        vertical_rebar_point_s = [vertical_rebar_bbox.max_x,vertical_rebar_bbox.max_z,0] # 起点坐标
        length_2 = abs(form_bbox.max_y-vertical_rebar_bbox.max_z)  # 长度
        direction_2 = np.asarray([0,1,0])  # 引出线方向
        text_2 = "2"  # 文本内容
        # 所有信息
        total_info = [[horizon_rebar_point_s,length_1,direction_1,text_1],\
                      [vertical_rebar_point_s,length_2,direction_2,text_2]]
        return total_info

    def generate_construct_vertical_rebar_cut_points(self):
        """
        产生构造竖向钢筋剖切点
        :return:
        """
        construct_vertical_rebar_model = self.occ_model.create_construct_vertical_rebar_model()
        # 获取构造竖向钢筋坐标点
        construct_vertical_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                               self.object_name[0])
        profile_points = construct_vertical_info["profile"]
        plane_point = list(profile_points[0][0])
        direction = [0, 0, 1]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_vertical_rebar_model, plane_point, direction)
        return cut_profile

    def generate_construct_horizon_cut_points(self):
        """
        产生构造横向钢筋剖切点
        :return:
        """
        construct_horizon_rebar_model = self.occ_model.create_construct_horizon_rebar_model()
        # 获取构造横向钢筋坐标点
        construct_horizon_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],
                                                                               self.object_name[0])
        profile_points = construct_horizon_info["profile"]
        plane_point = list(profile_points[0][0])
        direction = [0, 0, 1]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_horizon_rebar_model, plane_point, direction)
        return cut_profile

    def generate_truss_top_and_bottom_rebar_cut_points(self):
        """
        产生桁架顶部和底部钢筋剖切点
        :return:
        """
        truss_top_bottom_rebar_model = self.occ_model.obtain_overall_truss_top_bottom_long_rebar_model()
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        plane_point = [(form_bbox.min_x+form_bbox.max_x)/2,(form_bbox.min_z+form_bbox.max_z)/2,
                           (form_bbox.min_y+form_bbox.max_y)/2]
        direction = [0, 0, 1]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(truss_top_bottom_rebar_model, plane_point, direction)
        return cut_profile

    def generate_truss_top_rebar_location_points(self):
        """
        产生桁架上部钢筋位置点
        :return:
        """
        # 获取桁架上弦纵筋信息
        truss_top_long_rebar_info = self.occ_data.get_ifc_truss_top_long_rebar(self.entity_type[2],self.object_name[1])
        return truss_top_long_rebar_info

    def generate_truss_bottom_rebar_location_points(self):
        """
        产生桁架下部钢筋位置点
        :return:
        """
        # 获取桁架下弦纵筋信息
        truss_bottom_long_rebar_info = self.occ_data.get_ifc_truss_bottom_long_rebar(self.entity_type[2],\
                                                                                     self.object_name[1])
        return truss_bottom_long_rebar_info

    def generate_construct_vertical_rebar_location_points(self):
        """
        产生构造竖向钢筋位置点
        :return:
        """
        construct_vertical_rebar_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1], self.object_name[0])
        return construct_vertical_rebar_info

    def generate_one_to_one_section_bottom_dimension_points(self):
        """
        获取1-1剖面图底部标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_bottom_loc = [[form_bbox.min_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.min_y,0]]
        # 获取构造水平钢筋数据
        construct_horizon_rebar_data = self.generate_construct_horizon_cut_points()
        construct_horizon_rebar_bbox = get_polygon_bounding_box_points(construct_horizon_rebar_data)
        horizon_rebar_bottom_loc = [[construct_horizon_rebar_bbox.min_x,form_bbox.min_y,0],\
                                    [construct_horizon_rebar_bbox.max_x,form_bbox.min_y,0]]
        # 第一层标注
        first_dimension_points = []
        first_dimension_points.extend(form_bottom_loc)
        first_dimension_points.extend(horizon_rebar_bottom_loc)
        #
        index = 0
        first_dimension_sort_point = point_sets_sort(first_dimension_points,index)
        first_floor_dimension = transform_point_set_to_segment(first_dimension_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        total_dimension_info["second_floor"] = [form_bottom_loc]
        return total_dimension_info

    def generate_one_to_one_section_top_dimension_points(self):
        """
        获取1-1剖面图顶部标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_top_loc = [[form_bbox.min_x, form_bbox.max_y, 0], [form_bbox.max_x, form_bbox.max_y, 0]]
        # 获取构造水平钢筋数据
        construct_horizon_rebar_data = self.generate_construct_horizon_cut_points()
        construct_horizon_rebar_bbox = get_polygon_bounding_box_points(construct_horizon_rebar_data)
        horizon_rebar_top_loc = [[construct_horizon_rebar_bbox.min_x, form_bbox.max_y, 0], \
                                    [construct_horizon_rebar_bbox.max_x, form_bbox.max_y, 0]]
        # 获取构造竖向钢筋数据
        construct_vertical_rebar_data = self.generate_construct_vertical_rebar_location_points()
        vertical_profile = construct_vertical_rebar_data["profile"]
        middle_y = (form_bbox.min_y+form_bbox.max_y)/2
        index = 0
        vertical_point = choose_specific_value_from_polygon_points(vertical_profile,index,middle_y,flag=False)
        vertical_rebar_points = [[point[0],form_bbox.max_y,0] for point in vertical_point]

        # 第一层标注
        first_dimension_points = []
        first_dimension_points.extend(form_top_loc)
        first_dimension_points.extend(horizon_rebar_top_loc)
        first_dimension_points.extend(vertical_rebar_points)
        #
        index = 0
        first_dimension_sort_point = point_sets_sort(first_dimension_points, index,reverse=True)
        first_floor_dimension = transform_point_set_to_segment(first_dimension_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info

    def generate_one_to_one_section_right_dimension_points(self):
        """
        获取1-1剖面图右侧标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        form_right_loc = [[form_bbox.max_x, form_bbox.min_y, 0], [form_bbox.max_x, form_bbox.max_y, 0]]
        # 获取构造水平钢筋数据
        construct_horizon_rebar_data = self.generate_construct_horizon_cut_points()
        construct_horizon_loc = get_rectangle_rebar_shape_center_position(construct_horizon_rebar_data)
        horizon_rebar_right_loc = [[form_bbox.max_x, point[1], 0] for point in construct_horizon_loc]
        # 获取构造竖向钢筋数据
        construct_vertical_rebar_data = self.generate_construct_vertical_rebar_location_points()
        vertical_profile = construct_vertical_rebar_data["profile"]
        middle_y = (form_bbox.min_y+form_bbox.max_y)/2
        index = 1
        top_vertical_point = choose_specific_value_from_polygon_points(vertical_profile,index,middle_y,flag=False)
        bottom_vertical_point = choose_specific_value_from_polygon_points(vertical_profile, index, middle_y)
        vertical_rebar_points = [[form_bbox.max_x,top_vertical_point[0][1],0],[form_bbox.max_x,bottom_vertical_point[0][1],0]]

        # 第一层标注
        first_dimension_points = []
        first_dimension_points.extend(form_right_loc)
        first_dimension_points.extend(horizon_rebar_right_loc)
        first_dimension_points.extend(vertical_rebar_points)
        #
        index = 1
        first_dimension_sort_point = point_sets_sort(first_dimension_points, index)
        first_floor_dimension = transform_point_set_to_segment(first_dimension_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info


    def generate_rebar_section_one_to_one_view_outline_shape_points(self):
        """
        产生1-1剖切图引出线形状点:3、4
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        # 获取构造竖向钢筋数据
        construct_vertical_rebar_data = self.generate_construct_vertical_rebar_location_points()
        vertical_profile = construct_vertical_rebar_data["profile"]
        middle_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        top_vertical_point = choose_specific_value_from_polygon_points(vertical_profile, index, middle_y, flag=False)
        # 获取构造水平钢筋数据
        construct_horizon_rebar_data = self.generate_construct_horizon_cut_points()
        horizon_bbox = get_polygon_bounding_box_points(construct_horizon_rebar_data)
        # 横向钢筋引出线
        horizon_rebar_point_s = [(horizon_bbox.min_x+horizon_bbox.max_x)/2,horizon_bbox.max_y,0]
        length_1 = abs(form_bbox.max_y-horizon_bbox.max_y)
        direction_1 = np.asarray([0,1,0])
        text_1 = "3"
        # 纵向钢筋引出线
        vertical_rebar_point_s = [top_vertical_point[-1][0],top_vertical_point[-1][1],0] # 起点坐标
        length_2 = abs(form_bbox.max_y-top_vertical_point[-1][1])  # 长度
        direction_2 = np.asarray([0,1,0])  # 引出线方向
        text_2 = "4"  # 文本内容
        # 所有信息
        total_info = [[horizon_rebar_point_s,length_1,direction_1,text_1],\
                      [vertical_rebar_point_s,length_2,direction_2,text_2]]
        return total_info

    def generate_interior_wall_construct_vertical_rebar_YOZ_cut_points(self):
        """
        产生内皮墙构造竖向钢筋YOZ平面剖切点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        construct_vertical_rebar_model = self.occ_model.create_construct_vertical_rebar_model()
        # 获取构造竖向钢筋坐标点
        construct_vertical_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                               self.object_name[0])
        profile_points = construct_vertical_info["profile"]
        middle_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        interior_vertical_point = choose_specific_value_from_polygon_points(profile_points, index, middle_y, flag=True)
        plane_point = list(interior_vertical_point[0])
        direction = [1, 0, 0]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_vertical_rebar_model, plane_point, direction)
        # 选择满足要求的剖切线段
        index = 1
        cut_profile_small = choose_specific_value_from_polygon_points_to_specific_polygon(cut_profile,index,middle_y)
        return cut_profile_small

    def generate_exterior_wall_construct_vertical_rebar_YOZ_cut_points(self):
        """
        产生外皮墙构造竖向钢筋YOZ平面剖切点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        construct_vertical_rebar_model = self.occ_model.create_construct_vertical_rebar_model()
        # 获取构造竖向钢筋坐标点
        construct_vertical_info = self.occ_data.get_ifc_construct_vertical_rebar(self.entity_type[1],
                                                                                 self.object_name[0])
        profile_points = construct_vertical_info["profile"]
        middle_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        exterior_vertical_point = choose_specific_value_from_polygon_points(profile_points, index, middle_y,flag=False)
        plane_point = list(exterior_vertical_point[0])
        direction = [1, 0, 0]
        # 获取剖切轮廓
        cut_profile = compute_solid_cut_profile_shape(construct_vertical_rebar_model, plane_point, direction)
        index = 1
        cut_profile_big = choose_specific_value_from_polygon_points_to_specific_polygon(cut_profile,index,middle_y,flag=False)
        return cut_profile_big

    def generate_interior_wall_construct_horizon_rebar_YOZ_cut_points(self):
        """
        产生内皮墙构造水平钢筋YOZ平面剖切点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        # 获取构造水平钢筋坐标点
        construct_horizon_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],
                                                                               self.object_name[0])
        profile_points = construct_horizon_info["profile"]
        middle_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        interior_vertical_point = choose_specific_value_from_polygon_points_to_specific_polygon(profile_points, index, middle_y,flag=True)
        rebar_center_sets = [[seg[0][1],seg[0][2],0] for seg in interior_vertical_point]
        rebar_radius = construct_horizon_info["Radius"]
        # 所有信息
        total_rebar_info = {}
        total_rebar_info["profile"] = rebar_center_sets
        total_rebar_info["diam"] = 2*rebar_radius
        return total_rebar_info

    def generate_exterior_wall_construct_horizon_rebar_YOZ_cut_points(self):
        """
        产生外皮墙构造水平钢筋YOZ平面剖切点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        # 获取构造水平钢筋坐标点
        construct_horizon_info = self.occ_data.get_ifc_construct_horizon_rebar(self.entity_type[1],
                                                                               self.object_name[0])
        profile_points = construct_horizon_info["profile"]
        middle_y = (form_bbox.min_y + form_bbox.max_y) / 2
        index = 1
        exterior_vertical_point = choose_specific_value_from_polygon_points_to_specific_polygon(profile_points, index, middle_y,flag=False)
        rebar_center_sets = [[seg[0][1],seg[0][2],0] for seg in exterior_vertical_point]
        rebar_radius = construct_horizon_info["Radius"]
        # 所有信息
        total_rebar_info = {}
        total_rebar_info["profile"] = rebar_center_sets
        total_rebar_info["diam"] = 2*rebar_radius
        return total_rebar_info

    def generate_truss_stirrup_rebar_YOZ_projection_data(self):
        """
        产生桁架马镫筋YOZ平面投影数据
        :return:
        """
        truss_stirrup_rebar_model = self.occ_model.create_single_truss_stirrup_rebar_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(truss_stirrup_rebar_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        return projection_data

    def generate_reinforcement_two_section_top_dimension_points(self):
        """
        产生配筋2-2剖切图顶部标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        # 获取内皮墙构造横向钢筋坐标
        interior_horizon_rebar = self.generate_interior_wall_construct_horizon_rebar_YOZ_cut_points()
        interior_rebar_loc = interior_horizon_rebar["profile"]
        # 获取外皮墙构造横向钢筋坐标
        exterior_horizon_rebar = self.generate_exterior_wall_construct_horizon_rebar_YOZ_cut_points()
        exterior_rebar_loc = exterior_horizon_rebar["profile"]
        form_loc = [[form_bbox.min_x,form_bbox.max_y,0],[form_bbox.max_x,form_bbox.max_y,0]]
        rebar_loc = [[interior_rebar_loc[0][0],form_bbox.max_y,0],[exterior_rebar_loc[0][0],form_bbox.max_y,0]]
        # 所有信息
        total_info = []
        total_info.extend(form_loc)
        total_info.extend(rebar_loc)
        index = 0  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(total_info,index,reverse=True)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info

    def generate_reinforcement_two_section_right_dimension_points(self):
        """
        产生配筋2-2剖切图右侧标注点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)

        # 获取外皮墙构造横向钢筋坐标
        exterior_horizon_rebar = self.generate_exterior_wall_construct_horizon_rebar_YOZ_cut_points()
        exterior_rebar_loc = exterior_horizon_rebar["profile"]
        form_loc = [[form_bbox.max_x,form_bbox.min_y,0],[form_bbox.max_x,form_bbox.max_y,0]]
        rebar_loc = [[form_bbox.max_x,point[1],0] for point in exterior_rebar_loc]
        # 获取外皮构造竖向钢筋坐标
        exterior_vertical_rebar = self.generate_exterior_wall_construct_vertical_rebar_YOZ_cut_points()
        exterior_vertical_rebar_bbox = get_polygon_bounding_box_points(exterior_vertical_rebar)
        vertical_rebar_loc = [[form_bbox.max_x,exterior_vertical_rebar_bbox.min_z,0],[form_bbox.max_x,exterior_vertical_rebar_bbox.max_z,0]]
        # 所有信息
        total_info = []
        total_info.extend(form_loc)
        total_info.extend(rebar_loc)
        total_info.extend(vertical_rebar_loc)
        index = 1  # 按照x坐标进行排序
        total_sort_point = point_sets_sort(total_info,index)
        first_floor_dimension = transform_point_set_to_segment(total_sort_point)
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_dimension
        return total_dimension_info

    def generate_reinforcement_two_section_view_outline_shape_points(self):
        """
        产生配筋2-2剖切图引出线形状点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        # 获取内皮墙构造横向钢筋坐标
        interior_horizon_rebar = self.generate_interior_wall_construct_horizon_rebar_YOZ_cut_points()
        interior_rebar_loc = interior_horizon_rebar["profile"]
        index = 1  # 按照y坐标进行排序
        total_sort_point = point_sets_sort(interior_rebar_loc, index)
        # 形成内皮墙构造横向钢筋引出线--1号
        rebar_point_1 = [total_sort_point[-1][0],total_sort_point[-1][1],0]
        length_1 = abs(rebar_point_1[0]-form_bbox.min_x)
        direction_1 = np.asarray([-1,0,0])
        text_1 = "1"
        # 获取外皮构造横向钢筋坐标
        exterior_horizon_rebar = self.generate_exterior_wall_construct_horizon_rebar_YOZ_cut_points()
        exterior_rebar_loc = exterior_horizon_rebar["profile"]
        index = 1  # 按照y坐标进行排序
        total_sort_point = point_sets_sort(exterior_rebar_loc, index)
        # 形成外皮墙构造横向钢筋引出线--1号
        rebar_point_3 = [total_sort_point[-1][0],total_sort_point[-1][1],0]
        length_3 = abs(rebar_point_3[0]-form_bbox.max_x)
        direction_3 = np.asarray([1,0,0])
        text_3 = "3"
        # 获取内皮墙构造竖向钢筋坐标
        interior_vertical_rebar = self.generate_interior_wall_construct_vertical_rebar_YOZ_cut_points()
        interior_vertical_rebar_bbox = get_polygon_bounding_box_points(interior_vertical_rebar)
        # 形成内皮墙构造横向钢筋引出线--2号
        rebar_point_2 = [interior_vertical_rebar_bbox.min_y,(interior_vertical_rebar_bbox.min_z+interior_vertical_rebar_bbox.max_z)/2, 0]
        length_2 = abs(rebar_point_2[0] - form_bbox.min_x)
        direction_2 = np.asarray([-1, 0, 0])
        text_2 = "2"
        # 获取外皮墙构造竖向钢筋坐标
        exterior_vertical_rebar = self.generate_exterior_wall_construct_vertical_rebar_YOZ_cut_points()
        exterior_vertical_rebar_bbox = get_polygon_bounding_box_points(exterior_vertical_rebar)
        # 形成外皮墙构造横向钢筋引出线--4号
        rebar_point_4 = [exterior_vertical_rebar_bbox.max_y,(exterior_vertical_rebar_bbox.min_z+exterior_vertical_rebar_bbox.max_z)/2, 0]
        length_4 = abs(rebar_point_4[0] - form_bbox.max_x)
        direction_4 = np.asarray([1, 0, 0])
        text_4 = "4"
        # 所有信息
        total_info = [[rebar_point_1,length_1,direction_1,text_1],\
                      [rebar_point_2,length_2,direction_2,text_2],
                      [rebar_point_3,length_3,direction_3,text_3],
                      [rebar_point_4,length_4,direction_4,text_4]]
        return total_info

    def generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points(self):
        """
        产生桁架钢筋细部图的外部和内部构造水平钢筋坐标点
        :return:
        """
        # 获取模板数据
        form_projection_data = self.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        # 获取分界线
        mean_x = (form_bbox.min_x+form_bbox.max_x)/2
        mean_y = (form_bbox.min_y+form_bbox.max_y)/2
        construct_horizon_rebar = self.generate_construct_horizon_cut_points()  # 构造水平钢筋
        # 选择外侧的构造水平钢筋
        index = 1
        exterior_construct_horizon_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_horizon_rebar,index,mean_y,flag=False)
        # 选择内侧的构造水平钢筋
        interior_construct_horizon_rebar = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_horizon_rebar, index, mean_y)

        construct_vertical_rebar_info = self.generate_construct_vertical_rebar_location_points()  # 构造竖向钢筋
        construct_vertical_rebar = construct_vertical_rebar_info["profile"]
        # 筛选外侧构造竖向钢筋
        exterior_construct_vertical_rebar_line = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_vertical_rebar,index,mean_y,flag=False)
        exterior_construct_vertical_rebar = [list(rebar_line[0]) for rebar_line in exterior_construct_vertical_rebar_line]
        #　获取外皮构造竖向钢筋
        index_x = 0
        exterior_construct_vertical_rebar_sort = point_sets_sort(exterior_construct_vertical_rebar,index_x)
        # 筛选内侧构造竖向钢筋
        interior_construct_vertical_rebar_line = choose_specific_value_from_polygon_points_to_specific_polygon(
            construct_vertical_rebar,index,mean_y)
        interior_construct_vertical_rebar = [list(rebar_line[0]) for rebar_line in interior_construct_vertical_rebar_line]
        interior_construct_vertical_rebar_sort = point_sets_sort(interior_construct_vertical_rebar,index_x)
        # 获取剖切图总长
        total_length = max(exterior_construct_vertical_rebar_sort[2][0]+exterior_construct_vertical_rebar_sort[0][0],
                           interior_construct_vertical_rebar_sort[2][0]+interior_construct_vertical_rebar_sort[0][0])
        # 需绘制圆竖向钢筋坐标
        curr_interior_construct_vertical_rebar = interior_construct_vertical_rebar_sort[:3]
        curr_exterior_construct_vertical_rebar = exterior_construct_vertical_rebar_sort[:3]
        # 修正横向钢筋坐标
        exterior_y = [point[1] for seg in exterior_construct_horizon_rebar for point in seg]
        exterior_y = list(set(exterior_y))
        interior_y = [point[1] for seg in interior_construct_horizon_rebar for point in seg]
        interior_y = list(set(interior_y))
        exterior_horizon_rebar = [[[0,exterior_y[0],0],[total_length,exterior_y[0],0]],
                                  [[0,exterior_y[1],0],[total_length,exterior_y[1],0]]]
        interior_horizon_rebar = [[[0,interior_y[0],0],[total_length,interior_y[0],0]],
                                  [[0,interior_y[1],0],[total_length,interior_y[1],0]]]
        # 获取外页墙体轮廓信息
        exterior_wall_projection_data = self.generate_exterior_shear_wall_XOY_projection_data()
        exterior_form_bbox = get_polygon_bounding_box_points(exterior_wall_projection_data)

        interior_wall_projection_data = self.generate_interior_shear_wall_XOY_projection_data()
        interior_form_bbox = get_polygon_bounding_box_points(interior_wall_projection_data)
        # 获取外页墙体轮廓信息
        exterior_wall_profile = [[[0,exterior_form_bbox.min_y,0],[total_length,exterior_form_bbox.min_y,0]],
                                 [[0,exterior_form_bbox.max_y,0],[total_length,exterior_form_bbox.max_y,0]]]
        # 获取内页墙体轮廓信息
        interior_wall_profile = [[[0,interior_form_bbox.min_y,0],[total_length,interior_form_bbox.min_y,0]],
                                 [[0,interior_form_bbox.max_y,0],[total_length,interior_form_bbox.max_y,0]]]
        # 两端折断线
        left_break_line = [[0,form_bbox.min_y,0],[0,form_bbox.max_y,0]]
        right_break_line = [[total_length,form_bbox.min_y,0],[total_length,form_bbox.max_y,0]]
        total_break_line = [left_break_line,right_break_line]
        # 总体信息
        total_interior_construct_vertical_rebar_info = {}
        total_interior_construct_vertical_rebar_info["profile"] = curr_interior_construct_vertical_rebar
        total_interior_construct_vertical_rebar_info["diam"] = 2*construct_vertical_rebar_info["Radius"]
        total_exterior_construct_vertical_rebar_info = {}
        total_exterior_construct_vertical_rebar_info["profile"] = curr_exterior_construct_vertical_rebar
        total_exterior_construct_vertical_rebar_info["diam"] = 2*construct_vertical_rebar_info["Radius"]
        return exterior_horizon_rebar,interior_horizon_rebar,total_interior_construct_vertical_rebar_info,\
               total_exterior_construct_vertical_rebar_info,exterior_wall_profile, \
               interior_wall_profile,total_break_line

    def generate_truss_rebar_detail_view_truss_rebar_shape_points(self):
        """
        产生桁架钢筋细部视图桁架钢筋形状数据
        :return:
        """
        index_x = 0
        # 处理桁架上部钢筋
        truss_top_rebar_data = self.generate_truss_top_rebar_location_points()  # 桁架上弦钢筋
        truss_top_rebar_line = truss_top_rebar_data["profile"]
        truss_top_rebar = [list(rebar_line[0]) for rebar_line in truss_top_rebar_line]
        truss_top_rebar_sort = point_sets_sort(truss_top_rebar, index_x)
        curr_truss_top_rebar = truss_top_rebar_sort[:1]
        truss_bottom_rebar_data = self.generate_truss_bottom_rebar_location_points()  # 桁架下弦钢筋
        truss_bottom_rebar_line = truss_bottom_rebar_data["profile"]
        truss_bottom_rebar = [list(rebar_line[0]) for rebar_line in truss_bottom_rebar_line]
        truss_bottom_rebar_sort = point_sets_sort(truss_bottom_rebar, index_x)
        curr_truss_bottom_rebar = truss_bottom_rebar_sort[:2]
        truss_stirrup_rebar = self.generate_truss_stirrup_straight_rebar_XOY_projection_data()
        truss_bottom_rebar_max_x = max([point[0] for point in curr_truss_bottom_rebar])
        first_truss_stirrup = []
        for seg in truss_stirrup_rebar:
            curr_x = []
            for point in seg:
                curr_x.append(point[0])
            if max(curr_x) < truss_bottom_rebar_max_x:
                first_truss_stirrup.append(copy.deepcopy(seg))
        # 形成所有信息
        truss_top_rebar_info = {}
        truss_top_rebar_info["profile"] = curr_truss_top_rebar
        truss_top_rebar_info["diam"] = 2*truss_top_rebar_data["Radius"]
        truss_bottom_rebar_info = {}
        truss_bottom_rebar_info["profile"] = curr_truss_bottom_rebar
        truss_bottom_rebar_info["diam"] = 2*truss_bottom_rebar_data["Radius"]
        return truss_top_rebar_info,truss_bottom_rebar_info,first_truss_stirrup

    def generate_truss_rebar_detail_view_breakline_shape_points(self):
        """
        获取桁架钢筋细部图折断线形状数据
        :return:
        """
        extend_l = 50  # 两边延伸距离
        l_space = 40  # 间断
        offset = 30  # 偏移长度
        theta = math.pi / 9  # 弧度值
        _,__,_,_,_,_,total_break_line = self.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        # 左侧线段
        left_line = total_break_line[0]
        # 开始设置关键点
        mean_y = (left_line[0][1]+left_line[1][1])/2
        point_1 = copy.deepcopy(left_line[1])
        point_1[1] += extend_l
        point_2 = copy.deepcopy(left_line[1])
        point_3 = copy.deepcopy(left_line[1])
        point_3[1] = mean_y + l_space / 2
        point_4 = copy.deepcopy(point_3)
        point_4[0] += -offset * math.cos(theta)
        point_4[1] += -offset * math.sin(theta)
        point_5 = copy.deepcopy(point_3)
        point_5[0] += offset * math.cos(theta)
        point_5[1] += -l_space + offset * math.sin(theta)
        point_6 = copy.deepcopy(point_3)
        point_6[1] += -l_space
        point_7 = copy.deepcopy(left_line[0])
        point_8 = copy.deepcopy(point_7)
        point_8[1] += -extend_l
        break_line_1 = [point_1, point_2, point_3, point_4, point_5, point_6, point_7, point_8]
        # 右侧线段
        right_line = total_break_line[1]
        mean_y = (right_line[0][1]+right_line[1][1])
        point_1 = copy.deepcopy(right_line[1])
        point_1[1] += extend_l
        point_2 = copy.deepcopy(right_line[1])
        point_3 = copy.deepcopy(right_line[1])
        point_3[1] = mean_y + l_space / 2
        point_4 = copy.deepcopy(point_3)
        point_4[0] += -offset * math.cos(theta)
        point_4[1] += -offset * math.sin(theta)
        point_5 = copy.deepcopy(point_3)
        point_5[0] += offset * math.cos(theta)
        point_5[1] += -l_space + offset * math.sin(theta)
        point_6 = copy.deepcopy(point_3)
        point_6[1] += -l_space
        point_7 = copy.deepcopy(right_line[0])
        point_8 = copy.deepcopy(point_7)
        point_8[1] += -extend_l
        break_line_2 = [point_1, point_2, point_3, point_4, point_5, point_6, point_7, point_8]
        total_break_line_set = [break_line_1,break_line_2]
        return total_break_line_set

    def generate_truss_rebar_detail_view_outline_shape_points(self):
        """
        获取桁架钢筋细部图引出线形状数据:d--一级钢、D--二级钢、e---三级钢、E---四级钢
        :return:
        """
        single_length = 50  # 单段长度
        truss_top_rebar_info,truss_bottom_rebar_info,first_truss_stirrup = self.generate_truss_rebar_detail_view_truss_rebar_shape_points()
        top_rebar_profile = truss_top_rebar_info["profile"][0]
        top_rebar_diam = truss_top_rebar_info["diam"]
        # 形成上弦钢筋引出线
        point_1 = copy.deepcopy(top_rebar_profile)
        point_2 = np.array(point_1)+np.array([2*single_length*math.cos(math.pi/4),2*single_length*math.sin(math.pi/4),0])
        point_3 = point_2 + np.array([2*single_length,0,0])
        text_loc_1 = point_3.tolist()
        text_1 = "D"+str(int(top_rebar_diam))+"上弦钢筋"
        total_line_1 = [[point_1,point_2.tolist()],[point_2.tolist(),point_3.tolist()]]
        total_text_1 = [text_loc_1,text_1]
        # 形成腹杆钢筋引出线
        point_s1 = first_truss_stirrup[0][1]
        point_2 = np.array(point_s1) + np.array(
            [-2*single_length * math.cos(math.pi / 4), 2*single_length * math.sin(math.pi / 4), 0])
        point_3 = point_2 + np.array([-2 * single_length, 0, 0])
        diam_2 = int(np.linalg.norm(np.array(first_truss_stirrup[0][1])-np.array(first_truss_stirrup[0][2])))
        text_loc_2 = point_3.tolist()
        text_2 = "d" + str(int(diam_2)) + "腹杆钢筋"
        total_line_2 = [[point_s1, point_2.tolist()], [point_2.tolist(), point_3.tolist()]]
        total_text_2 = [text_loc_2, text_2]
        # 形成下弦钢筋引出线
        bottom_rebar_profile = truss_bottom_rebar_info["profile"][1]
        bottom_rebar_diam = truss_bottom_rebar_info["diam"]
        point_1 = copy.deepcopy(bottom_rebar_profile)
        point_2 = np.array(point_1) + np.array(
            [2*single_length * math.cos(math.pi / 4), -2*single_length * math.sin(math.pi / 4), 0])
        point_3 = point_2 + np.array([2 * single_length, 0, 0])
        text_loc_3 = point_3.tolist()
        text_3 = "D" + str(int(bottom_rebar_diam)) + "下弦钢筋"
        total_line_3 = [[point_1, point_2.tolist()], [point_2.tolist(), point_3.tolist()]]
        total_text_3 = [text_loc_3, text_3]
        total_info = [[total_line_1,total_text_1],[total_line_2,total_text_2],[total_line_3,total_text_3]]
        return total_info

    def generate_truss_rebar_detail_view_dimension_shape_points(self):
        """
        产生桁架钢筋细部视图标注形状点
        :return:
        """
        e_h_rebar,i_h_rebar,_,_,e_w_profile,i_w_profile,_ = self.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        truss_top_rebar_info,truss_bottom_rebar_info,first_truss_stirrup = self.generate_truss_rebar_detail_view_truss_rebar_shape_points()
        # 获取桁架下弦钢筋坐标点
        truss_bottom_rebar_profile = truss_bottom_rebar_info["profile"]
        truss_bottom_rebar_radius = truss_bottom_rebar_info["diam"]/2
        bottom_dimension_points = [[truss_bottom_rebar_profile[0][0]-truss_bottom_rebar_radius,0,0],
                                   [truss_bottom_rebar_profile[1][0]+truss_bottom_rebar_radius,0,0]]
        # 获取右侧轮廓
        max_x = max([point[0] for seg in i_w_profile for point in seg])
        curr_y_set = [point[1] for seg in e_w_profile for point in seg]
        total_y = [point[1] for seg in i_w_profile for point in seg]
        total_y.extend(curr_y_set)
        min_y = min(total_y)
        max_y = max(total_y)
        top_rebar_y = max([point[1] for seg in e_h_rebar for point in seg])
        bottom_rebar_y = min([point[1] for seg in i_h_rebar for point in seg])
        total_y_sort = [min_y,bottom_rebar_y,top_rebar_y,max_y]
        dimension_sort = [[max_x,p,0] for p in total_y_sort]
        dimension_seg = transform_point_set_to_segment(dimension_sort)
        total_dimension_seg = [bottom_dimension_points]
        total_dimension_seg.extend(dimension_seg)
        total_dimension_info = {}
        total_dimension_info["first_floor"] = total_dimension_seg
        return total_dimension_info

    def generate_single_area_truss_stirrup_rebar_YOZ_projection_data(self):
        """
        产生单根部分桁架马镫筋YOZ平面投影数据
        :return:
        """
        truss_stirrup_rebar_model = self.occ_model.create_single_area_truss_stirrup_rebar_model()
        project_coord_origin = [0,0,0]  # 投影坐标系原点
        project_coord_dir_x = [0,1,0]  # 以全局坐标系的某轴作为投影坐标系的x轴
        gazing_direction = [1,0,0]  # 视线方向
        # 获取投影数据
        projection_data = compute_project_shape_axis(truss_stirrup_rebar_model,project_coord_origin,
                                                     gazing_direction,project_coord_dir_x)
        # 坐标变换
        for seg in projection_data:
            for num in range(len(seg)):
                curr_point = seg[num]
                changed_point = transform_point_from_xy_plane_to_yx_plane(curr_point)
                seg[num] = changed_point
        rebar_bbox = get_polygon_bounding_box_points(projection_data)
        # 坐标变换
        move = np.array([-rebar_bbox.min_x,-rebar_bbox.min_y,-rebar_bbox.min_z])
        for seg in projection_data:
            for num in range(len(seg)):
                curr_point = seg[num]
                moved_point = np.array(curr_point) + move
                seg[num] = moved_point.tolist()
        return projection_data

    def generate_truss_top_bottom_rebar_shape_data(self):
        """
        产生桁架上弦和下弦钢筋形状点
        :return:
        """
        projection_data = self.generate_single_area_truss_stirrup_rebar_YOZ_projection_data()
        # 获取上弦和钢筋的直径
        truss_top_rebar_info,truss_bottom_rebar_info,first_truss_stirrup = self.generate_truss_rebar_detail_view_truss_rebar_shape_points()
        top_rebar_diam = truss_top_rebar_info["diam"]
        bottom_rebar_diam = truss_bottom_rebar_info["diam"]
        rebar_bbox = get_polygon_bounding_box_points(projection_data) # 获取包围框
        # 形成上弦钢筋的轮廓
        top_rebar_profile = [[[rebar_bbox.min_x,rebar_bbox.max_y,0],[rebar_bbox.max_x,rebar_bbox.max_y,0]],
                             [[rebar_bbox.max_x,rebar_bbox.max_y,0],[rebar_bbox.max_x,rebar_bbox.max_y-top_rebar_diam,0]],
                             [[rebar_bbox.max_x,rebar_bbox.max_y-top_rebar_diam,0],[rebar_bbox.min_x,rebar_bbox.max_y-top_rebar_diam,0]],
                             [[rebar_bbox.min_x,rebar_bbox.max_y-top_rebar_diam,0],[rebar_bbox.min_x,rebar_bbox.max_y,0]]]
        # 形成下弦钢筋的轮廓
        bottom_rebar_profile = [[[rebar_bbox.min_x,rebar_bbox.min_y+bottom_rebar_diam,0],[rebar_bbox.max_x,rebar_bbox.min_y+bottom_rebar_diam,0]],
                             [[rebar_bbox.max_x,rebar_bbox.min_y+bottom_rebar_diam,0],[rebar_bbox.max_x,rebar_bbox.min_y,0]],
                             [[rebar_bbox.max_x,rebar_bbox.min_y,0],[rebar_bbox.min_x,rebar_bbox.min_y,0]],
                             [[rebar_bbox.min_x,rebar_bbox.min_y,0],[rebar_bbox.min_x,rebar_bbox.min_y+bottom_rebar_diam,0]]]
        return top_rebar_profile,bottom_rebar_profile,top_rebar_diam,bottom_rebar_diam

    def generate_top_bottom_rebar_outline_shape_data(self):
        """
        产生上弦和下弦钢筋引出线形状数据:d--一级钢、D--二级钢、e---三级钢、E---四级钢
        :return:
        """
        single_length = 50
        top_rebar_profile, bottom_rebar_profile,top_rebar_diam,bottom_rebar_diam = self.generate_truss_top_bottom_rebar_shape_data()
        top_point = (np.array(top_rebar_profile[0][0])+np.array(top_rebar_profile[0][1]))/2
        bottom_point = (np.array(bottom_rebar_profile[0][0])+np.array(bottom_rebar_profile[0][1]))/2
        # 形成上弦钢筋引出线
        point_1 = copy.deepcopy(top_point.tolist())
        point_2 = np.array(point_1) + np.array(
            [single_length * math.cos(math.pi / 4), 2 * single_length * math.sin(math.pi / 4), 0])
        point_3 = point_2 + np.array([2 * single_length, 0, 0])
        text_loc_1 = point_3.tolist()
        text_1 = "D" + str(int(top_rebar_diam)) + "上弦钢筋"
        total_line_1 = [[point_1, point_2.tolist()], [point_2.tolist(), point_3.tolist()]]
        total_text_1 = [text_loc_1, text_1]
        # 形成腹杆钢筋引出线
        projection_data = self.generate_single_area_truss_stirrup_rebar_YOZ_projection_data()
        truss_stirrup_info = self.occ_data.get_ifc_truss_stirrup_rebar(self.entity_type[2], self.object_name[1])
        truss_diam = 2*truss_stirrup_info["Radius"]
        point_s1 = list(projection_data[-1][0])
        point_2 = np.array(point_s1) + np.array(
            [single_length * math.cos(math.pi / 4), single_length * math.sin(math.pi / 4), 0])
        point_3 = point_2 + np.array([2 * single_length, 0, 0])
        text_loc_2 = point_3.tolist()
        text_2 = "d" + str(int(truss_diam)) + "腹杆钢筋"
        total_line_2 = [[point_s1, point_2.tolist()], [point_2.tolist(), point_3.tolist()]]
        total_text_2 = [text_loc_2, text_2]
        # 形成下弦钢筋引出线
        point_1 = copy.deepcopy(bottom_point.tolist())
        point_2 = np.array(point_1) + np.array(
            [-single_length * math.cos(math.pi / 4), -single_length * math.sin(math.pi / 4), 0])
        point_3 = point_2 + np.array([-2 * single_length, 0, 0])
        text_loc_3 = point_3.tolist()
        text_3 = "D" + str(int(bottom_rebar_diam)) + "下弦钢筋"
        total_line_3 = [[point_1, point_2.tolist()], [point_2.tolist(), point_3.tolist()]]
        total_text_3 = [text_loc_3, text_3]
        total_info = [[total_line_1, total_text_1], [total_line_2, total_text_2], [total_line_3, total_text_3]]
        return total_info

    def generate_top_bottom_rebar_dimension_shape_data(self):
        """
        产生上弦和下弦钢筋标注形状数据:d--一级钢、D--二级钢、e---三级钢、E---四级钢
        :return:
        """
        top_rebar_profile, bottom_rebar_profile,_,_ = self.generate_truss_top_bottom_rebar_shape_data()
        left_top_point = top_rebar_profile[0][0]
        right_top_point = top_rebar_profile[0][1]
        left_bottom_point = bottom_rebar_profile[-2][1]
        right_bottom_point = bottom_rebar_profile[-2][0]
        middle_bottom_point = copy.deepcopy(left_bottom_point)
        middle_bottom_point[0] = (left_bottom_point[0]+right_bottom_point[0])/2
        # 左侧标注点
        left_dimension = [[left_top_point,left_bottom_point]]
        bottom_dimension_point = [[left_bottom_point,middle_bottom_point],[middle_bottom_point,right_bottom_point]]
        # 获取顶部标注点
        projection_data = self.generate_single_area_truss_stirrup_rebar_YOZ_projection_data()
        max_y = left_top_point[1]
        # 所有标注点
        total_x_value = []
        for seg in projection_data:
            for point in seg:
                if abs(point[1] - max_y)<0.000001:
                    total_x_value.append(point[0])
        total_x_value.sort(reverse=True)
        top_dimension_point = [[p_x,max_y,0] for p_x in total_x_value]
        # 所有标注点
        total_dimension = [top_dimension_point]
        total_dimension.extend(bottom_dimension_point)
        total_dimension.extend(left_dimension)
        total_dimension_info = { }
        total_dimension_info["first_floor"] = total_dimension
        return total_dimension_info

    def generate_hoist_embedded_part_detail_view_shape_points(self):
        """
        产生吊装预埋件详图形状点
        :return:
        """
        projection_data = self.generate_hoist_embedded_YOZ_projection_data()
        hoist_bbox = get_polygon_bounding_box_points(projection_data)
        min_x = hoist_bbox.min_x
        min_y = hoist_bbox.min_y
        min_z = hoist_bbox.min_z
        # 修正坐标点
        for seg in projection_data:
            for num in range(len(seg)):
                point_ = seg[num]
                moved_point = np.array(list(point_))-np.array([min_x,min_y,min_z])
                seg[num] = tuple(moved_point)
        return projection_data

    def generate_hoist_embedded_part_detail_view_bounding_box(self):
        """
        产生吊装预埋件详图包围框
        :return:
        """
        projection_data = self.generate_hoist_embedded_part_detail_view_shape_points()
        hoist_bbox = get_polygon_bounding_box_points(projection_data)
        return hoist_bbox

    def generate_hoist_embedded_part_detail_view_dimension_points(self):
        """
        产生吊装预埋件详图标注点
        :return:
        """
        hoist_bbox = self.generate_hoist_embedded_part_detail_view_bounding_box()
        projection_data = self.generate_hoist_embedded_part_detail_view_shape_points()
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        rebar_diam = hoist_embedded_info["diam"]
        left_projection_length = hoist_embedded_info["left_project_length"]
        left_line_length = hoist_embedded_info["bottom_line_length"]
        # 左侧标注点
        left_point_1 = [hoist_bbox.min_x,hoist_bbox.max_y-hoist_bbox.min_y,0]
        left_point_2 = [hoist_bbox.min_x,left_line_length,0]
        left_point_3 = [hoist_bbox.min_x,hoist_bbox.min_y,0]
        # 顶部标注点
        top_point_1 = [hoist_bbox.max_x,hoist_bbox.max_y-hoist_bbox.min_y,0]
        # 钢筋直径
        rebar_diam_point_1 = [hoist_bbox.max_x,left_line_length/2,0]
        rebar_diam_point_2 = [hoist_bbox.max_x-rebar_diam,left_line_length/2,0]
        # 产生所有标注点
        first_floor_points = [[rebar_diam_point_1,rebar_diam_point_2],[top_point_1,left_point_1],[left_point_1,left_point_2],
                              [left_point_2,left_point_3]]
        second_floor_points = [[left_point_1,left_point_3]]
        # 所有标注信息
        total_dimension_info = {}
        total_dimension_info["first_floor"] = first_floor_points
        total_dimension_info["second_floor"] = second_floor_points
        return total_dimension_info

    def generate_rebar_material_table_shape_info(self):
        """
        产生钢筋明细表形状信息
        :return:
        """
        interior_horizon_info = self.generate_interior_construct_horizon_rebar_info()
        exterior_horizon_info = self.generate_exterior_construct_horizon_rebar_info()
        interior_vertical_info = self.generate_interior_construct_vertical_rebar_info()
        exterior_vertical_info = self.generate_exterior_construct_vertical_rebar_info()
        # 直径集合
        rebar_diam_set = [interior_horizon_info["diam"],interior_vertical_info["diam"],exterior_horizon_info["diam"],
                            exterior_vertical_info["diam"]]
        # 钢筋数量集合
        interior_horizon_rebar = interior_horizon_info["profile"]
        interior_vertical_rebar = interior_vertical_info["profile"]
        exterior_horizon_rebar = exterior_horizon_info["profile"]
        exterior_vertical_rebar = exterior_vertical_info["profile"]
        rebar_number_set = [len(interior_horizon_rebar),len(interior_vertical_rebar),
                            len(exterior_horizon_rebar),len(exterior_vertical_rebar)]
        # 钢筋的长度值
        interior_horizon_length = round(np.linalg.norm(np.array(list(interior_horizon_rebar[0][0]))-np.array(list(interior_horizon_rebar[0][1]))))
        interior_vertical_length = round(np.linalg.norm(np.array(list(interior_vertical_rebar[0][0]))-np.array(list(interior_vertical_rebar[0][1]))))
        exterior_horizon_length = round(np.linalg.norm(np.array(list(exterior_horizon_rebar[0][0]))-np.array(list(exterior_horizon_rebar[0][1]))))
        exterior_vertical_length = round(np.linalg.norm(np.array(list(exterior_vertical_rebar[0][0]))-np.array(list(exterior_vertical_rebar[0][1]))))
        rebar_length_set = [interior_horizon_length,interior_vertical_length,exterior_horizon_length,exterior_vertical_length]
        # 名称集合
        rebar_name_set = ["内皮水平钢筋","内皮竖向钢筋","外皮水平钢筋","外皮竖向钢筋"]
        # 统计钢筋体积
        rebar_weight_set = []
        for num in range(len(rebar_diam_set)):
            curr_diam = rebar_diam_set[num]
            curr_length = rebar_length_set[num]
            curr_number = rebar_number_set[num]
            curr_weight = curr_diam*curr_diam*0.00617 * (curr_length/1000)*curr_number # (math.pi*(curr_diam**2)/4)*curr_length*curr_number/(1000*1000*1000)
            rebar_weight_set.append(round(curr_weight,2))
        return rebar_number_set,rebar_diam_set,rebar_length_set,rebar_name_set,rebar_weight_set

    def generate_rebar_material_table_shape_points(self):
        """
        产生钢筋材料表形状数据
        :return:
        """
        # 计算表格高度
        height = 150
        height_num = 6
        total_height = height*height_num
        # 计算表格宽度
        width_1 = 285
        width_2 = 285
        width_3 = 285
        width_4 = 1028
        width_5 = 285
        width_6 = 369
        total_width = width_1+width_2+width_3+width_4+width_5+width_6
        width_set = [0,width_1,width_2,width_3,width_4,width_5,width_6]
        total_profile = []
        # 开始确定每行轮廓线
        for num_i in range(height_num+1):
            point_s = [0,num_i*height,0]
            point_e = [total_width,num_i*height,0]
            total_profile.append([point_s,point_e])
        # 开始绘制每列轮廓
        point_s = [0,0,0]
        point_e = [0,total_height,0]
        for num_j in range(len(width_set)):
            point_s = copy.deepcopy(point_s)
            point_s[0] += width_set[num_j]
            point_e = copy.deepcopy(point_e)
            point_e[0] += width_set[num_j]
            if num_j ==0 or num_j == len(width_set)-1:
                point_e[1] = total_height
            else:
                point_e[1] = total_height - height
            total_profile.append([point_s,point_e])
        # 放置所有文本
        total_text_set = []
        # 产生钢筋明细表
        point_1 = [total_width/2,total_height-height/2,0]
        text_1 = "钢筋明细表"
        total_text_set.append([point_1,text_1])
        # 产生第二行所有数据
        # 第2行第1列数
        point_2_1 = [width_1/2,total_height-height*3/2,0]
        text_2_1 = "编号"
        total_text_set.append([point_2_1,text_2_1])
        # 第2行第2列数
        point_2_2 = [width_1+width_2/2,total_height-height*3/2,0]
        text_2_2 = "数量"
        total_text_set.append([point_2_2,text_2_2])
        # 第2行第3列数
        point_2_3 = [width_1+width_2+width_3/2,total_height-height*3/2,0]
        text_2_3 = "直径"
        total_text_set.append([point_2_3,text_2_3])
        # 第2行第4列数
        point_2_4 = [width_1+width_2+width_3+width_4/2,total_height-height*3/2,0]
        text_2_4 = "形状"
        total_text_set.append([point_2_4,text_2_4])
        # 第2行第5列数
        point_2_5 = [width_1+width_2+width_3+width_4+width_5/2,total_height-height*3/2,0]
        text_2_5 = "重量"
        total_text_set.append([point_2_5,text_2_5])
        # 第2行第6列数
        point_2_6 = [width_1+width_2+width_3+width_4+width_5+width_6/2,total_height-height*3/2,0]
        text_2_6 = "备注"
        total_text_set.append([point_2_6,text_2_6])
        # 开始产生其它信息
        rebar_number_set, rebar_diam_set, rebar_length_set, rebar_name_set, rebar_weight_set = self.generate_rebar_material_table_shape_info()
        # 编号圆的位置
        circle_loc = []
        for num in range(len(rebar_number_set)):
            # 编号信息
            bian_hao_info = [[width_1/2,total_height-(num+2.5)*height,0],str(num+1)]
            total_text_set.append(bian_hao_info)
            circle_loc.append([width_1/2,total_height-(num+2.5)*height,0])
            # 数量信息
            curr_number = rebar_number_set[num]
            number_info = [[width_1+width_2/2,total_height-(num+2.5)*height,0],str(curr_number)]
            total_text_set.append(number_info)
            # 直径信息
            curr_diam = int(rebar_diam_set[num])
            diam_info = [[width_1+width_2+width_3/2,total_height-(num+2.5)*height,0],"e"+str(curr_diam)]  #　附上钢筋强度等级
            total_text_set.append(diam_info)
            # 体积信息
            curr_volume = rebar_weight_set[num]
            volume_info = [[total_width-width_6-width_5/2,total_height-(num+2.5)*height,0],str(curr_volume)]
            total_text_set.append(volume_info)
            # 备注信息
            curr_name = rebar_name_set[num]
            name_info = [[total_width-width_6/2,total_height-(num+2.5)*height,0],curr_name]
            total_text_set.append(name_info)
        # 添加钢筋等级说明文本
        detail_notes_info = [[total_width/2,total_height+height/2,0],"d代表一级钢，D代表二级钢，e代表三级钢，E代表四级钢"]
        total_text_set.append(detail_notes_info)
        # 形成形状示意图
        rebar_shape = []
        rebar_shape_text_set = []
        for num in range(len(rebar_length_set)):
            curr_length = rebar_length_set[num]
            point_center = [width_1+width_2+width_3+width_4/2,total_height-(num+2.8)*height,0]  # 1/5
            point_l = copy.deepcopy(point_center)
            point_l[0] += - width_4*0.3
            point_r = copy.deepcopy(point_center)
            point_r[0] += width_4*0.3
            # 添加形状线段点
            rebar_shape.append([point_l,point_r])
            # 添加文字信息
            text_info = [point_center,str(curr_length)]
            rebar_shape_text_set.append(text_info)
        # 圆圈信息
        circle_info = {}
        circle_info["profile"] = circle_loc
        circle_info["diam"] = 0
        return total_profile,total_text_set,rebar_shape,rebar_shape_text_set,circle_info

    def generate_prefabricated_component_material_strength_table_shape_points(self):
        """
        产生预制构件材料强度表形状点：后期需要添加混凝土强度等级---C60  TODO
        :return:
        """
        height = 140
        height_num = 2
        total_height = height * height_num
        width = 577
        width_num = 2
        total_width = width * width_num
        width_set = [0,width,width]
        # 轮廓线
        total_profile = []
        for num in range(height_num+1):
            point_s = [0,num*height,0]
            point_e = [total_width,num*height,0]
            total_profile.append([point_s,point_e])
        # 开始绘制每列轮廓
        point_s = [0, 0, 0]
        point_e = [0, total_height, 0]
        for num_j in range(len(width_set)):
            point_s = copy.deepcopy(point_s)
            point_s[0] += width_set[num_j]
            point_e = copy.deepcopy(point_e)
            point_e[0] += width_set[num_j]
            if num_j == 0 or num_j == len(width_set) - 1:
                point_e[1] = total_height
            else:
                point_e[1] = total_height - height
            total_profile.append([point_s, point_e])
        # 所有文本信息
        total_text_info = []
        # 第一行内容
        point_1_1 = [total_width/2,total_height-height/2,0]
        text_1_1 = "预制构件材料强度"
        total_text_info.append([point_1_1,text_1_1])
        # 第二行第一列内容
        point_2_1 = [width/2,total_height-1.5*height,0]
        text_2_1 = "混凝土强度等级"
        total_text_info.append([point_2_1,text_2_1])
        # 第二行第二列内容
        point_2_2 = [1.5*width,total_height-1.5*height,0]
        text_2_2 = "C60"
        total_text_info.append([point_2_2,text_2_2])
        return total_text_info,total_profile

    def generate_embedded_part_material_table_info(self):
        """
        产生预埋件材料表信息
        :return:
        """
        hoist_embedded_info = self.occ_data.get_ifc_hoist_embedded_part_info()
        support_bolt_info = self.occ_data.get_ifc_support_bolt_info()
        pvc_hole_info = self.occ_data.get_ifc_pvc_hole_info()
        # 获取编号集合
        bian_hao_set = [hoist_embedded_info["number_list"],support_bolt_info["number_list"],pvc_hole_info["number_list"]]
        # 获取名称集合
        name_set = [hoist_embedded_info["name"],support_bolt_info["name"],pvc_hole_info["name"]]
        # 数量集合
        number_set = [hoist_embedded_info["number"],support_bolt_info["number"],pvc_hole_info["number"]]
        # 备注集合
        notes_set = [hoist_embedded_info["notes"],support_bolt_info["notes"],pvc_hole_info["notes"]]
        return bian_hao_set,name_set,number_set,notes_set

    def generate_embedded_part_material_table_shape_points(self):
        """
        产生预埋件材料表形状数据点
        :return:
        """
        height = 150
        height_num = 5
        total_height = height * height_num
        width_1 = 334
        width_2 = 420
        width_3 = 562
        width_4 = 217
        width_5 = 720
        width_set = [0,width_1,width_2,width_3,width_4,width_5]
        total_width = width_1 + width_2 + width_3 + width_4 + width_5
        # 获取轮廓线
        total_profile = []
        for num in range(height_num+1):
            point_s = [0,num*height,0]
            point_e = [total_width,num*height,0]
            total_profile.append([point_s,point_e])
        # 开始绘制每列轮廓
        point_s = [0, 0, 0]
        point_e = [0, total_height, 0]
        for num_j in range(len(width_set)):
            point_s = copy.deepcopy(point_s)
            point_s[0] += width_set[num_j]
            point_e = copy.deepcopy(point_e)
            point_e[0] += width_set[num_j]
            if num_j == 0 or num_j == len(width_set) - 1:
                point_e[1] = total_height
            else:
                point_e[1] = total_height - height
            total_profile.append([point_s, point_e])
        # 所有文本信息
        total_text_info = []
        # 第一行内容
        point_1_1 = [total_width / 2, total_height - height / 2, 0]
        text_1_1 = "预埋配件明细表"
        total_text_info.append([point_1_1, text_1_1])
        # 第二行第一列内容
        point_2_1 = [width_1 / 2, total_height - 1.5 * height, 0]
        text_2_1 = "编号"
        total_text_info.append([point_2_1, text_2_1])
        # 第二行第二列内容
        point_2_2 = [width_1+width_2/2, total_height - 1.5 * height, 0]
        text_2_2 = "图例"
        total_text_info.append([point_2_2,text_2_2])
        # 第二行第三列内容
        point_2_3 = [width_1+width_2+width_3/2,total_height - 1.5 * height, 0]
        text_2_3 = "名称"
        total_text_info.append([point_2_3,text_2_3])
        # 第二行第四列内容
        point_2_4 = [width_1+width_2+width_3+width_4/2,total_height - 1.5 * height, 0]
        text_2_4 = "数量"
        total_text_info.append([point_2_4,text_2_4])
        # 第二行第五列元素
        point_2_5 = [total_width-width_5/2,total_height - 1.5 * height, 0]
        text_2_5 = "备注"
        total_text_info.append([point_2_5,text_2_5])
        # 获取其它信息
        bian_hao_set,name_set,number_set,notes_set = self.generate_embedded_part_material_table_info()
        for num in range(len(bian_hao_set)):
            # 编号信息
            bian_hao_info = [[width_1 / 2, total_height - (num + 2.5) * height, 0], bian_hao_set[num]]
            total_text_info.append(bian_hao_info)
            # 名称信息
            name_info = [[width_1+width_2+width_3 / 2, total_height - (num + 2.5) * height, 0], name_set[num]]
            total_text_info.append(name_info)
            # 数量信息
            number_info = [[total_width-width_5-width_4 / 2, total_height - (num + 2.5) * height, 0], number_set[num]]
            total_text_info.append(number_info)
            # 备注信息
            notes_info = [[total_width-width_5 / 2, total_height - (num + 2.5) * height, 0], notes_set[num]]
            total_text_info.append(notes_info)
        # 吊装预埋件形状数据
        hoist_loc = [width_1+width_2/2,2.5*height,0]
        hoist_embedded_part = self.generate_hoist_embedded_part_detail_view_shape_points()
        hoist_bbox = get_polygon_bounding_box_points(hoist_embedded_part)
        y_max = abs(hoist_bbox.max_y-hoist_bbox.min_y)
        scale = (y_max/height)*1.2
        # 开始缩放
        for seg in hoist_embedded_part:
            for num in range(len(seg)):
                point = np.array(list(seg[num]))/scale
                seg[num] = tuple(point)
        # 开始平移
        hoist_bbox = get_polygon_bounding_box_points(hoist_embedded_part)
        center = [(hoist_bbox.max_x-hoist_bbox.min_x)/2,(hoist_bbox.max_y-hoist_bbox.min_y)/2,(hoist_bbox.max_z-hoist_bbox.min_z)/2]
        for seg in hoist_embedded_part:
            for num in range(len(seg)):
                moved_point = np.array(list(seg[num]))-np.array(center)+np.array(hoist_loc)
                seg[num] = tuple(moved_point)
        # 支撑螺栓形状数据
        bolt_width = 26
        bolt_height = 72
        plate_thick = 10
        plate_width = 126
        curr_loc = [width_1+width_2/2,1.5*height,0]
        # 螺栓
        point_bolt_l_b = [curr_loc[0]-bolt_width/2,curr_loc[1]-bolt_height/2,0]
        point_bolt_r_b = [curr_loc[0]+bolt_width/2,curr_loc[1]-bolt_height/2,0]
        point_bolt_l_t = [curr_loc[0]-bolt_width/2,curr_loc[1]+bolt_height/2,0]
        point_bolt_r_t = [curr_loc[0]+bolt_width/2,curr_loc[1]+bolt_height/2,0]
        # 焊板
        point_plate_l_b = [curr_loc[0]-plate_width/2,curr_loc[1]+bolt_height/2,0]
        point_plate_r_b = [curr_loc[0]+plate_width/2,curr_loc[1]+bolt_height/2,0]
        point_plate_l_t = [curr_loc[0]-plate_width/2,curr_loc[1]+bolt_height/2+plate_thick,0]
        point_plate_r_t = [curr_loc[0]+plate_width/2,curr_loc[1]+bolt_height/2+plate_thick,0]
        support_bolt = [[point_bolt_l_b,point_bolt_r_b],[point_bolt_r_b,point_bolt_r_t],[point_bolt_l_b,point_bolt_l_t],
                        [point_plate_l_b,point_plate_r_b],[point_plate_l_b,point_plate_l_t],[point_plate_l_t,point_plate_r_t],
                        [point_plate_r_t,point_plate_r_b]]
        pvc_hole_info = {}
        hole_loc = [width_1+width_2/2,height/2,0]
        hole_radius = 35/2
        pvc_hole_info["hole_loc"] = hole_loc
        pvc_hole_info["hole_diam"] = 2*hole_radius
        return total_profile,total_text_info,hoist_embedded_part,support_bolt,pvc_hole_info
