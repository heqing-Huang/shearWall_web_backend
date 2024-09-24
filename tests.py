import unittest
import logging
from unittest import TestCase

from DigitalDesign.create_bvbs import create_bvbs
from DoubleWallDesign.detailed_design import detailed_design
from DigitalDesign.shear_wall_ifc import shear_wall_IFC_creation
from DigitalDesign.shear_wall_pxml import shear_wall_pxml_creation

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

from DoubleWallDesign.models import DetailedDesign, ShearWallType, ShearWallID, GeometricDetailed, Material, \
    ConstructionDetailed, RebarDesignMode, RebarDetailed, RebarDiamSpac, WallHoleType, WallLengthType, TrussDetailed, \
    RebarDiam, TrussRebarMode, DistributedBar, WallHole, RectangleHole, InsertsDetailed, LiftingInsertsPosition, \
    SupportInsertsPosition, LiftingInsertsDesignMode, SupportInsertsDesignMode, CastInsertsDesignMode, \
    OtherInserts, CastInsertsNumber
# 出图模块内容
import ezdxf
import ifcopenshell
from GenerateDrawing.generate_occ_data import OCCData,generate_double_wall_geometry
from GenerateDrawing.occ_model import BuildOCCSolid

from OCC.Display.SimpleGui import init_display
from OCC.Display.OCCViewer import rgb_color
from DoubleWallDesign.geometry import DoubleSideWall
from GenerateDrawing.model_data import DoubleShearWallViewData
from GenerateDrawing.total_detail_view import DoubleShearWallTotalView

'''
5安装就位后，应按专项施工方 案要求设置斜支撑，斜支撑上 部与叶板、底部与楼板应可靠连接。
上部斜支撑宜设置 2道，斜支 撑与水平地面的夹角宜为 45。~60。上支撑点与板底的距离不宜小 于构件高度的2/3，且不应小于构件高度的1/2;

开洞双面叠合墙板洞口两侧墙体宽度不宜小于 200mm
洞口下方墙体高度不宜小于 150mm ，洞口上方墙体高度不宜小
200mm

'''


class TestCall(TestCase):
    def test_call_(self):
        """
        尝试自定义初始化数据,并尝试进行第三方调用测试
        :return:
        """

        shear_wall_id = ShearWallID(project_ID='CZ1', shear_wall_ID='WSPQ-1928-12')

        material = Material(
            rebar_name="HRB400",
            concrete_grade=60,
        )
        construction_detailed = ConstructionDetailed(
            concrete_cover_thickness=15
        )  # 有默认值
        geometric_detailed = GeometricDetailed(
            shear_wall_type=ShearWallType.EXTERIOR,
            length=1950,
            height=2800,
            thickness=250,
            interior_thickness=50,
            exterior_thickness=50,
            bottom_gap_height=50,
            top_gap_height=160,
            wall_length_type=WallLengthType.NO,     # 内墙短
            left_gap_length=0,
            right_gap_length=0,
            wall_hole=WallHole.YES,
            wall_hole_type=WallHoleType.RECTANGLE,
            wall_hole_parameter=RectangleHole(hole_height=200,
                                              hole_length=200,
                                              hole_horizontal=1000,
                                              hole_vertical=1400),
        )
        rebar_detailed = RebarDetailed(
            rebar_design_mode=RebarDesignMode.MANUAL,
            horizontal_rebars=[RebarDiamSpac(diameter=8, spacing=200), RebarDiamSpac(diameter=10, spacing=200)],
            vertical_rebars=[RebarDiamSpac(diameter=8, spacing=200), RebarDiamSpac(diameter=10, spacing=200)],
            horizontal_rebars_ratio=0.3,
            vertical_rebars_ratio=0.3)

        truss_detailed = TrussDetailed(
            truss_rebar_mode=TrussRebarMode.MANUAL,
            distributed_bar=DistributedBar.NO,
            lifting_bar=DistributedBar.NO,
            material_name='HPB300',
            top_rebar=RebarDiam(diameter=10),
            bottom_rebar=RebarDiam(diameter=8),
            diagonal_rebar=RebarDiamSpac(diameter=6, spacing=200),
            height=200,
            width=100,
            truss_number=6,
        )
        inserts_detailed = InsertsDetailed(lifting_inserts_design_mode=LiftingInsertsDesignMode.MANUAL,
                                           support_inserts_design_mode=SupportInsertsDesignMode.MANUAL,
                                           cast_inserts_design_mode=CastInsertsDesignMode.MANUAL,
                                           cast_inserts_number=CastInsertsNumber(left_number=6, right_number=6,
                                                                                 top_number=0, bottom_number=0),
                                           other_inserts=OtherInserts.YES, lifting_inserts_diameter=16,
                                           lifting_inserts_position=LiftingInsertsPosition(x1=412, x2=1560),
                                           support_inserts_parameter=30,
                                           support_inserts_position=SupportInsertsPosition(x1=350, x2=1600, y1=150,
                                                                                           y2=2000),
                                           other_inserts_number=1, other_inserts_parameters=[10],
                                           other_inserts_positions=[[350, 150]])
        detailed_parameter = DetailedDesign(
            shear_wall_id=shear_wall_id,
            material=material,
            construction_detailed=construction_detailed,
            geometric_detailed=geometric_detailed,
            rebar_detailed=rebar_detailed,
            truss_detailed=truss_detailed,
            inserts_detailed=inserts_detailed)
        data_back_detailed, rebar_for_BIM, rebar_for_BVBS, truss_rebar_for_BIM, shear_wall_data = detailed_design(
            detailed_parameter)

        ifc_doc = shear_wall_IFC_creation(rebar_for_BIM, truss_rebar_for_BIM, shear_wall_data)
        create_bvbs(ifc_doc, rebar_for_BVBS, shear_wall_data) # 生成bvbs数据
        shear_wall_pxml_creation(ifc_doc, rebar_for_BIM, shear_wall_data)

        # 开始获取数字化信息
        # Step 1: 加载IFC数据文件
        ifc_file = ifc_doc.ifcfile
        # Step 2: 获取实体信息
        entity_type = ["IfcStair", "IfcReinforcingBar", "IfcReinforcingBar"]  # 实体名称
        object_name = ["钢筋", "桁架筋"]  # 对象名称
        double_wall_geo = DoubleSideWall()
        double_wall_geo = generate_double_wall_geometry(ifc_file,entity_type[0],double_wall_geo)
        # Step 3: 创建OCCData数据
        occ_data = OCCData(ifc_file, double_wall_geo)
        # 获取桁架钢筋信息
        truss_result = occ_data.get_ifc_truss_rebar(entity_type[2], object_name[1])
        print("truss_result:", truss_result)
        # Step 4: 可视化OCC模型
        occ_model = BuildOCCSolid(ifc_file, entity_type, object_name, occ_data)
        # Step 5: 获取模型数据
        model_transform_data = DoubleShearWallViewData(double_wall_geo, entity_type, object_name, occ_model, occ_data)
        # Step 6: 模型变换数据
        file_name = "tmp/double_shear_wall_template.dxf"
        dxf_doc = ezdxf.readfile(file_name)
        detail_drawing = DoubleShearWallTotalView(dxf_doc, model_transform_data)
        detail_drawing.main_run_process()


def begin_double_shear_wall_design_information(file_name):
    """
    提取剪力墙设计信息
    """
    from InformationExtract.extract_dxf_data import extract_double_shear_wall_design_information,extract_shear_wall_design_information,\
        extract_beam_design_information,extract_floor_design_information
    double_shear_wall_information = extract_double_shear_wall_design_information(file_name)
    total_shear_wall_information = extract_shear_wall_design_information(file_name)
    total_beam_information = extract_beam_design_information(file_name)
    total_floor_information = extract_floor_design_information(file_name)

    # print("double_shear_wall_information:\n", double_shear_wall_information)
    # print("total_shear_wall_information:\n", total_shear_wall_information)
    # print("total_beam_information:\n", total_beam_information)
    # print("total_floor_information:\n", total_floor_information)


if __name__ == "__main__":
    # unittest.main()
    file_name = "Files/double_shear_wall_template.dxf"
    begin_double_shear_wall_design_information(file_name)