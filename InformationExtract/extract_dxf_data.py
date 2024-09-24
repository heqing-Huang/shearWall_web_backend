"""
从DXF文件中提取数据
"""
import ezdxf
from DoubleWallDesign.geometry import BoundingBox,Point2D,PolygonRegion
from typing import List
from InformationExtract.tool import get_point_sets_bounding_box,check_two_bboxes_is_double_side_wall


def extract_double_shear_wall_design_information(file_name):
    """
    提取设计信息
    双皮剪力墙图层名：double_shear_wall_region
    梁轮廓图层名：beam_profile
    剪力墙图层名：shear_wall
    楼层轮廓图层名：floor_profile
    """
    doc = ezdxf.readfile(file_name)
    model_space = doc.modelspace()
    # 解析shear_wall
    total_slab_bbox = []
    for entity in model_space:
        if entity.dxf.layer == "double_shear_wall_region": # 双皮剪力墙图层名
            points_set = entity.lwpoints
            point_num = int(len(points_set)) # 五点描述多段线
            total_point = []
            for i in range(point_num):
                curr_p:Point2D = Point2D(x=round(points_set[i][0]),y=round(points_set[i][1]))
                total_point.append(curr_p)
            bbox = get_point_sets_bounding_box(total_point)
            total_slab_bbox.append(bbox)
    # 形成两页墙体
    total_double_side_wall = []
    for num_i in range(len(total_slab_bbox)-1):
        for num_j in range(num_i+1,len(total_slab_bbox)):
            bbox_i = total_slab_bbox[num_i]
            bbox_j = total_slab_bbox[num_j]
            flag = check_two_bboxes_is_double_side_wall(bbox_i,bbox_j)
            if flag:
                if abs(bbox_i.min_x-bbox_j.min_x)<=2: # 两个包围框是上下关系
                    if bbox_i.min_y<bbox_j.min_y:
                        total_double_side_wall.append([bbox_i, bbox_j]) # 保证相对大小关系：小->大
                    else:
                        total_double_side_wall.append([bbox_j, bbox_i])
                else: # 两个包围框是左右关系
                    if bbox_i.min_x<bbox_j.min_x: # 左右关系
                        total_double_side_wall.append([bbox_i, bbox_j])  # 保证相对大小关系：小->大
                    else:
                        total_double_side_wall.append([bbox_j, bbox_i])
    return total_double_side_wall


def extract_shear_wall_design_information(file_name):
    """
    提取设计信息
    剪力墙图层名：shear_wall
    """
    doc = ezdxf.readfile(file_name)
    model_space = doc.modelspace()
    # 解析shear_wall
    total_shear_wall_info = []
    for entity in model_space:
        if entity.dxf.layer == "shear_wall": # 双皮剪力墙图层名
            points_set = entity.lwpoints
            point_num = int(len(points_set)) # 五点描述多段线
            total_point = []
            for i in range(point_num):
                curr_p:Point2D = Point2D(x=round(points_set[i][0]),y=round(points_set[i][1]))
                total_point.append(curr_p)
            total_shear_wall_info.append(total_point)
    return total_shear_wall_info

def extract_beam_design_information(file_name):
    """
    提取设计信息
    梁轮廓图层名：beam_profile
    """
    doc = ezdxf.readfile(file_name)
    model_space = doc.modelspace()
    # 解析shear_wall
    total_beam_info = []
    for entity in model_space:
        if entity.dxf.layer == "beam_profile": # 双皮剪力墙图层名
            start_p = entity.dxf.start
            end_p = entity.dxf.end
            points_set = [start_p,end_p]
            point_num = int(len(points_set)) # 五点描述多段线
            total_point = []
            for i in range(point_num):
                curr_p:Point2D = Point2D(x=round(points_set[i][0]),y=round(points_set[i][1]))
                total_point.append(curr_p)
            total_beam_info.append(total_point)
    return total_beam_info

def extract_floor_design_information(file_name):
    """
    提取设计信息
    楼层轮廓图层名：floor_profile
    """
    doc = ezdxf.readfile(file_name)
    model_space = doc.modelspace()
    # 解析shear_wall
    total_floor_info = []
    for entity in model_space:
        if entity.dxf.layer == "floor_profile": # 双皮剪力墙图层名
            points_set = entity.lwpoints
            point_num = int(len(points_set)) # 五点描述多段线
            for i in range(point_num):
                curr_p:Point2D = Point2D(x=round(points_set[i][0]),y=round(points_set[i][1]))
                total_floor_info.append(curr_p)
    return total_floor_info








