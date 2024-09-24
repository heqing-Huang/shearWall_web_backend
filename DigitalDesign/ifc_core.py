"""
# File       : ifc_core.py
# Time       ：2022/10/14 17:12
# Author     ：CR_X
# version    ：python 3.8
# Description：通用IFC文件生成, 用于楼梯
"""
import math
import time
import uuid
import warnings
from typing import Union, Optional, List, Dict
import logging
import ifcopenshell
# import ifcopenshell.util.pset
from ifcopenshell.file import file
from ifcopenshell.entity_instance import entity_instance
from ifcopenshell import ifcopenshell_wrapper
from ifcopenshell.ifcopenshell_wrapper import schema_definition

#
from ifcopenshell import guid

from DigitalDesign.get_data import ShearWallData
from DoubleWallDesign.models import TrussRebarforBIM, RebarParameter

from DigitalDesign.rebar_arc_point import IfcRebarData, rebar_arc

logger = logging.getLogger(__name__)
Vector = Union[List[float], entity_instance]

'''
file只要开头是六个字母是create，就可以创建一个实体（entity），并调用functools.partial方法
六位以后是IFC数据格式中的实体名（name）
#  例如 createIfcDirection 中 create是判断是否调用functools.partial方法，
'''


class IfcDocument(object):
    """
    封装ifc 相关操作,便于调用
    """
    _ifc_file: file
    _base_x: entity_instance
    _base_y: entity_instance
    _base_z: entity_instance
    _origin: entity_instance
    _global_placement: entity_instance
    _schema: schema_definition
    _person: entity_instance
    _organization: entity_instance
    _application: entity_instance
    _person_and_organization: entity_instance
    _owner_history: entity_instance
    _global_geometry_context: entity_instance
    _project: entity_instance

    def __init__(self, update_header: Optional[Dict] = None, init_document: Optional[Dict] = None, schema='IFC4X3'):
        self._ifc_file = file(schema=schema)  # 创建IFC文件instance实例 ifc 格式内存文件,后续操作都需要基于它
        self._origin = self.create_IfcCartesianPoint([0.0, 0.0, 0.0])  # 创建基于IFC的向量表示
        self._base_x = self.create_IfcDirection([1.0, 0.0, 0.0])
        self._base_y = self.create_IfcDirection([0.0, 1.0, 0.0])
        self._base_z = self.create_IfcDirection([0.0, 0.0, 1.0])
        self._global_placement = self.create_IfcAxis2Placement3D(self.origin, self.base_z, self.base_x)
        self._schema = ifcopenshell_wrapper.schema_by_name(schema)
        if update_header:
            self.update_Header(**update_header)
        else:
            self.update_Header()
        if init_document:
            self.init_document(**init_document)
        else:
            self.init_document()

    def filter_entity_by_attr(self, ifc_type: str, attr: str, value: str) -> List[entity_instance]:
        entity_s = []
        for entity in self.ifcfile.by_type(ifc_type):
            if getattr(entity, attr) == value:
                entity_s.append(entity)
        return entity_s

    def update_Header(self, **kwargs):
        '''
        更新header文件中的内容，参数输入的示例
        header_file = {'name': 'stair.ifc',
               'author': ['Chengran Xu'],
               'organization': ['ZJKJ-CQU'],
               'authorization': 'Chengran Xu, ChengranXu@cqu.edu.cn'}
        :param kwargs: 字典，其中包含各变量的key
        :return:
        '''
        if 'name' in kwargs:
            self.ifcfile.wrapped_data.header.file_name.name = kwargs['name']
        else:
            self.ifcfile.wrapped_data.header.file_name.name = 'shear_wall.ifc'
        if 'auther' in kwargs:
            self.ifcfile.wrapped_data.header.file_name.author = kwargs['author']
        else:
            self.ifcfile.wrapped_data.header.file_name.author = ['Chengran Xu']
        if 'authorization' in kwargs:
            self.ifcfile.wrapped_data.header.file_name.authorization = kwargs['authorization']
        else:
            self.ifcfile.wrapped_data.header.file_name.authorization = 'Chengran Xu, ChengranXu@cqu.edu.cn '
        if 'organization' in kwargs:
            self.ifcfile.wrapped_data.header.file_name.organization = kwargs['organization']
        else:
            self.ifcfile.wrapped_data.header.file_name.organization = ['ZJKJ-CQU']

    def init_document(self, **kwargs):
        # 创建 person
        if 'person' in kwargs:
            person = kwargs['person']
            self._person = self.create_Person(person)
        else:
            self._person = self.create_Person()
        assert self._person is not None, Exception(F"person_entity is None")

        if 'organization' in kwargs:
            organization = kwargs['organization']
            self._organization = self.create_Organization(organization)
        else:
            self._organization = self.create_Organization()
        assert self._organization is not None, Exception(F"_organization_entity is None")

        if 'application' in kwargs:
            application = kwargs['application']
            self._application = self.create_Application(self._organization, application)
        else:
            self._application = self.create_Application(self._organization)
        assert self._application is not None, Exception(F"_application_entity is None")
        self._person_and_organization = self.create_PersonAndOrganization(self._person, self._organization)

        self._owner_history: entity_instance = self.create_OwnerHistory(self._person_and_organization,
                                                                        self._application)
        if 'project_name' in kwargs:
            project_name = kwargs['project_name']
            self._project = self.create_project(name=project_name)
        else:
            self._project = self.create_project()

    def create_Unit(self):
        # 设置单位相关
        # 单位相关
        dimensional_exponents: entity_instance = self.ifcfile.create_entity("IfcDimensionalExponents", *[0] * 7)
        # 单位采用米
        length_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "LENGTHUNIT", "MILLI", "METRE")
        area_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "AREAUNIT", None, "SQUARE_METRE")
        volume_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "VOLUMEUNIT", None,
                                                                  "CUBIC_METRE")
        time_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "TIMEUNIT", None, "SECOND")
        plane_angle_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "PLANEANGLEUNIT",
                                                                       None, "RADIAN")
        energy_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "ENERGYUNIT", None, "JOULE")
        mass_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, "MASSUNIT", "KILO", "GRAM")
        # thermodynamic temperature 热力学温度
        thermodynamic_temperature_unit: entity_instance = self.ifcfile.create_entity("IfcSiunit", None,
                                                                                     "THERMODYNAMICTEMPERATUREUNIT",
                                                                                     None, "KELVIN")

        # 单位转换,对应角度和弧度的转换单位, 角度被进一步定义为相对于国际单位制单位弧度的换算单位(比例):
        plane_angle_measure: entity_instance = self.ifcfile.create_entity("IfcPlaneAngleMeasure", math.pi / 180)

        measure_with_unit: entity_instance = self.ifcfile.create_entity("IfcMeasureWithUnit", plane_angle_measure,
                                                                        plane_angle_unit)

        plane_angle_conversion_unit: entity_instance = self.ifcfile.create_entity("IfcConversionBasedUnit",
                                                                                  dimensional_exponents,
                                                                                  "PLANEANGLEUNIT",
                                                                                  "DEGREE",
                                                                                  measure_with_unit)

        # 比热容

        energy_unit_power: entity_instance = self.ifcfile.create_entity("IfcDerivedUnitElement", energy_unit, 1)
        mass_unit_power: entity_instance = self.ifcfile.create_entity("IfcDerivedUnitElement", mass_unit, -1)

        thermodynamic_temperature_unit_power: entity_instance = self.ifcfile.create_entity("IfcDerivedUnitElement",
                                                                                           thermodynamic_temperature_unit,
                                                                                           -1)
        specific_heat_capacity_unit: entity_instance = self.ifcfile.create_entity("IfcDerivedUnit",
                                                                                  [energy_unit_power,
                                                                                   mass_unit_power,
                                                                                   thermodynamic_temperature_unit_power],
                                                                                  "SPECIFICHEATCAPACITYUNIT", None)

        # 设置单位
        unit_assignment: entity_instance = self.ifcfile.create_entity("IfcUnitAssignment",
                                                                      [length_unit, area_unit, volume_unit,
                                                                       time_unit, plane_angle_conversion_unit,
                                                                       specific_heat_capacity_unit])

        return unit_assignment

    def add_Unit(self, unit_assignment: Optional[entity_instance] = None, add_unit_name: Optional[str] = None,
                 add_unit_unit: Optional[str] = None):
        '''
        设置单位，后续添加 IfcSiunit
        :parameter: unit_assignment 已经设置的单位
        :parameter: add_unit_name 增加的单位名称
        :parameter: add_unit_unit 增加的单位的单位
        :return:
        '''

        add_unit_entity: entity_instance = self.ifcfile.create_entity("IfcSiunit", None, add_unit_name, None,
                                                                      add_unit_unit)
        unit_list = list(unit_assignment.Units)
        unit_list.append(add_unit_entity)
        setattr(unit_assignment, 'Units', unit_list)
        return unit_assignment

    def create_geometry_context(self):
        global_placement3d: entity_instance = self.create_IfcAxis2Placement3D()
        global_true_north: entity_instance = self.create_IfcDirection([0.0, 1.0, 0.0])
        # global_true_north: entity_instance = None
        global_geometry_context: entity_instance = self.ifcfile.create_entity("IfcGeometricRepresentationContext",
                                                                              None,
                                                                              "Model",  # 三维model,二维plan
                                                                              3,  # 维度
                                                                              1.E-05,  # 精度
                                                                              global_placement3d,
                                                                              global_true_north)
        return global_geometry_context

    def create_project(self, name: Optional[str] = None):
        unit_assignment = self.create_Unit()
        self._global_geometry_context = self.create_geometry_context()
        # 定义项目,此时需要给项目传递单位参数,几何空间上下文,以及owner_history
        if name is None:
            name = "Stair"
        ifc_project: entity_instance = self.ifcfile.create_entity("IfcProject",
                                                                  self.get_global_id(),
                                                                  self.owner_history,
                                                                  name,
                                                                  None,
                                                                  None,
                                                                  None, None, [self._global_geometry_context],
                                                                  unit_assignment)
        return ifc_project

    def create_site(self):
        ifc_projects: List[entity_instance] = self.ifcfile.by_type("IfcProject")
        if not ifc_projects:
            raise Exception(f"未成功定义ifcProject")

        site_placement = self.create_IfcLocalplacement(relative_to=None, out_placement=self.global_placement)
        site = self.ifcfile.createIfcSite(self.get_global_id(), self.owner_history, "Site", None, None,
                                          site_placement,
                                          None, None,
                                          "ELEMENT",
                                          None, None, None, None, None)
        return site, site_placement

    def create_building(self, site_placement: Optional[entity_instance] = None):
        ifc_sites: List[entity_instance] = self.ifcfile.by_type("IfcSite")
        if not ifc_sites:
            raise Exception(f"未成功定义IfcSite")
        building_placement = self.create_IfcLocalplacement(site_placement, self.global_placement)

        building = self.ifcfile.createIfcBuilding(self.get_global_id(), self.owner_history, 'Building', None,
                                                  None,
                                                  building_placement,
                                                  None,
                                                  None, "ELEMENT", None, None, None)
        return building, building_placement

    def create_building_storey(self, building_placement: Optional[entity_instance] = None,
                               elevation: Optional[float] = 0.0):
        relative_placement = self.create_IfcAxis2Placement3D(origin=[0., 0., elevation])
        storey_placement = self.create_IfcLocalplacement(building_placement, relative_placement)

        building_storey = self.ifcfile.createIfcBuildingStorey(self.get_global_id(), self.owner_history, 'Storey',
                                                               None,
                                                               None,
                                                               storey_placement,
                                                               None, None, "ELEMENT", elevation)
        return building_storey, storey_placement

    def create_RelAggregates(self, Name: Optional[str] = None, superior_spatial: Optional[entity_instance] = None,
                             junior_spatial: Optional[entity_instance] = None):
        '''
        建立容器
        :param Name: "Building Container" "Site Container" "Project Container"
        :param superior_spatial:
        :param junior_spatial:
        :return:
        '''
        container = self.ifcfile.createIfcRelAggregates(self.get_global_id(), self.owner_history, Name, None,
                                                        superior_spatial, [junior_spatial])
        return container

    def create_material_layer(self, concrete_material: Optional[str] = None):

        # 全局使用的材料
        material = self.ifcfile.createIfcMaterial(concrete_material, None, "Concrete")  # 楼梯材质
        material_layer = self.ifcfile.createIfcMaterialLayer(material, 0.1, None)
        material_layer_set = self.ifcfile.createIfcMaterialLayerSet([material_layer], None)
        material_layer_set_usage = self.ifcfile.createIfcMaterialLayerSetUsage(material_layer_set, "AXIS2",
                                                                               "POSITIVE", -0.1)
        return material_layer_set_usage

    '''
    ＠property 修饰的方法，使得该方法是对象的一个只读属性， 无法重新赋值
    ->描述函数的返回类型
    '''

    @property
    def ifcfile(self) -> file:
        return self._ifc_file

    @property
    def origin(self) -> entity_instance:
        return self._origin

    @property
    def base_x(self) -> entity_instance:
        return self._base_x

    @property
    def base_y(self) -> entity_instance:
        return self._base_y

    @property
    def base_z(self) -> entity_instance:
        return self._base_z

    @property
    def global_placement(self) -> entity_instance:
        return self._global_placement

    @property
    def person(self) -> entity_instance:
        return self._person

    @staticmethod
    def get_global_id() -> str:
        '''
        生成GlobalId 在整个软件世界中分配全局唯一标识符。
        :return:
        '''
        return ifcopenshell.guid.compress(uuid.uuid1().hex)

    @property
    def global_geometry_context(self) -> entity_instance:
        return self._global_geometry_context

    @property
    def organization(self) -> entity_instance:
        return self._organization

    @property
    def application(self) -> entity_instance:
        return self._application

    @property
    def person_and_organization(self) -> entity_instance:
        return self._person_and_organization

    @property
    def owner_history(self) -> entity_instance:
        return self._owner_history

    @property
    def project(self) -> entity_instance:
        return self._project

    def create_IfcLocalplacement(self, relative_to: Optional[entity_instance] = None,  # LocalPlacement
                                 out_placement: Optional[entity_instance] = None) -> entity_instance:  # Axis2Placement
        if out_placement is None:
            out_placement = self.global_placement
        while True:
            ifclocalplacement2: entity_instance = self.ifcfile.createIfcLocalPlacement(relative_to, out_placement)
            if ifclocalplacement2.get_info().get("id") == 0:
                warnings.warn(f"创建局部坐标系失败,id 为0")
            else:
                break
        return ifclocalplacement2

    def create_IfcCartesianPoint(self, point: List) -> entity_instance:
        """
        create IfcCartesianPoint
        :param point:
        :return:
        """
        while True:
            point_back: entity_instance = self.ifcfile.createIfcCartesianPoint(point)
            if point_back.get_info().get("id") == 0:
                warnings.warn(f"创建点失败,id 为0")
            else:
                break
        return point_back

    def create_IfcDirection(self, vector: List) -> entity_instance:
        """
        create IfcDirection
        :param vector:
        :return:
        """
        while True:
            direction: entity_instance = self.ifcfile.createIfcDirection(vector)
            if direction.get_info().get("id") == 0:
                warnings.warn(f"创建方向向量失败,id为0,将重新创建")
            else:
                break
        return direction

    def create_IfcAxis2Placement3D(self, origin: Vector = None, z: Vector = None, x: Vector = None) -> entity_instance:
        """
        创建一个坐标系,满足z轴到x轴右手定则,建立全局或局部坐标系（origin为全局坐标系的坐标）
        通过两个轴创建一个三维坐标系
        创建一个坐标系,z 指向Z 轴,x 指向X 轴，需要满足右手定则
        如果未提供相关参数，默认新建一个并返回全局坐标系
        :param origin:
        :param z:
        :param x:
        :return:
        """
        while True:
            if origin is None and z is None and x is None:
                axis2placement3D: entity_instance = self.global_placement
            else:
                if origin is None:
                    origin = self.origin
                if z is None:
                    z = self.base_z
                if x is None:
                    x = self.base_x
                if not isinstance(origin, entity_instance):
                    origin = self.create_IfcCartesianPoint(origin)
                if not isinstance(z, entity_instance):
                    z = self.create_IfcDirection(z)
                if not isinstance(x, entity_instance):
                    x = self.create_IfcDirection(x)
                axis2placement3D: entity_instance = self.ifcfile.createIfcAxis2Placement3D(origin, z, x)
            if axis2placement3D.get_info().get("id") == 0:
                warnings.warn(f"坐标系创建id为0")
            else:
                break
        return axis2placement3D

    def create_Person(self, person: Optional[Dict] = None) -> Optional[entity_instance]:
        """
        创建 IfcPerson
        :param person: dic
        :return:
        """

        if person is None:
            person = {'Identification': 'Chengran Xu'}
        filter_person_entity_s = self.filter_entity_by_attr("IfcPerson", "Identification", person['Identification'])
        if not filter_person_entity_s:
            ifc_person = self.ifcfile.create_entity("IfcPerson")  # 创建开发人员
        else:
            ifc_person = filter_person_entity_s[0]
        for key, value in person.items():
            setattr(ifc_person, key, value)
        return ifc_person

    def create_Organization(self, organization: Optional[Dict] = None) -> Optional[entity_instance]:
        """
        创建组织
        :param organization:
        :return:
        """

        if organization is None:
            organization = {'Identification': 'ZJKJ-CQU', 'Name': '中建科技-重庆大学',
                            'Description': '中建科技-重庆大学'}
        else:
            if 'Identification' not in organization:
                organization['Identification'] = "ZJKJ-CQU"
            if 'Name' not in organization:
                organization['Name'] = "中建科技-重庆大学"
            if 'description' not in organization:
                organization['description'] = '中建科技-重庆大学'
        filter_organization_entity_s = self.filter_entity_by_attr("IfcOrganization", "Identification",
                                                                  organization['Identification'])
        if not filter_organization_entity_s:
            ifc_organization: entity_instance = self.ifcfile.create_entity("IfcOrganization")  # 创建组织
        else:
            ifc_organization = filter_organization_entity_s[0]
        for key, value in organization.items():
            setattr(ifc_organization, key, value)
        return ifc_organization

    def create_Application(self, organization: Optional[entity_instance] = None,
                           application_info: Optional[Dict] = None):
        if organization is None:
            ifc_organizations: List = self.ifcfile.by_type("IfcOrganization")
            if not ifc_organizations:
                logger.error(f"未找到组织信息,可能无法正确创建IfcApplication")
            else:
                organization = ifc_organizations[0]
        if application_info is None:
            application_info = {'Version': 'ZJKJ-CQU', 'ApplicationFullName': '中建科技-重庆大学',
                                'ApplicationIdentifier': '中建科技-重庆大学'}
        else:
            if 'Version' not in application_info:
                application_info['Version'] = ifcopenshell.version
            if 'ApplicationFullName' not in application_info:
                application_info['ApplicationFullName'] = "中建科技-重庆大学"
            if 'ApplicationIdentifier' not in application_info:
                application_info['ApplicationIdentifier'] = '中建科技-重庆大学'
        filter_application_entity_s = self.filter_entity_by_attr("IfcApplication", "ApplicationIdentifier",
                                                                 application_info['ApplicationIdentifier'])
        if not filter_application_entity_s:
            ifc_application: entity_instance = self.ifcfile.create_entity("IfcApplication", organization)  # 应用
        else:
            ifc_application = filter_application_entity_s[0]
        for key, value in application_info.items():
            setattr(ifc_application, key, value)
        return ifc_application

    def create_PersonAndOrganization(self, person: Optional[entity_instance] = None,
                                     organization: Optional[entity_instance] = None) -> entity_instance:
        if person is None:
            ifc_persons: List = self.ifcfile.by_type("IfcPerson")
            if not ifc_persons:
                logger.error(f"未找到人员信息,可能无法正确创建IfcPersonAndOrganization")
            else:
                person = ifc_persons[0]
        if organization is None:
            ifc_organizations: List = self.ifcfile.by_type("IfcOrganization")
            if not ifc_organizations:
                logger.error(f"未找到组织信息,可能无法正确创建IfcPersonAndOrganization")
            else:
                organization = ifc_organizations[0]

        ifc_person_and_organization: entity_instance = self.ifcfile.create_entity("IfcPersonAndOrganization", person,
                                                                                  organization)  # 组织和人员合并
        return ifc_person_and_organization

    def create_OwnerHistory(self, person_and_organization: Optional[entity_instance] = None,
                            application: Optional[entity_instance] = None) -> Optional[entity_instance]:
        owner_history: Optional[entity_instance] = None
        if person_and_organization is None:
            ifc_person_organizations: List = self.ifcfile.by_type("IfcPersonAndOrganization")
            if ifc_person_organizations:
                person_and_organization = ifc_person_organizations[-1]
            else:
                logger.warning(f"项目文件中未能找到IfcPersonAndOrganization")
        if application is None:
            ifc_applications: List[entity_instance] = self.ifcfile.by_type("IfcApplication")
            if ifc_applications:
                application = ifc_applications[-1]
            else:
                logger.warning(f"项目文件中未能找到IfcApplication")
        if person_and_organization and application:
            while True:
                owner_history = self.ifcfile.create_entity("IfcOwnerHistory",
                                                           person_and_organization,
                                                           application,
                                                           None,
                                                           "ADDED",
                                                           None,
                                                           person_and_organization,
                                                           application,
                                                           int(time.time()))
                if owner_history.get_info().get("id") == 0:
                    warnings.warn(
                        f"产生的history为0,{owner_history.get_info()},"
                        f"application:{application.get_info()},"
                        f"person_and_organization:{person_and_organization.get_info()}")
                else:
                    break
        else:
            logger.warning(f"未能成功寻找到IfcPersonAndOrganization或IfcApplication")
        return owner_history

    def create_ExtrudedAreaSolid(self, points: List = None, ifcaxis2placement: entity_instance = None,
                                 extrude_direction: List = None, extrude_length: float = None) -> entity_instance:
        # 局部坐标系中的拉伸方向
        ifc_direction = self.ifcfile.create_entity("IfcDirection", extrude_direction)
        ifc_points = []
        for point in points:
            point = self.ifcfile.createIfcCartesianPoint(point)
            ifc_points.append(point)
        poly_line = self.ifcfile.createIfcPolyLine(ifc_points)
        ifcclosedprofile = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, poly_line)  # 封闭平面几何
        # 创建拉伸的几何体，局部使用的坐标系是固定的，xyz
        ifc_extrudedareasolid = self.ifcfile.createIfcExtrudedAreaSolid(ifcclosedprofile, ifcaxis2placement,
                                                                        ifc_direction, extrude_length)
        return ifc_extrudedareasolid

    def create_ExtrudedAreaSolidTapered(self, section_1: List = None, ifcaxis2placement: entity_instance = None,
                                        extrude_direction: List = None, extrude_length: float = None,
                                        section_2: List = None, ) -> entity_instance:

        ifc_direction = self.ifcfile.create_entity("IfcDirection", extrude_direction)
        ifc_section_1 = []
        for point in section_1:
            point = self.ifcfile.createIfcCartesianPoint(point)
            ifc_section_1.append(point)
        poly_line_1 = self.ifcfile.createIfcPolyLine(ifc_section_1)
        ifcclosedprofile_1 = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, poly_line_1)  # 封闭平面几何
        ifc_section_2 = []
        for point in section_2:
            point = self.ifcfile.createIfcCartesianPoint(point)
            ifc_section_2.append(point)
        poly_line_2 = self.ifcfile.createIfcPolyLine(ifc_section_2)
        ifcclosedprofile_2 = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, poly_line_2)  # 封闭平面几何
        # 创建拉伸的几何体，局部使用的坐标系是固定的，xyz
        ifc_extrudedareasolid = self.ifcfile.createIfcExtrudedAreaSolidTapered(ifcclosedprofile_1, ifcaxis2placement,
                                                                               ifc_direction, extrude_length,
                                                                               ifcclosedprofile_2)
        return ifc_extrudedareasolid

    def create_SweptDiskSolid(self, rebar: IfcRebarData):
        """
        定义一个通用钢筋的绘制形式
        """
        points_entity_instance = self.ifcfile.create_entity("IfcCartesianPointList3D", rebar.points)
        seg_s_entity_instance = []
        for seg in rebar.seg_s:
            seg_s_entity_instance.append(self.ifcfile.create_entity(seg.seg_type, seg.index_s))
        ifc_indexed_poly_curve = self.ifcfile.create_entity("IfcIndexedPolyCurve", points_entity_instance,
                                                            seg_s_entity_instance)
        solid = self.ifcfile.create_entity(
            "IfcSweptDiskSolid",
            ifc_indexed_poly_curve,
            float(rebar.radius),
            None, None, None)  # InnerRadius 空心圆柱内半径

        return solid

    def create_RevolvedAreaSolid(self, section: List, solid_placement, Axis1Placement, angle=360):
        """
        定义一个圆台，半横截面是多边形
        """
        ifc_points = []
        for point in section:
            point = self.ifcfile.createIfcCartesianPoint(point)
            ifc_points.append(point)
        poly_line = self.ifcfile.createIfcPolyLine(ifc_points)
        ifcclosedprofile = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, poly_line)  # 封闭平面几何
        # 创建拉伸的几何体，局部使用的坐标系是固定的，xyzbeam_placement_2
        solid = self.ifcfile.createIfcRevolvedAreaSolid(ifcclosedprofile, solid_placement,
                                                        Axis1Placement, angle)
        return solid

    def create_SurfaceCurveSweptAreaSolid(self, curve: List, points: List = None,
                                          water_drop_shape=None) -> entity_instance:
        curve_points = []
        for p in curve:
            p = self.ifcfile.createIfcCartesianPoint(p)
            curve_points.append(p)
        ifc_curve = self.ifcfile.createIfcPolyLine(curve_points)

        if water_drop_shape.value == 0:  # TRAPEZOID = 0 SEMICIRCLE = 1
            profile_seg_s = [self.ifcfile.create_entity("IfcLineIndex", [1, 2]),
                             self.ifcfile.create_entity("IfcLineIndex", [2, 3]),
                             self.ifcfile.create_entity("IfcLineIndex", [3, 4]),
                             self.ifcfile.create_entity("IfcLineIndex", [4, 1])]
            points_list = self.ifcfile.create_entity("IfcCartesianPointList2D", points)
            profile = self.ifcfile.createIfcIndexedPolyCurve(points_list, profile_seg_s)
            ifc_closedprofile = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, profile)  # 封闭平面几何
        else:
            profile_seg_s = [self.ifcfile.create_entity("IfcArcIndex", [1, 2, 3]),
                             self.ifcfile.create_entity("IfcLineIndex", [3, 1])]
            points_list = self.ifcfile.create_entity("IfcCartesianPointList2D", points)
            profile = self.ifcfile.createIfcIndexedPolyCurve(points_list, profile_seg_s)

            ifc_closedprofile = self.ifcfile.createIfcArbitraryClosedProfileDef("AREA", None, profile)  # 封闭平面几何
        # placement = self.create_IfcAxis2Placement3D(z=[0., 0., -1.], x=[0., 1., 0.])
        ifc_surface = self.ifcfile.createIfcPlane(self.global_placement)
        # 创建截面沿曲线拉伸
        solid = self.ifcfile.createIfcSurfaceCurveSweptAreaSolid(ifc_closedprofile,
                                                                 self.global_placement,
                                                                 ifc_curve,
                                                                 None,
                                                                 None,
                                                                 ifc_surface)
        return solid

    def create_rebar(self, shear_wall_placement, rebar: IfcRebarData, name: str = "钢筋"):
        """
        通用的钢筋绘制函数
        :param rebar_data:
        :param name:
        :return:
        """

        solid = self.create_SweptDiskSolid(rebar)
        representation = self.ifcfile.createIfcShapeRepresentation(self.global_geometry_context, "Body", "SweptSolid",
                                                                   [solid])

        rebar_shape = self.ifcfile.createIfcProductDefinitionShape(None, None, [representation])
        local_placement = self.ifcfile.createIfcLocalPlacement(shear_wall_placement, self.global_placement)
        instance_show = self.ifcfile.create_entity("IfcReinforcingBar",
                                                   self.get_global_id(),
                                                   self.owner_history,
                                                   name,
                                                   None,
                                                   None,
                                                   local_placement,
                                                   rebar_shape,
                                                   None)

        return instance_show

    def create_truss_rebars(self, shear_wall_placement, truss_rebars: TrussRebarforBIM, shear_wall_data: ShearWallData,
                            shear_wall, building_storey,name: str = "桁架筋"):
        """
        通用的钢筋绘制函数
        :param shear_wall_data:
        :param name:
        :return:
        """
        truss_rebar_name = shear_wall_data.detailed_design.truss_detailed.material_name  # 钢筋强度等级 无量纲
        truss_rebar_parameter = RebarParameter.by_name(truss_rebar_name)  # 钢筋参数-类
        truss_rebar_steel_name = truss_rebar_parameter.name
        truss_rebar_steel_material = self.ifcfile.createIfcMaterial(truss_rebar_steel_name, None, "Steel")  # 桁架材质
        truss_rebars_ifc = []
        for i in range(len(truss_rebars.truss_rebars)):
            #  单个桁架筋
            representations = []
            for attr, value in truss_rebars.truss_rebars[i].__dict__.items():

                new_rebar = rebar_arc(value, truss_rebar_parameter.grade)
                solid = self.create_SweptDiskSolid(new_rebar)
                representation = self.ifcfile.createIfcShapeRepresentation(self.global_geometry_context, "Body",
                                                                           "SweptSolid",
                                                                           [solid])
                representations.append(representation)
            rebar_shape = self.ifcfile.createIfcProductDefinitionShape(None, None, representations)
            local_placement = self.ifcfile.createIfcLocalPlacement(shear_wall_placement, self.global_placement)
            instance_show = self.ifcfile.create_entity("IfcReinforcingBar",
                                                       self.get_global_id(),
                                                       self.owner_history,
                                                       name,
                                                       None,
                                                       None,
                                                       local_placement,
                                                       rebar_shape,
                                                       None)
            truss_rebars_ifc.append(instance_show)

        entity_instance_write = self.ifcfile.createIfcRelContainedInSpatialStructure(
            self.get_global_id(),
            self.owner_history,
            "Building Storey Container",
            None,
            truss_rebars_ifc,
            building_storey)

        self.ifcfile.createIfcRelAssociatesMaterial(self.get_global_id(), self._owner_history,
                                                       None, None,
                                                       RelatedObjects=truss_rebars_ifc,
                                                       RelatingMaterial=truss_rebar_steel_material)
        rel_aggregate = self.ifcfile.createIfcRelAggregates(
            self.get_global_id(),
            self.owner_history,
            "Shear_wall Container",
            None,
            shear_wall,
            truss_rebars_ifc)  #
        return truss_rebars_ifc
