"""
单个深化设计图
"""
import copy

from GenerateDrawing.model_data import DoubleShearWallViewData
from ezdxf.enums import TextEntityAlignment
from ezdxf.document import Drawing
from GenerateDrawing.special_function import adjust_drawing_scale,transform_point_from_xz_plane_to_xy_plane,\
    point_sets_sort,transform_point_set_to_segment,calculate_normal_vector,rotation_3d,get_polygon_bounding_box_points
import math
import numpy as np


class DoubleWallFormFrontView(object):
    """
    生成双皮剪力墙模板主视图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.form_front_view = self.dxf_doc
        self.model_space = self.form_front_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.form_front_view_block = self.form_front_view.blocks.new("form_front_view_block")  # 添加视图块
        self.form_front_view_top_rebar_block = self.form_front_view.blocks.new("form_front_view_top_rebar_block")  # 添加视图块
        self.form_front_view_dimension_block = self.form_front_view.blocks.new("form_front_view_dimension_block")  # 模板主视图标注块
        self.form_front_view_text_block = self.form_front_view.blocks.new("form_front_view_text_block")  # 模板主视图文本块

    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_XOZ_projection_data()
        for seg in profile_data:
            point_s = seg[0]
            point_e = seg[1]
            point_s = adjust_drawing_scale(list(point_s),1/self.scale)
            point_e = adjust_drawing_scale(list(point_e),1/self.scale)
            self.form_front_view_block.add_line(point_s,point_e,dxfattribs={"layer":"form_front_view_profile"})

    def begin_draw_hoist_embedded_part_xoy_projection_shape(self):
        """
        开始绘制吊装预埋件xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_hoist_embedded_part_XOZ_projection_data()
        for single_rebar in profile_data:
            for seg in single_rebar:
                point_s = seg[0]
                point_e = seg[1]
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.form_front_view_block.add_line(point_s,point_e,dxfattribs={"layer":"form_front_view_embedded"})

    def begin_draw_truss_top_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架上弦钢筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_truss_top_long_rebar_XOZ_projection_data()
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s = adjust_drawing_scale(list(point_s), 1/self.scale)
                point_e = adjust_drawing_scale(list(point_e), 1/self.scale)
                point_s = transform_point_from_xz_plane_to_xy_plane(point_s)
                point_e = transform_point_from_xz_plane_to_xy_plane(point_e)
                self.form_front_view_top_rebar_block.add_line(tuple(point_s), tuple(point_e),
                                                    dxfattribs={"layer": "form_front_view_truss_rebar"})

    def begin_draw_pvc_hole_xoy_projection_shape(self):
        """
        开始绘制pvc孔洞xoy平面投影形状
        :return:
        """
        projection_info = self.model_transform_data.generate_pvc_hole_XOZ_projection_data()
        hole_diam = projection_info["hole_diam"]  # 获取pvc管的孔洞直径
        hole_loc = projection_info["hole_loc"]  # 获取pvc管的中心位置
        for point in hole_loc:
            point_c = adjust_drawing_scale(list(point), 1/self.scale)
            point_c = transform_point_from_xz_plane_to_xy_plane(point_c)
            curr_radius = hole_diam*(1/self.scale)/2
            self.form_front_view_block.add_circle(point_c, curr_radius,
                                                  dxfattribs={"layer":"form_front_view_embedded"})

    def begin_draw_support_bolt_xoy_projection_shape(self):
        """
        开始绘制斜撑螺栓xoy平面投影形状
        :return:
        """
        projection_info = self.model_transform_data.generate_support_bolt_XOZ_projection_data()
        bolt_exterior_radius = projection_info["bolt_outer_radius"]
        bolt_interior_radius = projection_info["bolt_inner_radius"]
        plate_shape = projection_info["plate_shape"]
        bolt_loc = projection_info["bolt_loc"]
        # 开始变换形状
        multi_changed_plate_shape = []
        # 开始绘制图形
        for curr_loc in bolt_loc:
            # 全局位置
            changed_plate_shape = []
            for point in plate_shape:
                global_p = np.array(copy.deepcopy(point))+np.array(list(copy.deepcopy(curr_loc)))
                global_p = adjust_drawing_scale(list(global_p), 1 / self.scale)
                point_c = transform_point_from_xz_plane_to_xy_plane(global_p)
                changed_plate_shape.append(point_c)
            multi_changed_plate_shape.append(changed_plate_shape)

        # 开始绘制图形
        for curr_loc in bolt_loc:
            # 全局位置
            curr_point = copy.deepcopy(curr_loc)
            point_c = adjust_drawing_scale(list(curr_point), 1/self.scale)
            point_c = transform_point_from_xz_plane_to_xy_plane(point_c)
            exterior_radius = bolt_exterior_radius*(1/self.scale)
            interior_radius = bolt_interior_radius*(1/self.scale)

            # 开始绘制外圆
            self.form_front_view_block.add_circle(point_c, exterior_radius,
                                                  dxfattribs={"layer": "form_front_view_embedded"})
            # 开始绘制内圆
            self.form_front_view_block.add_circle(point_c, interior_radius,
                                                  dxfattribs={"layer": "form_front_view_embedded"})
        # 开始绘制多边形
        for single_shape in multi_changed_plate_shape:
            for num in range(len(single_shape)-1):
                point_s = copy.deepcopy(single_shape[num])
                point_e = copy.deepcopy(single_shape[num+1])
                self.form_front_view_block.add_line(tuple(point_s), tuple(point_e),
                                                    dxfattribs={"layer": "form_front_view_embedded"})

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.form_front_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_front_view_dimension"}
                        )
                    else:
                        dim = self.form_front_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_front_view_dimension"}
                        )
                    dim.render()

    def begin_draw_xoy_bottom_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_front_view_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)


    def begin_draw_xoy_top_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面顶部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_front_view_top_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_draw_xoy_left_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面左侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_front_view_left_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_draw_xoy_right_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面右侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_front_view_right_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "模板主视图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.form_front_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_front_view_text"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_hoist_embedded_part_xoy_projection_shape()
        self.begin_draw_truss_top_rebar_xoy_projection_shape()
        self.begin_draw_pvc_hole_xoy_projection_shape()
        self.begin_draw_support_bolt_xoy_projection_shape()
        self.begin_draw_xoy_bottom_dimension_shape()
        self.begin_draw_xoy_top_dimension_shape()
        self.begin_draw_xoy_left_dimension_shape()
        self.begin_draw_xoy_right_dimension_shape()
        self.begin_add_xoy_view_name_text()


class DoubleWallFormRightView(object):
    """
    生成双皮剪力墙模板右视图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.form_right_view = self.dxf_doc
        self.model_space = self.form_right_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.form_right_view_block = self.form_right_view.blocks.new("form_right_view_block")  # 添加视图块
        self.form_right_view_top_rebar_block = self.form_right_view.blocks.new("form_right_view_top_rebar_block")  # 添加视图块
        self.form_right_view_dimension_block = self.form_right_view.blocks.new("form_right_view_dimension_block")  # 模板右视图标注块
        self.form_right_view_text_block = self.form_right_view.blocks.new("form_right_view_text_block")  # 模板右视图文本块

    # 绘制所有右视图形状
    def tool_draw_right_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.form_right_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状---右视图
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_right_view_solid_projection_shape(profile_data,layer_name)


    def begin_draw_hoist_embedded_right_projection_shape(self):
        """
        创建吊装预埋件实体形状---右视图
        :return:
        """
        profile_data = self.model_transform_data.generate_hoist_embedded_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_right_view_solid_projection_shape(profile_data, layer_name)

    def begin_draw_support_embedded_right_projection_shape(self):
        """
        开始绘制斜撑预埋件右侧投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_support_embedded_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_right_view_solid_projection_shape(profile_data, layer_name)

    def begin_draw_pvc_hole_right_projection_shape(self):
        """
        开始绘制PVC管右侧投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_pvc_hole_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_right_view_solid_projection_shape(profile_data, layer_name)

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.form_right_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_right_view_dimension"}
                        )
                    else:
                        dim = self.form_right_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_right_view_dimension"}
                        )
                    dim.render()

    def begin_draw_yoz_bottom_dimension_shape(self):
        """
        开始绘制模板右视图yoz平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_right_view_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_yoz_left_dimension_shape(self):
        """
        开始绘制模板右视图yoz平面左侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_right_view_left_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_yoz_view_name_text(self):
        """
        开始添加yoz平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "模板右视图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.form_right_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_right_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_hoist_embedded_right_projection_shape()
        self.begin_draw_pvc_hole_right_projection_shape()
        self.begin_draw_support_embedded_right_projection_shape()
        self.begin_draw_yoz_bottom_dimension_shape()
        self.begin_draw_yoz_left_dimension_shape()
        self.begin_add_yoz_view_name_text()


class DoubleWallFormTopView(object):
    """
    生成双皮剪力墙模板俯视图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.form_top_view = self.dxf_doc
        self.model_space = self.form_top_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.form_top_view_block = self.form_top_view.blocks.new("form_top_view_block")  # 添加视图块
        self.form_top_view_top_rebar_block = self.form_top_view.blocks.new("form_top_view_top_rebar_block")  # 添加视图块
        self.form_top_view_dimension_block = self.form_top_view.blocks.new("form_top_view_dimension_block")  # 模板右视图标注块
        self.form_top_view_text_block = self.form_top_view.blocks.new("form_top_view_text_block")  # 模板俯视图文本块

    # 绘制所有右视图形状
    def tool_draw_top_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.form_top_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})


    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状---俯视图
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_pvc_hole_xoy_projection_shape(self):
        """
        创建pvc孔洞xoy投影形状---俯视图
        :return:
        """
        profile_data = self.model_transform_data.generate_pvc_hole_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_top_and_bottom_long_rebar_xoy_projection_shape(self):
        """
        创建桁架上弦和下弦纵向钢筋xoy投影形状---俯视图
        :return:
        """
        profile_data = self.model_transform_data.generate_truss_bottom_and_top_long_rebar_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_construct_rebar_xoy_projection_shape(self):
        """
        创建桁架构造钢筋xoy投影形状---俯视图
        :return:
        """
        profile_data = self.model_transform_data.generate_truss_construct_rebar_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_stirrup_rebar_xoy_projection_shape(self):
        """
        创建桁架马镫筋xoy投影形状---俯视图
        :return:
        """
        # profile_data = self.model_transform_data.generate_truss_stirrup_rebar_XOY_projection_data()
        profile_data_ = self.model_transform_data.generate_truss_stirrup_straight_rebar_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data_,layer_name)

    def begin_draw_support_bolt_xoy_projection_shape(self):
        """
        创建斜撑螺栓xoy投影形状---俯视图
        :return:
        """
        profile_data = self.model_transform_data.generate_support_bolt_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_top_view_solid_projection_shape(profile_data,layer_name)

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.form_top_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_top_view_dimension"}
                        )
                    else:
                        dim = self.form_top_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_top_view_dimension"}
                        )
                    dim.render()

    def begin_draw_xoy_left_dimension_shape(self):
        """
        开始绘制模板俯视图xoy平面左侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_top_view_left_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_xoy_bottom_dimension_shape(self):
        """
        开始绘制模板俯视图xoy平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_top_view_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "模板俯视图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.form_top_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_pvc_hole_xoy_projection_shape()
        self.begin_draw_support_bolt_xoy_projection_shape()
        self.begin_draw_truss_construct_rebar_xoy_projection_shape()
        self.begin_draw_truss_top_and_bottom_long_rebar_xoy_projection_shape()
        self.begin_draw_truss_stirrup_rebar_xoy_projection_shape()
        self.begin_draw_xoy_bottom_dimension_shape()
        self.begin_draw_xoy_left_dimension_shape()
        self.begin_add_xoy_view_name_text()


class DoubleWallFormThreeDView(object):
    """
    生成双皮剪力墙模板3D图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.form_three_dim_view = self.dxf_doc
        self.model_space = self.form_three_dim_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.form_three_dim_view_block = self.form_three_dim_view.blocks.new("form_three_dim_view_block")  # 添加视图块
        self.form_three_dim_view_text_block = self.form_three_dim_view.blocks.new("form_three_dim_view_text_block")  # 模板3D图文本块

    # 绘制所有右视图形状
    def tool_draw_solid_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体3D投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.form_three_dim_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def begin_draw_double_wall_solid_three_dim_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状---俯视图
        :return:
        """
        double_wall_projection_data, hoist_embedded_projection_data, pvc_hole_projection_data, \
        support_bolt_projection_data = self.model_transform_data.generate_double_wall_three_dim_XOZ_projection_data()
        layer_name = "form_three_dim_view_profile"
        self.tool_draw_solid_view_solid_projection_shape(double_wall_projection_data,layer_name)
        # self.tool_draw_solid_view_solid_projection_shape(hoist_embedded_projection_data,layer_name)
        # self.tool_draw_solid_view_solid_projection_shape(pvc_hole_projection_data,layer_name)
        # self.tool_draw_solid_view_solid_projection_shape(support_bolt_projection_data,layer_name)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data,_,_,_ = self.model_transform_data.generate_double_wall_three_dim_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "3D视图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.form_three_dim_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_three_dim_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_three_dim_projection_shape()
        self.begin_add_xoy_view_name_text()


class DoubleWallReinforcementDView(object):
    """
    生成双皮剪力墙配筋图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.rebar_reinforcement_view = self.dxf_doc
        self.model_space = self.rebar_reinforcement_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.rebar_reinforcement_view_block = self.rebar_reinforcement_view.blocks.new("rebar_reinforcement_view_block")  # 添加视图块
        self.rebar_reinforcement_view_text_block = self.rebar_reinforcement_view.blocks.new("rebar_reinforcement_view_text_block")  # 配筋图图名
        self.rebar_reinforcement_view_top_rebar_block = self.rebar_reinforcement_view.blocks.new("rebar_reinforcement_view_top_rebar_block")
        self.rebar_reinforcement_view_dimension_block = self.rebar_reinforcement_view.blocks.new("rebar_reinforcement_view_dimension_block")
        self.rebar_reinforcement_view_cut_line_block = self.rebar_reinforcement_view.blocks.new("rebar_reinforcement_view_cut_line_block")
        self.rebar_reinforcement_view_outline_block = self.rebar_reinforcement_view.blocks.new(
            "rebar_reinforcement_view_outline_block")

    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_XOZ_projection_data()
        for seg in profile_data:
            point_s = seg[0]
            point_e = seg[1]
            point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
            point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
            self.rebar_reinforcement_view_block.add_line(point_s, point_e, dxfattribs={"layer": "form_front_view_profile"})

    def begin_draw_hoist_embedded_part_xoy_projection_shape(self):
        """
        开始绘制吊装预埋件xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_hoist_embedded_part_XOZ_projection_data()
        for single_rebar in profile_data:
            for seg in single_rebar:
                point_s = seg[0]
                point_e = seg[1]
                point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
                point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
                self.rebar_reinforcement_view_block.add_line(point_s, point_e, dxfattribs={"layer": "form_front_view_embedded"})

    def begin_draw_truss_top_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架上弦钢筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_truss_top_long_rebar_XOZ_projection_data()
        for seg in profile_data:
            point_s = seg[0]
            point_e = seg[1]
            point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
            point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
            point_s = transform_point_from_xz_plane_to_xy_plane(point_s)
            point_e = transform_point_from_xz_plane_to_xy_plane(point_e)
            self.rebar_reinforcement_view_top_rebar_block.add_line(tuple(point_s), tuple(point_e),
                                                          dxfattribs={"layer": "form_front_view_truss_rebar"})

    def begin_draw_pvc_hole_xoy_projection_shape(self):
        """
        开始绘制pvc孔洞xoy平面投影形状
        :return:
        """
        projection_info = self.model_transform_data.generate_pvc_hole_XOZ_projection_data()
        hole_diam = projection_info["hole_diam"]  # 获取pvc管的孔洞直径
        hole_loc = projection_info["hole_loc"]  # 获取pvc管的中心位置
        for point in hole_loc:
            point_c = adjust_drawing_scale(list(point), 1 / self.scale)
            point_c = transform_point_from_xz_plane_to_xy_plane(point_c)
            curr_radius = hole_diam * (1 / self.scale) / 2
            self.rebar_reinforcement_view_top_rebar_block.add_circle(point_c, curr_radius,
                                                  dxfattribs={"layer": "form_front_view_embedded"})

    def begin_draw_support_bolt_xoy_projection_shape(self):
        """
        开始绘制斜撑螺栓xoy平面投影形状
        :return:
        """
        projection_info = self.model_transform_data.generate_support_bolt_XOZ_projection_data()
        bolt_exterior_radius = projection_info["bolt_outer_radius"]
        bolt_interior_radius = projection_info["bolt_inner_radius"]
        plate_shape = projection_info["plate_shape"]
        bolt_loc = projection_info["bolt_loc"]
        # 开始变换形状
        multi_changed_plate_shape = []
        # 开始绘制图形
        for curr_loc in bolt_loc:
            # 全局位置
            changed_plate_shape = []
            for point in plate_shape:
                global_p = np.array(copy.deepcopy(point)) + np.array(list(copy.deepcopy(curr_loc)))
                global_p = adjust_drawing_scale(list(global_p), 1 / self.scale)
                point_c = transform_point_from_xz_plane_to_xy_plane(global_p)
                changed_plate_shape.append(point_c)
            multi_changed_plate_shape.append(changed_plate_shape)

        # 开始绘制图形
        for curr_loc in bolt_loc:
            # 全局位置
            curr_point = copy.deepcopy(curr_loc)
            point_c = adjust_drawing_scale(list(curr_point), 1 / self.scale)
            point_c = transform_point_from_xz_plane_to_xy_plane(point_c)
            exterior_radius = bolt_exterior_radius * (1 / self.scale)
            interior_radius = bolt_interior_radius * (1 / self.scale)

            # 开始绘制外圆
            self.rebar_reinforcement_view_top_rebar_block.add_circle(point_c, exterior_radius,
                                                  dxfattribs={"layer": "form_front_view_embedded"})
            # 开始绘制内圆
            self.rebar_reinforcement_view_top_rebar_block.add_circle(point_c, interior_radius,
                                                  dxfattribs={"layer": "form_front_view_embedded"})

        # 开始绘制多边形
        for single_shape in multi_changed_plate_shape:
            for num in range(len(single_shape) - 1):
                point_s = copy.deepcopy(single_shape[num])
                point_e = copy.deepcopy(single_shape[num + 1])
                self.rebar_reinforcement_view_top_rebar_block.add_line(tuple(point_s), tuple(point_e),
                                                    dxfattribs={"layer": "form_front_view_embedded"})

    def begin_draw_construct_horizon_rebar_xoy_projection_shape(self):
        """
        开始绘制构造横向钢筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_construct_horizon_rebar_XOZ_cut_data()
        for seg in profile_data:
            point_s = seg[0]
            point_e = seg[1]
            point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
            point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
            point_s = transform_point_from_xz_plane_to_xy_plane(point_s)
            point_e = transform_point_from_xz_plane_to_xy_plane(point_e)
            self.rebar_reinforcement_view_top_rebar_block.add_line(tuple(point_s), tuple(point_e),
                                                          dxfattribs={"layer": "form_front_view_embedded"})

    def begin_draw_construct_vertical_rebar_xoy_projection_shape(self):
        """
        开始绘制构造竖向钢筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_construct_vertical_rebar_XOZ_cut_data()
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
                point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
                point_s = transform_point_from_xz_plane_to_xy_plane(point_s)
                point_e = transform_point_from_xz_plane_to_xy_plane(point_e)
                self.rebar_reinforcement_view_top_rebar_block.add_line(tuple(point_s), tuple(point_e),
                                                              dxfattribs={"layer": "form_front_view_embedded"})

    def tool_normal_two_floor_dimension_template(self, total_dimension_points, total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1 / self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1 / self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.rebar_reinforcement_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_front_view_dimension"}
                        )
                    else:
                        dim = self.rebar_reinforcement_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_front_view_dimension"}
                        )
                    dim.render()

    def begin_draw_xoy_bottom_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_rebar_reinforcement_view_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points, second_floor_points]
        total_offset = [self.dimension_offset * 0.5, self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_draw_xoy_top_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面顶部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_rebar_reinforcement_view_top_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points, second_floor_points]
        total_offset = [self.dimension_offset * 0.5, self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_draw_xoy_left_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面左侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_rebar_reinforcement_view_left_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points, second_floor_points]
        total_offset = [self.dimension_offset * 0.5, self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_draw_xoy_right_dimension_shape(self):
        """
        开始绘制模板主视图xoy平面右侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_rebar_reinforcement_view_right_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset * 0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points, total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_XOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x + form_bbox.max_x) / 2, -(self.dimension_offset + self.note_text_size), 0]
        # 添加文本
        view_text_name = "配筋图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1 / self.scale)
        self.rebar_reinforcement_view_text_block.add_text(view_text_name,
                                                 height=self.note_text_size,
                                                 dxfattribs={"layer": "form_front_view_text"}
                                                 ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def tool_draw_single_cut_sign(self,point,direction,text,align_loc):
        """
        绘制单个剖切符号:剖切符号的位置1---BOTTOM_CENTER，2---LEFT
        :param point:
        :param direction:
        :param text:
        :param align_loc:
        :return:
        """
        point_1 = np.array(point)+direction*self.dimension_offset/2/3
        point_2 = np.array(point) + direction * self.dimension_offset / 2
        text_loc = [(point_1[0]+point_2[0])/2,(point_1[1]+point_2[1])/2,(point_1[2]+point_2[2])/2]
        self.rebar_reinforcement_view_cut_line_block.add_line(tuple(point_1.tolist()), tuple(point_2.tolist()),
                                                          dxfattribs={"layer": "cut_line"})
        if align_loc == 1:
            text_align = TextEntityAlignment.BOTTOM_CENTER
        else:
            text_align = TextEntityAlignment.RIGHT
        self.rebar_reinforcement_view_text_block.add_text(text,
                                                 height=self.cut_line_text_size,
                                                 dxfattribs={"layer": "form_front_view_text"}
                                                 ).set_placement(text_loc, align=text_align)

    def begin_draw_rebar_reinforcement_view_cut_sign_shape(self):
        """
        开始绘制配筋图剖切符形状
        :return:
        """
        total_cut_info = self.model_transform_data.generate_rebar_reinforcement_view_cut_line_points()
        for single_cut_info in total_cut_info:
            point_left_1 = single_cut_info[0]
            direction_left_1 = single_cut_info[1]
            text_left_right = single_cut_info[2]
            align_loc = single_cut_info[3]
            self.tool_draw_single_cut_sign(point_left_1,direction_left_1,text_left_right,align_loc)

    def tool_draw_outline_shape(self,point_s,length_1,direction_1,text_1):
        """
        绘制引出线形状
        :param point_s:
        :param length_1:
        :param direction_1:
        :param text_1:
        :return:
        """
        point_e = np.array(point_s) + direction_1*(length_1+self.dimension_offset/2/3)
        center = point_e + direction_1*self.cut_line_text_size/2
        self.rebar_reinforcement_view_outline_block.add_line(tuple(point_s), tuple(point_e.tolist()),
                                                          dxfattribs={"layer": "cut_line"})
        self.rebar_reinforcement_view_outline_block.add_circle(tuple(center.tolist()), self.cut_line_text_size/2,
                                                  dxfattribs={"layer": "cut_line"})
        self.rebar_reinforcement_view_text_block.add_text(text_1,
                                                          height=self.cut_line_text_size,
                                                          dxfattribs={"layer": "form_front_view_text"}
                                                          ).set_placement(center,
                                                                          align=TextEntityAlignment.MIDDLE_CENTER)

    def begin_draw_rebar_reinforcement_view_outline_shape(self):
        """
        开始绘制配筋图引出线形状
        :return:
        """
        total_outline_info = self.model_transform_data.generate_rebar_reinforcement_view_outline_shape_points()
        for single_outline_info in total_outline_info:
            point_s = single_outline_info[0]
            length_1 = single_outline_info[1]
            direction_1 = single_outline_info[2]
            text_1 = single_outline_info[3]
            self.tool_draw_outline_shape(point_s,length_1,direction_1,text_1)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_hoist_embedded_part_xoy_projection_shape()
        self.begin_draw_truss_top_rebar_xoy_projection_shape()
        self.begin_draw_pvc_hole_xoy_projection_shape()
        self.begin_draw_support_bolt_xoy_projection_shape()
        self.begin_draw_construct_horizon_rebar_xoy_projection_shape()
        self.begin_draw_construct_vertical_rebar_xoy_projection_shape()
        self.begin_draw_xoy_bottom_dimension_shape()
        self.begin_draw_xoy_top_dimension_shape()
        self.begin_draw_xoy_left_dimension_shape()
        self.begin_draw_xoy_right_dimension_shape()
        self.begin_add_xoy_view_name_text()
        self.begin_draw_rebar_reinforcement_view_cut_sign_shape()
        self.begin_draw_rebar_reinforcement_view_outline_shape()


class ReinforcementOneToOneSectionView(object):
    """
    生成双皮剪力墙配筋1-1剖切图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.reinforce_section_one_view = self.dxf_doc
        self.model_space = self.reinforce_section_one_view.modelspace()

    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.reinforce_section_one_view_block = self.reinforce_section_one_view.blocks.new("reinforce_section_one_view_block")  # 添加视图块
        self.reinforce_section_one_view_rebar_block = self.reinforce_section_one_view.blocks.new("reinforce_section_one_view_rebar_block")  # 添加视图块
        self.reinforce_section_one_view_dimension_block = self.reinforce_section_one_view.blocks.new("reinforce_section_one_view_dimension_block")  # 配筋图标注块
        self.reinforce_section_one_view_text_block = self.reinforce_section_one_view.blocks.new("reinforce_section_one_view_text_block")  # 配筋图文本块
        self.reinforce_section_one_view_outline_block = self.reinforce_section_one_view.blocks.new("reinforce_section_one_view_outline_block")  # 配筋图文本块

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.reinforce_section_one_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_rebar_section_shape(self,point_sets,diam):
        """
        开始绘制钢筋截面形状
        :param point_sets:
        :param diam:
        :return:
        """
        for point in point_sets:
            point_c = list(adjust_drawing_scale(list(point), 1/self.scale))
            point_c[2] = 0
            curr_radius = diam*(1/self.scale)/2
            self.reinforce_section_one_view_block.add_circle(tuple(point_c), curr_radius,
                                                  dxfattribs={"layer":"form_front_view_embedded"})

    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状---1-1剖面图
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_top_and_bottom_long_rebar_xoy_projection_shape(self):
        """
        创建桁架上弦和下弦纵向钢筋xoy投影形状---1-1剖面图
        :return:
        """
        top_rebar_data = self.model_transform_data.generate_truss_top_rebar_location_points()
        top_rebar_profile = [seg[0] for seg in top_rebar_data["profile"]]
        top_rebar_diam = 2*top_rebar_data["Radius"]
        bottom_rebar_data = self.model_transform_data.generate_truss_bottom_rebar_location_points()
        bottom_rebar_profile = [seg[0] for seg in bottom_rebar_data["profile"]]
        bottom_rebar_diam = 2*bottom_rebar_data["Radius"]
        self.tool_draw_rebar_section_shape(top_rebar_profile,top_rebar_diam)
        self.tool_draw_rebar_section_shape(bottom_rebar_profile,bottom_rebar_diam)

    def begin_draw_truss_construct_horizon_rebar_xoy_projection_shape(self):
        """
        创建桁架构造横向钢筋xoy投影形状---1-1剖面图
        :return:
        """
        profile_data = self.model_transform_data.generate_construct_horizon_cut_points()
        layer_name = "form_front_view_embedded"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_construct_vertical_rebar_xoy_projection_shape(self):
        """
        创建桁架构造竖向钢筋xoy投影形状---1-1剖面图
        :return:
        """
        construct_vertical_rebar_info = self.model_transform_data.generate_construct_vertical_rebar_location_points()
        construct_vertical_rebar_profile = [seg[0] for seg in construct_vertical_rebar_info["profile"]]
        vertical_rebar_diam = 2 * construct_vertical_rebar_info["Radius"]
        self.tool_draw_rebar_section_shape(construct_vertical_rebar_profile,vertical_rebar_diam)


    def begin_draw_truss_stirrup_rebar_xoy_projection_shape(self):
        """
        创建桁架马镫筋xoy投影形状---1-1剖面图
        :return:
        """
        profile_data_ = self.model_transform_data.generate_truss_stirrup_straight_rebar_XOY_projection_data()
        layer_name = "form_top_view_profile"
        self.tool_draw_view_solid_projection_shape(profile_data_,layer_name)

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.reinforce_section_one_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_top_view_dimension"}
                        )
                    else:
                        dim = self.reinforce_section_one_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_top_view_dimension"}
                        )
                    dim.render()

    def begin_draw_xoy_right_dimension_shape(self):
        """
        开始绘制1-1剖面图xoy平面右侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_one_to_one_section_right_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_xoy_bottom_dimension_shape(self):
        """
        开始绘制1-1剖面图xoy平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_one_to_one_section_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_xoy_top_dimension_shape(self):
        """
        开始绘制1-1剖面图xoy平面顶部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_one_to_one_section_top_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_XOY_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "1-1剖面图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.reinforce_section_one_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def tool_draw_outline_shape(self,point_s,length_1,direction_1,text_1):
        """
        绘制引出线形状
        :param point_s:
        :param length_1:
        :param direction_1:
        :param text_1:
        :return:
        """
        point_e = np.array(point_s) + direction_1*(length_1+self.dimension_offset/2/3)
        center = point_e + direction_1*self.cut_line_text_size/2
        self.reinforce_section_one_view_outline_block.add_line(tuple(point_s), tuple(point_e.tolist()),
                                                          dxfattribs={"layer": "cut_line"})
        self.reinforce_section_one_view_outline_block.add_circle(tuple(center.tolist()), self.cut_line_text_size/2,
                                                  dxfattribs={"layer": "cut_line"})
        self.reinforce_section_one_view_text_block.add_text(text_1,
                                                          height=self.cut_line_text_size,
                                                          dxfattribs={"layer": "form_front_view_text"}
                                                          ).set_placement(center,
                                                                          align=TextEntityAlignment.MIDDLE_CENTER)

    def begin_draw_reinforcement_section_one_to_one_view_outline_shape(self):
        """
        开始绘制1-1剖切图引出线形状
        :return:
        """
        total_outline_info = self.model_transform_data.generate_rebar_section_one_to_one_view_outline_shape_points()
        for single_outline_info in total_outline_info:
            point_s = single_outline_info[0]
            length_1 = single_outline_info[1]
            direction_1 = single_outline_info[2]
            text_1 = single_outline_info[3]
            self.tool_draw_outline_shape(point_s,length_1,direction_1,text_1)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_truss_top_and_bottom_long_rebar_xoy_projection_shape()
        self.begin_draw_truss_construct_horizon_rebar_xoy_projection_shape()
        self.begin_draw_truss_construct_vertical_rebar_xoy_projection_shape()
        self.begin_draw_truss_top_and_bottom_long_rebar_xoy_projection_shape()
        self.begin_draw_truss_stirrup_rebar_xoy_projection_shape()
        self.begin_draw_xoy_bottom_dimension_shape()
        self.begin_draw_xoy_top_dimension_shape()
        self.begin_draw_xoy_right_dimension_shape()
        self.begin_add_xoy_view_name_text()
        self.begin_draw_reinforcement_section_one_to_one_view_outline_shape()


class ReinforcementTwoToTwoSectionView(object):
    """
    生成双皮剪力墙钢筋2-2剖面图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.reinforce_section_two_view = self.dxf_doc
        self.model_space = self.reinforce_section_two_view.modelspace()


    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.reinforce_section_two_view_block = self.reinforce_section_two_view.blocks.new("reinforce_section_two_view_block")  # 添加视图块
        self.reinforce_section_two_view_rebar_block = self.reinforce_section_two_view.blocks.new("reinforce_section_two_view_rebar_block")  # 添加视图块
        self.reinforce_section_two_view_dimension_block = self.reinforce_section_two_view.blocks.new("reinforce_section_two_view_dimension_block")  # 配筋图标注块
        self.reinforce_section_two_view_text_block = self.reinforce_section_two_view.blocks.new("reinforce_section_two_view_text_block")  # 配筋图文本块
        self.reinforce_section_two_view_outline_block = self.reinforce_section_two_view.blocks.new("reinforce_section_two_view_outline_block")  # 配筋图文本块

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.reinforce_section_two_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape_yz_to_xy(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s_1 = [point_s[1],point_s[2],0]
                point_e_1 = [point_e[1],point_e[2],0]
                point_s = adjust_drawing_scale(list(point_s_1),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e_1),1/self.scale)
                self.reinforce_section_two_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_rebar_section_shape(self,point_sets,diam):
        """
        开始绘制钢筋截面形状
        :param point_sets:
        :param diam:
        :return:
        """
        for point in point_sets:
            point_c = list(adjust_drawing_scale(list(point), 1/self.scale))
            point_c[2] = 0
            curr_radius = diam*(1/self.scale)/2
            self.reinforce_section_two_view_block.add_circle(tuple(point_c), curr_radius,
                                                  dxfattribs={"layer":"form_front_view_embedded"})

    def begin_draw_double_wall_solid_xoy_projection_shape(self):
        """
        创建双皮剪力墙实体xoy投影形状---右视图
        :return:
        """
        profile_data = self.model_transform_data.generate_double_shear_wall_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_interior_wall_construct_vertical_rebar_xoy_projection_shape(self):
        """
        开始绘制内皮墙构造竖向钢筋xoy平面投影数据
        :return:
        """
        profile_data = self.model_transform_data.generate_interior_wall_construct_vertical_rebar_YOZ_cut_points()
        layer_name = "form_right_view_profile"
        self.tool_draw_view_solid_projection_shape_yz_to_xy(profile_data,layer_name)

    def begin_draw_exterior_wall_construct_vertical_rebar_xoy_projection_shape(self):
        """
        开始绘制外皮墙构造竖向钢筋xoy平面投影数据
        :return:
        """
        profile_data = self.model_transform_data.generate_exterior_wall_construct_vertical_rebar_YOZ_cut_points()
        layer_name = "form_right_view_profile"
        self.tool_draw_view_solid_projection_shape_yz_to_xy(profile_data,layer_name)

    def begin_draw_interior_wall_construct_horizon_rebar_xoy_projection_shape(self):
        """
        创建内皮墙构造水平钢筋xoy投影形状
        :return:
        """
        construct_horizon_rebar_data = self.model_transform_data.generate_interior_wall_construct_horizon_rebar_YOZ_cut_points()
        rebar_profile = construct_horizon_rebar_data["profile"]
        rebar_diam = construct_horizon_rebar_data["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile,rebar_diam)

    def begin_draw_exterior_wall_construct_horizon_rebar_xoy_projection_shape(self):
        """
        创建外皮墙构造水平钢筋xoy投影形状
        :return:
        """
        construct_horizon_rebar_data = self.model_transform_data.generate_exterior_wall_construct_horizon_rebar_YOZ_cut_points()
        rebar_profile = construct_horizon_rebar_data["profile"]
        rebar_diam = construct_horizon_rebar_data["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile,rebar_diam)

    def begin_draw_truss_stirrup_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架马镫筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_truss_stirrup_rebar_YOZ_projection_data()
        layer_name = "form_right_view_profile"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)


    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.reinforce_section_two_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_right_view_dimension"}
                        )
                    else:
                        dim = self.reinforce_section_two_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_right_view_dimension"}
                        )
                    dim.render()

    def begin_draw_yoz_bottom_dimension_shape(self):
        """
        开始绘制模板右视图yoz平面底部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_right_view_bottom_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_yoz_left_dimension_shape(self):
        """
        开始绘制模板右视图yoz平面左侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_form_right_view_left_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_yoz_top_dimension_shape(self):
        """
        开始绘制配筋2-2剖切图yoz平面顶部标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_reinforcement_two_section_top_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_draw_yoz_right_dimension_shape(self):
        """
        开始绘制配筋2-2剖切图yoz平面右侧标注形状
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_reinforcement_two_section_right_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        form_projection_data = self.model_transform_data.generate_double_shear_wall_YOZ_projection_data()
        form_bbox = get_polygon_bounding_box_points(form_projection_data)
        text_loc = [(form_bbox.min_x+form_bbox.max_x)/2,-(self.dimension_offset+self.note_text_size),0]
        # 添加文本
        view_text_name = "2-2剖面图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.reinforce_section_two_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def tool_draw_outline_shape(self,point_s,length_1,direction_1,text_1):
        """
        绘制引出线形状
        :param point_s:
        :param length_1:
        :param direction_1:
        :param text_1:
        :return:
        """
        point_e = np.array(point_s) + direction_1*(length_1+self.dimension_offset/2/3)
        center = point_e + direction_1*self.cut_line_text_size/2
        self.reinforce_section_two_view_outline_block.add_line(tuple(point_s), tuple(point_e.tolist()),
                                                          dxfattribs={"layer": "cut_line"})
        self.reinforce_section_two_view_outline_block.add_circle(tuple(center.tolist()), self.cut_line_text_size/2,
                                                  dxfattribs={"layer": "cut_line"})
        self.reinforce_section_two_view_text_block.add_text(text_1,
                                                          height=self.cut_line_text_size,
                                                          dxfattribs={"layer": "form_front_view_text"}
                                                          ).set_placement(center,
                                                                          align=TextEntityAlignment.MIDDLE_CENTER)

    def begin_draw_reinforcement_section_two_to_two_view_outline_shape(self):
        """
        开始绘制2-2剖切图引出线形状
        :return:
        """
        total_outline_info = self.model_transform_data.generate_reinforcement_two_section_view_outline_shape_points()
        for single_outline_info in total_outline_info:
            point_s = single_outline_info[0]
            length_1 = single_outline_info[1]
            direction_1 = single_outline_info[2]
            text_1 = single_outline_info[3]
            self.tool_draw_outline_shape(point_s,length_1,direction_1,text_1)

    def main_run_process(self):
        """
        主要运行过程
        :return:
        """
        self.begin_draw_double_wall_solid_xoy_projection_shape()
        self.begin_draw_interior_wall_construct_vertical_rebar_xoy_projection_shape()
        self.begin_draw_exterior_wall_construct_vertical_rebar_xoy_projection_shape()
        self.begin_draw_interior_wall_construct_horizon_rebar_xoy_projection_shape()
        self.begin_draw_exterior_wall_construct_horizon_rebar_xoy_projection_shape()
        self.begin_draw_truss_stirrup_rebar_xoy_projection_shape()
        self.begin_draw_yoz_bottom_dimension_shape()
        self.begin_draw_yoz_left_dimension_shape()
        self.begin_draw_yoz_top_dimension_shape()
        self.begin_draw_yoz_right_dimension_shape()
        self.begin_add_xoy_view_name_text()
        self.begin_draw_reinforcement_section_two_to_two_view_outline_shape()


class TrussRebarDetailView(object):
    """
    桁架钢筋细部详图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.truss_rebar_detail_view = self.dxf_doc
        self.model_space = self.truss_rebar_detail_view.modelspace()

    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.truss_rebar_detail_view_block = self.truss_rebar_detail_view.blocks.new("truss_rebar_detail_view_block")  # 添加视图块
        self.truss_rebar_detail_view_rebar_block = self.truss_rebar_detail_view.blocks.new("truss_rebar_detail_view_rebar_block")  # 添加视图块
        self.truss_rebar_detail_view_dimension_block = self.truss_rebar_detail_view.blocks.new("truss_rebar_detail_view_dimension_block")  # 配筋图标注块
        self.truss_rebar_detail_view_text_block = self.truss_rebar_detail_view.blocks.new("truss_rebar_detail_view_text_block")  # 配筋图文本块
        self.truss_rebar_detail_view_outline_block = self.truss_rebar_detail_view.blocks.new("truss_rebar_detail_view_outline_block")  # 配筋图文本块

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.truss_rebar_detail_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_rebar_section_shape(self, point_sets, diam):
        """
        开始绘制钢筋截面形状
        :param point_sets:
        :param diam:
        :return:
        """
        for point in point_sets:
            point_c = list(adjust_drawing_scale(list(point), 1 / self.scale))
            point_c[2] = 0
            curr_radius = diam * (1 / self.scale) / 2
            self.truss_rebar_detail_view_rebar_block.add_circle(tuple(point_c), curr_radius,
                                                                dxfattribs={"layer": "form_front_view_embedded"})

    def begin_draw_truss_rebar_detail_view_wall_profile_xoy_projection_shape(self):
        """
        开始绘制桁架钢筋细部图墙体xoy平面投影形状
        :return:
        """
        _,_,_,_,e_w_profile,i_w_profile,_ = self.model_transform_data.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        layer_name = "form_right_view_profile"
        self.tool_draw_view_solid_projection_shape(e_w_profile,layer_name)
        self.tool_draw_view_solid_projection_shape(i_w_profile,layer_name)

    def begin_draw_truss_rebar_detail_view_horizon_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架钢筋细部图横向钢筋xoy平面投影形状
        :return:
        """
        e_h_rebar,i_h_rebar,_,_,_,_,_ = self.model_transform_data.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        layer_name = "form_right_view_embedded"
        self.tool_draw_view_solid_projection_shape(e_h_rebar,layer_name)
        self.tool_draw_view_solid_projection_shape(i_h_rebar,layer_name)

    def begin_draw_construct_vertical_rebar_xoy_projection_shape(self):
        """
        创建内皮墙构造水平钢筋xoy投影形状
        :return:
        """
        _, _, interior_vertical_rebar, exterior_vertical_rebar, _, _, _ = self.model_transform_data.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        # 内层钢筋
        rebar_profile = interior_vertical_rebar["profile"]
        rebar_diam = interior_vertical_rebar["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile, rebar_diam)
        # 外层钢筋
        rebar_profile = exterior_vertical_rebar["profile"]
        rebar_diam = exterior_vertical_rebar["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile, rebar_diam)

    def begin_draw_truss_top_bottom_rebar_xoy_projection_shape(self):
        """
        创建内皮墙桁架上弦和下弦钢筋xoy投影形状
        :return:
        """
        truss_top_rebar_info,truss_bottom_rebar_info,_ = self.model_transform_data.generate_truss_rebar_detail_view_truss_rebar_shape_points()
        # 内层钢筋
        rebar_profile = truss_top_rebar_info["profile"]
        rebar_diam = truss_top_rebar_info["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile, rebar_diam)
        # 外层钢筋
        rebar_profile = truss_bottom_rebar_info["profile"]
        rebar_diam = truss_bottom_rebar_info["diam"]
        self.tool_draw_rebar_section_shape(rebar_profile, rebar_diam)

    def begin_draw_truss_stirrup_xoy_projection_shape(self):
        """
        开始绘制桁架马凳筋xoy平面投影形状
        :return:
        """
        _, _, first_truss_stirrup = self.model_transform_data.generate_truss_rebar_detail_view_truss_rebar_shape_points()
        layer_name = "form_right_view_embedded"
        self.tool_draw_view_solid_projection_shape(first_truss_stirrup,layer_name)


    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.truss_rebar_detail_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_right_view_dimension"}
                        )
                    else:
                        dim = self.truss_rebar_detail_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_right_view_dimension"}
                        )
                    dim.render()


    def begin_draw_truss_rebar_detail_view_dimension_shape(self):
        """
        开始绘制桁架钢筋细部构造视图标注形状点
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_truss_rebar_detail_view_dimension_shape_points()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)


    def tool_draw_outline_shape(self,total_line,total_text):
        """
        绘制引出线形状
        :param total_line:
        :param total_text:

        :return:
        """
        for seg in total_line:
            point_s = list(seg[0])
            point_e = list(seg[1])
            point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
            point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
            self.truss_rebar_detail_view_outline_block.add_line(tuple(point_s), tuple(point_e),
                                                          dxfattribs={"layer": "break_line"})
        self.truss_rebar_detail_view_text_block.add_text(total_text[1],
                                                          height=self.cut_line_text_size,
                                                          dxfattribs={"layer": "form_front_view_text"}
                                                          ).set_placement(tuple(total_text[0]),
                                                                          align=TextEntityAlignment.BOTTOM_CENTER)

    def begin_draw_truss_rebar_view_outline_shape(self):
        """
        开始绘制桁架马凳筋图引出线形状
        :return:
        """
        total_outline_info = self.model_transform_data.generate_truss_rebar_detail_view_outline_shape_points()
        for single_outline_info in total_outline_info:
            total_line_1 = single_outline_info[0]
            total_text_1 = single_outline_info[1]
            self.tool_draw_outline_shape(total_line_1,total_text_1)

    def begin_draw_left_right_breakline_shape(self):
        """
        开始绘制折断线形状
        :return:
        """
        total_break_line = self.model_transform_data.generate_truss_rebar_detail_view_breakline_shape_points()
        layer_name = "break_line"
        self.tool_draw_view_solid_projection_shape(total_break_line,layer_name)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        _, _, _, _, e_w_profile, i_w_profile, _ = self.model_transform_data.generate_truss_rebar_detail_view_exterior_interior_construct_horizon_rebar_shape_points()
        point_1 = i_w_profile[0][0]
        point_2 = i_w_profile[0][1]
        text_loc = [(point_1[0]+point_2[0])/2,-(self.dimension_offset/2+self.note_text_size),0]
        # 添加文本
        view_text_name = "桁架筋细部构造图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.truss_rebar_detail_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主程序
        :return:
        """
        self.begin_draw_truss_rebar_detail_view_wall_profile_xoy_projection_shape()
        self.begin_draw_truss_rebar_detail_view_horizon_rebar_xoy_projection_shape()
        self.begin_draw_construct_vertical_rebar_xoy_projection_shape()
        self.begin_draw_truss_top_bottom_rebar_xoy_projection_shape()
        self.begin_draw_truss_stirrup_xoy_projection_shape()
        self.begin_draw_truss_rebar_view_outline_shape()
        self.begin_draw_left_right_breakline_shape()
        self.begin_draw_truss_rebar_detail_view_dimension_shape()
        self.begin_add_xoy_view_name_text()


class TrussRebarDetailRebarView(object):
    """
    桁架钢筋细部钢筋详图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.truss_rebar_detail_rebar_view = self.dxf_doc
        self.model_space = self.truss_rebar_detail_rebar_view.modelspace()

    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.truss_rebar_detail_rebar_view_block = self.truss_rebar_detail_rebar_view.blocks.new("truss_rebar_detail_rebar_view_block")  # 添加视图块
        self.truss_rebar_detail_rebar_view_dimension_block = self.truss_rebar_detail_rebar_view.blocks.new("truss_rebar_detail_rebar_view_dimension_block")  # 配筋图标注块
        self.truss_rebar_detail_rebar_view_text_block = self.truss_rebar_detail_rebar_view.blocks.new("truss_rebar_detail_rebar_view_text_block")  # 配筋图文本块
        self.truss_rebar_detail_rebar_view_outline_block = self.truss_rebar_detail_rebar_view.blocks.new("truss_rebar_detail_rebar_view_outline_block")  # 配筋图文本块

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.truss_rebar_detail_rebar_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_outline_shape(self,total_line,total_text):
        """
        绘制引出线形状
        :param total_line:
        :param total_text:

        :return:
        """
        for seg in total_line:
            point_s = list(seg[0])
            point_e = list(seg[1])
            point_s = adjust_drawing_scale(list(point_s), 1 / self.scale)
            point_e = adjust_drawing_scale(list(point_e), 1 / self.scale)
            self.truss_rebar_detail_rebar_view_outline_block.add_line(tuple(point_s), tuple(point_e),
                                                          dxfattribs={"layer": "break_line"})
        self.truss_rebar_detail_rebar_view_text_block.add_text(total_text[1],
                                                          height=self.cut_line_text_size,
                                                          dxfattribs={"layer": "form_front_view_text"}
                                                          ).set_placement(tuple(total_text[0]),
                                                                          align=TextEntityAlignment.BOTTOM_CENTER)

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.truss_rebar_detail_rebar_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_right_view_dimension"}
                        )
                    else:
                        dim = self.truss_rebar_detail_rebar_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_right_view_dimension"}
                        )
                    dim.render()

    def begin_draw_single_area_truss_stirrup_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架马镫筋xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_single_area_truss_stirrup_rebar_YOZ_projection_data()
        layer_name = "form_right_view_embedded"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_truss_top_bottom_rebar_xoy_projection_shape(self):
        """
        开始绘制桁架上弦和下弦钢筋xoy平面投影形状
        :return:
        """
        top_rebar_profile,bottom_rebar_profile,_,_ = self.model_transform_data.generate_truss_top_bottom_rebar_shape_data()
        layer_name = "form_right_view_embedded"
        self.tool_draw_view_solid_projection_shape(top_rebar_profile,layer_name)
        self.tool_draw_view_solid_projection_shape(bottom_rebar_profile,layer_name)

    def begin_draw_truss_rebar_view_outline_shape(self):
        """
        开始绘制桁架马凳筋图引出线形状
        :return:
        """
        total_outline_info = self.model_transform_data.generate_top_bottom_rebar_outline_shape_data()
        for single_outline_info in total_outline_info:
            total_line_1 = single_outline_info[0]
            total_text_1 = single_outline_info[1]
            self.tool_draw_outline_shape(total_line_1,total_text_1)

    def begin_draw_truss_rebar_detail_rebar_view_dimension_shape(self):
        """
        开始绘制桁架钢筋细部钢筋构造视图标注形状点
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_top_bottom_rebar_dimension_shape_data()
        first_floor_points = total_dimension_info["first_floor"]
        total_dimension_points = [first_floor_points]
        total_offset = [self.dimension_offset*0.5]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        _, bottom_rebar_profile, _, _ = self.model_transform_data.generate_truss_top_bottom_rebar_shape_data()
        point_1 = bottom_rebar_profile[0][0]
        point_2 = bottom_rebar_profile[0][1]
        text_loc = [(point_1[0]+point_2[0])/2,-(self.dimension_offset/2+self.note_text_size),0]
        # 添加文本
        view_text_name = "桁架筋细部钢筋构造图"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.truss_rebar_detail_rebar_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主程序
        :return:
        """
        self.begin_draw_single_area_truss_stirrup_rebar_xoy_projection_shape()
        self.begin_draw_truss_rebar_view_outline_shape()
        self.begin_draw_truss_top_bottom_rebar_xoy_projection_shape()
        self.model_transform_data.generate_single_area_truss_stirrup_rebar_YOZ_projection_data()
        self.begin_draw_truss_rebar_detail_rebar_view_dimension_shape()
        self.begin_add_xoy_view_name_text()


class HoistEmbeddedPartDetailView(object):
    """
    吊装预埋件详图
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.maximum_dimension_floor = 2
        self.rotate_angle = math.pi / 2  # 图形旋转角度，初始方向和最终放置方向旋转的角度
        self.scale = 1  # 实际尺寸与绘图尺寸的比例
        self.dimension_offset = 300 / self.scale  # 单层标注偏移

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.hoist_embedded_part_detail_view = self.dxf_doc
        self.model_space = self.hoist_embedded_part_detail_view.modelspace()

    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.hoist_embedded_part_detail_view_block = self.hoist_embedded_part_detail_view.blocks.new("hoist_embedded_part_view_block")  # 添加视图块
        self.hoist_embedded_part_detail_view_dimension_block = self.hoist_embedded_part_detail_view.blocks.new("hoist_embedded_part_view_dimension_block")  # 配筋图标注块
        self.hoist_embedded_part_detail_view_text_block = self.hoist_embedded_part_detail_view.blocks.new("hoist_embedded_part_view_text_block")  # 配筋图文本块

    # 绘制所有右视图形状
    def tool_draw_view_solid_projection_shape(self,profile_data,layer_name):
        """
        开始绘制实体右视图投影形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.hoist_embedded_part_detail_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_normal_two_floor_dimension_template(self,total_dimension_points,total_offset):
        """
        两层标注模板
        :param total_dimension_points:
        :param total_offset:
        :return:
        """
        for num_i in range(len(total_dimension_points)):
            offset = total_offset[num_i]
            floor_points = total_dimension_points[num_i]
            for num_j in range(len(floor_points)):
                current_object = floor_points[num_j]
                start_point = adjust_drawing_scale(list(current_object[0]), 1/self.scale)
                end_point = adjust_drawing_scale(list(current_object[1]), 1/self.scale)
                start_point = tuple(start_point)
                end_point = tuple(end_point)
                value = np.linalg.norm(np.array(end_point) - np.array(start_point))
                if value != 0:  # 排除无挑耳的情况
                    # 对尺寸数字反向内容进行特殊操作
                    direction = calculate_normal_vector(start_point, end_point, 0)
                    base_p_ = np.array(direction) * (offset) + np.array(list(end_point))
                    base_p = tuple(base_p_)  # 对齐点
                    if direction[1] < 0 and abs(direction[1]) > 0.0001:  # 存在截断误差
                        dim = self.hoist_embedded_part_detail_view_dimension_block.add_linear_dim(
                            base=base_p,
                            p1=start_point,
                            p2=end_point,
                            dimstyle="DS_1",
                            dxfattribs={"layer":"form_right_view_dimension"}
                        )
                    else:
                        dim = self.hoist_embedded_part_detail_view_dimension_block.add_aligned_dim(
                            p1=end_point,
                            p2=start_point,
                            distance=offset,
                            dimstyle="DS_1",
                            dxfattribs={"layer": "form_right_view_dimension"}
                        )
                    dim.render()

    def begin_draw_host_embedded_part_rebar_xoy_projection_shape(self):
        """
        开始绘吊装预埋件xoy平面投影形状
        :return:
        """
        profile_data = self.model_transform_data.generate_hoist_embedded_part_detail_view_shape_points()
        layer_name = "form_right_view_embedded"
        self.tool_draw_view_solid_projection_shape(profile_data,layer_name)

    def begin_draw_hoist_embedded_part_rebar_view_dimension_shape(self):
        """
        开始绘制吊装预埋件钢筋视图标注形状点
        :return:
        """
        total_dimension_info = self.model_transform_data.generate_hoist_embedded_part_detail_view_dimension_points()
        first_floor_points = total_dimension_info["first_floor"]
        second_floor_points = total_dimension_info["second_floor"]
        total_dimension_points = [first_floor_points,second_floor_points]
        total_offset = [self.dimension_offset*0.5,self.dimension_offset ]
        self.tool_normal_two_floor_dimension_template(total_dimension_points,total_offset)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        hoist_bbox = self.model_transform_data.generate_hoist_embedded_part_detail_view_bounding_box()
        point_1 = [hoist_bbox.min_x,hoist_bbox.min_y,hoist_bbox.min_z]
        point_2 = [hoist_bbox.max_x,hoist_bbox.min_y,hoist_bbox.min_z]
        text_loc = [(point_1[0]+point_2[0])/2,-self.note_text_size,0]
        # 添加文本
        view_text_name = "吊环大样"
        top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
        self.hoist_embedded_part_detail_view_text_block.add_text(view_text_name,
                               height=self.note_text_size,
                               dxfattribs={"layer": "form_top_view_text_block"}
                               ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主要运行程序
        :return:
        """
        self.begin_draw_host_embedded_part_rebar_xoy_projection_shape()
        self.begin_draw_hoist_embedded_part_rebar_view_dimension_shape()
        self.begin_add_xoy_view_name_text()


class TotalDesignInfoTable(object):
    """
    所有设计信息表
    color：1---red、2---yellow、3---green、4----cyan、5----blue、6----purple、7----white
    """
    def __init__(self,dxf_doc:Drawing,model_transform_data:DoubleShearWallViewData):
        self.dxf_doc = dxf_doc
        self.model_transform_data = model_transform_data
        self.load_dxf_file()  # 加载dxf文件
        self.create_total_block() # 创建所有图块
        self.note_text_size = 40  # 文字大小
        self.cut_line_text_size = 25  # 文字大小
        self.scale = 1  # 实际尺寸与绘图尺寸的比例

    def load_dxf_file(self):
        """
        加载dxf文件
        :return:
        """
        self.table_info_view = self.dxf_doc
        self.model_space = self.table_info_view.modelspace()

    def create_total_block(self):
        """
        产生所有图层块
        :return:
        """
        self.rebar_material_table_view_block = self.table_info_view.blocks.new("rebar_material_view_block")  # 添加视图块
        self.rebar_material_table_text_block = self.table_info_view.blocks.new("rebar_material_table_text_block")  # 钢筋材料表文本块
        self.component_material_table_view_block = self.table_info_view.blocks.new("component_material_view_block")  # 添加视图块
        self.component_material_table_text_block = self.table_info_view.blocks.new("component_material_table_text_block")  # 钢筋材料表文本块
        self.embedded_material_table_view_block = self.table_info_view.blocks.new("embedded_material_view_block")  # 添加埋件视图块
        self.embedded_material_table_text_block = self.table_info_view.blocks.new("embedded_material_table_text_block")  # 埋件材料表文本块

    # 绘制所有右视图形状
    def tool_draw_rebar_material_table_profile_shape(self,profile_data,layer_name):
        """
        钢筋材料表轮廓形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.rebar_material_table_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_component_material_table_profile_shape(self,profile_data,layer_name):
        """
        钢筋材料表轮廓形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.component_material_table_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def tool_draw_embedded_material_table_profile_shape(self,profile_data,layer_name):
        """
        埋件材料表轮廓形状
        :param profile_data: 投影数据
        :param layer_name: 投影形状图层名
        :return:
        """
        for seg in profile_data:
            for num in range(len(seg)-1):
                point_s = list(seg[num])
                point_e = list(seg[num+1])
                point_s[2] = 0
                point_e[2] = 0
                point_s = adjust_drawing_scale(list(point_s),1/self.scale)
                point_e = adjust_drawing_scale(list(point_e),1/self.scale)
                self.embedded_material_table_view_block.add_line(point_s,point_e,dxfattribs={"layer":layer_name})

    def begin_draw_rebar_material_table_profile_shape(self):
        """
        开始绘制钢筋材料表轮廓形状
        :return:
        """
        total_profile,_,rebar_shape,_,_ = self.model_transform_data.generate_rebar_material_table_shape_points()
        # 钢筋下料表轮廓形状
        profile_layer_name = "form_right_view_profile"  # form_right_view_embedded
        self.tool_draw_rebar_material_table_profile_shape(total_profile,profile_layer_name)
        # 钢筋下料表钢筋形状
        rebar_layer_name = "form_right_view_embedded"
        self.tool_draw_rebar_material_table_profile_shape(rebar_shape,rebar_layer_name)

    def begin_add_xoy_view_name_text(self):
        """
        开始添加xoy平面视图名称文本
        :return:
        """
        _,total_text_info,_,total_rebar_shape_info,_ = self.model_transform_data.generate_rebar_material_table_shape_points()
        # 添加文本
        for text_info in total_text_info:
            view_text_name = text_info[1]
            text_loc = text_info[0]
            top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
            self.rebar_material_table_text_block.add_text(view_text_name,
                                   height=self.note_text_size,
                                   dxfattribs={"layer": "form_top_view_text_block"}
                                   ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)
        # 添加文本
        for text_info in total_rebar_shape_info:
            view_text_name = text_info[1]
            text_loc = text_info[0]
            top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
            self.rebar_material_table_text_block.add_text(view_text_name,
                                   height=self.note_text_size,
                                   dxfattribs={"layer": "form_top_view_text_block"}
                                   ).set_placement(top_mid_loc_t, align=TextEntityAlignment.BOTTOM_CENTER)

    def begin_draw_rebar_material_table_shape(self):
        """
        开始绘制钢筋材料表形状
        :return:
        """
        _,_,_,_,circle_info = self.model_transform_data.generate_rebar_material_table_shape_points()
        hole_diam = self.note_text_size+5  # 获取pvc管的孔洞直径
        hole_loc = circle_info["profile"]  # 获取圆心
        for point in hole_loc:
            point_c = adjust_drawing_scale(list(point), 1/self.scale)
            curr_radius = hole_diam*(1/self.scale)/2
            self.rebar_material_table_view_block.add_circle(point_c, curr_radius,
                                                  dxfattribs={"layer":"form_front_view_profile"})

    def begin_draw_component_material_table_profile_shape(self):
        """
        开始绘制预制构件材料表轮廓形状
        :return:
        """
        _,total_profile = self.model_transform_data.generate_prefabricated_component_material_strength_table_shape_points()
        # 钢筋下料表轮廓形状
        profile_layer_name = "form_right_view_profile"
        self.tool_draw_component_material_table_profile_shape(total_profile,profile_layer_name)

    def begin_add_component_material_table_xoy_view_name_text(self):
        """
        开始添加预制构件材料表名称文本
        :return:
        """
        total_text_info,_ = self.model_transform_data.generate_prefabricated_component_material_strength_table_shape_points()
        # 添加文本
        for text_info in total_text_info:
            view_text_name = text_info[1]
            text_loc = text_info[0]
            top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
            self.component_material_table_text_block.add_text(view_text_name,
                                   height=self.note_text_size,
                                   dxfattribs={"layer": "form_top_view_text_block"}
                                   ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def begin_draw_embedded_material_table_profile_shape(self):
        """
        开始绘制埋件材料表轮廓形状
        :return:
        """
        total_profile,total_text_info,hoist_embedded_part,support_bolt,pvc_hole_info = self.model_transform_data.generate_embedded_part_material_table_shape_points()
        # 埋件材料表轮廓形状
        profile_layer_name = "form_right_view_profile"
        self.tool_draw_embedded_material_table_profile_shape(total_profile,profile_layer_name)
        # 图例形状
        # 吊装埋件
        profile_layer_name = "form_right_view_profile"
        self.tool_draw_embedded_material_table_profile_shape(hoist_embedded_part,profile_layer_name)
        # 支撑埋件
        profile_layer_name = "form_right_view_profile"
        self.tool_draw_embedded_material_table_profile_shape(support_bolt,profile_layer_name)
        # pvc管
        hole_diam = pvc_hole_info["hole_diam"]  # 获取pvc管的孔洞直径
        hole_loc = pvc_hole_info["hole_loc"]  # 获取pvc管的中心位置
        point_c = adjust_drawing_scale(list(hole_loc), 1 / self.scale)
        curr_radius = hole_diam * (1 / self.scale) / 2
        self.embedded_material_table_view_block.add_circle(point_c, curr_radius,
                                              dxfattribs={"layer": "form_front_view_embedded"})

    def begin_add_embedded_material_table_xoy_view_name_text(self):
        """
        开始添加埋件材料表名称文本
        :return:
        """
        _,total_text_info,_,_,_ = self.model_transform_data.generate_embedded_part_material_table_shape_points()
        # 添加文本
        for text_info in total_text_info:
            view_text_name = text_info[1]
            text_loc = text_info[0]
            top_mid_loc_t = adjust_drawing_scale(list(text_loc), 1/self.scale)
            self.embedded_material_table_text_block.add_text(view_text_name,
                                   height=self.note_text_size,
                                   dxfattribs={"layer": "form_top_view_text_block"}
                                   ).set_placement(top_mid_loc_t, align=TextEntityAlignment.MIDDLE_CENTER)

    def main_run_process(self):
        """
        主程序运行
        :return:
        """
        # 添加钢筋下料表
        self.begin_draw_rebar_material_table_profile_shape()
        self.begin_add_xoy_view_name_text()
        self.begin_draw_rebar_material_table_shape()
        # 添加预制构件材料强度表
        self.begin_draw_component_material_table_profile_shape()
        self.begin_add_component_material_table_xoy_view_name_text()
        # 添加埋件配置表
        self.begin_draw_embedded_material_table_profile_shape()
        self.begin_add_embedded_material_table_xoy_view_name_text()


