import logging
from io import BytesIO
from typing import IO, Tuple, Any
from docxtpl import DocxTemplate

from DigitalDesign.get_data import ShearWallData
from RebarLayout.layout_opt import layout_opt
from DoubleWallDesign.models import RebarDesignMode, ShearWallType, DetailedDesign, DetailedDesignResult, \
    ConcreteParameter, RebarforBIM, RebarforBVBS, RebarParameter, WallLengthType, TrussRebarMode, WallHole
from RebarLayout.tools import get_volume, get_area, rebar_opt, truss_design
from RebarLayout.collision_detection import ShearWallFCLModel

from DoubleWallDesign.tools import (
    DetailedCalculationBook
)

_logger = logging.getLogger(__name__)


def detailed_design(parameter: DetailedDesign):
    """
    该部分需要完成结构计算的逻辑,并返回结构计算对应的数据
    :param parameter:
    :return: ConstructionResult_detailed
    x 墙长， y 墙厚， z墙高
    """
    assert isinstance(parameter, DetailedDesign), Exception(f"parameter 数据异常")

    # 几何信息
    shear_wall_type: ShearWallType = parameter.geometric_detailed.shear_wall_type  # 剪力墙类型
    length: int = parameter.geometric_detailed.length  # 剪力墙长度 mm
    thickness: int = parameter.geometric_detailed.thickness  # 剪力墙总厚度 mm
    height: int = parameter.geometric_detailed.height  # 剪力墙总高度 mm
    interior_thickness: int = parameter.geometric_detailed.interior_thickness  # 内墙厚度
    exterior_thickness: int = parameter.geometric_detailed.exterior_thickness  # 外墙厚度
    bottom_gap_height: int = parameter.geometric_detailed.bottom_gap_height  # 底部间隙
    top_gap_height: int = parameter.geometric_detailed.top_gap_height  # 顶部间隙
    if shear_wall_type == ShearWallType.INTERIOR:  # 内外墙等高
        interior_height = height - bottom_gap_height - top_gap_height  # 内墙高度
        exterior_height = height - bottom_gap_height - top_gap_height  # 外墙高度
    else:  # shear_wall_type ==ShearWallType.EXTERIOR: # 外墙比内墙高
        interior_height = height - bottom_gap_height - top_gap_height  # 内墙高度
        exterior_height = height - bottom_gap_height  # 外墙高度
    wall_length_type: WallLengthType = parameter.geometric_detailed.wall_length_type  # 内外墙是否等长

    if wall_length_type == WallLengthType.YES:  # 若内外 等长
        left_gap_length = 0
        right_gap_length = 0
        interior_length: int = length  # 内墙长度
        exterior_length: int = length  # 外墙长度
    else:  # wall_length_type == WallLengthType.NO:  # 若内外不等长
        left_gap_length = parameter.geometric_detailed.left_gap_length
        right_gap_length = parameter.geometric_detailed.right_gap_length
        interior_length: int = length - left_gap_length - right_gap_length  # 内墙长度
        exterior_length: int = length  # 外墙长度

    if parameter.geometric_detailed.wall_hole == WallHole.YES:
        wall_hole_parameter = parameter.geometric_detailed.wall_hole_parameter
        wall_hole_height = parameter.geometric_detailed.wall_hole_parameter.hole_height
        wall_hole_length = parameter.geometric_detailed.wall_hole_parameter.hole_length
        wall_hole_horizontal = parameter.geometric_detailed.wall_hole_parameter.hole_horizontal
        wall_hole_vertical = parameter.geometric_detailed.wall_hole_parameter.hole_vertical

    else:
        wall_hole_height = 0
        wall_hole_length = 0
        wall_hole_horizontal =0
        wall_hole_vertical = 0
    wall_hole_region = [[wall_hole_horizontal - wall_hole_length / 2, wall_hole_vertical - wall_hole_height / 2],
                        [wall_hole_horizontal + wall_hole_length / 2, wall_hole_vertical + wall_hole_height / 2]]

    cover = parameter.construction_detailed.concrete_cover_thickness
    # 材料信息
    concrete_grade = parameter.material.concrete_grade  # 混凝土强度等级 无量纲
    concrete_parameter = ConcreteParameter.by_grade(concrete_grade)  # 混凝土参数-类
    rebar_name = parameter.material.rebar_name  # 钢筋强度等级 无量纲
    rebar_parameter = RebarParameter.by_name(rebar_name)  # 钢筋参数-类

    rc = concrete_parameter.rc  # 混凝土容重
    # 体积、面积、重量
    volume = get_volume(interior_length=interior_length, interior_thickness=interior_thickness, interior_height=interior_height,
                        exterior_length = exterior_length, exterior_thickness=exterior_thickness, exterior_height=exterior_height,
                        wall_hole_height=wall_hole_height, wall_hole_length=wall_hole_length)  # m^3
    area = get_area(length=length, interior_height=interior_height, exterior_height=exterior_height)  # m^2
    weight = rc / 10 * volume  # T

    # 钢筋设计
    rebar_design_mode = parameter.rebar_detailed.rebar_design_mode
    if rebar_design_mode == RebarDesignMode.AUTOMATIC:
        horizontal_rebars_ratio = parameter.rebar_detailed.vertical_rebars_ratio
        vertical_rebars_ratio = parameter.rebar_detailed.vertical_rebars_ratio
        horizontal_rebars = rebar_opt(thickness, horizontal_rebars_ratio, interior_thickness, exterior_thickness, cover)
        vertical_rebars = rebar_opt(thickness, vertical_rebars_ratio, interior_thickness, exterior_thickness, cover)
    else:  # rebar_design_mode == RebarDesignMode.MANUAL:
        horizontal_rebars = parameter.rebar_detailed.horizontal_rebars
        vertical_rebars = parameter.rebar_detailed.vertical_rebars
    # 桁架钢筋设计
    truss_rebar_mode = parameter.truss_detailed.truss_rebar_mode
    if truss_rebar_mode == TrussRebarMode.AUTOMATIC:
        parameter = truss_design(parameter)

    result = DetailedDesignResult(
        detailed_design=parameter,
        interior_height=interior_height,
        exterior_height=exterior_height,
        left_gap_length=left_gap_length,
        right_gap_length=right_gap_length,
        interior_length=interior_length,
        exterior_length=exterior_length,
        volume=volume,
        area=area,
        weight=weight,
        horizontal_rebars=horizontal_rebars,
        vertical_rebars=vertical_rebars,
    )
    rebar_for_BIM = RebarforBIM()  # 创建用于生成钢筋BIM模型的实例
    rebar_for_BVBS = RebarforBVBS()
    fcl_model = ShearWallFCLModel()  # 创建fcl碰撞检测模型
    shear_wall_data = ShearWallData(detailed_design_result=result)

    # 保护层障碍物
    cover_objs = shear_wall_data.get_cover()
    fcl_model.add_obj(cover_objs)

    # 横向钢筋
    horizontal_rebars_BVBS, horizontal_rebars_objs, horizontal_rebars_BIM = shear_wall_data.get_horizontal_rebars()
    rebar_for_BVBS.horizontal_rebars = horizontal_rebars_BVBS
    rebar_for_BIM.horizontal_rebars = horizontal_rebars_BIM
    fcl_model.add_obj(horizontal_rebars_objs)

    # 竖向钢筋
    vertical_rebars_BVBS, vertical_rebars_objs, vertical_rebars_BIM = shear_wall_data.get_vertical_rebars(
        number_s=len(horizontal_rebars_BVBS))  # number_s = bvbs钢筋编号开始数字
    rebar_for_BVBS.vertical_rebars = vertical_rebars_BVBS
    rebar_for_BIM.vertical_rebars = vertical_rebars_BIM
    fcl_model.add_obj(vertical_rebars_objs)

    truss_layout = layout_opt(fcl_model, detailed_design_result=result)
    truss_rebar_for_BIM = shear_wall_data.get_truss_rebars(truss_layout)

    return result, rebar_for_BIM, rebar_for_BVBS, truss_rebar_for_BIM, shear_wall_data,

def to_word_detailed(
    data: DetailedCalculationBook, file: IO[bytes]
) -> Tuple[IO[bytes], Any]:
    """
    基于word模板渲染生成word文件
    :param data:
    :param file:
    :return:
    """
    doc = DocxTemplate(file)

    detailed = data.detailed_design_result.detailed_design
    detailed_result = data.detailed_design_result

    concrete_parameter = ConcreteParameter.by_grade(
        detailed.material.concrete_grade
    )
    rebar_parameter = RebarParameter.by_name(detailed.material.rebar_name)

    context = {
        "detailed_cal_book": {
            "project_ID": detailed.shear_wall_id.project_ID,
            "shear_wall_ID": detailed.shear_wall_id.shear_wall_ID,

            "concrete_name": concrete_parameter.name,
            "concrete_f_tk": concrete_parameter.f_tk,
            "rebar_name": rebar_parameter.name,

            "interior_height": detailed_result.interior_height,
            "exterior_height": detailed_result.exterior_height,
            "left_gap_length": detailed_result.left_gap_length,
            "right_gap_length": detailed_result.right_gap_length,
            "interior_length": detailed_result.interior_length,
            "exterior_length": detailed_result.exterior_length,
            "volume": detailed_result.volume,
            "area": detailed_result.area,
            "weight": detailed_result.weight,
            "horizontal_rebars": detailed_result.horizontal_rebars,
            "vertical_rebars": detailed_result.vertical_rebars,
        }
    }
    doc.render(context)  # 转换成字典使用
    bytes_back = BytesIO()
    doc.save(bytes_back)
    bytes_back.seek(0)
    set_of_variables = doc.get_undeclared_template_variables()
    return bytes_back, set_of_variables