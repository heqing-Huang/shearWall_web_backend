"""
双皮剪力墙几何
"""
from dataclasses import dataclass
from typing import List


@dataclass
class DoubleSideWall(object):
    """
    双皮剪力墙
    """
    inner_side_wall_width:float=1200
    inner_side_wall_height:float=2590
    inner_side_wall_thick:float=50.0
    outer_side_wall_width:float=1200
    outer_side_wall_height:float=2590
    outer_side_wall_thick:float=50
    inner_hole_thick:float= 150
    total_wall_thick:float=250


@dataclass
class BoundingBox(object):
    """
    包围框
    """
    min_x:float=0
    max_x:float=0
    min_y:float=0
    max_y:float=0
    min_z:float=0
    max_z:float=0


@dataclass
class Point2D(object):
    """
    建立平面坐标点
    """
    x:float=0
    y:float=0


@dataclass
class PolygonRegion(object):
    """
    建立多边形区域：楼层平面水平向右为x轴正方向，竖直向上为y轴正方向
    """
    left_bottom:Point2D=Point2D(x=0,y=0)
    right_bottom:Point2D=Point2D(x=0,y=0)
    left_top:Point2D=Point2D(x=0,y=0)
    right_top:Point2D=Point2D(x=0,y=0)
    profile_points:List[Point2D] = None