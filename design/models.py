from django.db import models
from django.core.exceptions import ValidationError

from DoubleWallDesign.models import (
    LiftingInsertsDesignMode,
    OtherInserts,
    SupportInsertsDesignMode,
    CastInsertsDesignMode,
    WallHole,
    WallHoleType,
    DistributedBar,
    LiftingBar,
    WallLengthType,
    ShearWallType,
    RebarDesignMode,
    TrussRebarMode,
)

from DoubleWallDesign.config import REBAR_NAME_CONFIG

REBAR_CONFIG_NAME = [[name, name] for name in REBAR_NAME_CONFIG.keys()]

CONCRETE_GRADE = [
    [30, "C30"],
    [35, "C35"],
    [40, "C40"],
    [45, "C45"],
    [50, "C50"],
    [60, "C60"],
]

def get_default_remark_name():
    """
    生成默认项目名
    """
    query_set = WallDetailedData.objects.all()
    if query_set.count() > 0:
        max_id = WallDetailedData.objects.all().last().id
    else:
        max_id = 0
    return f"ShearWall-{max_id + 1}"

# Create your models here.
class WallDetailedData(models.Model):
    """
    双皮剪力墙深化设计参数
    """
    # 项目编号
    project_num = models.CharField(
        verbose_name="项目编号",
        null=True,
        blank=True,
        max_length=32,
        help_text="下层结构计算需要该参数",
    )
    shear_wall_num = models.CharField(
        verbose_name="剪力墙编号",
        null=True,
        blank=True,
        max_length=32,
        help_text="下层结构计算需要该参数",
    )
    # 数据别名
    remark_name = models.CharField(
        verbose_name="参数编号",
        null=True,
        blank=False,
        default=get_default_remark_name,
        max_length=64,
    )
    # 材料相关
    rebar_name = models.CharField(
        choices=REBAR_CONFIG_NAME,
        verbose_name="钢筋等级",
        max_length=32,
        default=REBAR_CONFIG_NAME[0][0],
    )
    concrete_grade = models.IntegerField(
        verbose_name="混凝土等级",
        choices=CONCRETE_GRADE,
        default=CONCRETE_GRADE[0][0],
    )
    # 构造相关
    protective_layer_thickness = models.IntegerField(
        verbose_name="保护层厚度 c(mm)", default=20
    )
    # 几何参数
    length = models.IntegerField(verbose_name="剪力墙长度 (mm)", null=True)
    height = models.IntegerField(verbose_name="剪力墙高度 (mm)", null=True)
    thickness = models.IntegerField(verbose_name="剪力墙厚度 (mm)", null=True)
    interior_thickness = models.IntegerField(verbose_name="内墙厚度 (mm)", null=True)
    exterior_thickness = models.IntegerField(verbose_name="外墙厚度 (mm)", null=True)
    bottom_gap_height = models.IntegerField(verbose_name="底部间隙 (mm)", null=True)
    top_gap_height = models.IntegerField(verbose_name="顶部间隙 (mm)", null=True)
    # 剪力墙类型
    SHEAR_WALL_TYPE_CHOICE = (
        (ShearWallType.EXTERIOR.value, "外墙"),
        (ShearWallType.INTERIOR.value, "内墙"),
    )
    shear_wall_type = models.IntegerField(
        verbose_name="剪力墙类型",
        choices=SHEAR_WALL_TYPE_CHOICE,
        default=ShearWallType.EXTERIOR.value,
    )
    WALL_LENGTH_TYPE_CHOICE = (
        (WallLengthType.YES.value, "内外墙板等长"),
        (WallLengthType.NO.value, "内墙短"),
    )
    wall_length_type = models.IntegerField(
        verbose_name="剪力墙长度类型",
        choices=WALL_LENGTH_TYPE_CHOICE,
        default=WallLengthType.YES.value,
    )

    left_gap_length = models.IntegerField(verbose_name="左间隙长度 (mm)", null=True)
    right_gap_length = models.IntegerField(verbose_name="右间隙长度 (mm)", null=True)

    # 剪力墙洞口相关
    WALL_HOLE_CHOICE = (
        (WallHole.YES.value, "有洞口"),
        (WallHole.NO.value, "没有洞口"),
    )
    wall_hole = models.IntegerField(
        verbose_name="剪力墙洞口",
        choices=WALL_HOLE_CHOICE,
        default=WallHole.YES.value,
    )
    WALL_HOLE_TYPE_CHOICE = (
        (WallHoleType.RECTANGLE.value, "矩形洞口"),
        (WallHoleType.CIRCLE.value, "圆形洞口"),
    )
    wall_hole_type = models.IntegerField(
        verbose_name="剪力墙洞口类型",
        choices=WALL_HOLE_TYPE_CHOICE,
        default=WallHoleType.RECTANGLE.value,
    )
    # 剪力墙矩形洞口参数
    rectangle_hole_height = models.IntegerField(verbose_name="洞口高度 (mm)", null=True, blank=True)
    rectangle_hole_length = models.IntegerField(verbose_name="洞口长度 (mm)", null=True, blank=True)
    rectangle_hole_horizontal = models.IntegerField(verbose_name="洞口中心点水平定位 (mm)", null=True, blank=True)
    rectangle_hole_vertical = models.IntegerField(verbose_name="洞口中心点竖向定位 (mm)", null=True, blank=True)
    # 剪力墙圆形洞口参数
    circle_hole_diameter = models.IntegerField(verbose_name="洞口直径 (mm)", null=True, blank=True)
    circle_hole_horizontal = models.IntegerField(verbose_name="洞口中心点水平定位 (mm)", null=True, blank=True)
    circle_hole_vertical = models.IntegerField(verbose_name="洞口中心点竖向定位 (mm)", null=True, blank=True)

    # 钢筋深化设计
    REBAR_DESIGN_MODE_CHOICE = (
        (RebarDesignMode.AUTOMATIC.value, "自动"),
        (RebarDesignMode.MANUAL.value, "手动"),
    )
    rebar_design_mode = models.IntegerField(
        verbose_name="钢筋设计方式",
        choices=REBAR_DESIGN_MODE_CHOICE,
        default=RebarDesignMode.AUTOMATIC.value,
    )

    horizontal_rebar_diameter = models.IntegerField(verbose_name="水平钢筋直径 (mm)", null=True, blank=True)
    horizontal_rebar_spacing = models.IntegerField(verbose_name="水平钢筋间距 (mm)", null=True, blank=True)
    horizontal_rebar_ratio = models.FloatField(verbose_name="水平钢筋配筋率", null=True, blank=True)
    vertical_rebar_diameter = models.IntegerField(verbose_name="竖向钢筋直径 (mm)", null=True, blank=True)
    vertical_rebar_spacing = models.IntegerField(verbose_name="竖向钢筋间距 (mm)", null=True, blank=True)
    vertical_rebar_ratio = models.FloatField(verbose_name="竖向钢筋配筋率", null=True, blank=True)

    def validate_rebar_design_mode(self):
        rebar_dm = RebarDesignMode(self.rebar_design_mode)
        errors = "钢筋设计方式为手动时，钢筋信息不能为空！"
        if rebar_dm == RebarDesignMode.MANUAL:
            if (
                self.horizontal_rebar_diameter is None
                or self.horizontal_rebar_spacing is None
                or self.horizontal_rebar_ratio is None
            ) and (
                self.vertical_rebar_diameter is None
                or self.vertical_rebar_spacing is None
                or self.vertical_rebar_ratio is None
            ):
                raise ValidationError(errors)

    def clean(self):
        super().clean()
        custom_validators = [self.validate_rebar_design_mode]
        for fun in custom_validators:
            fun()

    # 桁架钢筋深化设计
    TRUSS_REBAR_MODE_CHOICE = (
        (TrussRebarMode.AUTOMATIC.value, "自动"),
        (TrussRebarMode.MANUAL.value, "手动"),
    )
    truss_rebar_mode = models.IntegerField(
        verbose_name="桁架钢筋设计方式",
        choices=TRUSS_REBAR_MODE_CHOICE,
        default=TrussRebarMode.AUTOMATIC.value,
    )
    DISTRIBUTED_REBAR_CHOICE = (
        (DistributedBar.YES.value, "桁架筋作为分布筋"),
        (DistributedBar.NO.value, "桁架筋不作为分布筋"),
    )
    LIFTING_REBAR_CHOICE = (
        (LiftingBar.YES.value, "桁架筋作为吊装筋"),
        (LiftingBar.NO.value, "桁架筋不作为吊装筋"),
    )
    distributed_rebar = models.IntegerField(
        verbose_name="桁架筋是否作为分布筋",
        choices=DISTRIBUTED_REBAR_CHOICE,
        default=DistributedBar.YES.value,
    )
    lifting_rebar = models.IntegerField(
        verbose_name="桁架筋是否作为吊装筋",
        choices=LIFTING_REBAR_CHOICE,
        default=LiftingBar.YES.value,
    )
    trussing_rebar_name = models.CharField(
        choices=REBAR_CONFIG_NAME,
        verbose_name="桁架钢筋等级",
        max_length=32,
        default=REBAR_CONFIG_NAME[0][0],
    )
    truss_top_rebar_diameter = models.IntegerField(verbose_name="桁架上部钢筋直径 (mm)", null=True, blank=True)
    truss_bottom_rebar_diameter = models.IntegerField(verbose_name="桁架底部钢筋直径 (mm)", null=True, blank=True)
    diagonal_rebar_diameter = models.IntegerField(verbose_name="桁架腹筋直径 (mm)", null=True, blank=True)
    diagonal_rebar_spacing = models.IntegerField(verbose_name="桁架腹筋间距 (mm)", null=True, blank=True)

    truss_height = models.IntegerField(verbose_name="桁架高度 (mm)", null=True, blank=True)
    truss_width = models.IntegerField(verbose_name="桁架宽度 (mm)", null=True, blank=True)
    truss_number = models.IntegerField(
        verbose_name="桁架数量",
        null=True,
        blank=True,
        default=2,
    )

    # 吊装预埋件深化设计
    LIFTING_INSERTS_DESIGN_MODE_CHOICE = (
        (LiftingInsertsDesignMode.AUTOMATIC.value, "自动"),
        (LiftingInsertsDesignMode.MANUAL.value, "手动"),
    )
    lifting_inserts_design_mode = models.IntegerField(
        verbose_name="吊装预埋件设计方式",
        choices=LIFTING_INSERTS_DESIGN_MODE_CHOICE,
        default=LiftingInsertsDesignMode.AUTOMATIC.value,
    )
    lifting_inserts_diameter = models.IntegerField(verbose_name="吊装预埋件直径 (mm)", null=True, blank=True)
    lifting_inserts_position_x1 = models.IntegerField(
        verbose_name="左吊装预埋件距左边界位置 (mm)",
        null=True,
        blank=True,
    )
    lifting_inserts_position_x2 = models.IntegerField(
        verbose_name="右吊装预埋件距右边界位置 (mm)",
        null=True,
        blank=True,
    )
    # 支撑预埋件深化设计
    SUPPORT_INSERTS_DESIGN_MODE_CHOICE = (
        (SupportInsertsDesignMode.AUTOMATIC.value, "自动"),
        (SupportInsertsDesignMode.MANUAL.value, "手动"),
    )
    support_inserts_design_mode = models.IntegerField(
        verbose_name="支撑预埋件设计方式",
        choices=SUPPORT_INSERTS_DESIGN_MODE_CHOICE,
        default=SupportInsertsDesignMode.AUTOMATIC.value,
    )

    support_inserts_hole_diameter = models.IntegerField(verbose_name="支撑预埋件孔洞大小 (mm)", null=True, blank=True)

    support_inserts_position_x1 = models.IntegerField(
        verbose_name="距左边界位置 (mm)",
        null=True,
        blank=True,
    )
    support_inserts_position_x2 = models.IntegerField(
        verbose_name="距右边界位置 (mm)",
        null=True,
        blank=True,
    )
    support_inserts_position_y1 = models.IntegerField(
        verbose_name="距下边界位置 (mm)",
        null=True,
        blank=True,
    )
    support_inserts_position_y2 = models.IntegerField(
        verbose_name="距上边界位置 (mm)",
        null=True,
        blank=True,
    )

    # ???预埋件
    CAST_INSERTS_DESIGN_MODE_CHOICE = (
        (CastInsertsDesignMode.AUTOMATIC.value, "自动"),
        (CastInsertsDesignMode.MANUAL.value, "手动"),
    )
    cast_inserts_design_mode = models.IntegerField(
        verbose_name="???预埋件设计方式",
        choices=CAST_INSERTS_DESIGN_MODE_CHOICE,
        default=CastInsertsDesignMode.AUTOMATIC.value,
    )
    cast_inserts_left_number = models.IntegerField(
        verbose_name="左部数量 (mm)",
        null=True,
        blank=True,
    )
    cast_inserts_right_number = models.IntegerField(
        verbose_name="右部数量 (mm)",
        null=True,
        blank=True,
    )
    cast_inserts_top_number = models.IntegerField(
        verbose_name="顶部数量 (mm)",
        null=True,
        blank=True,
    )
    cast_inserts_bottom_number = models.IntegerField(
        verbose_name="底部数量 (mm)",
        null=True,
        blank=True,
    )

    # 其他预埋件
    OTHER_INSERTS_CHOICE = (
        (OtherInserts.YES.value, "是"),
        (OtherInserts.NO.value, "否"),
    )
    other_inserts = models.IntegerField(
        verbose_name="是否有其他预埋件",
        choices=OTHER_INSERTS_CHOICE,
        default=OtherInserts.NO.value,
    )
    other_inserts_number = models.IntegerField(verbose_name="其他预埋件数量", null=True, blank=True)
    other_inserts_parameters = models.TextField(
        verbose_name="其他预埋件的直径尺寸列表",
        null=True,
        blank=True,
        help_text="以[ ]列表的形式呈现",
    )
    other_inserts_positions = models.TextField(
        verbose_name="其他预埋件距离墙左方、下方的距离",
        null=True,
        blank=True,
        help_text="以[ [ ] ]的形式呈现",
    )

    class Meta:
        verbose_name = "深化设计"
        verbose_name_plural = verbose_name


class WallDetailedResult(models.Model):
    """
    双皮剪力墙深化设计结果
    """
    wall = models.ForeignKey(
        to=WallDetailedData,
        verbose_name="关联参数",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    interior_height = models.FloatField(verbose_name="内墙高度 (mm)", null=True)
    exterior_height = models.FloatField(verbose_name="外墙高度 (mm)", null=True)
    left_gap_length = models.FloatField(verbose_name="左边间隙 (mm)", null=True)
    right_gap_length = models.FloatField(verbose_name="右边间隙 (mm)", null=True)
    interior_length = models.FloatField(verbose_name="内墙长度 (mm)", null=True)
    exterior_length = models.FloatField(verbose_name="外墙长度 (mm)", null=True)
    volume = models.FloatField(verbose_name="体积", null=True)
    area = models.FloatField(verbose_name="面积", null=True)
    weight = models.FloatField(verbose_name="重量", null=True)
    horizontal_rebars = models.TextField(
        verbose_name="水平钢筋",
        null=True,
        blank=True,
    )
    vertical_rebars = models.TextField(
        verbose_name="竖向钢筋",
        null=True,
        blank=True,
    )

    # 调用状态
    success = models.BooleanField(
        verbose_name="计算状态", default=False, help_text="调用计算的状态"
    )
    message = models.CharField(
        verbose_name="错误原因",
        null=True,
        blank=True,
        help_text="错误原因",
        max_length=256,
    )

    class Meta:
        verbose_name = "深化设计结果"
        verbose_name_plural = verbose_name