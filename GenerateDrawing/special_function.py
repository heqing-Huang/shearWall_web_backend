"""
生成图形数据通用函数
"""
import copy

from OCC.Core.gp import gp_Pnt,gp_Pln,gp_Dir,gp_Ax2,gp_Ax1,gp_Trsf
from OCC.Core.TopoDS import TopoDS_Shape,TopoDS_Wire,TopoDS_Vertex,topods_Vertex, topods_Edge  # 拓扑顶点
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.HLRBRep import HLRBRep_Algo,HLRBRep_HLRToShape
from OCC.Core.HLRAlgo import HLRAlgo_Projector
from OCC.Extend.TopologyUtils import list_of_shapes_to_compound, discretize_edge,get_sorted_hlr_edges,WireExplorer, \
    is_wire  # 获取每条边的端点信息
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Fuse,BRepAlgoAPI_Cut,BRepAlgoAPI_Common,BRepAlgoAPI_Section
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire,BRepBuilderAPI_MakeEdge,BRepBuilderAPI_Transform
from OCC.Core.TopExp import TopExp_Explorer
from typing import List,Optional,Tuple
import numpy as np
from DoubleWallDesign.geometry import BoundingBox


def get_solid_projection_data(model:TopoDS_Shape,project_coord_origin:List[float],gazing_direction:List[float],
                              project_coord_dir_x:List[float]):
    """
    获取实体投影坐标数据
    :param model: 拓扑模型
    :param project_coord_origin: 投影坐标原点
    :param gazing_direction: 视线方向
    :param project_coord_x: 将原始坐标系的某方向作为投影坐标系x轴
    :return:
    """
    project_data = compute_project_shape_axis(model,project_coord_origin,gazing_direction,project_coord_dir_x)
    return project_data


def rewrite_get_sorted_hlr_edges_axis(topods_shape: TopoDS_Shape,origin:gp_Pnt,normal:gp_Dir,vector_dir:gp_Dir,
                                 export_hidden_edges: Optional[bool] = True) -> Tuple[List, List]:
    """
    参见 OCC.Extend.TopologyUtils.get_sorted_hlr_edges
    修改传入参数,以满足内部逻辑
    Args:
        topods_shape:
        ax3:局部坐标系
        export_hidden_edges:
    Returns:
    """
    # 1.加载模型
    hlr = HLRBRep_Algo()  # 获得线段本身
    hlr.Add(topods_shape)
    # 2.设置视点及投影方向、投影平面
    ax2 = gp_Ax2(origin,normal,vector_dir)
    projector = HLRAlgo_Projector(ax2)  # 投影函数确定投影平面

    hlr.Projector(projector)  # 设置投影平面
    # 3.计算投影
    hlr.Update()  # 隐藏线移除算法更新
    hlr.Hide()  # 通过该算法计算模型可见性与隐藏线，仅HLRBRep_Algo算法独有
    # 4.提取边
    hlr_shapes = HLRBRep_HLRToShape(hlr)  # 开始投影形状操作

    # 可视化边
    # 可提取边的类型有
    # 垂直于视线方向的边
    visible = []
    visible_sharp_edges_as_compound = hlr_shapes.VCompound()
    if visible_sharp_edges_as_compound:  # 探测尖边
        visible += list(TopologyExplorer(visible_sharp_edges_as_compound).edges())
    # visible_smooth_edges_as_compound = hlr_shapes.Rg1LineVCompound()  # 探测平滑边---实体与实体相连接的接触边
    # if visible_smooth_edges_as_compound:
    #     visible += list(TopologyExplorer(visible_smooth_edges_as_compound).edges())
    # visible_rgnline_as_compound = hlr_shapes.RgNLineVCompound()  # 去掉sewn edges线----圆头吊钉缝边
    # if visible_rgnline_as_compound:
    #     visible += list(TopologyExplorer(visible_rgnline_as_compound).edges())
    visible_contour_edges_as_compound = hlr_shapes.OutLineVCompound()  # 探测垂直轮廓边---形成形状的主要函数
    if visible_contour_edges_as_compound:
        visible += list(TopologyExplorer(visible_contour_edges_as_compound).edges())
    # visible_isoline_edges_as_compound = hlr_shapes.IsoLineVCompound()
    # if visible_isoline_edges_as_compound:
    #    visible += list(TopologyExplorer(visible_isoline_edges_as_compound).edges())

    # 隐藏线的边--平行于视线方向的边
    hidden = []
    if export_hidden_edges:  # 导出隐藏边
        hidden_sharp_edges_as_compound = hlr_shapes.HCompound()
        if hidden_sharp_edges_as_compound:  # 隐藏尖边
            hidden += list(TopologyExplorer(hidden_sharp_edges_as_compound).edges())
        hidden_contour_edges_as_compound = hlr_shapes.OutLineHCompound()  # 隐藏轮廓边
        if hidden_contour_edges_as_compound:
            hidden += list(TopologyExplorer(hidden_contour_edges_as_compound).edges())
    return visible, hidden


def compute_project_shape_axis(shape: TopoDS_Shape,origin:List[float],normal:List[float],vector_x:List[float]):
    """
    计算一个shape 投影后在平面内的的形状。返回的shape是在这个ax3 下坐标系表示的
    Args:
        shape:
        origin:坐标原点
        normal:主方向方向---视线方向
        vector_x:全局坐标系的某方向作为投影坐标系的x轴
        投影后的另一个方向为
    Returns:

    """
    origin = gp_Pnt(float(origin[0]),float(origin[1]),float(origin[2]))
    project_dir = gp_Dir(float(normal[0]),float(normal[1]),float(normal[2]))
    vector_x = gp_Dir(float(vector_x[0]),float(vector_x[1]),float(vector_x[2]))
    visible, hidden = rewrite_get_sorted_hlr_edges_axis(shape, origin,project_dir,vector_x,
                                              export_hidden_edges=False)
    make_wire = BRepBuilderAPI_MakeWire()
    points = []
    for edg in visible:
        points_3d = discretize_edge(edg, 0.01)  # 转换成点
        points.append(points_3d)
        # 可视化图形
        for i in range(len(points_3d) - 1):
            point_start = points_3d[i]
            start_pnt = gp_Pnt(*point_start)
            point_end = points_3d[i + 1]
            end_pnt = gp_Pnt(*point_end)
            make_edg_api = BRepBuilderAPI_MakeEdge(start_pnt, end_pnt)
            edg = make_edg_api.Edge()
            make_wire.Add(edg)
    # make_wire.Shape()
    return points


def compute_solid_cut_profile_shape(shape:TopoDS_Shape,point:List[float],direction:List[float]):
    """
    计算实体剖切轮廓形状
    :param shape:实体形状
    :param point: 平面上的点
    :param direction:平面法线
    """
    plane = gp_Pln(gp_Pnt(float(point[0]),float(point[1]),float(point[2])),
                   gp_Dir(float(direction[0]),float(direction[1]),float(direction[2])))
    compound_ = BRepAlgoAPI_Section(shape, plane).Shape()  # 获取平面剖切后的线框图
    edge = []
    if compound_:
        edge += list(TopologyExplorer(compound_).edges())
    points_ = []
    for edge_ in edge:
        points_3d = discretize_edge(edge_, 0.001)  # 转换成点
        points_.append(points_3d)
    return points_


def rotation_solid(solid:TopoDS_Shape,base:List[float],rotation_axis:List[float],angle:float)->TopoDS_Shape:
    """
    将实体绕指定轴逆时针旋转一定角度
    :param solid:TopoDS_Shape
    :param base:旋转基点
    :param rotation_axis:旋转轴
    :param angle:旋转角度---弧度制
    :return:
    """

    transform = gp_Trsf()
    transform.SetRotation(gp_Ax1(gp_Pnt(base[0],base[1],base[2]),gp_Dir(rotation_axis[0],rotation_axis[1],rotation_axis[2])),angle)
    transform_solid = BRepBuilderAPI_Transform(solid,transform).Shape()
    return transform_solid

def rotation_3d(position: np.asarray, axis: np.asarray, angle: float) -> np.ndarray:
    """
    工具函数,用于依仗特定轴旋转特定向量特定角度，此处必须用np.asarray，不然容易报错。
    position:原坐标(x, y, z)
    axis:旋转的坐标轴(ex, ey, ez)
    angle: 旋转弧度
    """

    ex, ey, ez = axis
    ex, ey, ez = [x / np.sqrt(ex ** 2 + ey ** 2 + ez ** 2)  # 归一化
                  for x in axis]
    s, c = np.sin(angle), np.cos(angle),
    matrix1 = np.array([[ex ** 2, ex * ey, ex * ez],
                        [ey * ex, ey ** 2, ey * ez],
                        [ex * ez, ey * ez, ez ** 2]])
    matrix2 = np.array([[c, -ez * s, ey * s],
                        [ez * s, c, -ex * s],
                        [-ey * s, ex * s, c]])
    matrix = (1 - c) * matrix1 + matrix2
    return matrix.dot(np.array(position).reshape(3, 1)).reshape(1, 3)[0]


def calculate_normal_vector(point_1: Tuple[float], point_2: Tuple[float], theta: float) -> np.array:
    """
    开始计算两个元组与平面向外叉乘的法向量
    :param point_1:
    :param point_2:
    :param theta:
    :return:
    """
    vector_1 = np.array(np.array(list(point_2)) - np.array(list(point_1))) / np.linalg.norm(
        np.array(list(point_2)) - np.array(list(point_1)))
    vector_0 = rotation_3d(np.asarray(vector_1), np.asarray([0, 0, 1]), theta)
    vector_2 = np.array([0, 0, 1])
    normal = np.cross(vector_0, vector_2)
    normal_ = np.array(normal) / np.linalg.norm(normal)
    return normal_


def move_solid(solid:TopoDS_Shape,vector:List[float]):
    """
    将实体进行平移变换
    :param solid:
    :param vector:
    :return:
    """
    from OCC.Core.gp import gp_Trsf,gp_Vec
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
    transform = gp_Trsf()
    transform.SetTranslation(gp_Vec(vector[0],vector[1],vector[2]))
    transform_solid = BRepBuilderAPI_Transform(solid,transform).Shape()
    return transform_solid


def adjust_drawing_scale(point: List[float], scale: float) -> Tuple[float]:
    """
    调整图纸的比例
    :param point: [float,float,float]
    :param scale: float
    :return:
    """
    for num in range(len(point)):
        point[num] *= scale
    final_point = tuple(point)
    return final_point


def transform_point_from_xz_plane_to_xy_plane(point:Tuple[float]):
    """
    将xz平面上的点转换到xy平面上:转换xz平面上的点到xy平面上
    :param point:
    :return:
    """
    curr_point = np.array(copy.deepcopy(list(point))).T
    matrix = np.array([[1,0,0],
                       [0,0,1],
                       [0,0,0]])
    result = np.matmul(matrix,curr_point).T
    return result.tolist()

def transform_point_from_xy_plane_to_yx_plane(point:Tuple[float]):
    """
    将xy平面上的点转换到yx平面上:即x作为y的值，y作为x的值
    :param point:
    :return:
    """
    curr_point = np.array(copy.deepcopy(list(point))).T
    matrix = np.array([[0,1,0],
                       [1,0,0],
                       [0,0,0]])
    result = np.matmul(matrix,curr_point).T
    return result.tolist()


def point_sets_sort(points:List[List[float]],index:int,reverse=False)->List[List[float]]:
    """
    针对指定点集合对某个指标进行排序
    reverse为False。从小到大，反之由大到小排序
    """
    if reverse:  # 由大到小排序
        for i in range(len(points)-1):
            for j in range(i+1,len(points)):
                if points[i][index]< points[j][index]:  # 交换两点
                    mid_point = points[i]
                    points[i] = points[j]
                    points[j] = mid_point
    else:  # 由小到大
        for i in range(len(points) - 1):
            for j in range(i + 1, len(points)):
                if points[i][index] > points[j][index]:  # 交换两点
                    mid_point = points[i]
                    points[i] = points[j]
                    points[j] = mid_point
    return points


def transform_point_set_to_segment(point_sets:List[List[float]]):
    """
    将点集合转化为线段
    :param point_sets:点集合
    :return:
    """
    segment_sets = []
    for num in range(len(point_sets)-1):
        point_s = copy.deepcopy(point_sets[num])
        point_e = copy.deepcopy(point_sets[num+1])
        segment_sets.append([point_s,point_e])
    return segment_sets


def get_polygon_bounding_box_points(polygon_points:List[List[Tuple[float]]])->BoundingBox:
    """
    获取多段包围框点集合
    :param polygon_points:多边形轮廓点
    :param plane:  作用平面
    """
    max_x = -float('inf')  # 无穷大的数
    max_y = -float('inf')
    max_z = -float('inf')
    min_x = float('inf')
    min_y = float('inf')
    min_z = float('inf')
    for seg in polygon_points:
        for num in range(len(seg)):
            current_p = list(seg[num])
            # 获取x的最大值和最小值
            if current_p[0] <= min_x:
                min_x=current_p[0]
            if current_p[0] >= max_x:
                max_x = current_p[0]
            # 获取y的最大值和最小值
            if current_p[1] <= min_y:
                min_y = current_p[1]
            if current_p[1] >= max_y:
                max_y = current_p[1]
            # 获取z的最大值和最小值
            if current_p[2] <= min_z:
                min_z = current_p[2]
            if current_p[2] >= max_z:
                max_z = current_p[2]
    bbox = BoundingBox(min_x=min_x,max_x=max_x,min_y=min_y,max_y=max_y,min_z=min_z,max_z=max_z)
    return bbox


def get_point_sequence_bounding_box_points(polygon_points:List[List[float]])->BoundingBox:
    """
    获取序列点集合的包围框点集合
    :param polygon_points:多边形轮廓点
    :param plane:  作用平面
    """
    max_x = -float('inf')  # 无穷大的数
    max_y = -float('inf')
    max_z = -float('inf')
    min_x = float('inf')
    min_y = float('inf')
    min_z = float('inf')
    for num in range(len(polygon_points)):
        current_p = list(polygon_points[num])
        # 获取x的最大值和最小值
        if current_p[0] <= min_x:
            min_x=current_p[0]
        if current_p[0] >= max_x:
            max_x = current_p[0]
        # 获取y的最大值和最小值
        if current_p[1] <= min_y:
            min_y = current_p[1]
        if current_p[1] >= max_y:
            max_y = current_p[1]
        # 获取z的最大值和最小值
        if current_p[2] <= min_z:
            min_z = current_p[2]
        if current_p[2] >= max_z:
            max_z = current_p[2]
    bbox = BoundingBox(min_x=min_x,max_x=max_x,min_y=min_y,max_y=max_y,min_z=min_z,max_z=max_z)
    return bbox


def get_rectangle_rebar_shape_center_position(polygon_points:List[List[Tuple[float]]]):
    """
    获取钢筋剖切轮廓的形状中心点，每根直条钢筋右四根线段组成。
    :param polygon_points:
    :return:
    """
    rebar_num = int(len(polygon_points)/4)
    rebar_loc = []
    for i in range(rebar_num):
        value_x = []
        value_y = []
        value_z = []
        seg_1 = polygon_points[4*i]
        seg_2 = polygon_points[4*i+1]
        seg_3 = polygon_points[4*i+2]
        seg_4 = polygon_points[4*i+3]
        value_x.extend([seg_1[0][0],seg_1[1][0],seg_2[0][0],seg_2[1][0],seg_3[0][0],seg_3[1][0],seg_4[0][0],seg_4[1][0]])
        value_y.extend([seg_1[0][1],seg_1[1][1],seg_2[0][1],seg_2[1][1],seg_3[0][1],seg_3[1][1],seg_4[0][1],seg_4[1][1]])
        value_z.extend([seg_1[0][2],seg_1[1][2],seg_2[0][2],seg_2[1][2],seg_3[0][2],seg_3[1][2],seg_4[0][2],seg_4[1][2]])
        mean_x = sum(value_x)/len(value_x)
        mean_y = sum(value_y)/len(value_y)
        mean_z = sum(value_z)/len(value_z)
        rebar_loc.append([mean_x,mean_y,mean_z])
    return rebar_loc


def move_polygon_points_to_positive_value(polygon_points:List[List[Tuple[float]]],move:List[float])->List[List[Tuple[float]]]:
    """
    获取多段包围框点集合
    :param polygon_points:多边形轮廓点
    :param move:  平移量
    """
    for seg in polygon_points:
        for num in range(len(seg)):
            current_p = list(seg[num])
            moved_point = np.array(current_p) + np.array(move)
            seg[num] = tuple(moved_point.tolist())
    return polygon_points


def get_polygon_points_y_to_positive_value(polygon_points:List[List[Tuple[float]]])->List[List[Tuple[float]]]:
    """
    获取将所有坐标点的y值变为正数
    :param polygon_points:多边形轮廓点
    """
    for seg in polygon_points:
        for num in range(len(seg)):
            current_p = list(seg[num])
            seg[num] = tuple([current_p[0],abs(current_p[1]),current_p[2]])
    return polygon_points


def choose_specific_value_from_polygon_points(polygon_points:List[List[Tuple[float]]],index,limit,flag=True):
    """
    从多段线中根据指定索引按照阈值将点分类，并按要求返回需要的值
    :param polygon_points:
    :param index: 相应索引
    :param limit: 阈值
    :param flag: 选择大还是小，默认选小
    :return:
    """
    point_set_big = []
    point_set_small = []
    for seg in polygon_points:
        for num in range(len(seg)):
            current_p = list(seg[num])
            if current_p[index]>=limit:
                point_set_big.append(current_p)
            else:
                point_set_small.append(current_p)
    # 选择合适的
    if flag:
        return point_set_small
    return point_set_big

def choose_specific_value_from_polygon_points_to_specific_polygon(polygon_points,index,limit,flag=True):
    """
    根据多项段/多个点，选择指定值要求下的多线段/多个点
    :param polygon_points:List[List[Tuple[floa
    :param index:
    :param limit:
    :param flag:
    :return:
    """
    point_set_big = []
    point_set_small = []
    for seg in polygon_points:
        if isinstance(seg[0],tuple):
            current_p = list(seg[0])
            if current_p[index]>=limit:
                point_set_big.append(seg)
            else:
                point_set_small.append(seg)
        else:
            if seg[index]>=limit:
                point_set_big.append(seg)
            else:
                point_set_small.append(seg)
    # 选择合适的
    if flag:
        return point_set_small
    return point_set_big

def calculate_segment_normal_rectangle_point(seg,radius):
    """
    计算线段法线的矩形点
    :param seg:
    :param radius:
    :return:
    """
    direction = np.array(np.array(seg[1])-np.array(seg[0]))/np.linalg.norm(np.array(seg[1])-np.array(seg[0]))
    direction_z_add = np.array([0,0,1])
    direction_z_minus = np.array([0,0,-1])
    direction_right = np.cross(direction,direction_z_add)  # 方向向量右侧法线
    direction_left = np.cross(direction,direction_z_minus)  # 方向向量左侧法线
    #　左侧底部点
    point_l_b = np.array(seg[0]) + direction_left * radius
    # 右侧底部点
    point_r_b = np.array(seg[0]) + direction_right * radius
    # 左侧顶部点
    point_l_t = np.array(seg[1]) + direction_left * radius
    # 右侧顶部点
    point_r_t = np.array(seg[1]) + direction_right * radius
    rectangle = [point_l_b.tolist(),point_l_t.tolist(),point_r_t.tolist(),point_r_b.tolist(),point_l_b.tolist()]
    return rectangle


def form_total_straight_rebar_rectangle(rebar_seg,radius:float):
    """
    形成所有直钢筋矩形数据
    :param rebar_seg: 所有钢筋段:List[List[List[Tuple[float],Tuple[float]]]]
    :param radius: 钢筋直径
    :return:
    """
    total_rebar_seg = []
    for double_seg in rebar_seg:
        for single_seg in double_seg:
            point_1 = copy.deepcopy(list(single_seg[0]))
            point_2 = copy.deepcopy(list(single_seg[1]))
            point_1[2] = 0
            point_2[2] = 0
            seg = [point_1,point_2]
            index = 1
            seg_1 = point_sets_sort(seg,index)
            rectangle_ = calculate_segment_normal_rectangle_point(seg_1,radius)
            total_rebar_seg.append(rectangle_)
    return total_rebar_seg



