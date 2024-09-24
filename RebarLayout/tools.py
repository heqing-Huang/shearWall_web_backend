import math

import numpy as np

from DoubleWallDesign.models import RebarDiamSpac, RebarDiam

# 钢筋配筋计算
def rebar_opt(wall_thickness, rebar_ratio, interior_thickness, exterior_thickness, cover):
    rebar_area = wall_thickness * rebar_ratio * 10 / 2  # 计算配筋面积
    dia_max = min(int(wall_thickness / 10), (min(interior_thickness, exterior_thickness) - 2 * cover) / 2)
    dia_sets = [8, 10, 12, 14, 16, 18, 20]
    spacing_sets = [100, 125, 150, 180, 200, 220, 240, 250]
    # 筛选可选钢筋集合
    allow_dia_sets = []
    for diam in dia_sets:
        if diam <= dia_max:
            allow_dia_sets.append(diam)
    combine_diam_sets = []
    for num in range(len(allow_dia_sets)):
        combine_diam_sets.append([allow_dia_sets[num]])
        if num < len(allow_dia_sets) - 1:
            combine_diam_sets.append([allow_dia_sets[num], allow_dia_sets[num + 1]])
    row = len(spacing_sets)  # 表的行
    column = len(combine_diam_sets)  # 表的列
    rebar_area_table = np.zeros((row, column))  # 钢筋面积表
    for row_ in range(row):
        for column_ in range(column):
            average_area = 0
            for num in range(len(combine_diam_sets[column_])):
                current_diam = combine_diam_sets[column_][num]
                average_area += (math.pi * current_diam ** 2) / 4
            average_area = average_area / len(combine_diam_sets[column_])
            rebar_area_table[row_][column_] = average_area * (1000 / spacing_sets[row_])
    min_area = ((math.pi * dia_max ** 2) / 4 * (1000 / spacing_sets[0]))
    min_area_row = 0
    min_area_column = 0
    for row_ in range(row):
        for column_ in range(column):
            current_area = rebar_area_table[row_][column_]  # 当前面积
            if current_area >= rebar_area and current_area < min_area:
                min_area = current_area
                min_area_row = row_
                min_area_column = column_
    rebar_diam_sets = combine_diam_sets[min_area_column]
    rebar_spacing = spacing_sets[min_area_row]
    rebars = []
    for dia in rebar_diam_sets:
        rebars.append(RebarDiamSpac(diameter=dia, spacing=rebar_spacing))
    return rebars


def truss_design(detailed_design):
    detailed_design.truss_detailed.top_rebar = RebarDiam(diameter=10)
    detailed_design.truss_detailed.bottom_rebar = RebarDiam(diameter=8)
    detailed_design.truss_detailed.diagonal_rebar = RebarDiamSpac(diameter=6, spacing=200)
    detailed_design.truss_detailed.height = 204
    detailed_design.truss_detailed.width = 100
    detailed_design.truss_detailed.truss_number = 6,
    return detailed_design


def get_truss_layout(detailed_design_result, truss_spacing, truss_lengths_plan):
    detailed_design = detailed_design_result.detailed_design
    truss_detailed = detailed_design.truss_detailed
    truss_position_x = np.cumsum(truss_spacing)[0:-1]
    truss_lengths = (np.int_(np.array(truss_lengths_plan) /
                             (truss_detailed.diagonal_rebar.spacing / 2)) * (
                             truss_detailed.diagonal_rebar.spacing / 2)).tolist()
    truss_position_z = []
    for truss_length in truss_lengths:
        truss_position_z.append([float(detailed_design.geometric_detailed.bottom_gap_height +
                                       detailed_design.construction_detailed.concrete_cover_thickness),
                                 float(detailed_design.geometric_detailed.bottom_gap_height +
                                       detailed_design.construction_detailed.concrete_cover_thickness + truss_length)])
    truss_position_y = float(detailed_design.geometric_detailed.thickness - \
                             detailed_design.construction_detailed.concrete_cover_thickness - \
                             max([rebar_dia_spc.diameter for rebar_dia_spc in
                                  detailed_design_result.horizontal_rebars]) - \
                             truss_detailed.top_rebar.diameter / 2)
    truss_layout = []
    for i in range(len(truss_position_x)):
        truss_layout.append([[truss_position_x[i], truss_position_y, truss_position_z[i][0]],
                             [truss_position_x[i], truss_position_y, truss_position_z[i][1]]])
    return truss_layout


# 计算剪力墙体积
def get_volume(interior_length=None, interior_thickness=None, interior_height=None,
               exterior_length = None,exterior_thickness=None, exterior_height=None, wall_hole_height=None, wall_hole_length=None):
    """
    计算楼梯的体积
    :param length:剪力墙长度
    :param interior_thickness: 板厚
    :param interior_height: 余弦
    :param exterior_thickness: 踏步高度
    :param exterior_height: 踏步宽度
    :return: 剪力墙体积
    """
    v_interior = (interior_length * interior_height -wall_hole_height*wall_hole_length) * interior_thickness  / 10 ** 9
    v_exterior = (exterior_length * exterior_height -wall_hole_height*wall_hole_length) * exterior_thickness  / 10 ** 9
    volume_ = v_exterior + v_interior  # 体积
    return volume_


# 计算剪力墙面积
def get_area(length=None, interior_height=None, exterior_height=None):
    """
    计算楼梯的体积
    :param length:梯步个数
    :param interior_thickness: 板厚
    :param interior_height: 余弦
    :param exterior_thickness: 踏步高度
    :param exterior_height: 踏步宽度
    :return: 剪力墙体积
    """
    a_interior = length * interior_height / 10 ** 6
    a_exterior = length * exterior_height / 10 ** 6
    area_ = a_exterior + a_interior  # 面积
    return area_


def rotation_matrix_from_vectors(vec1, vec2):
    """ Find the rotation matrix that aligns vec1 to vec2
    :param vec1: A 3d "source" vector
    :param vec2: A 3d "destination" vector
    :return mat: A transform matrix (3x3) which when applied to vec1, aligns it with vec2.
    """
    a, b = (vec1 / np.linalg.norm(vec1)).reshape(3), (vec2 / np.linalg.norm(vec2)).reshape(3)
    v = np.cross(a, b)
    if any(v):  # if not all zeros then
        c = np.dot(a, b)
        s = np.linalg.norm(v)
        kmat = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
        return np.eye(3) + kmat + kmat.dot(kmat) * ((1 - c) / (s ** 2))

    else:
        return np.eye(3)  # cross of all zeros only occurs on identical directions


def rebar_mandrel_diameter(radius=5, steel_grade=1):
    if steel_grade == 1:
        mandrel_diameter = 1.25 * radius * 2
    elif steel_grade == 2:
        mandrel_diameter = 2.0 * radius * 2
    elif steel_grade == 3:
        mandrel_diameter = 2.5 * radius * 2
    else:
        mandrel_diameter = 2.5 * radius * 2
    return int(mandrel_diameter)
