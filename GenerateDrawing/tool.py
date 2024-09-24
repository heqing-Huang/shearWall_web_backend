from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Common
from typing import Tuple
import numpy as np
import math
import copy


def transform_cartesian_to_point(cartesian_points):
    """
    将IFC的Cartesian坐标转化为三点的坐标
    :param cartesian_points:
    :return:
    """
    curve_points = []
    for cart_point_set in cartesian_points:
        point = cart_point_set.Coordinates
        curve_points.append((point[0],point[1],0))
    return curve_points


def addition_of_two_points(point_1,point_2):
    """
    两点的加法
    :param point_1:
    :param point_2:
    :return:
    """
    final_point = [point_1[0]+point_2[0],point_1[1]+point_2[1],
                   point_1[2]+point_2[2]]
    return tuple(final_point)


def my_BRepAlgoAPI_Fuse(shape1: TopoDS_Shape, shape2: TopoDS_Shape):
    """
    对两实体作布尔并运算
    :param shape1:
    :param shape2:
    :return:
    """
    fuse_solid = BRepAlgoAPI_Fuse(shape1, shape2)
    fuse_solid.SimplifyResult()
    return fuse_solid


def my_BRepAlgoAPI_Cut(shape1: TopoDS_Shape, shape2: TopoDS_Shape):
    """
    对两实体作布尔差运算
    :param shape1:
    :param shape2:
    :return:
    """
    cut_solid = BRepAlgoAPI_Cut(shape1, shape2)
    cut_solid.SimplifyResult()
    return cut_solid


def my_BRepAlgoAPI_Common(shape1: TopoDS_Shape, shape2: TopoDS_Shape):
    """
    对两实体作布尔交运算
    :param shape1:
    :param shape2:
    :return:
    """
    common_solid = BRepAlgoAPI_Common(shape1, shape2)
    common_solid.SimplifyResult()
    return common_solid


def form_truss_stirrup_shape_data(stirrup_points:Tuple[Tuple[float]]):
    """
    形成桁架马镫筋形状数据
    :param stirrup_points:
    :return:
    """
    stirrup_points = list(stirrup_points)
    total_num = len(stirrup_points)
    three_point_seg_num = int((total_num-2)/3)
    three_point_seg = []
    for num in range(three_point_seg_num):
        point_1 = stirrup_points[3*num+1]
        point_2 = stirrup_points[3*num+2]
        point_3 = stirrup_points[3*num+3]
        three_point_seg.append([point_1,point_2,point_3])
    total_seg_set = [[stirrup_points[0],stirrup_points[1]]]
    for num in range(three_point_seg_num):
        # 添加三点弧线
        total_seg_set.append(three_point_seg[num])
        # 添加两点线
        if num != three_point_seg_num-1:
            curr_seg = [three_point_seg[num][-1],three_point_seg[num+1][0]]
        else:
            curr_seg = [three_point_seg[num][-1], stirrup_points[-1]]
        total_seg_set.append(curr_seg)
    return total_seg_set


def radian_bt_vectors(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """
    计算两个向量之间的弧度值

    :param vector1:
    :param vector2:
    :return:
    """
    a_norm = np.linalg.norm(vector1)
    b_norm = np.linalg.norm(vector2)
    a_dot_b = vector1.dot(vector2)
    radian = np.arccos(a_dot_b / (a_norm * b_norm))
    return radian


def rotated_total_points_around_z_axis(total_segment,theta):
    """
    绕z轴旋转所有点
    :param total_segment: 所有点集合
    :param theta: 旋转角度
    :return:
    """
    matrix = np.array([[math.cos(theta),-math.sin(theta),0],
                       [math.sin(theta),math.cos(theta),0],
                       [0,0,1]])
    point_s = np.array(list(total_segment[0][0]))
    for seg in total_segment:
        for num in range(len(seg)):
            vector = np.array(copy.deepcopy(list(seg[num])))-point_s  # 向量
            vector_result = np.matmul(matrix,vector.T).T
            result = vector_result + point_s
            seg[num] = tuple(result)
    return total_segment


def rotated_total_points_around_y_axis(total_segment,theta):
    """
    绕y轴旋转所有点
    :param total_segment: 所有点集合
    :param theta: 旋转角度
    :return:
    """
    matrix = np.array([[math.cos(theta),0,-math.sin(theta)],
                       [0,1,0],
                       [math.sin(theta),0,math.cos(theta)]])
    point_s = np.array(list(total_segment[3][0]))
    for seg in total_segment:
        for num in range(len(seg)):
            vector = np.array(copy.deepcopy(list(seg[num])))-point_s  # 向量
            vector_result = np.matmul(matrix,vector.T).T
            result = vector_result + point_s
            seg[num] = tuple(result)
    return total_segment


def transform_truss_rebar_xy_plane_to_zx_plane(total_segment):
    """
    将xy平面的桁架筋变换到zx平面上
    :param total_segment:
    :return:
    """
    matrix = np.array([[0,0,1],
                       [0,1,0],
                       [1,0,0]])
    for seg in total_segment:
        for num in range(len(seg)):
            vector = np.array(copy.deepcopy(list(seg[num]))) # 向量
            result = np.matmul(matrix,vector.T).T
            seg[num] = tuple(result)
    return total_segment



