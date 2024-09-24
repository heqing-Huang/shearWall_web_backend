"""
工具
"""
from typing import List
from DoubleWallDesign.geometry import Point2D,BoundingBox


def get_point_sets_bounding_box(point_sets:List[Point2D]):
    """
    获取点集合的包围框
    :param point_sets:点序列集合
    :return:
    """
    bbox:BoundingBox = BoundingBox()
    min_x = float('inf')
    min_y = float("inf")
    max_x = -float("inf")
    max_y = -float("inf")
    for point in point_sets:
        min_x = min(min_x,point.x)
        min_y = min(min_y,point.y)
        max_x = max(max_x,point.x)
        max_y = max(max_y,point.y)
    bbox.min_x = min_x
    bbox.min_y = min_y
    bbox.max_x = max_x
    bbox.max_y = max_y
    return bbox


def check_two_bboxes_is_double_side_wall(bbox_1:BoundingBox,bbox_2:BoundingBox)->bool:
    """
    检查两个包围框是否能形成双皮剪力墙：判断bbox_2是否与bbox_1匹配形成双皮剪力墙
    """
    double_shear_wall_threshold = 300 # 双皮剪力墙之间的距离阈值
    distance_x_status = abs(bbox_1.max_x-bbox_1.min_x)==abs(bbox_2.max_x-bbox_2.min_x) # 两个包围框x方向的长度是否相等
    distance_y_status = abs(bbox_1.max_y-bbox_1.min_y)==abs(bbox_2.max_y-bbox_2.min_y) # 两个包围框y方向的长度是否相等
    if distance_x_status and distance_y_status:
        short_edge_dir = "x" # 包围框短边平行方向
        if abs(bbox_1.max_x-bbox_1.min_x)>abs(bbox_1.max_y-bbox_1.min_y): # 短边平行于y方向
            short_edge_dir="y"
        if short_edge_dir=="x":
            if abs(bbox_1.min_x-bbox_2.min_x)<=double_shear_wall_threshold and abs(bbox_1.min_y-bbox_2.min_y)<=2: # 两页剪力墙的间距是否小于阈值
                flag=True
            else:
                flag = False
        else:
            if abs(bbox_1.min_y-bbox_2.min_y)<=double_shear_wall_threshold and abs(bbox_1.min_x-bbox_2.min_x)<=2: # 两页剪力墙的间距是否小于阈值
                flag=True
            else:
                flag = False
    else:
        flag=False
    return flag
