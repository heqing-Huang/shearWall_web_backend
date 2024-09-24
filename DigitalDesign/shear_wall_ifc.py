"""
# File       : stair_ifc.py
# Time       ：2022/11/3 15:41
# Author     ：CR_X
# version    ：python 3.8
# Description：
"""

from typing import Optional
import ifcopenshell
from ifcopenshell.entity_instance import entity_instance

from DigitalDesign.ifc_core import IfcDocument
from DoubleWallDesign.models import RebarforBIM, ConcreteParameter, RebarParameter, \
    TrussRebarforBIM
from DigitalDesign.get_data import ShearWallData
from DigitalDesign.rebar_arc_point import rebar_arc


def create_ifc_doc(header_file: Optional[dict] = None, init_doc: Optional[dict] = None):
    ifc_doc = IfcDocument(header_file, init_doc)  # 创建IFC文件的实例
    return ifc_doc


def create_shear_wall_ifc(ifc_doc: IfcDocument, rebar_data: RebarforBIM, truss_rebar_data:TrussRebarforBIM, shear_wall_data: ShearWallData):
    schema = ifcopenshell.ifcopenshell_wrapper.schema_by_name(ifc_doc._schema.name())
    ifc_ReinforcingBarSurfaceEnum = schema.declaration_by_name("IfcReinforcingBarSurfaceEnum")
    ifc_ReinforcingBarTypeEnum = schema.declaration_by_name("IfcReinforcingBarTypeEnum")
    ReinforcingBarSurface = ifc_ReinforcingBarSurfaceEnum.enumeration_items()  # 钢筋表面类型
    ReinforcingBarType = ifc_ReinforcingBarTypeEnum.enumeration_items()  # 钢筋类型

    detailed_design_result = shear_wall_data.detailed_design_result
    detailed_design = shear_wall_data.detailed_design_result.detailed_design
    concrete_grade = detailed_design.material.concrete_grade  # 混凝土强度等级 无量纲
    concrete_parameter = ConcreteParameter.by_grade(concrete_grade)  # 混凝土参数-类
    concrete_name = concrete_parameter.name
    rebar_name = detailed_design.material.rebar_name  # 钢筋强度等级 无量纲
    rebar_parameter = RebarParameter.by_name(rebar_name)  # 钢筋参数-类
    steel_name = rebar_parameter.name

    # 全局使用的材料
    concrete_material = ifc_doc.ifcfile.createIfcMaterial(concrete_name, None, "Concrete")  # 混凝土材质
    steel_material = ifc_doc.ifcfile.createIfcMaterial(steel_name, None, "Steel")  # 钢筋材质

    site, site_placement = ifc_doc.create_site()
    building, building_placement = ifc_doc.create_building(site_placement)
    elevation = 0.0
    building_storey, storey_placement = ifc_doc.create_building_storey(building_placement, elevation)
    # 建立层级关系
    container_building = ifc_doc.create_RelAggregates("Building Container", building, building_storey)
    container_site = ifc_doc.create_RelAggregates("Site Container", site, building)

    container_project = ifc_doc.create_RelAggregates("Project Container", ifc_doc.project, site)
    owner_history = ifc_doc.owner_history

    # 混凝土主体建模
    shear_wall_position = ifc_doc.create_IfcAxis2Placement3D(origin=[0., 0., 0.])
    shear_wall_placement = ifc_doc.create_IfcLocalplacement(storey_placement, shear_wall_position)
    shear_wall_solids = []

    # 剪力墙信息获取
    interior_section = shear_wall_data.get_interior_section()  # 内板，需要收尾相连
    exterior_section = shear_wall_data.get_exterior_section()  # 外板，需要收尾相连

    # 混凝土部分数据
    interior_height = shear_wall_data.get_interior_height()  # 拉伸长度
    exterior_height = shear_wall_data.get_exterior_height()  # 拉伸长度

    extrude_direction = [0., 0., 1.]
    interior_position = ifc_doc.create_IfcAxis2Placement3D(
        origin=[float(shear_wall_data.left_gap_length), 0., float(shear_wall_data.bottom_gap_height)],
        z=[0., 0., 1.], x=[1., 0., 0.])
    interior_body = ifc_doc.create_ExtrudedAreaSolid(interior_section, interior_position, extrude_direction,
                                                     interior_height)
    shear_wall_solids.append(interior_body)
    top_ear_position = ifc_doc.create_IfcAxis2Placement3D(
        origin=[0., float(shear_wall_data.thickness - shear_wall_data.exterior_thickness),
                float(shear_wall_data.bottom_gap_height)], z=[0., 0., 1.], x=[1., 0., 0.])
    exterior_body = ifc_doc.create_ExtrudedAreaSolid(exterior_section, top_ear_position, extrude_direction,
                                                     exterior_height)
    shear_wall_solids.append(exterior_body)

    global_geometry_context: entity_instance = ifc_doc.global_geometry_context
    representation = ifc_doc.ifcfile.createIfcShapeRepresentation(global_geometry_context, "Body", "SolidModel",
                                                                  shear_wall_solids)
    product_shape = ifc_doc.ifcfile.createIfcProductDefinitionShape(None, None, [representation])

    # 双面叠合剪力墙
    shear_wall = ifc_doc.ifcfile.createIfcStair(ifc_doc.get_global_id(),
                                                owner_history,
                                                "双面叠合剪力墙",
                                                "双面叠合剪力墙",
                                                None,
                                                shear_wall_placement,  # 存放位置,局部坐标
                                                product_shape,  # 几何形状
                                                None)

    # 将双面叠合剪力墙绑定到标高处
    ifc_doc.ifcfile.createIfcRelContainedInSpatialStructure(ifc_doc.get_global_id(),
                                                            owner_history,
                                                            "Building Storey Container",
                                                            None,
                                                            [shear_wall],
                                                            building_storey)  # 设置在那个楼层

    ifc_doc.ifcfile.createIfcRelAssociatesMaterial(ifc_doc.get_global_id(), owner_history,
                                                   None, None,
                                                   RelatedObjects=[shear_wall],
                                                   RelatingMaterial=concrete_material)
    # 创建钢筋
    rebars = []
    for attr, value in rebar_data.__dict__.items():
        for rebar in value:
            new_rebar = rebar_arc(rebar, shear_wall_data.rebar_parameter.grade)

            rebar_instance = ifc_doc.create_rebar(shear_wall_placement, new_rebar)
            rebars.append(rebar_instance)
    ifc_doc.ifcfile.createIfcRelAssociatesMaterial(ifc_doc.get_global_id(), owner_history,
                                                   None, None,
                                                   RelatedObjects=rebars,
                                                   RelatingMaterial=steel_material)
    rel_aggregate = ifc_doc.ifcfile.createIfcRelAggregates(
        ifc_doc.get_global_id(),
        ifc_doc.owner_history,
        "Shear_wall Container",
        None,
        shear_wall,
        rebars)
    # entity_instance_write = ifc_doc.ifcfile.createIfcRelContainedInSpatialStructure(
    #     ifc_doc.get_global_id(),
    #     ifc_doc.owner_history,
    #     "Building Storey Container",
    #     None,
    #     rebars,
    #     building_storey)

    # 创建桁架筋

    truss_rebars_ifc = ifc_doc.create_truss_rebars(shear_wall_placement, truss_rebar_data, shear_wall_data, shear_wall,
                                                   building_storey)

    with open(ifc_doc.ifcfile.wrapped_data.header.file_name.name, "w") as f:
        f.write(ifc_doc.ifcfile.to_string())
    return ifc_doc


def shear_wall_IFC_creation(rebar_data: RebarforBIM, truss_rebar_data: TrussRebarforBIM, shear_wall_data: ShearWallData):
    '''
    绘制楼梯主体并绑定到指定位置,同时绘制开洞
    :param rebar_data:
    :param truss_rebar_for_BIM:
    :param shear_wall_data:
    :return: ifc
    '''

    header_file = {'name': 'shear_wall.ifc',
                   'author': ['Chengran Xu'],
                   'organization': ['ZJKJ-CQU'],
                   'authorization': 'Chengran Xu, ChengranXu@cqu.edu.cn'}

    init_doc = {'person': {'Identification': 'XCR'}, 'application': {'Version': 'ifc4x3'}}
    ifc_doc = create_ifc_doc(header_file, init_doc)

    ifc_doc = create_ifc_doc()
    ifc_doc = create_shear_wall_ifc(ifc_doc, rebar_data, truss_rebar_data, shear_wall_data)
    print("IFC文件保存成功!!!")
    return ifc_doc
