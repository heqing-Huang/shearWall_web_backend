import ast
import logging
import traceback
from collections import OrderedDict
from dataclasses import asdict, dataclass
from typing import Optional, Dict, Callable

from rest_framework import serializers

from DoubleWallDesign.models import (
    LiftingInsertsDesignMode,
    OtherInserts,
    RebarDesignMode,
    SupportInsertsDesignMode,
    CastInsertsDesignMode,
    WallHole,
    WallHoleType,
    DistributedBar,
    LiftingBar,
    DetailedDesignResult,
    WallLengthType,
    ShearWallType,
    TrussRebarMode,
    CircleHole,
    RectangleHole,
)

from design import exchange
from design.exchange.tools import custom_asdict_contain_enum
from design.models import (
    DetailDataCopyChangeWrite,
    WallDetailedData,
    WallDetailedResult,
)

import traceback

_logger = logging.getLogger(__name__)


class _ShearWallIDSerializer(serializers.ModelSerializer):
    """
        该序列化,特用于向下层楼梯结构计算数据作转换,变量名为适应下层变化,不要轻易变动
        """

    project_ID = serializers.CharField(source="project_num")
    shear_wall_ID = serializers.CharField(source="shear_wall_num")

    class Meta:
        model = WallDetailedData
        # 不可修改,对应下层 stairID 内部属性的奇葩命名,应该用驼峰命名
        fields = [
            "project_ID",
            "shear_wall_ID",
        ]

class _MaterialSerializer(serializers.ModelSerializer):
    """
    用于从 django-orm 转换至下层结构计算的 dataclass对应的key-value参数
    """
    class Meta:
        model = WallDetailedData
        fields = [
            "rebar_name",
            "concrete_grade",
        ]
        read_only_fields = fields

class _StructureSerializer(serializers.ModelSerializer):
    """
    构造相关词参数序列导出,用于顶层构件结构深化设计时的组合数据
    """
    concrete_cover_thickness = serializers.IntegerField(
        source="protective_layer_thickness"
    )
    class Meta:
        model = WallDetailedData
        fields = [
            "concrete_cover_thickness",
        ]
        read_only_fields = fields

class _RectangleWallHoleSerializer(serializers.ModelSerializer):
    hole_height = serializers.IntegerField(source="rectangle_hole_height")
    hole_length = serializers.IntegerField(source="rectangle_hole_length")
    hole_horizontal = serializers.IntegerField(source="rectangle_hole_horizontal")
    hole_vertical = serializers.IntegerField(source="rectangle_hole_vertical")
    class Meta:
        model = WallDetailedData
        fields = [
            "hole_height",
            "hole_length",
            "hole_horizontal",
            "hole_vertical",
        ]

class _CircleWallHoleSerializer(serializers.ModelSerializer):
    hole_diameter = serializers.IntegerField(source="circle_hole_diameter")
    hole_horizontal = serializers.IntegerField(source="circle_hole_horizontal")
    hole_vertical = serializers.IntegerField(source="circle_hole_vertical")
    class Meta:
        model = WallDetailedData
        fields = [
            "hole_diameter",
            "hole_horizontal",
            "hole_vertical",
        ]

_SERIALIZER_RECTANGLE_WALL_HOLE = _RectangleWallHoleSerializer
_SERIALIZER_CIRCLE_WALL_HOLE = _CircleWallHoleSerializer

class _DetailData2RebarDiamSpaceSerializer(serializers.ModelSerializer):
    def __init__(self, head, *args, **kwargs):
        self.head = head
        super(_DetailData2RebarDiamSpaceSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = WallDetailedData
        fields = [
            "diameter",
            "spacing",
        ]

    def get_fields(self):
        fields = OrderedDict()
        fields["diameter"] = serializers.IntegerField(source=f"{self.head}_diameter")
        fields["spacing"] = serializers.IntegerField(source=f"{self.head}_spacing")
        return fields

class _DetailData2RebarDiamSerializer(serializers.ModelSerializer):
    head: str

    def __init__(self, head, *args, **kwargs):
        self.head = head
        super(_DetailData2RebarDiamSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = WallDetailedData
        fields = [
            "diameter",
        ]

    def get_fields(self):
        fields = OrderedDict()
        fields["diameter"] = serializers.IntegerField(source=f"{self.head}_diameter")
        return fields




class _LiftingInsertsPositionSerializer(serializers.ModelSerializer):
    x1 = serializers.IntegerField(source="lifting_inserts_position_x1")
    x2 = serializers.IntegerField(source="lifting_inserts_position_x2")
    class Meta:
        model = WallDetailedData
        fields = ["x1", "x2"]

class _SupportInsertsPositionSerializer(serializers.ModelSerializer):
    x1 = serializers.IntegerField(source="support_inserts_position_x1")
    x2 = serializers.IntegerField(source="support_inserts_position_x2")
    y1 = serializers.IntegerField(source="support_inserts_position_y1")
    y2 = serializers.IntegerField(source="support_inserts_position_y2")
    class Meta:
        model = WallDetailedData
        fields = ["x1", "x2", "y1", "y2"]

class _CastInsertsNumberSerializer(serializers.ModelSerializer):
    left_number = serializers.IntegerField(source="cast_inserts_left_number")
    right_number = serializers.IntegerField(source="cast_inserts_right_number")
    top_number = serializers.IntegerField(source="cast_inserts_top_number")
    bottom_number = serializers.IntegerField(source="cast_inserts_bottom_number")
    class Meta:
        model = WallDetailedData
        fields = [
            "left_number",
            "right_number",
            "top_number",
            "bottom_number",
        ]

class _TrussMaterialSerializer(serializers.ModelSerializer):
    """
    用于从 django-orm 转换至下层结构计算的 dataclass对应的key-value参数

    """
    class Meta:
        model = WallDetailedData
        fields = [
            "rebar_name",
        ]
        read_only_fields = fields


class _RebarDetailedSerializer(serializers.ModelSerializer):
    horizontal_rebars = serializers.SerializerMethodField()
    vertical_rebars = serializers.SerializerMethodField()

    horizontal_rebars_ratio = serializers.FloatField()
    vertical_rebars_ratio = serializers.FloatField()

    def get_horizontal_rebars(self, obj):
        if obj.rebar_design_mode == RebarDesignMode.MANUAL.value:
            return _DetailData2RebarDiamSpaceSerializer(
                head="horizontal_rebar", instance=obj
            ).data

    def get_vertical_rebars(self, obj):
        if obj.rebar_design_mode == RebarDesignMode.MANUAL.value:
            return _DetailData2RebarDiamSpaceSerializer(
                head="vertical_rebar", instance=obj
            ).data

    class Meta:
        model = WallDetailedData
        fields = [
            "rebar_design_mode",
            "horizontal_rebars",
            "vertical_rebars",
            "horizontal_rebars_ratio",
            "vertical_rebars_ratio",
        ]

class _GeometricDetailedSerializer(serializers.ModelSerializer):
    wall_hole_parameter = serializers.SerializerMethodField()

    def get_wall_hole_parameter(self, obj: WallDetailedData):
        if obj.wall_hole == WallHole.YES.value:
            if obj.wall_hole_type == WallHoleType.RECTANGLE.value:
                return _SERIALIZER_RECTANGLE_WALL_HOLE(obj).data
            else:
                return _SERIALIZER_CIRCLE_WALL_HOLE(obj).data

    class Meta:
        model = WallDetailedData
        fields = [
            "shear_wall_type",
            "wall_length_type",

            "length",
            "thickness",
            "height",
            "interior_thickness",
            "exterior_thickness",
            "bottom_gap_height",
            "top_gap_height",
            "left_gap_length",
            "right_gap_length",

            "wall_hole",
            "wall_hole_type",

            "wall_hole_parameter",
        ]

class _InsertsDetailedSerializer(serializers.ModelSerializer):
    # 吊装预埋件
    lifting_inserts_design_mode = serializers.IntegerField()
    lifting_inserts_diameter = serializers.IntegerField()
    lifting_inserts_position = serializers.SerializerMethodField()

    def get_lifting_inserts_position(self, obj: WallDetailedData):
        if obj.lifting_inserts_design_mode == LiftingInsertsDesignMode.MANUAL.value:
            return _LiftingInsertsPositionSerializer(obj).data

    # 支撑预埋件
    support_inserts_design_mode = serializers.IntegerField()
    support_inserts_parameter = serializers.IntegerField(source="support_inserts_hole_diameter")
    support_inserts_position = serializers.SerializerMethodField()

    def get_support_inserts_position(self, obj: WallDetailedData):
        if obj.support_inserts_design_mode == SupportInsertsDesignMode.MANUAL.value:
            return _SupportInsertsPositionSerializer(obj).data

    # ???预埋件
    cast_inserts_design_mode = serializers.IntegerField()
    cast_inserts_number = serializers.SerializerMethodField()

    def get_cast_inserts_number(self, obj: WallDetailedData):
        if obj.cast_inserts_design_mode == CastInsertsDesignMode.MANUAL.value:
            return _CastInsertsNumberSerializer(obj).data

    # 其他预埋件
    other_inserts = serializers.IntegerField()
    other_inserts_number = serializers.IntegerField()
    other_inserts_parameters = serializers.SerializerMethodField()
    other_inserts_positions = serializers.SerializerMethodField()

    def get_other_inserts_parameters(self, obj: WallDetailedData):
        try:
            results = list(map(int, obj.other_inserts_parameters.split(",")))
        except Exception as e:
            _logger.error(f"{e}, data: {obj.other_inserts_parameters}")
            results = []
        return results

    def get_other_inserts_positions(self, obj: WallDetailedData):
        try:
            results_middle = f"[{obj.other_inserts_positions}]"
            results = ast.literal_eval(results_middle)
        except Exception as e:
            _logger.error(f"{e}, data: {obj.other_inserts_positions}")
            results = []
        return results

    class Meta:
        model = WallDetailedData
        fields = [
            "lifting_inserts_design_mode",
            "lifting_inserts_diameter",
            "lifting_inserts_position",
            "support_inserts_design_mode",
            "support_inserts_parameter",
            "support_inserts_position",
            "cast_inserts_design_mode",
            "cast_inserts_number",
            "other_inserts",
            "other_inserts_number",
            "other_inserts_parameters",
            "other_inserts_positions",
        ]

class _TrussDetailedSerializer(serializers.ModelSerializer):
    truss_rebar_mode = serializers.IntegerField()

    distributed_rebar = serializers.IntegerField()
    lifting_rebar = serializers.IntegerField()

    truss_number = serializers.IntegerField()

    height = serializers.IntegerField(source="truss_height")
    width = serializers.IntegerField(source="truss_width")

    material_name = serializers.SerializerMethodField()

    def get_material_name(self, obj: WallDetailedData):
        return _TrussMaterialSerializer(instance=obj).data

    top_rebar = serializers.SerializerMethodField()
    bottom_rebar = serializers.SerializerMethodField()
    diagonal_rebar = serializers.SerializerMethodField()

    def get_top_rebar(self, obj: WallDetailedData):
        if obj.truss_rebar_mode == TrussRebarMode.MANUAL.value:
            return _DetailData2RebarDiamSerializer(
                head="truss_top_rebar", instance=obj
            ).data

    def get_bottom_rebar(self, obj: WallDetailedData):
        if obj.truss_rebar_mode == TrussRebarMode.MANUAL.value:
            return _DetailData2RebarDiamSerializer(
                head="truss_bottom_rebar", instance=obj
            ).data

    def get_diagonal_rebar(self, obj: WallDetailedData):
        if obj.truss_rebar_mode == TrussRebarMode.MANUAL.value:
            return _DetailData2RebarDiamSpaceSerializer(
                head="diagonal_rebar", instance=obj
            ).data

    class Meta:
        model = WallDetailedData
        fields = [
            "truss_rebar_mode",
            "distributed_rebar",
            "lifting_rebar",
            "height",
            "width",
            "truss_number",
            "material_name",
            "top_rebar",
            "bottom_rebar",
            "diagonal_rebar",
        ]


class DetailedDataSerializer(serializers.ModelSerializer):
    """
        该序列化仅需要完成内部表结构到外层dataclass的转换,不需要考虑反向存储
    """
    shear_wall_id = serializers.SerializerMethodField()
    material = serializers.SerializerMethodField()
    construction_detailed = serializers.SerializerMethodField()

    def get_shear_wall_id(self, obj: WallDetailedData):
        return dict(_ShearWallIDSerializer(obj).data)

    def get_material(self, obj: WallDetailedData):
        return dict(_MaterialSerializer(instance=obj).data)

    def get_construction_detailed(self, obj: WallDetailedData):
        return dict(_StructureSerializer(instance=obj).data)

    rebar_detailed = serializers.SerializerMethodField()
    geometric_detailed = serializers.SerializerMethodField()
    inserts_detailed = serializers.SerializerMethodField()
    truss_detailed = serializers.SerializerMethodField()

    def get_rebar_detailed(self, obj: WallDetailedData):
        return _RebarDetailedSerializer(instance=obj).data

    def get_geometric_detailed(self, obj: WallDetailedData):
        return _GeometricDetailedSerializer(instance=obj).data

    def get_inserts_detailed(self, obj: WallDetailedData):
        return _InsertsDetailedSerializer(instance=obj).data

    def get_truss_detailed(self, obj: WallDetailedData):
        return _TrussDetailedSerializer(instance=obj).data


    class Meta:
        model = WallDetailedData
        fields = [
            "shear_wall_id",
            "material",
            "construction_detailed",
            "geometric_detailed",
            "rebar_detailed",
            "truss_detailed",
            "inserts_detailed",
        ]



class SerializerBtnDesignResultCopyWrite(serializers.ModelSerializer):
    """
    完成复制出来的参数的插入和导出——双向
    """
    class Meta:
        model = DetailDataCopyChangeWrite
        fields = ["content"]
