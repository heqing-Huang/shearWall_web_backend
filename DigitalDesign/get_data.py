"""
# File       : data_initial.py
# Time       ：2022/9/09 11:27
# Author     ：CR_X
# version    ：python 3.8
# Description：
"""
import math
from typing import List

import numpy as np
from dc_rebar import Rebar, IndexedPolyCurve

from RebarLayout.fcl_models import Rebar_fcl, Box_fcl, Cylinder_fcl
from DoubleWallDesign.models import DetailedDesignResult, ShearWallType, RebarDiamSpac, WallLengthType, \
    RebarGeoBVBS, RebarBVBS, RebarParameter, TrussRebar, TrussRebarforBIM, ConcreteParameter, WallHole
from RebarLayout.tools import rotation_matrix_from_vectors, rebar_mandrel_diameter


class ShearWallData:

    def __init__(self, detailed_design_result: DetailedDesignResult):
        self.detailed_design = detailed_design_result.detailed_design
        self.detailed_design_result = detailed_design_result
        self.project_ID = self.detailed_design.shear_wall_id.project_ID
        self.shear_wall_ID = self.detailed_design.shear_wall_id.shear_wall_ID

        self.concrete_parameter = ConcreteParameter.by_grade(self.detailed_design.material.concrete_grade)  # 混凝土参数
        self.rebar_parameter = RebarParameter.by_name(self.detailed_design.material.rebar_name)  # 钢筋参数

        # 几何信息
        self.shear_wall_type: ShearWallType = self.detailed_design.geometric_detailed.shear_wall_type  # 剪力墙类型
        self.length: int = self.detailed_design.geometric_detailed.length  # 剪力墙长度 mm
        self.thickness: int = self.detailed_design.geometric_detailed.thickness  # 剪力墙总厚度 mm
        self.height: int = self.detailed_design.geometric_detailed.height  # 剪力墙总高度 mm
        self.interior_thickness: int = self.detailed_design.geometric_detailed.interior_thickness  # 内页厚度
        self.exterior_thickness: int = self.detailed_design.geometric_detailed.exterior_thickness  # 外页厚度
        self.bottom_gap_height: int = self.detailed_design.geometric_detailed.bottom_gap_height  # 底部间隙
        self.top_gap_height: int = self.detailed_design.geometric_detailed.top_gap_height  # 顶部间隙
        self.cover: int = self.detailed_design.construction_detailed.concrete_cover_thickness  # 保护层厚度
        self.interior_height: int = self.detailed_design_result.interior_height  # 内页高度
        self.exterior_height: int = self.detailed_design_result.exterior_height  # 外页高度
        self.wall_length_type: WallLengthType = self.detailed_design.geometric_detailed.wall_length_type  # 内外墙是否等长
        self.left_gap_length: int = self.detailed_design_result.left_gap_length  # 左侧缺口
        self.right_gap_length: int = self.detailed_design_result.right_gap_length  # 右侧缺口
        self.interior_length: int = self.detailed_design_result.interior_length  # 内页长度
        self.exterior_length: int = self.detailed_design_result.exterior_length  # 外页长度
        self.wall_hole: WallHole = self.detailed_design.geometric_detailed.wall_hole  # 是否有洞口

        self.horizontal_rebars: List[RebarDiamSpac] = self.detailed_design_result.horizontal_rebars  # 横向钢筋配筋
        self.vertical_rebars: List[RebarDiamSpac] = self.detailed_design_result.vertical_rebars  # 竖向钢筋配筋

        self.horizontal_rebar_dias = [rebar_dia_spc.diameter for rebar_dia_spc in self.horizontal_rebars]
        self.horizontal_rebar_dia_max = max(self.horizontal_rebar_dias)
        self.horizontal_rebar_dia_min = min(self.horizontal_rebar_dias)
        self.vertical_rebar_dias = [rebar_dia_spc.diameter for rebar_dia_spc in self.vertical_rebars]
        self.vertical_rebar_dia_max = max(self.vertical_rebar_dias)
        self.vertical_rebar_dia_min = min(self.vertical_rebar_dias)

        self.truss_detailed = self.detailed_design.truss_detailed  # 桁架输入钢筋设计参数

        if self.wall_hole == WallHole.YES:
            self.wall_hole_type = self.detailed_design.geometric_detailed.wall_hole_type  # 洞口类型
            self.wall_hole_parameter = self.detailed_design.geometric_detailed.wall_hole_parameter
        else:
            self.wall_hole_type = None  # 洞口类型
            self.wall_hole_parameter = None # 洞口参数

    def get_cover(self) -> List:
        """
        计算双皮墙保护层厚度形成的边界障碍物
        :return:
        """

        cover_objs = []

        cover_objs.append(Box_fcl(x=float(self.length), y=float(self.thickness),
                                  z=float(self.bottom_gap_height + self.cover),
                                  position=np.array([self.length / 2, self.thickness / 2,
                                                     (self.bottom_gap_height + self.cover) / 2])))  # 底部缺口
        cover_objs.append(Box_fcl(x=float(self.length), y=float(self.cover), z=float(self.interior_height),
                                  position=np.array([float(self.length / 2), float(self.cover / 2),
                                                     float(self.interior_height / 2)])))
        cover_objs.append(Box_fcl(x=float(self.length), y=float(self.cover), z=float(self.interior_height),
                                  position=np.array([float(self.length / 2),
                                                     float(self.interior_thickness - self.cover / 2),
                                                     float(self.interior_height / 2)])))
        cover_objs.append(Box_fcl(x=float(self.length), y=float(self.cover), z=float(self.exterior_height),
                                  position=np.array([float(self.length / 2),
                                                     float(self.thickness - self.exterior_thickness + self.cover / 2),
                                                     float(self.exterior_height / 2)])))
        cover_objs.append(Box_fcl(x=float(self.length), y=float(self.cover), z=float(self.exterior_height),
                                  position=np.array([float(self.length / 2),
                                                     float(self.thickness - self.cover / 2),
                                                     float(self.exterior_height / 2)])))
        cover_objs.append(Box_fcl(x=float(self.length),
                                  y=float(self.thickness - self.interior_thickness - self.exterior_thickness),
                                  z=float(self.height - self.top_gap_height - self.bottom_gap_height),
                                  position=np.array(
                                      [float(self.length / 2), float(self.thickness / 2),
                                       float((self.height - self.top_gap_height + self.bottom_gap_height) / 2)])))
        if self.shear_wall_type == ShearWallType.INTERIOR:
            cover_objs.append(Box_fcl(x=float(self.length),
                                      y=float(self.thickness),
                                      z=float(self.top_gap_height + self.cover),
                                      position=np.array(
                                          [float(self.length / 2), float(self.thickness / 2),
                                           float((self.height - (self.top_gap_height + self.cover) / 2))])))
        else:  # shear_wall_type ==ShearWallType.EXTERIOR:
            cover_objs.append(Box_fcl(x=float(self.length),
                                      y=float(self.thickness - self.exterior_thickness),
                                      z=float(self.top_gap_height + self.cover),
                                      position=np.array(
                                          [float(self.length / 2),
                                           float((self.thickness - self.exterior_thickness) / 2),
                                           float((self.height - (self.top_gap_height + self.cover) / 2))])))
            cover_objs.append(Box_fcl(x=float(self.length),
                                      y=float(self.exterior_thickness),
                                      z=float(self.cover),
                                      position=np.array(
                                          [float(self.length / 2),
                                           float(self.thickness - self.exterior_thickness / 2),
                                           float(self.height - self.cover / 2)])))
        return cover_objs

    def get_hole(self) -> List:
        """
        获取包围盒的两顶点坐标，格式：[[左下角=Point(min_x,min_y,min_z)，右上角=Point(max_x,max_y,max_z)]]
        :return:
        """
        hole_objs = []
        # 顶端孔洞边距
        top_right_long_a1 = self.detailed_design.construction_detailed.top_hole_position.a1  # 顶端右侧纵向边距
        top_right_horizon_b1 = self.detailed_design.construction_detailed.top_hole_position.b1  # 顶端右侧横向边距
        top_left_long_a2 = self.detailed_design.construction_detailed.top_hole_position.a2  # 顶端左侧纵向边距
        top_left_horizon_b2 = self.detailed_design.construction_detailed.top_hole_position.b2  # 顶端左侧横向边距
        # 底端孔洞边距
        bottom_right_long_a3 = self.detailed_design.construction_detailed.bottom_hole_position.a3  # 底端右侧纵向边距
        bottom_right_horizon_b3 = self.detailed_design.construction_detailed.bottom_hole_position.b3  # 底端右侧横向边距
        bottom_left_long_a4 = self.detailed_design.construction_detailed.bottom_hole_position.a4  # 底端左侧纵向边距
        bottom_left_horizon_b4 = self.detailed_design.construction_detailed.bottom_hole_position.b4  # 底端左侧横向边距

        top_hole_length = self.detailed_design.geometric_detailed.top_thickness
        bottom_hole_length = self.detailed_design.geometric_detailed.bottom_thickness

        if self.top_hole_type.value == 0:  # HoleType.FIXED_HINGE =0 , HoleType.SLIDING_HINGE=1
            top_radius = self.detailed_design.construction_detailed.top_hole.fix_hinge_c2 / 2
        else:
            top_radius = self.detailed_design.construction_detailed.top_hole.sliding_hinge_c1 / 2
        if self.bottom_hole_type.value == 0:  # HoleType.FIXED_HINGE =0 , HoleType.SLIDING_HINGE=1
            bottom_radius = self.detailed_design.construction_detailed.bottom_hole.fix_hinge_c2 / 2
        else:
            bottom_radius = self.detailed_design.construction_detailed.bottom_hole.sliding_hinge_c1 / 2

        hole_objs.append(Cylinder_fcl(radius=bottom_radius, length=bottom_hole_length,
                                      position=np.array([bottom_left_horizon_b4, bottom_left_long_a4,
                                                         0 + bottom_hole_length / 2])))
        hole_objs.append(Cylinder_fcl(radius=bottom_radius, length=bottom_hole_length,
                                      position=np.array([self.width - bottom_right_horizon_b3, bottom_right_long_a3,
                                                         0 + bottom_hole_length / 2])))
        hole_objs.append(Cylinder_fcl(radius=top_radius, length=top_hole_length,
                                      position=np.array([top_left_horizon_b2, self.l_total - top_left_long_a2,
                                                         self.h_total - top_hole_length / 2])))
        hole_objs.append(Cylinder_fcl(radius=top_radius, length=top_hole_length,
                                      position=np.array([self.width - top_right_horizon_b1,
                                                         self.l_total - top_right_long_a1,
                                                         self.h_total - top_hole_length / 2])))
        return hole_objs

    def get_horizontal_rebars(self):
        """
        横向钢筋数据
        :return:
        """
        rebars_BVBS = []
        rebars_objs = []
        rebars_BIM = []
        horizontal_rebar_spac = self.horizontal_rebars[0].spacing


        interior_horizontal_rebar_max = []
        interior_horizontal_rebar_min = []
        exterior_horizontal_rebar_max = []
        exterior_horizontal_rebar_min = []
        start_distance = 50  # 水平钢筋的起步间距
        interior_rebar_x_1 = self.left_gap_length + self.cover  # 内墙钢筋左端
        interior_rebar_x_2 = self.left_gap_length + self.interior_length - self.cover  # 内墙钢筋右端
        exterior_rebar_x_1 = self.cover  # 外墙钢筋左端
        exterior_rebar_x_2 = self.exterior_length - self.cover  # 外墙钢筋右端
        interior_rebar_length = interior_rebar_x_2 - interior_rebar_x_1
        exterior_rebar_length = exterior_rebar_x_2 - exterior_rebar_x_1
        interior_geometric = [RebarGeoBVBS(length=interior_rebar_length, angle=0)]
        exterior_geometric = [RebarGeoBVBS(length=exterior_rebar_length, angle=0)]
        interior_rebar_number = math.ceil((self.interior_height - 2 * start_distance) / horizontal_rebar_spac) + 1
        exterior_rebar_number = math.ceil((self.exterior_height - 2 * start_distance) / horizontal_rebar_spac) + 1
        for i in range(interior_rebar_number):
            if i == 0:
                interior_horizontal_rebar_max.append([[interior_rebar_x_1,
                                                       self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                       start_distance + self.bottom_gap_height],
                                                      [interior_rebar_x_2,
                                                       self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                       start_distance + self.bottom_gap_height]])
            elif i == interior_rebar_number - 1:
                interior_horizontal_rebar_max.append([[interior_rebar_x_1,
                                                       self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                       self.bottom_gap_height + self.interior_height - start_distance],
                                                      [interior_rebar_x_2,
                                                       self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                       self.bottom_gap_height + self.interior_height - start_distance]])
            else:
                if i % 2 == 0:
                    interior_horizontal_rebar_max.append([[interior_rebar_x_1,
                                                           self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac],
                                                          [interior_rebar_x_2,
                                                           self.cover + 0.5 * self.horizontal_rebar_dia_max,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac]])
                elif i % 2 == 1:
                    interior_horizontal_rebar_min.append([[interior_rebar_x_1,
                                                           self.cover + 0.5 * self.horizontal_rebar_dia_min,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac],
                                                          [interior_rebar_x_2,
                                                           self.cover + 0.5 * self.horizontal_rebar_dia_min,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac]])

        for i in range(exterior_rebar_number):
            if i == 0:
                exterior_horizontal_rebar_max.append([[exterior_rebar_x_1,
                                                       self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                       start_distance + self.bottom_gap_height],
                                                      [exterior_rebar_x_2,
                                                       self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                       start_distance + self.bottom_gap_height]])
            elif i == exterior_rebar_number - 1:
                exterior_horizontal_rebar_max.append([[exterior_rebar_x_1,
                                                       self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                       self.bottom_gap_height + self.exterior_height - start_distance],
                                                      [exterior_rebar_x_2,
                                                       self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                       self.bottom_gap_height + self.exterior_height - start_distance]])
            else:
                if i % 2 == 0:
                    exterior_horizontal_rebar_max.append([[exterior_rebar_x_1,
                                                           self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac],
                                                          [exterior_rebar_x_2,
                                                           self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_max,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac]])
                elif i % 2 == 1:
                    exterior_horizontal_rebar_min.append([[exterior_rebar_x_1,
                                                           self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_min,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac],
                                                          [exterior_rebar_x_2,
                                                           self.thickness - self.cover - 0.5 * self.horizontal_rebar_dia_min,
                                                           start_distance + self.bottom_gap_height + i * horizontal_rebar_spac]])

        if self.wall_length_type == WallLengthType.YES:
            if len(self.horizontal_rebar_dias) == 1:
                rebar_quantity = len(interior_horizontal_rebar_max) + len(interior_horizontal_rebar_min) + \
                                 len(exterior_horizontal_rebar_max) + len(exterior_horizontal_rebar_min)
                mandrel_diameter = rebar_mandrel_diameter(self.horizontal_rebar_dia_max / 2, self.rebar_parameter.grade)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=1, rebar_length=interior_rebar_length, rebar_quantity=rebar_quantity,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=interior_geometric))
            else:
                rebar_quantity_max = len(interior_horizontal_rebar_max) + len(interior_horizontal_rebar_max)
                rebar_quantity_min = len(interior_horizontal_rebar_min) + len(exterior_horizontal_rebar_min)
                mandrel_diameter_max = rebar_mandrel_diameter(self.horizontal_rebar_dia_max / 2,
                                                              self.rebar_parameter.grade)
                mandrel_diameter_min = rebar_mandrel_diameter(self.horizontal_rebar_dia_min / 2,
                                                              self.rebar_parameter.grade)

                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=1, rebar_length=interior_rebar_length,
                                             rebar_quantity=rebar_quantity_max,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_max,
                                             geometric=interior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=2, rebar_length=interior_rebar_length,
                                             rebar_quantity=rebar_quantity_min,
                                             rebar_diameter=self.horizontal_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=interior_geometric))
        else:  # self.wall_length_type == WallLengthType.NO:
            if len(self.horizontal_rebar_dias) == 1:
                mandrel_diameter = rebar_mandrel_diameter(self.horizontal_rebar_dia_max / 2, self.rebar_parameter.grade)
                interior_rebar_quantity = len(interior_horizontal_rebar_max) + len(interior_horizontal_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=1, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=interior_geometric))
                exterior_rebar_quantity = len(exterior_horizontal_rebar_max) + len(exterior_horizontal_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=2, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=exterior_geometric))
            else:
                mandrel_diameter_max = rebar_mandrel_diameter(self.horizontal_rebar_dia_max / 2,
                                                              self.rebar_parameter.grade)
                mandrel_diameter_min = rebar_mandrel_diameter(self.horizontal_rebar_dia_min / 2,
                                                              self.rebar_parameter.grade)
                interior_rebar_quantity_max = len(interior_horizontal_rebar_max)
                interior_rebar_quantity_min = len(interior_horizontal_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=1, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity_max,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_max,
                                             geometric=interior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=2, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity_min,
                                             rebar_diameter=self.horizontal_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=interior_geometric))
                exterior_rebar_quantity_max = len(exterior_horizontal_rebar_max)
                exterior_rebar_quantity_min = len(exterior_horizontal_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=3, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity_max,
                                             rebar_diameter=self.horizontal_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=exterior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=4, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity_min,
                                             rebar_diameter=self.horizontal_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=exterior_geometric))
        transformation = rotation_matrix_from_vectors(np.array([[0, 0, 1]]), np.array([[1, 0, 0]]))
        for i in range(len(interior_horizontal_rebar_max)):
            rebars_BIM.append(Rebar(radius=int(self.horizontal_rebar_dia_max / 2),
                                    poly=IndexedPolyCurve(interior_horizontal_rebar_max[i])))
            position = np.array(
                [(interior_horizontal_rebar_max[i][0][0] + interior_horizontal_rebar_max[i][1][0]) / 2,
                 (interior_horizontal_rebar_max[i][0][1] + interior_horizontal_rebar_max[i][1][1]) / 2,
                 (interior_horizontal_rebar_max[i][0][2] + interior_horizontal_rebar_max[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.horizontal_rebar_dia_max, length=interior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(interior_horizontal_rebar_min)):
            rebars_BIM.append(Rebar(radius=int(self.horizontal_rebar_dia_min / 2),
                                    poly=IndexedPolyCurve(interior_horizontal_rebar_min[i])))
            position = np.array(
                [(interior_horizontal_rebar_min[i][0][0] + interior_horizontal_rebar_min[i][1][0]) / 2,
                 (interior_horizontal_rebar_min[i][0][1] + interior_horizontal_rebar_min[i][1][1]) / 2,
                 (interior_horizontal_rebar_min[i][0][2] + interior_horizontal_rebar_min[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.horizontal_rebar_dia_min, length=interior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(exterior_horizontal_rebar_max)):
            rebars_BIM.append(Rebar(radius=int(self.horizontal_rebar_dia_max / 2),
                                    poly=IndexedPolyCurve(exterior_horizontal_rebar_max[i])))
            position = np.array(
                [(exterior_horizontal_rebar_max[i][0][0] + exterior_horizontal_rebar_max[i][1][0]) / 2,
                 (exterior_horizontal_rebar_max[i][0][1] + exterior_horizontal_rebar_max[i][1][1]) / 2,
                 (exterior_horizontal_rebar_max[i][0][2] + exterior_horizontal_rebar_max[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.horizontal_rebar_dia_max, length=exterior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(exterior_horizontal_rebar_min)):
            rebars_BIM.append(Rebar(radius=int(self.horizontal_rebar_dia_min / 2),
                                    poly=IndexedPolyCurve(exterior_horizontal_rebar_min[i])))
            position = np.array(
                [(exterior_horizontal_rebar_min[i][0][0] + exterior_horizontal_rebar_min[i][1][0]) / 2,
                 (exterior_horizontal_rebar_min[i][0][1] + exterior_horizontal_rebar_min[i][1][1]) / 2,
                 (exterior_horizontal_rebar_min[i][0][2] + exterior_horizontal_rebar_min[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.horizontal_rebar_dia_min, length=exterior_rebar_length,
                                         transformation=transformation, position=position))
        return rebars_BVBS, rebars_objs, rebars_BIM

    def get_vertical_rebars(self, number_s: int):
        '''
        水平钢筋数据
        :param number_s: bvbs钢筋编号开始数字
        :return:
        '''
        rebars_BVBS = []
        rebars_objs = []
        rebars_BIM = []

        vertical_rebar_spac = self.vertical_rebars[0].spacing
        interior_vertical_rebar_max = []
        interior_vertical_rebar_min = []
        exterior_vertical_rebar_max = []
        exterior_vertical_rebar_min = []
        start_distance = 50  # 竖向钢筋的起步间距
        interior_rebar_z_1 = self.bottom_gap_height + self.cover  # 内墙钢筋底端
        interior_rebar_z_2 = self.bottom_gap_height + self.interior_height - self.cover  # 内墙钢筋顶端
        exterior_rebar_z_1 = self.bottom_gap_height + self.cover  # 外墙钢筋底端
        exterior_rebar_z_2 = self.bottom_gap_height + self.exterior_height - self.cover  # 外墙钢筋顶端
        interior_rebar_length = interior_rebar_z_2 - interior_rebar_z_1
        exterior_rebar_length = exterior_rebar_z_2 - exterior_rebar_z_1
        interior_geometric = [RebarGeoBVBS(length=interior_rebar_length, angle=0)]
        exterior_geometric = [RebarGeoBVBS(length=exterior_rebar_length, angle=0)]
        interior_rebar_number = math.ceil((self.interior_length - 2 * start_distance) / vertical_rebar_spac) + 1
        exterior_rebar_number = math.ceil((self.exterior_length - 2 * start_distance) / vertical_rebar_spac) + 1
        for i in range(interior_rebar_number):
            if i == 0:
                interior_vertical_rebar_max.append([[self.left_gap_length + start_distance,
                                                     self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                                                     interior_rebar_z_1],
                                                    [self.left_gap_length + start_distance,
                                                     self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                                                     interior_rebar_z_2]])
            elif i == interior_rebar_number - 1:
                interior_vertical_rebar_max.append([[self.left_gap_length + self.interior_length - start_distance,
                                                     self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                                                     interior_rebar_z_1],
                                                    [self.left_gap_length + self.interior_length - start_distance,
                                                     self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                                                     interior_rebar_z_2]])
            else:
                if i % 2 == 0:
                    interior_vertical_rebar_max.append(
                        [[self.left_gap_length + start_distance + i * vertical_rebar_spac,
                          self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                          interior_rebar_z_1],
                         [self.left_gap_length + start_distance + i * vertical_rebar_spac,
                          self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_max,
                          interior_rebar_z_2]])
                elif i % 2 == 1:
                    interior_vertical_rebar_min.append(
                        [[self.left_gap_length + start_distance + i * vertical_rebar_spac,
                          self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_min,
                          interior_rebar_z_1],
                         [self.left_gap_length + start_distance + i * vertical_rebar_spac,
                          self.cover + self.horizontal_rebar_dia_max + 0.5 * self.vertical_rebar_dia_min,
                          interior_rebar_z_2]])

        for i in range(exterior_rebar_number):
            if i == 0:
                exterior_vertical_rebar_max.append([[start_distance,
                                                     self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                                                     exterior_rebar_z_1],
                                                    [start_distance,
                                                     self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                                                     exterior_rebar_z_2]])
            elif i == exterior_rebar_number - 1:
                exterior_vertical_rebar_max.append([[self.length - start_distance,
                                                     self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                                                     exterior_rebar_z_1],
                                                    [self.length - start_distance,
                                                     self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                                                     exterior_rebar_z_2]])
            else:
                if i % 2 == 0:
                    exterior_vertical_rebar_max.append(
                        [[start_distance + i * vertical_rebar_spac,
                          self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                          exterior_rebar_z_1],
                         [start_distance + i * vertical_rebar_spac,
                          self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_max,
                          exterior_rebar_z_2]])
                elif i % 2 == 1:
                    exterior_vertical_rebar_min.append(
                        [[start_distance + i * vertical_rebar_spac,
                          self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_min,
                          exterior_rebar_z_1],
                         [start_distance + i * vertical_rebar_spac,
                          self.thickness - self.cover - self.horizontal_rebar_dia_max - 0.5 * self.vertical_rebar_dia_min,
                          exterior_rebar_z_2]])

        if self.shear_wall_type == ShearWallType.INTERIOR:
            if len(self.vertical_rebar_dias) == 1:
                rebar_quantity = len(interior_vertical_rebar_max) + len(interior_vertical_rebar_min) + \
                                 len(exterior_vertical_rebar_max) + len(exterior_vertical_rebar_min)
                mandrel_diameter = rebar_mandrel_diameter(self.vertical_rebar_dia_max / 2, self.rebar_parameter.grade)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 1, rebar_length=interior_rebar_length,
                                             rebar_quantity=rebar_quantity,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=interior_geometric))
            else:
                rebar_quantity_max = len(interior_vertical_rebar_max) + len(interior_vertical_rebar_max)
                rebar_quantity_min = len(interior_vertical_rebar_min) + len(exterior_vertical_rebar_min)
                mandrel_diameter_max = rebar_mandrel_diameter(self.vertical_rebar_dia_max / 2,
                                                              self.rebar_parameter.grade)
                mandrel_diameter_min = rebar_mandrel_diameter(self.vertical_rebar_dia_min / 2,
                                                              self.rebar_parameter.grade)

                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 1, rebar_length=interior_rebar_length,
                                             rebar_quantity=rebar_quantity_max,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_max,
                                             geometric=interior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 2, rebar_length=interior_rebar_length,
                                             rebar_quantity=rebar_quantity_min,
                                             rebar_diameter=self.vertical_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=interior_geometric))
        else:  # self.wall_type == WallType.EXTERIOR:
            if len(self.vertical_rebar_dias) == 1:
                mandrel_diameter = rebar_mandrel_diameter(self.vertical_rebar_dia_max / 2, self.rebar_parameter.grade)
                interior_rebar_quantity = len(interior_vertical_rebar_max) + len(interior_vertical_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 1, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=interior_geometric))
                exterior_rebar_quantity = len(exterior_vertical_rebar_max) + len(exterior_vertical_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 2, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter,
                                             geometric=exterior_geometric))
            else:
                mandrel_diameter_max = rebar_mandrel_diameter(self.vertical_rebar_dia_max / 2,
                                                              self.rebar_parameter.grade)
                mandrel_diameter_min = rebar_mandrel_diameter(self.vertical_rebar_dia_min / 2,
                                                              self.rebar_parameter.grade)
                interior_rebar_quantity_max = len(interior_vertical_rebar_max)
                interior_rebar_quantity_min = len(interior_vertical_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 1, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity_max,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_max,
                                             geometric=interior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 2, rebar_length=interior_rebar_length,
                                             rebar_quantity=interior_rebar_quantity_min,
                                             rebar_diameter=self.vertical_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=interior_geometric))
                exterior_rebar_quantity_max = len(exterior_vertical_rebar_max)
                exterior_rebar_quantity_min = len(exterior_vertical_rebar_min)
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 3, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity_max,
                                             rebar_diameter=self.vertical_rebar_dia_max,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=exterior_geometric))
                rebars_BVBS.append(RebarBVBS(project_ID=self.project_ID, shear_wall_ID=self.shear_wall_ID,
                                             mark=number_s + 4, rebar_length=exterior_rebar_length,
                                             rebar_quantity=exterior_rebar_quantity_min,
                                             rebar_diameter=self.vertical_rebar_dia_min,
                                             rebar_grade=self.rebar_parameter.name,
                                             mandrel_diameter=mandrel_diameter_min,
                                             geometric=exterior_geometric))
        transformation = rotation_matrix_from_vectors(np.array([[0, 0, 1]]), np.array([[0, 0, 1]]))
        for i in range(len(interior_vertical_rebar_max)):
            rebars_BIM.append(Rebar(radius=int(self.vertical_rebar_dia_max / 2),
                                    poly=IndexedPolyCurve(interior_vertical_rebar_max[i])))
            position = np.array(
                [(interior_vertical_rebar_max[i][0][0] + interior_vertical_rebar_max[i][1][0]) / 2,
                 (interior_vertical_rebar_max[i][0][1] + interior_vertical_rebar_max[i][1][1]) / 2,
                 (interior_vertical_rebar_max[i][0][2] + interior_vertical_rebar_max[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.vertical_rebar_dia_max, length=interior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(interior_vertical_rebar_min)):
            rebars_BIM.append(Rebar(radius=int(self.vertical_rebar_dia_min / 2),
                                    poly=IndexedPolyCurve(interior_vertical_rebar_min[i])))
            position = np.array(
                [(interior_vertical_rebar_min[i][0][0] + interior_vertical_rebar_min[i][1][0]) / 2,
                 (interior_vertical_rebar_min[i][0][1] + interior_vertical_rebar_min[i][1][1]) / 2,
                 (interior_vertical_rebar_min[i][0][2] + interior_vertical_rebar_min[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.vertical_rebar_dia_min, length=interior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(exterior_vertical_rebar_max)):
            rebars_BIM.append(Rebar(radius=int(self.vertical_rebar_dia_max / 2),
                                    poly=IndexedPolyCurve(exterior_vertical_rebar_max[i])))
            position = np.array(
                [(exterior_vertical_rebar_max[i][0][0] + exterior_vertical_rebar_max[i][1][0]) / 2,
                 (exterior_vertical_rebar_max[i][0][1] + exterior_vertical_rebar_max[i][1][1]) / 2,
                 (exterior_vertical_rebar_max[i][0][2] + exterior_vertical_rebar_max[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.vertical_rebar_dia_max, length=exterior_rebar_length,
                                         transformation=transformation, position=position))
        for i in range(len(exterior_vertical_rebar_min)):
            rebars_BIM.append(Rebar(radius=int(self.vertical_rebar_dia_min / 2),
                                    poly=IndexedPolyCurve(exterior_vertical_rebar_min[i])))
            position = np.array(
                [(exterior_vertical_rebar_min[i][0][0] + exterior_vertical_rebar_min[i][1][0]) / 2,
                 (exterior_vertical_rebar_min[i][0][1] + exterior_vertical_rebar_min[i][1][1]) / 2,
                 (exterior_vertical_rebar_min[i][0][2] + exterior_vertical_rebar_min[i][1][2]) / 2])
            rebars_objs.append(Rebar_fcl(diameter=self.vertical_rebar_dia_min, length=exterior_rebar_length,
                                         transformation=transformation, position=position))
        return rebars_BVBS, rebars_objs, rebars_BIM

    def get_interior_section(self) -> List[List]:
        """
        内页墙截面。
        :return:
        """
        interior_section = [
            [0.,
             0.],
            [float(self.interior_length),
             0.],
            [float(self.interior_length),
             float(self.interior_thickness)],
            [0.,
             float(self.interior_thickness)],
            [0.,
             0.]]
        return interior_section

    def get_exterior_section(self) -> List[List]:
        """
        外页墙截面
        :return:
        """
        exterior_section = [
            [0.,
             0.],
            [float(self.exterior_length),
             0.],
            [float(self.exterior_length),
             float(self.exterior_thickness)],
            [0.,
             float(self.exterior_thickness)],
            [0.,
             0.]]
        return exterior_section

    def get_interior_height(self) -> float:
        '''
        内页墙高度
        :return:
        '''
        return float(self.interior_height)

    def get_exterior_height(self) -> float:
        '''
        外页墙高度
        :return:
        '''
        return float(self.exterior_height)

    def get_truss_rebars(self, truss_layout_result) -> TrussRebarforBIM:
        truss_rebar_for_bim = TrussRebarforBIM()
        for i in range(len(truss_layout_result)):
            top_rebar_poly = truss_layout_result[i]
            bottom_rebar_left_poly = [
                [float(truss_layout_result[i][0][0] - self.truss_detailed.width / 2
                       + self.truss_detailed.bottom_rebar.diameter / 2),
                 float(self.cover + self.horizontal_rebar_dia_max + self.truss_detailed.bottom_rebar.diameter / 2),
                 truss_layout_result[i][0][2]],
                [float(truss_layout_result[i][0][0] - self.truss_detailed.width / 2
                       + self.truss_detailed.bottom_rebar.diameter / 2),
                 float(self.cover + self.horizontal_rebar_dia_max + self.truss_detailed.bottom_rebar.diameter / 2),
                 truss_layout_result[i][1][2]]]
            bottom_rebar_right_poly = [
                [float(truss_layout_result[i][0][0] + self.truss_detailed.width / 2
                       - self.truss_detailed.bottom_rebar.diameter / 2),
                 float(self.cover + self.horizontal_rebar_dia_max + self.truss_detailed.bottom_rebar.diameter / 2),
                 truss_layout_result[i][0][2]],
                [float(truss_layout_result[i][0][0] + self.truss_detailed.width / 2
                       - self.truss_detailed.bottom_rebar.diameter / 2),
                 float(self.cover + self.horizontal_rebar_dia_max + self.truss_detailed.bottom_rebar.diameter / 2),
                 truss_layout_result[i][1][2]]]

            connection_number = int((truss_layout_result[i][1][2] - truss_layout_result[i][0][2])
                                    / self.truss_detailed.diagonal_rebar.spacing * 2)
            diagonal_rebar_left_poly = []
            diagonal_rebar_right_poly = []
            if connection_number % 2 == 0:
                for j in range(int(connection_number / 2)):
                    diagonal_rebar_left_poly.append(
                        [float(truss_layout_result[i][0][0] - self.truss_detailed.width / 2 +
                               self.truss_detailed.bottom_rebar.diameter + self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.cover + self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] + 2 * j * self.truss_detailed.diagonal_rebar.spacing / 2)])
                    diagonal_rebar_left_poly.append(
                        [float(truss_layout_result[i][0][0] - self.truss_detailed.top_rebar.diameter / 2 -
                               self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.thickness - self.cover - self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] +
                               (2 * j + 1) * self.truss_detailed.diagonal_rebar.spacing / 2)])
                    diagonal_rebar_right_poly.append(
                        [float(truss_layout_result[i][0][0] + self.truss_detailed.width / 2 -
                               self.truss_detailed.bottom_rebar.diameter - self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.cover + self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] + 2 * j * self.truss_detailed.diagonal_rebar.spacing / 2)])

                    diagonal_rebar_right_poly.append(
                        [float(truss_layout_result[i][0][0] + self.truss_detailed.bottom_rebar.diameter -
                               self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.thickness - self.cover - self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] +
                               (2 * j + 1) * self.truss_detailed.diagonal_rebar.spacing / 2)])
                diagonal_rebar_left_poly.append(
                    [float(truss_layout_result[i][0][0] - self.truss_detailed.width / 2 +
                           self.truss_detailed.bottom_rebar.diameter + self.truss_detailed.diagonal_rebar.diameter / 2),
                     float(self.cover + self.horizontal_rebar_dia_max),
                     float(truss_layout_result[i][0][2] +
                           2 * int(connection_number / 2) * self.truss_detailed.diagonal_rebar.spacing / 2)])
                diagonal_rebar_right_poly.append(
                    [float(truss_layout_result[i][0][0] + self.truss_detailed.width / 2 -
                           self.truss_detailed.bottom_rebar.diameter - self.truss_detailed.diagonal_rebar.diameter / 2),
                     float(self.cover + self.horizontal_rebar_dia_max),
                     float(truss_layout_result[i][0][2] +
                           2 * int(connection_number / 2) * self.truss_detailed.diagonal_rebar.spacing / 2)])
            else:
                for j in range(int(connection_number / 2) + 1):
                    diagonal_rebar_left_poly.append(
                        [float(truss_layout_result[i][0][0] - self.truss_detailed.width / 2 +
                               self.truss_detailed.bottom_rebar.diameter + self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.cover + self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] + 2 * j * self.truss_detailed.diagonal_rebar.spacing / 2)])
                    diagonal_rebar_left_poly.append(
                        [float(truss_layout_result[i][0][0] - self.truss_detailed.top_rebar.diameter / 2 -
                               self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.thickness - self.cover - self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] +
                               (2 * j + 1) * self.truss_detailed.diagonal_rebar.spacing / 2)])
                    diagonal_rebar_right_poly.append([float(
                        truss_layout_result[i][0][0] + self.truss_detailed.width / 2 -
                        self.truss_detailed.bottom_rebar.diameter - self.truss_detailed.diagonal_rebar.diameter / 2),
                        float(self.cover + self.horizontal_rebar_dia_max),
                        float(truss_layout_result[i][0][2] +
                              2 * j * self.truss_detailed.diagonal_rebar.spacing / 2)])

                    diagonal_rebar_right_poly.append(
                        [float(truss_layout_result[i][0][0] + self.truss_detailed.top_rebar.diameter / 2 +
                               self.truss_detailed.diagonal_rebar.diameter / 2),
                         float(self.thickness - self.cover - self.horizontal_rebar_dia_max),
                         float(truss_layout_result[i][0][2] +
                               (2 * j + 1) * self.truss_detailed.diagonal_rebar.spacing / 2)])
            truss_rebar_for_ifc = TrussRebar(
                top_rebar=Rebar(radius=int(self.truss_detailed.top_rebar.diameter / 2),
                                poly=IndexedPolyCurve(top_rebar_poly)),
                bottom_rebar_left=Rebar(radius=int(self.truss_detailed.bottom_rebar.diameter / 2),
                                        poly=IndexedPolyCurve(bottom_rebar_left_poly)),
                bottom_rebar_right=Rebar(radius=int(self.truss_detailed.bottom_rebar.diameter / 2),
                                         poly=IndexedPolyCurve(bottom_rebar_right_poly)),
                diagonal_rebar_left=Rebar(radius=int(self.truss_detailed.diagonal_rebar.diameter / 2),
                                          poly=IndexedPolyCurve(diagonal_rebar_left_poly)),
                diagonal_rebar_right=Rebar(radius=int(self.truss_detailed.diagonal_rebar.diameter / 2),
                                           poly=IndexedPolyCurve(diagonal_rebar_right_poly)))

            truss_rebar_for_bim.truss_rebars.append(truss_rebar_for_ifc)
        return truss_rebar_for_bim

    def get_top_hole_position(self) -> List[List[float]]:
        """
        计算销键或连接孔洞的位置,以孔洞的下边缘的圆心为标志点
        :return:
        """
        # 顶端孔洞边距
        top_right_long_a1 = self.detailed_design.construction_detailed.top_hole_position.a1  # 顶端右侧纵向边距
        top_right_horizon_b1 = self.detailed_design.construction_detailed.top_hole_position.b1  # 顶端右侧横向边距
        top_left_long_a2 = self.detailed_design.construction_detailed.top_hole_position.a2  # 顶端左侧纵向边距
        top_left_horizon_b2 = self.detailed_design.construction_detailed.top_hole_position.b2  # 顶端左侧横向边距

        top_hole_position = [[float(top_left_horizon_b2),
                              float(self.l_total - top_left_long_a2),
                              float(self.h_total - self.top_thickness)],
                             [float(self.width - top_right_horizon_b1),
                              float(self.l_total - top_right_long_a1),
                              float(self.h_total - self.top_thickness)]]  # 由底端到顶端，由左到向右
        return top_hole_position

    def get_bottom_hole_position(self) -> List[List[float]]:
        """
        计算销键或连接孔洞的位置,以孔洞的下边缘的圆心为标志点
        :return:
        """
        bottom_right_long_a3 = self.detailed_design.construction_detailed.bottom_hole_position.a3  # 底端右侧纵向边距
        bottom_right_horizon_b3 = self.detailed_design.construction_detailed.bottom_hole_position.b3  # 底端右侧横向边距
        bottom_left_long_a4 = self.detailed_design.construction_detailed.bottom_hole_position.a4  # 底端左侧纵向边距
        bottom_left_horizon_b4 = self.detailed_design.construction_detailed.bottom_hole_position.b4  # 底端左侧横向边距

        bottom_hole_position = [[float(bottom_left_horizon_b4),
                                 float(bottom_left_long_a4),
                                 0.],
                                [float(self.width - bottom_right_horizon_b3),
                                 float(bottom_right_long_a3),
                                 0.]]

        return bottom_hole_position

    def get_top_hole_section(self) -> List[List[float]]:
        top_hole_type = self.detailed_design.construction_detailed.top_hole_type
        top_hole = self.detailed_design.construction_detailed.top_hole
        if top_hole_type.value == 0:  # 固定支座
            self.top_hole_section = [[0., 0.],
                                     [top_hole.fix_hinge_d2 / 2., 0.],
                                     [top_hole.fix_hinge_c2 / 2., float(self.top_thickness)],
                                     [0., float(self.top_thickness)],
                                     [0., 0.]]
        else:  # 滑动支座
            self.top_hole_section = [[0., 0.],
                                     [top_hole.sliding_hinge_f1 / 2., 0.],
                                     [top_hole.sliding_hinge_d1 / 2.,
                                      float(self.top_thickness - top_hole.sliding_hinge_h1)],
                                     [top_hole.sliding_hinge_e1 / 2.,
                                      float(self.top_thickness - top_hole.sliding_hinge_h1)],
                                     [top_hole.sliding_hinge_c1 / 2., float(self.top_thickness)],
                                     [0., float(self.top_thickness)],
                                     [0., 0.]]
        return self.top_hole_section

    def get_bottom_hole_section(self) -> List[List[float]]:
        bottom_hole_type = self.detailed_design.construction_detailed.bottom_hole_type
        bottom_hole = self.detailed_design.construction_detailed.bottom_hole
        if bottom_hole_type.value == 0:  # 固定支座
            self.bottom_hole_section = [[0., 0.],
                                        [bottom_hole.fix_hinge_d2 / 2., 0.],
                                        [bottom_hole.fix_hinge_c2 / 2., float(self.top_thickness)],
                                        [0., float(self.bottom_thickness)],
                                        [0., 0.]]
        else:  # 滑动支座
            self.bottom_hole_section = [[0., 0.],
                                        [bottom_hole.sliding_hinge_f1 / 2., 0.],
                                        [bottom_hole.sliding_hinge_d1 / 2.,
                                         float(self.bottom_thickness - bottom_hole.sliding_hinge_h1)],
                                        [bottom_hole.sliding_hinge_e1 / 2.,
                                         float(self.bottom_thickness - bottom_hole.sliding_hinge_h1)],
                                        [bottom_hole.sliding_hinge_c1 / 2., float(self.bottom_thickness)],
                                        [0., float(self.bottom_thickness)],
                                        [0., 0.]]
        return self.bottom_hole_section

    def get_step_slot_position(self) -> List[List[float]]:
        """
        计算防滑槽的位置信息
        :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
        """
        step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
        step_slot_c3 = self.detailed_design.construction_detailed.step_slot_position.c3
        positions = []
        init_position = [float(step_slot_c1),
                         float(self.bottom_top_length + step_slot_c3),
                         float(self.bottom_thickness)]  # 初始位置
        for num in range(self.steps_number):
            position = [init_position[0],
                        init_position[1] + float(num * self.steps_b),
                        init_position[2] + float((num + 1) * self.steps_h)]
            positions.append(position)

        return positions

    def get_slot_position(self) -> List[List[float]]:
        """
        计算防滑槽的位置信息
        :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
        """
        step_slot_e = self.detailed_design.construction_detailed.step_slot.e
        step_slot_a = self.detailed_design.construction_detailed.step_slot.a
        step_slot_b = self.detailed_design.construction_detailed.step_slot.b
        step_slot_c = self.detailed_design.construction_detailed.step_slot.c

        positions = [[float(step_slot_e),
                      0.,
                      0.],
                     [float(step_slot_e),
                      float(step_slot_a + step_slot_b + step_slot_c),
                      0.]]
        return positions

    def get_slot_length(self):
        """
        计算防滑槽的位置信息 用于拉伸的主体长度
        :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]]
        """
        step_slot_e = self.detailed_design.construction_detailed.step_slot.e
        step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
        step_slot_c2 = self.detailed_design.construction_detailed.step_slot_position.c2
        length = float(self.width - step_slot_c1 - step_slot_c2 - 2 * step_slot_e)  # 防滑槽的长度

        return length

    def get_slot_section(self) -> List[List[float]]:
        """
        计算防滑槽的配置信息 用于拉伸的主要参数
        :return: Dict
        """
        step_slot_a = self.detailed_design.construction_detailed.step_slot.a
        step_slot_b = self.detailed_design.construction_detailed.step_slot.b
        step_slot_d = self.detailed_design.construction_detailed.step_slot.d
        sections = [[0., 0.],
                    [float(step_slot_a + step_slot_b), 0.],
                    [float(step_slot_b), float(-step_slot_d)],
                    [0., 0.]]
        return sections

    def get_slope_position(self):
        """
        计算斜坡的位置信息
        :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
        """
        step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
        step_slot_c2 = self.detailed_design.construction_detailed.step_slot_position.c2
        step_slot_a = self.detailed_design.construction_detailed.step_slot.a
        step_slot_b = self.detailed_design.construction_detailed.step_slot.b
        step_slot_c = self.detailed_design.construction_detailed.step_slot.c
        step_slot_e = self.detailed_design.construction_detailed.step_slot.e
        length = float(self.width - step_slot_c2 - step_slot_c1 - step_slot_e)  # 防滑槽的长度
        positions = [[[0., 0., 0.],
                      [float(length), 0., 0.]],
                     [[0., float(step_slot_a + step_slot_b + step_slot_c), 0.],
                      [float(length), float(step_slot_a + step_slot_b + step_slot_c), 0.]],
                     ]
        return positions

    def get_slope_section(self):
        """
        计算防滑槽的配置信息  小坡面
        :return: Dict
        """
        step_slot_a = self.detailed_design.construction_detailed.step_slot.a
        step_slot_b = self.detailed_design.construction_detailed.step_slot.b
        step_slot_e = self.detailed_design.construction_detailed.step_slot.e
        sections_1 = [[[0., 0.],
                       [0., float(step_slot_e)],
                       [float(step_slot_a + step_slot_b), float(step_slot_e)],
                       [float(step_slot_a + step_slot_b), 0.],
                       [0., 0.]],
                      [[0., 0.],
                       [0., float(step_slot_e)],
                       [float(step_slot_a + step_slot_b), float(step_slot_e)],
                       [float(step_slot_a + step_slot_b), 0.],
                       [0., 0.]]]
        sections_2 = [[float(step_slot_b), float(step_slot_e)],
                      [float(step_slot_b), 0.]]  # 截面2的位置

        return sections_1, sections_2

    def get_slope_length(self):
        """
        计算防滑槽的位置信息 用于拉伸的主体长度
        :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]]
        """
        step_slot_d = self.detailed_design.construction_detailed.step_slot.d
        length = float(step_slot_d)  # 防滑槽的长度

        return length

    def get_water_drip_curve(self):
        """
        滴水线槽坐标位置
        :return:
        """
        curves = []
        a1 = self.detailed_design.construction_detailed.water_drip_position.a1
        a2 = self.detailed_design.construction_detailed.water_drip_position.a2
        a3 = self.detailed_design.construction_detailed.water_drip_position.a3
        if self.water_drop_layout.value == 0:  # 只有上部
            curves.append([[float(self.width + self.bottom_b), float(a2), 0.],
                           [float(self.width - a3), float(a2), 0.],
                           [float(self.width - a3), float(self.bottom_bottom_length), 0.],
                           [float(self.width - a3), float(self.l_total - self.top_bottom_length),
                            float(self.h_total - self.top_thickness)],
                           [float(self.width - a3), float(self.l_total - a1),
                            float(self.h_total - self.top_thickness)],
                           [float(self.width + self.top_b), float(self.l_total - a1),
                            float(self.h_total - self.top_thickness)],
                           ])
        elif self.water_drop_layout.value == 1:  # 只有下部
            curves.append([[0., float(a2), 0.],
                           [float(a3), float(a2), 0.],
                           [float(a3), float(self.bottom_bottom_length), 0.],
                           [float(a3), float(self.l_total - self.top_bottom_length),
                            float(self.h_total - self.top_thickness)],
                           [float(a3), float(self.l_total - a1), float(self.h_total - self.top_thickness)],
                           [0., float(self.l_total - a1), float(self.h_total - self.top_thickness)],
                           ])
        else:
            curves.append([[float(self.width + self.bottom_b), float(a2), 0.],
                           [float(self.width - a3), float(a2), 0.],
                           [float(self.width - a3), float(self.bottom_bottom_length), 0.],
                           [float(self.width - a3), float(self.l_total - self.top_bottom_length),
                            float(self.h_total - self.top_thickness)],
                           [float(self.width - a3), float(self.l_total - a1),
                            float(self.h_total - self.top_thickness)],
                           [float(self.width + self.top_b), float(self.l_total - a1),
                            float(self.h_total - self.top_thickness)],
                           ])
            curves.append([[0., float(a2), 0.],
                           [float(a3), float(a2), 0.],
                           [float(a3), float(self.bottom_bottom_length), 0.],
                           [float(a3), float(self.l_total - self.top_bottom_length),
                            float(self.h_total - self.top_thickness)],
                           [float(a3), float(self.l_total - a1), float(self.h_total - self.top_thickness)],
                           [0., float(self.l_total - a1), float(self.h_total - self.top_thickness)],
                           ])
        return curves

    def get_water_drop_section(self):
        """
        滴水线槽配置信息
        :return:
        """
        section_shape = self.detailed_design.construction_detailed.water_drip_shape
        sections = []
        if section_shape.value == 0:  # TRAPEZOID = 0 SEMICIRCLE = 1
            water_drop_a = self.detailed_design.construction_detailed.water_drip.a
            water_drop_b = self.detailed_design.construction_detailed.water_drip.b
            water_drop_c = self.detailed_design.construction_detailed.water_drip.c
            if self.water_drop_layout.value == 0:  # 只有上部

                sections.append([[0., 0.],
                                 [-float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
                                 [-float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
                                 [0., float(water_drop_b)]])
                return sections, section_shape
            elif self.water_drop_layout.value == 1:  # 只有下部
                sections.append([[0., 0.],
                                 [float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
                                 [float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
                                 [0., float(water_drop_b)]])
                return sections, section_shape
            else:
                sections.append([[0., 0.],
                                 [-float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
                                 [-float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
                                 [0., float(water_drop_b)]])

                sections.append([[0., 0.],
                                 [float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
                                 [float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
                                 [0., float(water_drop_b)]])
                return sections, section_shape
        else:
            water_drop_a = self.detailed_design.construction_detailed.water_drip.a
            water_drop_b = self.detailed_design.construction_detailed.water_drip.b
            if self.water_drop_layout.value == 0:  # 只有上部
                sections.append([[0., 0.],
                                 [-float(water_drop_b), float(water_drop_a / 2)],
                                 [0., float(water_drop_a)]])
                return sections, section_shape
            elif self.water_drop_layout.value == 1:  # 只有下部
                sections.append([[0., 0.],
                                 [float(water_drop_b), float(water_drop_a / 2)],
                                 [0., float(water_drop_a)]])
                return sections, section_shape
            else:
                sections.append([[0., 0.],
                                 [-float(water_drop_b), float(water_drop_a / 2)],
                                 [0., float(water_drop_a)]])
                sections.append([[0., 0.],
                                 [float(water_drop_b), float(water_drop_a / 2)],
                                 [0., float(water_drop_a)]])
                return sections, section_shape

    def get_rail_embedded_parts_position(self) -> List[List[float]]:
        """
        计算栏杆预埋件的坐标点：栏杆上表面,栏杆布置侧为 上楼梯方向的左右侧
        :return:
        """
        rail_number = self.detailed_design.inserts_detailed.rail_number  # 栏杆所在的阶数

        x_a = self.detailed_design.inserts_detailed.rail_position.a  # 横向边距
        y_b = self.detailed_design.inserts_detailed.rail_position.b  # 纵向距离台阶
        # 栏杆布置左右侧
        position_x = []
        if self.rail_layout.value == 0:  # ONLY_RIGHT = 0 ONLY_LEFT = 1   BOTH = 2
            position_x.append(float(self.width - x_a))
        elif self.rail_layout.value == 1:
            position_x.append(float(x_a))
        else:
            position_x.append(float(x_a))
            position_x.append(float(self.width - x_a))
        position_y = []
        for i in rail_number:
            position_y.append(float(self.bottom_top_length + i * self.steps_b - y_b))
        position_z = []
        for i in rail_number:
            position_z.append(float(self.bottom_thickness + i * self.steps_h))
        positions = []
        for i in range(len(position_x)):
            for j in range(len(rail_number)):
                positions.append([position_x[i], position_y[j], position_z[j]])
        return positions

    def get_lifting_embedded_parts_position(self) -> List[List[float]]:
        """
        计算吊装预埋件的坐标点：预埋件上部中心点
        :return:
        """
        lifting_position_a = self.detailed_design.inserts_detailed.lifting_position.a
        lifting_position_b = self.detailed_design.inserts_detailed.lifting_position.b
        lifting_position_c = float(self.detailed_design.inserts_detailed.lifting_position.c)  # 吊装预埋件左侧横向边距
        lifting_position_d = float(self.detailed_design.inserts_detailed.lifting_position.d)  # 吊装预埋件右侧横向边距

        edge_a = self.bottom_top_length + (lifting_position_a - 0.5) * self.steps_b  # 吊装预埋件顶端纵向边距
        edge_b = self.bottom_top_length + (lifting_position_b - 0.5) * self.steps_b  # 吊装预埋件底端纵向边距
        top_h = self.bottom_thickness + lifting_position_a * self.steps_h  # 下部吊装件坐标
        bottom_h = self.bottom_thickness + lifting_position_b * self.steps_h  # 上部吊装件坐标

        position_x = [lifting_position_c, float(self.width - lifting_position_d)]
        position_y = [float(edge_b), float(edge_a)]
        position_z = [float(bottom_h), float(top_h)]
        positions = [[position_x[0], position_y[0], position_z[0]],
                     [position_x[0], position_y[1], position_z[1]],
                     [position_x[1], position_y[0], position_z[0]],
                     [position_x[1], position_y[1], position_z[1]]]

        return positions

    def get_demoulding_embedded_parts_position(self):
        """
        计算脱模预埋件的坐标点
        :return:
        """
        # 获取信息
        # 侧面脱模预埋件的定位
        # 顶端侧面脱模预埋件y坐标
        demolding_a = float(self.detailed_design.inserts_detailed.demolding_position.a)  # 脱模埋件顶端纵向边距
        demolding_b = float(self.detailed_design.inserts_detailed.demolding_position.b)  # 脱模埋件底端纵向边距
        demolding_c = float(self.detailed_design.inserts_detailed.demolding_position.c)  # 脱模埋件左侧横向边距
        demolding_d = float(self.detailed_design.inserts_detailed.demolding_position.d)  # 脱模埋件右侧横向边距
        demolding_t = float(self.detailed_design.inserts_detailed.demolding_position.t)  # 脱模埋件厚度方向边距
        demolding_t_y = self.l_total - demolding_a  # 顶端侧面脱模预埋件y坐标
        # 顶端侧面脱模预埋件z坐标
        demolding_t_z = (self.l_total - self.bottom_bottom_length - demolding_a) * self.tan + demolding_t / self.cos
        # 底端侧面脱模预埋件y坐标
        demolding_b_y = demolding_b
        # 底端侧面脱模预埋件z坐标
        demolding_b_z = (demolding_b - self.bottom_bottom_length) * self.tan + demolding_t / self.cos

        positions = [[float(self.width), demolding_t_y, demolding_t_z],
                     [float(self.width), demolding_b_y, demolding_b_z]]
        z_direction = [-1., 0., 0.]
        x_direction = [0., -self.sin, self.cos]

        return positions, z_direction, x_direction

# class StairGeometryData:
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult):
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#
#         self.steps_number = self.structure_design.geometric.steps_number
#         self.steps_h = self.structure_design_result.steps_h
#         self.steps_b = self.structure_design_result.steps_b
#         self.width = self.detailed_design.geometric_detailed.width
#
#         self.top_b = self.detailed_design.geometric_detailed.top_b  # 上部挑耳
#         self.bottom_b = self.detailed_design.geometric_detailed.bottom_b  # 下部挑耳
#         self.bottom_thickness = self.detailed_design.geometric_detailed.bottom_thickness
#         self.top_thickness = self.detailed_design.geometric_detailed.top_thickness
#         self.bottom_top_length = self.detailed_design.geometric_detailed.bottom_top_length
#         self.top_bottom_length = self.detailed_design_result.top_bottom_length
#         self.bottom_bottom_length = self.detailed_design_result.bottom_bottom_length
#         self.ln = self.structure_design.geometric.clear_span
#         self.height = self.structure_design.geometric.height
#         self.l_total = self.detailed_design_result.l_total  # 纵向总长
#         self.h_total = self.detailed_design_result.h_total  # 楼梯总高度
#
#     def get_step_points(self) -> List[List]:
#         """
#         计算楼梯主体几何角点
#         要求：1.顶端和底端挑耳除外；2.以楼梯立面图右下角为初始点(0,0,0)，逆时针方向前进。
#         :return:
#         """
#         # 添加底端板三角点
#         geometry_points = [[0., 0.],
#                            [0., float(self.bottom_thickness)],
#                            [float(self.bottom_top_length), float(self.bottom_thickness)]]
#         for i in range(self.steps_number - 1):
#             geometry_points.append(
#                 [self.bottom_top_length + i * self.steps_b, self.bottom_thickness + (i + 1) * self.steps_h])
#             geometry_points.append(
#                 [self.bottom_top_length + (i + 1) * self.steps_b, self.bottom_thickness + (i + 1) * self.steps_h])
#
#         geometry_points = geometry_points + [
#             [float(self.bottom_top_length + self.ln), float(self.h_total)],
#             [float(self.l_total), float(self.h_total)],
#             [float(self.l_total), float(self.height)],
#             [float(self.l_total - self.top_bottom_length), float(self.height)],
#             [float(self.bottom_bottom_length), 0.],
#             [0., 0.]]
#         return geometry_points
#
#     def get_top_ear(self) -> List[List]:
#         """
#         顶端挑耳，逆时针方向。
#         :return:
#         """
#         top_ear_points = [
#             [float(self.bottom_top_length + self.ln),
#              float(self.height)],
#             [float(self.bottom_top_length + self.ln),
#              float(self.h_total)],
#             [float(self.l_total),
#              float(self.h_total)],
#             [float(self.l_total),
#              float(self.height)],
#             [float(self.bottom_top_length + self.ln),
#              float(self.height)], ]
#         return top_ear_points
#
#     def get_bottom_ear(self) -> List[List]:
#         """
#         顶端挑耳，逆时针方向。
#         :return:
#         """
#         bottom_ear_points = [
#             [0., 0.],
#             [0., float(self.bottom_thickness)],
#             [float(self.bottom_bottom_length), float(self.bottom_thickness)],
#             [float(self.bottom_bottom_length), 0.],
#             [0., 0.]]
#         return bottom_ear_points
#
#     def get_body_width(self) -> float:
#         return float(self.width)
#
#     def get_top_ear_width(self) -> float:
#         return float(self.detailed_design.geometric_detailed.top_b)
#
#     def get_bottom_ear_width(self) -> float:
#         return float(self.detailed_design.geometric_detailed.bottom_b)
#
#
# class StairHoleData(object):
#     """
#     预留孔洞定位信息
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#         self.width = self.detailed_design.geometric_detailed.width
#         self.bottom_thickness = self.detailed_design.geometric_detailed.bottom_thickness
#         self.top_thickness = self.detailed_design.geometric_detailed.top_thickness
#
#         # 顶端孔洞边距
#         self.top_right_long_a1 = self.detailed_design.construction_detailed.top_hole_position.a1  # 顶端右侧纵向边距
#         self.top_right_horizon_b1 = self.detailed_design.construction_detailed.top_hole_position.b1  # 顶端右侧横向边距
#         self.top_left_long_a2 = self.detailed_design.construction_detailed.top_hole_position.a2  # 顶端左侧纵向边距
#         self.top_left_horizon_b2 = self.detailed_design.construction_detailed.top_hole_position.b2  # 顶端左侧横向边距
#         # 底端孔洞边距
#         self.bottom_right_long_a3 = self.detailed_design.construction_detailed.bottom_hole_position.a3  # 底端右侧纵向边距
#         self.bottom_right_horizon_b3 = self.detailed_design.construction_detailed.bottom_hole_position.b3  # 底端右侧横向边距
#         self.bottom_left_long_a4 = self.detailed_design.construction_detailed.bottom_hole_position.a4  # 底端左侧纵向边距
#         self.bottom_left_horizon_b4 = self.detailed_design.construction_detailed.bottom_hole_position.b4  # 底端左侧横向边距
#         self.l_total = self.detailed_design_result.l_total  # 纵向总长
#         self.h_total = self.detailed_design_result.h_total  # 楼梯总高度
#
#     def get_top_hole_position(self) -> List[List[float]]:
#         """
#         计算销键或连接孔洞的位置,以孔洞的下边缘的圆心为标志点
#         :return:
#         """
#         top_hole_position = [[float(self.top_left_horizon_b2),
#                               float(self.l_total - self.top_left_long_a2),
#                               float(self.h_total - self.top_thickness)],
#                              [float(self.width - self.top_right_horizon_b1),
#                               float(self.l_total - self.top_right_long_a1),
#                               float(self.h_total - self.top_thickness)]]  # 由底端到顶端，由左到向右
#         return top_hole_position
#
#     def get_bottom_hole_position(self) -> List[List[float]]:
#         """
#         计算销键或连接孔洞的位置,以孔洞的下边缘的圆心为标志点
#         :return:
#         """
#         bottom_hole_position = [[float(self.bottom_left_horizon_b4),
#                                  float(self.bottom_left_long_a4),
#                                  0.],
#                                 [float(self.width - self.bottom_right_horizon_b3),
#                                  float(self.bottom_right_long_a3),
#                                  0.]]
#
#         return bottom_hole_position
#
#     def get_top_hole_section(self) -> List[List[float]]:
#         top_hole_type = self.detailed_design.construction_detailed.top_hole_type
#         top_hole = self.detailed_design.construction_detailed.top_hole
#         if top_hole_type.value == 0:  # 固定支座
#             self.top_hole_section = [[0., 0.],
#                                      [top_hole.fix_hinge_d2 / 2., 0.],
#                                      [top_hole.fix_hinge_c2 / 2., float(self.top_thickness)],
#                                      [0., float(self.top_thickness)],
#                                      [0., 0.]]
#         else:  # 滑动支座
#             self.top_hole_section = [[0., 0.],
#                                      [top_hole.sliding_hinge_f1 / 2., 0.],
#                                      [top_hole.sliding_hinge_d1 / 2.,
#                                       float(self.top_thickness - top_hole.sliding_hinge_h1)],
#                                      [top_hole.sliding_hinge_e1 / 2.,
#                                       float(self.top_thickness - top_hole.sliding_hinge_h1)],
#                                      [top_hole.sliding_hinge_c1 / 2., float(self.top_thickness)],
#                                      [0., float(self.top_thickness)],
#                                      [0., 0.]]
#         return self.top_hole_section
#
#     def get_bottom_hole_section(self) -> List[List[float]]:
#         bottom_hole_type = self.detailed_design.construction_detailed.bottom_hole_type
#         bottom_hole = self.detailed_design.construction_detailed.bottom_hole
#         if bottom_hole_type.value == 0:  # 固定支座
#             self.bottom_hole_section = [[0., 0.],
#                                         [bottom_hole.fix_hinge_d2 / 2., 0.],
#                                         [bottom_hole.fix_hinge_c2 / 2., float(self.top_thickness)],
#                                         [0., float(self.bottom_thickness)],
#                                         [0., 0.]]
#         else:  # 滑动支座
#             self.bottom_hole_section = [[0., 0.],
#                                         [bottom_hole.sliding_hinge_f1 / 2., 0.],
#                                         [bottom_hole.sliding_hinge_d1 / 2.,
#                                          float(self.bottom_thickness - bottom_hole.sliding_hinge_h1)],
#                                         [bottom_hole.sliding_hinge_e1 / 2.,
#                                          float(self.bottom_thickness - bottom_hole.sliding_hinge_h1)],
#                                         [bottom_hole.sliding_hinge_c1 / 2., float(self.bottom_thickness)],
#                                         [0., float(self.bottom_thickness)],
#                                         [0., 0.]]
#         return self.bottom_hole_section
#
#
# class StepSlotData(object):
#     """
#     计算防滑槽的位置信息
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#
#         self.steps_number = self.structure_design.geometric.steps_number
#         self.steps_h = self.structure_design_result.steps_h
#         self.steps_b = self.structure_design_result.steps_b
#         self.width = self.detailed_design.geometric_detailed.width
#
#         self.bottom_top_length = self.detailed_design.geometric_detailed.bottom_top_length
#         self.bottom_thickness = self.detailed_design.geometric_detailed.bottom_thickness
#         self.step_slot_mode = self.detailed_design.construction_detailed.step_slot_design_mode
#
#     def get_step_slot_position(self) -> List[List[float]]:
#         """
#         计算防滑槽的位置信息
#         :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
#         """
#         step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
#         step_slot_c3 = self.detailed_design.construction_detailed.step_slot_position.c3
#         positions = []
#         init_position = [float(step_slot_c1),
#                          float(self.bottom_top_length + step_slot_c3),
#                          float(self.bottom_thickness)]  # 初始位置
#         for num in range(self.steps_number):
#             position = [init_position[0],
#                         init_position[1] + float(num * self.steps_b),
#                         init_position[2] + float((num + 1) * self.steps_h)]
#             positions.append(position)
#
#         return positions
#
#     def get_slot_position(self) -> List[List[float]]:
#         """
#         计算防滑槽的位置信息
#         :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
#         """
#         step_slot_e = self.detailed_design.construction_detailed.step_slot.e
#         step_slot_a = self.detailed_design.construction_detailed.step_slot.a
#         step_slot_b = self.detailed_design.construction_detailed.step_slot.b
#         step_slot_c = self.detailed_design.construction_detailed.step_slot.c
#
#         positions = [[float(step_slot_e),
#                       0.,
#                       0.],
#                      [float(step_slot_e),
#                       float(step_slot_a + step_slot_b + step_slot_c),
#                       0.]]
#         return positions
#
#     def get_slot_length(self):
#         """
#         计算防滑槽的位置信息 用于拉伸的主体长度
#         :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]]
#         """
#         step_slot_e = self.detailed_design.construction_detailed.step_slot.e
#         step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
#         step_slot_c2 = self.detailed_design.construction_detailed.step_slot_position.c2
#         length = float(self.width - step_slot_c1 - step_slot_c2 - 2 * step_slot_e)  # 防滑槽的长度
#
#         return length
#
#     def get_slot_section(self) -> List[List[float]]:
#         """
#         计算防滑槽的配置信息 用于拉伸的主要参数
#         :return: Dict
#         """
#         step_slot_a = self.detailed_design.construction_detailed.step_slot.a
#         step_slot_b = self.detailed_design.construction_detailed.step_slot.b
#         step_slot_d = self.detailed_design.construction_detailed.step_slot.d
#         sections = [[0., 0.],
#                     [float(step_slot_a + step_slot_b), 0.],
#                     [float(step_slot_b), float(-step_slot_d)],
#                     [0., 0.]]
#         return sections
#
#     def get_slope_position(self):
#         """
#         计算斜坡的位置信息
#         :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]] 最右侧
#         """
#         step_slot_c1 = self.detailed_design.construction_detailed.step_slot_position.c1
#         step_slot_c2 = self.detailed_design.construction_detailed.step_slot_position.c2
#         step_slot_a = self.detailed_design.construction_detailed.step_slot.a
#         step_slot_b = self.detailed_design.construction_detailed.step_slot.b
#         step_slot_c = self.detailed_design.construction_detailed.step_slot.c
#         step_slot_e = self.detailed_design.construction_detailed.step_slot.e
#         length = float(self.width - step_slot_c2 - step_slot_c1 - step_slot_e)  # 防滑槽的长度
#         positions = [[[0., 0., 0.],
#                       [float(length), 0., 0.]],
#                      [[0., float(step_slot_a + step_slot_b + step_slot_c), 0.],
#                       [float(length), float(step_slot_a + step_slot_b + step_slot_c), 0.]],
#                      ]
#         return positions
#
#     def get_slope_section(self):
#         """
#         计算防滑槽的配置信息  小坡面
#         :return: Dict
#         """
#         step_slot_a = self.detailed_design.construction_detailed.step_slot.a
#         step_slot_b = self.detailed_design.construction_detailed.step_slot.b
#         step_slot_e = self.detailed_design.construction_detailed.step_slot.e
#         sections_1 = [[[0., 0.],
#                        [0., float(step_slot_e)],
#                        [float(step_slot_a + step_slot_b), float(step_slot_e)],
#                        [float(step_slot_a + step_slot_b), 0.],
#                        [0., 0.]],
#                       [[0., 0.],
#                        [0., float(step_slot_e)],
#                        [float(step_slot_a + step_slot_b), float(step_slot_e)],
#                        [float(step_slot_a + step_slot_b), 0.],
#                        [0., 0.]]]
#         sections_2 = [[float(step_slot_b), float(step_slot_e)],
#                       [float(step_slot_b), 0.]]  # 截面2的位置
#
#         return sections_1, sections_2
#
#     def get_slope_length(self):
#         """
#         计算防滑槽的位置信息 用于拉伸的主体长度
#         :return:[[防滑槽组1],[防滑槽组2],[防滑槽组3],[防滑槽组4]]
#         """
#         step_slot_d = self.detailed_design.construction_detailed.step_slot.d
#         length = float(step_slot_d)  # 防滑槽的长度
#
#         return length
#
#
# class WaterDripData(object):
#     """
#     滴水线槽的位置信息
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#
#         self.water_drop_mode = self.detailed_design.construction_detailed.water_drip_design_mode
#         self.water_drop_layout = self.detailed_design.construction_detailed.water_drip_layout  # 上 0  下 1  都有 2
#
#         self.top_b = self.detailed_design.geometric_detailed.top_b  # 上部挑耳
#         self.bottom_b = self.detailed_design.geometric_detailed.bottom_b  # 下部挑耳
#         self.bottom_bottom_length = self.detailed_design_result.bottom_bottom_length
#         self.top_bottom_length = self.detailed_design_result.top_bottom_length
#         self.width = self.structure_design.geometric.width
#         self.l_total = self.detailed_design_result.l_total  # 纵向总长
#         self.h_total = self.detailed_design_result.h_total  # 楼梯总高度
#         self.top_thickness = self.detailed_design.geometric_detailed.top_thickness
#
#     def get_water_drip_curve(self):
#         """
#         滴水线槽坐标位置
#         :return:
#         """
#         curves = []
#         a1 = self.detailed_design.construction_detailed.water_drip_position.a1
#         a2 = self.detailed_design.construction_detailed.water_drip_position.a2
#         a3 = self.detailed_design.construction_detailed.water_drip_position.a3
#         if self.water_drop_layout.value == 0:  # 只有上部
#             curves.append([[float(self.width + self.bottom_b), float(a2), 0.],
#                            [float(self.width - a3), float(a2), 0.],
#                            [float(self.width - a3), float(self.bottom_bottom_length), 0.],
#                            [float(self.width - a3), float(self.l_total - self.top_bottom_length),
#                             float(self.h_total - self.top_thickness)],
#                            [float(self.width - a3), float(self.l_total - a1),
#                             float(self.h_total - self.top_thickness)],
#                            [float(self.width + self.top_b), float(self.l_total - a1),
#                             float(self.h_total - self.top_thickness)],
#                            ])
#         elif self.water_drop_layout.value == 1:  # 只有下部
#             curves.append([[0., float(a2), 0.],
#                            [float(a3), float(a2), 0.],
#                            [float(a3), float(self.bottom_bottom_length), 0.],
#                            [float(a3), float(self.l_total - self.top_bottom_length),
#                             float(self.h_total - self.top_thickness)],
#                            [float(a3), float(self.l_total - a1), float(self.h_total - self.top_thickness)],
#                            [0., float(self.l_total - a1), float(self.h_total - self.top_thickness)],
#                            ])
#         else:
#             curves.append([[float(self.width + self.bottom_b), float(a2), 0.],
#                            [float(self.width - a3), float(a2), 0.],
#                            [float(self.width - a3), float(self.bottom_bottom_length), 0.],
#                            [float(self.width - a3), float(self.l_total - self.top_bottom_length),
#                             float(self.h_total - self.top_thickness)],
#                            [float(self.width - a3), float(self.l_total - a1),
#                             float(self.h_total - self.top_thickness)],
#                            [float(self.width + self.top_b), float(self.l_total - a1),
#                             float(self.h_total - self.top_thickness)],
#                            ])
#             curves.append([[0., float(a2), 0.],
#                            [float(a3), float(a2), 0.],
#                            [float(a3), float(self.bottom_bottom_length), 0.],
#                            [float(a3), float(self.l_total - self.top_bottom_length),
#                             float(self.h_total - self.top_thickness)],
#                            [float(a3), float(self.l_total - a1), float(self.h_total - self.top_thickness)],
#                            [0., float(self.l_total - a1), float(self.h_total - self.top_thickness)],
#                            ])
#         return curves
#
#     def get_water_drop_section(self):
#         """
#         滴水线槽配置信息
#         :return:
#         """
#         section_shape = self.detailed_design.construction_detailed.water_drip_shape
#         sections = []
#         if section_shape.value == 0:  # TRAPEZOID = 0 SEMICIRCLE = 1
#             water_drop_a = self.detailed_design.construction_detailed.water_drip.a
#             water_drop_b = self.detailed_design.construction_detailed.water_drip.b
#             water_drop_c = self.detailed_design.construction_detailed.water_drip.c
#             if self.water_drop_layout.value == 0:  # 只有上部
#
#                 sections.append([[0., 0.],
#                                  [-float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
#                                  [-float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
#                                  [0., float(water_drop_b)]])
#                 return sections, section_shape
#             elif self.water_drop_layout.value == 1:  # 只有下部
#                 sections.append([[0., 0.],
#                                  [float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
#                                  [float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
#                                  [0., float(water_drop_b)]])
#                 return sections, section_shape
#             else:
#                 sections.append([[0., 0.],
#                                  [-float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
#                                  [-float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
#                                  [0., float(water_drop_b)]])
#
#                 sections.append([[0., 0.],
#                                  [float(water_drop_c), float((water_drop_b - water_drop_a) / 2)],
#                                  [float(water_drop_c), float((water_drop_b + water_drop_a) / 2)],
#                                  [0., float(water_drop_b)]])
#                 return sections, section_shape
#         else:
#             water_drop_a = self.detailed_design.construction_detailed.water_drip.a
#             water_drop_b = self.detailed_design.construction_detailed.water_drip.b
#             if self.water_drop_layout.value == 0:  # 只有上部
#                 sections.append([[0., 0.],
#                                  [-float(water_drop_b), float(water_drop_a / 2)],
#                                  [0., float(water_drop_a)]])
#                 return sections, section_shape
#             elif self.water_drop_layout.value == 1:  # 只有下部
#                 sections.append([[0., 0.],
#                                  [float(water_drop_b), float(water_drop_a / 2)],
#                                  [0., float(water_drop_a)]])
#                 return sections, section_shape
#             else:
#                 sections.append([[0., 0.],
#                                  [-float(water_drop_b), float(water_drop_a / 2)],
#                                  [0., float(water_drop_a)]])
#                 sections.append([[0., 0.],
#                                  [float(water_drop_b), float(water_drop_a / 2)],
#                                  [0., float(water_drop_a)]])
#                 return sections, section_shape
#
#
# class RailingEmbeddedPartsData(object):
#     """
#     栏杆预埋件定位信息
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#
#         self.rail_design_mode = self.detailed_design.inserts_detailed.rail_design_mode
#         self.rail_layout = self.detailed_design.inserts_detailed.rail_layout
#         self.width = self.detailed_design.geometric_detailed.width
#         self.bottom_top_length = self.detailed_design.geometric_detailed.bottom_top_length
#         self.bottom_thickness = self.detailed_design.geometric_detailed.bottom_thickness
#         self.steps_h = self.structure_design_result.steps_h
#         self.steps_b = self.structure_design_result.steps_b
#
#     def get_rail_embedded_parts_position(self) -> List[List[float]]:
#         """
#         计算栏杆预埋件的坐标点：栏杆上表面,栏杆布置侧为 上楼梯方向的左右侧
#         :return:
#         """
#         rail_number = self.detailed_design.inserts_detailed.rail_number  # 栏杆所在的阶数
#
#         x_a = self.detailed_design.inserts_detailed.rail_position.a  # 横向边距
#         y_b = self.detailed_design.inserts_detailed.rail_position.b  # 纵向距离台阶
#         # 栏杆布置左右侧
#         position_x = []
#         if self.rail_layout.value == 0:  # ONLY_RIGHT = 0 ONLY_LEFT = 1   BOTH = 2
#             position_x.append(float(self.width - x_a))
#         elif self.rail_layout.value == 1:
#             position_x.append(float(x_a))
#         else:
#             position_x.append(float(x_a))
#             position_x.append(float(self.width - x_a))
#         position_y = []
#         for i in rail_number:
#             position_y.append(float(self.bottom_top_length + i * self.steps_b - y_b))
#         position_z = []
#         for i in rail_number:
#             position_z.append(float(self.bottom_thickness + i * self.steps_h))
#         positions = []
#         for i in range(len(position_x)):
#             for j in range(len(rail_number)):
#                 positions.append([position_x[i], position_y[j], position_z[j]])
#         return positions
#
#
# class LiftingEmbeddedPartsData(object):
#     """
#     吊装预埋件定位坐标
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#
#         self.steps_b = self.structure_design_result.steps_b
#         self.steps_h = self.structure_design_result.steps_h
#         self.lifting_type = self.detailed_design_result.lifting_type
#         self.bottom_top_length = self.detailed_design.geometric_detailed.bottom_top_length
#         self.bottom_thickness = self.detailed_design.geometric_detailed.bottom_thickness
#         self.width = self.detailed_design.geometric_detailed.width
#         self.lifting_position_a = self.detailed_design.inserts_detailed.lifting_position.a
#         self.lifting_position_b = self.detailed_design.inserts_detailed.lifting_position.b
#         self.lifting_position_c = float(self.detailed_design.inserts_detailed.lifting_position.c)  # 吊装预埋件左侧横向边距
#         self.lifting_position_d = float(self.detailed_design.inserts_detailed.lifting_position.d)  # 吊装预埋件右侧横向边距
#
#     def get_lifting_embedded_parts_position(self) -> List[List[float]]:
#         """
#         计算吊装预埋件的坐标点：预埋件上部中心点
#         :return:
#         """
#         edge_a = self.bottom_top_length + (self.lifting_position_a - 0.5) * self.steps_b  # 吊装预埋件顶端纵向边距
#         edge_b = self.bottom_top_length + (self.lifting_position_b - 0.5) * self.steps_b  # 吊装预埋件底端纵向边距
#         top_h = self.bottom_thickness + self.lifting_position_a * self.steps_h  # 下部吊装件坐标
#         bottom_h = self.bottom_thickness + self.lifting_position_b * self.steps_h  # 上部吊装件坐标
#
#         position_x = [self.lifting_position_c, float(self.width - self.lifting_position_d)]
#         position_y = [float(edge_b), float(edge_a)]
#         position_z = [float(bottom_h), float(top_h)]
#         positions = [[position_x[0], position_y[0], position_z[0]],
#                      [position_x[0], position_y[1], position_z[1]],
#                      [position_x[1], position_y[0], position_z[0]],
#                      [position_x[1], position_y[1], position_z[1]]]
#
#         return positions
#
#
# class DemouldingEmbeddedPartsData(object):
#     """
#     脱模预埋件位置
#     """
#
#     def __init__(self, structure_design: StructuralDesign, structure_design_result: StructuralDesignResult,
#                  detailed_design: DetailedDesign, detailed_design_result: DetailedDesignResult) -> None:
#         self.structure_design = structure_design
#         self.structure_design_result = structure_design_result
#         self.detailed_design = detailed_design
#         self.detailed_design_result = detailed_design_result
#         self.tan = self.detailed_design_result.tan
#         self.cos = self.detailed_design_result.cos
#         self.sin = self.detailed_design_result.sin
#         self.pouring_way = self.detailed_design.inserts_detailed.pouring_way  # 楼梯的浇筑方式,影响预埋件的位置及数量
#         self.demolding_type = self.detailed_design.inserts_detailed.demolding_type  # 脱模预埋件类型
#         self.demolding_parameter = self.detailed_design_result.demolding_parameter  # 脱模预埋件参数
#         self.demolding_a = float(self.detailed_design.inserts_detailed.demolding_position.a)  # 脱模埋件顶端纵向边距
#         self.demolding_b = float(self.detailed_design.inserts_detailed.demolding_position.b)  # 脱模埋件底端纵向边距
#         self.demolding_c = float(self.detailed_design.inserts_detailed.demolding_position.c)  # 脱模埋件左侧横向边距
#         self.demolding_d = float(self.detailed_design.inserts_detailed.demolding_position.d)  # 脱模埋件右侧横向边距
#         self.demolding_t = float(self.detailed_design.inserts_detailed.demolding_position.t)  # 脱模埋件厚度方向边距
#         self.h_total = float(self.detailed_design_result.h_total)  # 楼梯总高度
#         self.l_total = float(self.detailed_design_result.l_total)  # 纵向总长
#         self.width = float(self.detailed_design.geometric_detailed.width)
#         self.bottom_bottom_length = float(self.detailed_design_result.bottom_bottom_length)
#
#     def get_demoulding_embedded_parts_position(self):
#         """
#         计算脱模预埋件的坐标点
#         :return:
#         """
#         # 获取信息
#         # 侧面脱模预埋件的定位
#         # 顶端侧面脱模预埋件y坐标
#         demolding_t_y = self.l_total - self.demolding_a  # 顶端侧面脱模预埋件y坐标
#         # 顶端侧面脱模预埋件z坐标
#         demolding_t_z = (self.l_total - self.bottom_bottom_length - self.demolding_a) \
#                         * self.tan + self.demolding_t / self.cos
#         # 底端侧面脱模预埋件y坐标
#         demolding_b_y = self.demolding_b
#         # 底端侧面脱模预埋件z坐标
#         demolding_b_z = (self.demolding_b - self.bottom_bottom_length) * self.tan + self.demolding_t / self.cos
#
#         positions = [[self.width, demolding_t_y, demolding_t_z],
#                      [self.width, demolding_b_y, demolding_b_z]]
#         z_direction = [-1., 0., 0.]
#         x_direction = [0., -self.sin, self.cos]
#
#         return positions, z_direction, x_direction
