"""
# File       : models.py
# Time       ：2022/9/19 18:45
# Author     ：CR_X
# version    ：python 3.6
# Description：
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Union
from dc_rebar import Rebar
from DoubleWallDesign.config import CONCRETE_CONFIG_DICT, REBAR_GRADE_CONFIG, REBAR_NAME_CONFIG


class LiftingInsertsDesignMode(Enum):
    """
    吊装预埋件设计模式枚举
    """
    AUTOMATIC = 0
    MANUAL = 1


class OtherInserts(Enum):
    """
    是否有其他的预埋件
    """
    NO = 0
    YES = 1


class SupportInsertsDesignMode(Enum):
    """
    支撑预埋件设计模式
    """
    AUTOMATIC = 0
    MANUAL = 1


class CastInsertsDesignMode(Enum):

    AUTOMATIC = 0
    MANUAL = 1


class WallHole(Enum):
    """
    剪力墙洞口枚举
    """
    NO = 0  # 没有洞口
    YES = 1  # 有洞口


class WallHoleType(Enum):
    """
    剪力墙洞口类型枚举
    """
    CIRCLE = 0  # 圆形
    RECTANGLE = 1  # 矩形


class DistributedBar(Enum):
    """
    桁架筋是否作为分布筋
    """
    NO = 0  # 否
    YES = 1  # 是


class LiftingBar(Enum):
    """
    桁架筋是否作为吊装筋
    """
    NO = 0  # 否
    YES = 1  # 是


class WallLengthType(Enum):
    """
    内外墙板是否等长
    """
    NO = 0  # 内墙短
    YES = 1  # 内外等长


class ShearWallType(Enum):
    """
    剪力墙类型枚举
    """
    EXTERIOR = 0  # 外墙
    INTERIOR = 1  # 内墙


class RebarDesignMode(Enum):
    """
    钢筋设计模式枚举
    """
    AUTOMATIC = 0
    MANUAL = 1


class TrussRebarMode(Enum):
    """
    桁架钢筋设计模式枚举
    """
    AUTOMATIC = 0
    MANUAL = 1


@dataclass
class CircleHole:
    """
    圆形洞口属性
    """
    # 洞口直径：
    hole_diameter: Optional[int]
    # 洞口中心点定位（水平）：
    hole_horizontal: Optional[int]
    # 洞口中心点定位（竖向）：
    hole_vertical: Optional[int]


@dataclass
class RectangleHole:
    """
    矩形洞口属性
    """
    # 洞口高度：
    hole_height: Optional[int]
    # 洞口长度：
    hole_length: Optional[int]
    # 洞口中心点定位（水平）：
    hole_horizontal: Optional[int]
    # 洞口中心点定位（竖向）：
    hole_vertical: Optional[int]


@dataclass(frozen=True)     # 不可变的数据类
class ConcreteParameter:
    """
    混凝土详细配置参数获取
    """
    name: str
    f_c: float
    f_t: float
    a_erf: float
    b_ta: float
    f_ck: float
    f_tk: float
    ec: float
    grade: float
    rc: float = 25

    @classmethod
    def by_grade(cls, concrete_grade: int) -> Optional["ConcreteParameter"]:
        """
        根据混凝土强度等级,查找混凝土相关参数
        """
        data = CONCRETE_CONFIG_DICT.get(concrete_grade, None)
        if data is None:
            return data
        else:
            return ConcreteParameter(**data)

@dataclass(frozen=True)
class SteelParameter:
    """
    钢筋强度相关配置
    """
    f_y: int
    f1_y: int
    d_min: int
    d_max: int
    fyk: int
    fstk: int
    es: int

    @classmethod
    def by_grade(cls, rebar_grade: int) -> Optional["SteelParameter"]:
        """
        根据钢筋强度查找钢筋配置
        """
        data: dict = REBAR_GRADE_CONFIG.get(rebar_grade, None)
        if data is None:
            return data
        else:
            return SteelParameter(**data)


@dataclass
class RebarParameter:
    name: str
    grade: int
    symbol: str
    steel: SteelParameter

    @classmethod
    def by_name(cls, name: str) -> Optional["RebarParameter"]:
        name_config: Optional[dict] = REBAR_NAME_CONFIG.get(name, None)
        if name_config is None:
            return None
        steel = SteelParameter.by_grade(name_config["grade"])

        return RebarParameter(name=name, steel=steel, **name_config)


@dataclass
class ShearWallID:
    # 剪力墙的编号
    project_ID: str
    shear_wall_ID: str


@dataclass
class ConstructionDetailed:
    """
    构造相关
    """
    # 保护层厚度,单位毫米
    concrete_cover_thickness: int = field(default=15)


@dataclass
class Material:
    """
    材质相关的设置
    """
    # 钢筋等级
    rebar_name: str
    # 混凝土等级,对应C30 等
    concrete_grade: int = field(default=30)

    def __post_init__(self):
        assert self.concrete_grade in [30, 35, 40, 45, 50, 60], Exception(f"混凝土等级异常:{self.concrete_grade}")


@dataclass
class GeometricDetailed:
    """
    几何参数,可以用于唯一确定剪力墙几何外形
    长度单位均为毫米
    """
    # 剪力墙类型
    shear_wall_type: ShearWallType
    # 剪力墙长度
    length: int
    # 剪力墙总厚度
    thickness: int
    # 剪力墙总高度
    height: int
    # 内页厚度
    interior_thickness: int
    # 外页厚度
    exterior_thickness: int
    # 底部间隙
    bottom_gap_height: int
    # 顶部间隙
    top_gap_height: int
    # 内外面板是否等长
    wall_length_type: WallLengthType
    # 内板左侧短的长度
    left_gap_length: int
    # 内板右侧短的长度
    right_gap_length: int
    # 是否有孔洞
    wall_hole: WallHole
    # 孔洞类型
    wall_hole_type: WallHoleType
    # 孔洞参数
    wall_hole_parameter: Union[CircleHole, RectangleHole]

    def __post_converter__(self):
        if self.wall_hole == WallHole.YES:  # 是否有孔洞
            # 孔洞信息
            assert self.wall_hole_type is not None, Exception(f"wall_hole_type 不能为空")
            if isinstance(self.wall_hole_type, dict):  # 兼容
                if self.wall_hole_type == WallHoleType.CIRCLE:
                    if isinstance(self.wall_hole_parameter, dict):
                        self.wall_hole_parameter = CircleHole(**self.wall_hole_parameter)
                elif self.wall_hole_type == WallHoleType.RECTANGLE:
                    if isinstance(self.wall_hole_parameter, dict):
                        self.wall_hole_parameter = RectangleHole(**self.wall_hole_parameter)
            if not isinstance(self.wall_hole_parameter, CircleHole) and not isinstance(
                    self.wall_hole_parameter, RectangleHole):
                raise Exception(f"wall_hole_parameter 数据异常:{self.wall_hole_parameter}")


@dataclass
class RebarDiamSpac(object):
    """
    钢筋基本信息：直径，间距
    """
    diameter: int  # 钢筋的直径
    spacing: int  # 钢筋的间距


@dataclass
class RebarDiam(object):
    """
    钢筋基本信息：直径
    """
    diameter: int  # 钢筋的直径


@dataclass
class RebarDetailed:
    """
    深化设计钢筋设计各类钢筋的直径和间距计算类，后期可在此类中增加判断逻辑,也可以增加钢筋边距要求。
    深化钢筋名称及对应编号：
    """

    # 0 代表自动计算,1 代表手动输入
    rebar_design_mode: RebarDesignMode = RebarDesignMode.AUTOMATIC
    # 手动输入需要的参数
    horizontal_rebars: List[RebarDiamSpac] = None  # 水平钢筋的直径和间距
    vertical_rebars: List[RebarDiamSpac] = None  # 竖向钢筋的直径和间距
    horizontal_rebars_ratio: Optional[float] = None  # 水平钢筋的配筋率
    vertical_rebars_ratio: Optional[float] = None  # 竖向钢筋的配筋率

    def __post_converter__(self):
        if isinstance(self.rebar_design_mode, int):
            self.rebar_design_mode: int
            self.rebar_design_mode = RebarDesignMode(self.rebar_design_mode)
        assert isinstance(self.rebar_design_mode, RebarDesignMode), Exception(f"rebar_design_mode 传入类型错误")

        if self.rebar_design_mode == RebarDesignMode.AUTOMATIC:
            assert self.horizontal_rebars_ratio is not None, Exception(
                f"horizontal_rebars_radio 不能为空")
            if isinstance(self.horizontal_rebars_ratio, dict):
                self.horizontal_rebars_ratio: dict
                self.horizontal_rebars_ratio = float(**self.horizontal_rebars_ratio)
            if not isinstance(self.horizontal_rebars_ratio, float):
                raise Exception(f"horizontal_rebars_radio 数据异常:{self.horizontal_rebars_ratio}")
            assert self.vertical_rebars_ratio is not None, Exception(
                f"vertical_rebars_radio 不能为空")
            if isinstance(self.vertical_rebars_ratio, dict):
                self.vertical_rebars_ratio: dict
                self.vertical_rebars_ratio = float(**self.vertical_rebars_ratio)
            if not isinstance(self.vertical_rebars_ratio, float):
                raise Exception(f"vertical_rebars_radio 数据异常:{self.vertical_rebars_ratio}")

        else:
            assert self.horizontal_rebars is not None, Exception(
                f"horizontal_rebars 不能为空")
            if isinstance(self.horizontal_rebars, dict):
                for i in range(len(self.horizontal_rebars)):
                    self.horizontal_rebars[i]: dict
                    self.horizontal_rebars[i] = RebarDiamSpac(**self.horizontal_rebars[i])
                    if not isinstance(self.horizontal_rebars[i], RebarDiamSpac):
                        raise Exception(f"horizontal_rebars 数据异常:{self.horizontal_rebars}")
            assert self.vertical_rebars is not None, Exception(
                f"vertical_rebar 不能为空")
            if isinstance(self.vertical_rebars, dict):
                for i in range(len(self.vertical_rebars)):
                    self.vertical_rebars[i]: dict
                    self.vertical_rebars[i] = RebarDiamSpac(**self.vertical_rebars[i])
                    if not isinstance(self.vertical_rebars[i], RebarDiamSpac):
                        raise Exception(f"vertical_rebars 数据异常:{self.vertical_rebars}")


@dataclass
class CastInsertsNumber:
    left_number: int
    right_number: int
    top_number: int
    bottom_number: int


@dataclass
class SupportInsertsPosition:
    """
    安装预埋件定位信息
    """
    x1: int  # 距左边界位置
    x2: int  # 距右边界位置
    y1: int  # 距下边界位置
    y2: int  # 距上边界位置


@dataclass
class LiftingInsertsPosition:
    """
    吊装预埋件定位信息
    """
    x1: int  # 左吊装预埋件距左边界位置
    x2: int  # 右吊装预埋件距右边界位置


@dataclass
class CommonInserts:
    inserts_number: int  # 普通预埋件的数量
    inserts_diameter: List[int]  # 普通预埋件的直径尺寸列表[10,15,20]
    inserts_positions: List[List[int]]  # 距离墙左边，下边距离


@dataclass
class InsertsDetailed:
    """
    预埋件设计的参数输入
    """
    lifting_inserts_design_mode: LiftingInsertsDesignMode = LiftingInsertsDesignMode.MANUAL  # automatic为掉装自动计算，manual为手动输入，默认为自动计算
    support_inserts_design_mode: SupportInsertsDesignMode = SupportInsertsDesignMode.MANUAL  # automatic自动计算，manual手动输入
    cast_inserts_design_mode: CastInsertsDesignMode = CastInsertsDesignMode.MANUAL  # automatic自动计算，manual手动输入
    cast_inserts_number: Optional[CastInsertsNumber] = None
    other_inserts: OtherInserts = OtherInserts.NO  # 是否有其他的预埋件
    lifting_inserts_diameter: Optional[int] = 16  # 吊装预埋件的直径
    lifting_inserts_position: Optional[LiftingInsertsPosition] = None  # 吊装预埋件的直径
    support_inserts_parameter: Optional[int] = 30  # 安装预埋件孔洞大小
    support_inserts_position: Optional[SupportInsertsPosition] = None
    other_inserts_number: Optional[int] = None
    other_inserts_parameters: Optional[List[int]] = None  # 普通预埋件的直径尺寸列表[10,15,20]
    other_inserts_positions: Optional[List[List[int]]] = None  # 距离墙左边，下边距离

    #     # 吊装预埋件
    #     lifting_type: Optional[LiftingType] = None  # 吊装预埋件类型
    #     lifting_position: Optional[LiftingPosition] = field(converter=LiftingPosition.converter, default=None)  # 吊装预位置参数
    #     lifting_name: Optional[str] = None  # 吊装预埋件规格
    #     # 脱模预埋件
    #     # vertical_horizontal立式浇筑卧式脱模，vertical_vertical立式浇筑立式脱模， horizontal_horizontal卧式浇筑卧式脱模
    #     pouring_way: Optional[PouringWay] = None  # 脱模方式
    #     demolding_type: Optional[DemoldingType] = None  # 脱模类型
    #     demolding_position: Optional[DemoldingPosition] = field(converter=DemoldingPosition.converter,
    #                                                             default=None)  # 脱模预位置参数
    #     demolding_name: Optional[str] = None  # 脱模预埋件规格
    #
    #     # 栏杆预埋件
    #     rail_layout: Optional[RailLayout] = None  # 栏杆预埋件布局
    #     rail_number: Optional[list] = None  # 栏杆预埋件所在的阶数，以底端板为第0阶开始计数
    #     rail_position: Optional[RailPosition] = None  # 栏杆位置
    #     rail_name: Optional[str] = None  # 栏杆预埋件型号
    #

    #         # 埋件设计--吊装预埋件
    #         if isinstance(self.lifting_design_mode, int):
    #             self.lifting_design_mode = LiftingDesignMode(self.lifting_design_mode)
    #         assert isinstance(self.lifting_design_mode, LiftingDesignMode), Exception(f"lifting_design_mode 传入类型错误")
    #
    #         if self.lifting_design_mode == LiftingDesignMode.AUTOMATIC:
    #             self.lifting_type: Optional[LiftingType] = LiftingType.ROUNDING_HEAD  # 吊装预埋件类型
    #         elif self.lifting_design_mode == LiftingDesignMode.MANUAL:
    #             assert self.lifting_type is not None, Exception(f"lifting_type 不能为空")
    #             if isinstance(self.lifting_type, int):
    #                 self.lifting_type = LiftingType(self.lifting_type)
    #             if not isinstance(self.lifting_type, LiftingType):
    #                 raise Exception(f"lifting_type 数据异常:{self.lifting_type}")
    #
    #             assert self.lifting_position is not None, Exception(f"lifting_position 不能为空")
    #             if isinstance(self.lifting_position, dict):
    #                 self.lifting_position = LiftingPosition(**self.lifting_position)
    #             if not isinstance(self.lifting_position, LiftingPosition):
    #                 raise Exception(f"lifting_position 数据异常:{self.lifting_position}")
    #
    #             assert self.lifting_name is not None, Exception(f"lifting_name 不能为空")
    #             if self.lifting_type == LiftingType.ROUNDING_HEAD:
    #                 assert self.lifting_name in ["DJ-13-120", "DJ-20-140", "DJ-25-170", "DJ-30-210",
    #                                              "DJ-75-300"], Exception(f"吊装预埋件名称异常:{self.lifting_name}")
    #             elif self.lifting_type == LiftingType.ANCHOR:
    #                 assert self.lifting_name in ["MS-6-60", "MS-9-60", "MS-12-70", "MS-15-75", "MS-24-80",
    #                                              "MS-36-90", "MS-60-115", "MS-75-120", "MS-120-172"], Exception(
    #                     f"吊装预埋件名称异常:{self.lifting_name}")
    #             if not isinstance(self.lifting_name, str):
    #                 raise Exception(f"lifting_name 数据异常:{self.lifting_name}")

    def __post_converter__(self):
        assert self.other_inserts is not None, Exception(f"other_inserts 不能为空")
        if isinstance(self.other_inserts, int):
            self.other_inserts = OtherInserts(self.other_inserts)
        assert isinstance(self.other_inserts, OtherInserts), Exception(f"other_inserts 传入类型错误")
        if self.other_inserts == OtherInserts.YES:
            assert self.other_inserts_number is not None, Exception(f"other_inserts_number 不能为空")
            if isinstance(self.other_inserts_number, dict):
                self.other_inserts_number: dict
                self.other_inserts_number = int(**self.other_inserts_number)
            assert self.other_inserts_parameters is not None, Exception(f"other_inserts_parameters 不能为空")
            if isinstance(self.other_inserts_parameters, dict):
                self.other_inserts_parameters: dict
                self.other_inserts_parameters = list(**self.other_inserts_parameters)
            assert self.other_inserts_positions is not None, Exception(f"other_inserts_positions 不能为空")
            if isinstance(self.other_inserts_positions, dict):
                self.other_inserts_positions: dict
                self.other_inserts_positions = list(**self.other_inserts_positions)

        assert self.lifting_inserts_design_mode is not None, Exception(f"lifting_design_mode 不能为空")
        if isinstance(self.lifting_inserts_design_mode, int):
            self.lifting_inserts_design_mode = LiftingInsertsDesignMode(self.lifting_inserts_design_mode)
        assert isinstance(self.lifting_inserts_design_mode, LiftingInsertsDesignMode), Exception(
            f"lifting_design_mode 传入类型错误")

        if self.lifting_inserts_design_mode == LiftingInsertsDesignMode.MANUAL:
            assert self.lifting_inserts_diameter is not None, Exception(f"lifting_inserts_diameter 不能为空")
            if isinstance(self.lifting_inserts_diameter, dict):
                self.lifting_inserts_diameter: dict
                self.lifting_inserts_diameter = int(**self.lifting_inserts_diameter)
            assert self.lifting_inserts_position is not None, Exception(f"lifting_inserts_position 不能为空")
            if isinstance(self.lifting_inserts_position, dict):
                self.lifting_inserts_position = LiftingInsertsPosition(**self.lifting_inserts_position)
            if not isinstance(self.lifting_inserts_position, LiftingInsertsPosition):
                raise Exception(f"lifting_inserts_position 数据异常:{self.lifting_inserts_position}")

        elif self.support_inserts_design_mode == SupportInsertsDesignMode.AUTOMATIC:
            pass

        assert self.support_inserts_design_mode is not None, Exception(f"support_design_mode 不能为空")
        if isinstance(self.support_inserts_design_mode, int):
            self.support_inserts_design_mode = SupportInsertsDesignMode(self.support_inserts_design_mode)
        assert isinstance(self.support_inserts_design_mode, SupportInsertsDesignMode), Exception(
            f"support_design_mode 传入类型错误")

        if self.support_inserts_design_mode == SupportInsertsDesignMode.MANUAL:
            assert self.support_inserts_parameter is not None, Exception(f"support_parameter 不能为空")
            if isinstance(self.support_inserts_parameter, dict):
                self.support_inserts_parameter: dict
                self.support_inserts_parameter = int(**self.support_inserts_parameter)
            assert self.support_inserts_position is not None, Exception(f"support_position 不能为空")
            if isinstance(self.support_inserts_position, dict):
                self.support_inserts_position = SupportInsertsPosition(**self.support_inserts_position)
            if not isinstance(self.support_inserts_position, SupportInsertsDesignMode):
                raise Exception(f"support_position 数据异常:{self.support_inserts_position}")

        elif self.support_inserts_design_mode == SupportInsertsDesignMode.AUTOMATIC:
            pass


#         # 埋件设计--脱模预埋件
#         if isinstance(self.demolding_design_mode, int):
#             self.demolding_design_mode = DemoldingDesignMode(self.demolding_design_mode)
#         assert isinstance(self.demolding_design_mode, DemoldingDesignMode), Exception(
#             f"demolding_design_mode 传入类型错误")
#
#         if self.demolding_design_mode == DemoldingDesignMode.AUTOMATIC:
#             self.pouring_way: Optional[PouringWay] = PouringWay.VERTICAL_HORIZONTAL  # 脱模方式
#             self.demolding_type: Optional[DemoldingType] = DemoldingType.ROUNDING_HEAD  # 脱模类型
#         elif self.demolding_design_mode == DemoldingDesignMode.MANUAL:
#             assert self.pouring_way is not None, Exception(f"pouring_way 不能为空")
#             if isinstance(self.pouring_way, int):
#                 self.pouring_way = PouringWay(self.pouring_way)
#             if not isinstance(self.pouring_way, PouringWay):
#                 raise Exception(f"pouring_way 数据异常:{self.pouring_way}")
#
#             assert self.demolding_type is not None, Exception(f"demolding_type 不能为空")
#             if isinstance(self.demolding_type, int):
#                 self.demolding_type = DemoldingType(self.demolding_type)
#             if not isinstance(self.demolding_type, DemoldingType):
#                 raise Exception(f"demolding_type 数据异常:{self.demolding_type}")
#
#             assert self.demolding_position is not None, Exception(f"demolding_position 不能为空")
#             if isinstance(self.demolding_position, dict):
#                 self.demolding_position = DemoldingPosition(**self.demolding_position)
#             if not isinstance(self.demolding_position, DemoldingPosition):
#                 raise Exception(f"demolding_position 数据异常:{self.demolding_position}")
#
#             assert self.demolding_name is not None, Exception(f"demolding_name 不能为空")
#
#             if self.demolding_type == DemoldingType.ROUNDING_HEAD:
#                 assert self.demolding_name in ["DJ-13-120", "DJ-20-140", "DJ-25-170", "DJ-30-210",
#                                                "DJ-75-300"], Exception(f"脱模预埋件名称异常:{self.demolding_name}")
#             elif self.demolding_type == DemoldingType.ANCHOR:
#                 assert self.demolding_name in ["MS-6-60", "MS-9-60", "MS-12-70", "MS-15-75", "MS-24-80",
#                                                "MS-36-90", "MS-60-115", "MS-75-120", "MS-120-172"], Exception(
#                     f"脱模预埋件名称异常:{self.demolding_name}")
#             # elif self.demolding_type == DemoldingType.LIFT_HOOK:
#             #     assert self.demolding_name in ["WDG-6", "WDG-14"], Exception(
#             #         f"脱模预埋件名称异常:{self.demolding_name}")
#             if not isinstance(self.demolding_name, str):
#                 raise Exception(f"demolding_name 数据异常:{self.demolding_name}")


@dataclass
class TrussDetailed:
    """
    深化设计桁架钢筋设计
    """
    # 0 代表自动计算,1 代表手动输入
    truss_rebar_mode: TrussRebarMode = TrussRebarMode.AUTOMATIC  # 设计模式
    distributed_bar: DistributedBar = DistributedBar.NO  # 桁架筋不作为分布筋
    lifting_bar: DistributedBar = DistributedBar.NO  # 桁架筋不作为吊装筋
    # 手动输入需要的参数
    material_name: str = 'HPB300'
    top_rebar: RebarDiam = None  # 上部钢筋直径
    bottom_rebar: RebarDiam = None  # 下部钢筋直径
    diagonal_rebar: RebarDiamSpac = None  # 腹筋钢筋直径和间距
    height: Optional[int] = None  # 桁架高度
    width: Optional[int] = None  # 桁架宽度
    truss_number: int = 2  # 桁架数量

    def __post_converter__(self):
        if isinstance(self.truss_rebar_mode, int):
            self.truss_rebar_mode: int
            self.truss_rebar_mode = TrussRebarMode(self.truss_rebar_mode)
        assert isinstance(self.truss_rebar_mode, TrussRebarMode), Exception(f"truss_rebar_mode 传入类型错误")

        if self.truss_rebar_mode == TrussRebarMode.MANUAL:
            assert self.top_rebar is not None, Exception(
                f"top_rebar 不能为空")
            if isinstance(self.top_rebar, dict):
                self.top_rebar: dict
                self.top_rebar = RebarDiam(**self.top_rebar)
            if not isinstance(self.top_rebar, RebarDiam):
                raise Exception(f"top_rebar 数据异常:{self.top_rebar}")
            assert self.bottom_rebar is not None, Exception(
                f"bottom_rebar 不能为空")
            if isinstance(self.bottom_rebar, dict):
                self.bottom_rebar: dict
                self.bottom_rebar = RebarDiam(**self.bottom_rebar)
            if not isinstance(self.bottom_rebar, RebarDiam):
                raise Exception(f"bottom_rebar 数据异常:{self.bottom_rebar}")
            assert self.diagonal_rebar is not None, Exception(
                f"diagonal_rebar 不能为空")
            if isinstance(self.diagonal_rebar, dict):
                self.diagonal_rebar: dict
                self.diagonal_rebar = RebarDiamSpac(**self.diagonal_rebar)
            if not isinstance(self.diagonal_rebar, RebarDiamSpac):
                raise Exception(f"diagonal_rebar 数据异常:{self.bottom_rebar}")
            assert self.height is not None, Exception(
                f"height 不能为空")
            if isinstance(self.height, dict):
                self.height: dict
                self.height = int(**self.height)
            if not isinstance(self.height, int):
                raise Exception(f"height 数据异常:{self.height}")
            assert self.width is not None, Exception(
                f"width 不能为空")
            if isinstance(self.width, dict):
                self.width: dict
                self.width = int(**self.width)
            if not isinstance(self.width, int):
                raise Exception(f"width 数据异常:{self.width}")
            assert self.truss_number is not None, Exception(
                f"truss_number 不能为空")
            if isinstance(self.truss_number, dict):
                self.truss_number: dict
                self.truss_number = int(**self.truss_number)
            if not isinstance(self.truss_number, int):
                raise Exception(f"truss_number 数据异常:{self.truss_number}")


@dataclass
class DetailedDesign:
    """
    整个深化计算需要传递的参数
    """
    shear_wall_id: ShearWallID
    material: Material
    construction_detailed: ConstructionDetailed
    geometric_detailed: GeometricDetailed
    rebar_detailed: RebarDetailed
    truss_detailed: TrussDetailed
    inserts_detailed: InsertsDetailed

    def __post_init__(self):
        if isinstance(self.construction_detailed, dict):
            self.construction_detailed = ConstructionDetailed(**self.construction_detailed)
        if isinstance(self.geometric_detailed, dict):
            self.geometric_detailed = GeometricDetailed(**self.geometric_detailed)
        if isinstance(self.rebar_detailed, dict):
            self.rebar_detailed = RebarDetailed(**self.rebar_detailed)
        if isinstance(self.truss_detailed, dict):
            self.truss_detailed = TrussDetailed(**self.truss_detailed)
        if isinstance(self.inserts_detailed, dict):
            self.inserts_detailed = InsertsDetailed(**self.inserts_detailed)


@dataclass
class DetailedDesignResult:
    """
    定义深化设计返回的计算结果
    """
    detailed_design: DetailedDesign
    interior_height: int
    exterior_height: int
    left_gap_length: int
    right_gap_length: int
    interior_length: int
    exterior_length: int
    volume: float  # 顶端下边长 mm
    area: float  # 底端下边长 mm
    weight: int  # "计算跨度 mm.
    horizontal_rebars: List[RebarDiamSpac]
    vertical_rebars: List[RebarDiamSpac]

    def __post_init__(self):
        pass
        # if self.h_total == 1:
        #     self.lifting_parameter = 1
        # elif self.h_total == 0:
        #     self.lifting_parameter = 1
        # else:
        #     raise Exception(f"{self.h_total=} 强制类型转换后只会有两种类型")


@dataclass
class RebarGeoBVBS:
    length: float
    angle: float


@dataclass
class RebarBVBS:
    '''
    为bvbs准备的钢筋属性
    '''
    project_ID: str = None
    shear_wall_ID: str = None
    mark: int = None  # 钢筋序号
    rebar_length: int = None  # 钢筋长度
    rebar_quantity: int = None  # 钢筋数量
    rebar_diameter: int = None  # 钢筋直径
    rebar_grade: str = None  # 钢筋等级 使用name
    mandrel_diameter: int = None  # 弯曲直径
    geometric: List[RebarGeoBVBS] = field(default_factory=list)  # 钢筋形状


@dataclass
class RebarforBIM:
    '''
    为生成BIM模型准备的钢筋集合的类
    '''
    horizontal_rebars: List[Rebar] = field(default_factory=list)
    vertical_rebars: List[Rebar] = field(default_factory=list)


@dataclass
class RebarforBVBS():
    '''
    为生成bvbs准备的钢筋集合的类
    '''
    horizontal_rebars: List[RebarBVBS] = field(default_factory=list)
    vertical_rebars: List[RebarBVBS] = field(default_factory=list)


@dataclass
class TrussRebar:
    """
    钢筋定义需要的:
        - 半径
        - 轨迹
        - 材质 [暂不需要]

    """
    top_rebar: Optional[Rebar] = None  # 上部钢筋布置
    bottom_rebar_left: Optional[Rebar] = None  # 下部左边钢筋钢筋布置
    bottom_rebar_right: Optional[Rebar] = None  # 下部右边钢筋布置
    diagonal_rebar_left: Optional[Rebar] = None  # 腹筋左边钢筋布置
    diagonal_rebar_right: Optional[List[float]] = None  # 腹筋右边钢筋布置


@dataclass
class TrussRebarforBIM:
    '''
    为生成BIM模型准备的钢筋集合的类
    '''
    truss_rebars: List[TrussRebar] = field(default_factory=list)