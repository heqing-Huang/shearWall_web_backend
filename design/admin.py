from django.contrib import admin
from design.models import WallDetailedData, WallDetailedResult
from design.tools import call_detailed_design, call_detailed_design_by_model

# 登录界面标题
admin.site.site_header = '复杂预制构件智能深化设计系统'
# 网页标题
admin.site.site_title = '双皮剪力墙深化设计'
# 后台主页标题
admin.site.index_title = '站点管理'

# Register your models here.
@admin.register(WallDetailedData)
class AdminWallDetailedData(admin.ModelAdmin):
    list_display = ["project_num", "shear_wall_num", "remark_name", "pub_date"]
    fieldsets = [
        ("剪力墙项目", {
            "fields": [
                "project_num", "shear_wall_num", "remark_name"
            ],
        }),
        ("材料参数", {
            "fields": [
                "rebar_name", "concrete_grade",
            ],
        }),
        ("构造参数", {
            "fields": [
                "protective_layer_thickness",
            ],
        }),

        ("剪力墙几何参数", {
            "fields": [
                "length",
                "height",
                "thickness",
                "interior_thickness",
                "exterior_thickness",
                "bottom_gap_height",
                "top_gap_height",
            ],
        }),
        ("剪力墙类型", {
            "fields": [
                "shear_wall_type",
                "wall_length_type",
                "left_gap_length",
                "right_gap_length",
            ],
        }),

        ("剪力墙洞口", {
            "fields": [
                'wall_hole',
            ],
        }),
        ("剪力墙洞口类型", {
            "fields": [
                "wall_hole_type",
            ],
        }),
        ("矩形洞口参数", {
            "fields": [
                "rectangle_hole_height",
                "rectangle_hole_length",
                "rectangle_hole_horizontal",
                "rectangle_hole_vertical",
            ],
        }),
        ("圆形洞口参数", {
            "fields": [
                "circle_hole_diameter",
                "circle_hole_horizontal",
                "circle_hole_vertical",
            ],
        }),

        ("钢筋深化设计", {
            "fields": [
                "rebar_design_mode",
            ],
        }),
        ("钢筋相关参数", {
            "fields": [
                "horizontal_rebar_diameter",
                "horizontal_rebar_spacing",
                "horizontal_rebars_ratio",
                "vertical_rebar_diameter",
                "vertical_rebar_spacing",
                "vertical_rebars_ratio",
            ],
        }),

        ("桁架钢筋深化设计", {
            "fields": [
                "truss_rebar_mode",
            ],
        }),
        ("桁架相关参数", {
            "fields": [
                "truss_height",
                "truss_width",
                "truss_number",
            ],
        }),
        ("桁架钢筋相关参数", {
            "fields": [
                "distributed_rebar",
                "lifting_rebar",
                "trussing_rebar_name",
                "truss_top_rebar_diameter",
                "truss_bottom_rebar_diameter",
                "diagonal_rebar_diameter",
                "diagonal_rebar_spacing",
            ],
        }),

        ("吊装预埋件深化设计", {
            "fields": [
                "lifting_inserts_design_mode",
            ],
        }),
        ("吊装预埋件设计参数", {
            "fields": [
                "lifting_inserts_diameter",
                "lifting_inserts_position_x1",
                "lifting_inserts_position_x2",
            ],
        }),

        ("支撑预埋件深化设计", {
            "fields": [
                "support_inserts_design_mode",
            ],
        }),
        ("支撑预埋件设计参数", {
            "fields": [
                "support_inserts_hole_diameter",
                "support_inserts_position_x1",
                "support_inserts_position_x2",
                "support_inserts_position_y1",
                "support_inserts_position_y2",
            ],
        }),

        ("???预埋件深化设计", {
            "fields": [
                "cast_inserts_design_mode",
            ],
        }),
        ("???预埋件设计参数", {
            "fields": [
                "cast_inserts_left_number",
                "cast_inserts_right_number",
                "cast_inserts_top_number",
                "cast_inserts_bottom_number",
            ],
        }),

        ("其他预埋件深化设计", {
            "fields": [
                "other_inserts",
            ],
        }),
        ("其他预埋件设计参数", {
            "fields": [
                "other_inserts_number",
                "other_inserts_parameters",
                "other_inserts_positions",
            ],
        }),
    ]

    def get_inlines(self, request, obj):
        if obj is None:
            return list()
        if WallDetailedResult.objects.filter(wall=obj).count() == 0:
            return list()

        return super(AdminWallDetailedData, self).get_inlines(request, obj)

    def save_model(self, request, obj, form, change):
        # 执行保存
        data_back = super(AdminWallDetailedData, self).save_model(request, obj, form, change)
        instance: WallDetailedResult
        obj: WallDetailedData
        if obj:
            # 在这里调用结构计算
            detailed_result_row = call_detailed_design_by_model(obj)
            # tasks.total_back_handle.apply_async((detailed_result_row.id,))
        return data_back

@admin.register(WallDetailedResult)
class AdminWallDetailedResult(admin.ModelAdmin):
    list_display = [
        "remark_name",
        "success",
    ]

    def get_fieldsets(self, request, obj=None):
        obj: WallDetailedResult
        if obj.success:
            fieldsets = [
                ("双皮剪力墙设计参数", {
                    "fields": [
                        "interior_height",
                        "exterior_height",
                        "left_gap_length",
                        "right_gap_length",
                        "interior_length",
                        "exterior_length",
                        "volume",
                        "area",
                        "weight",
                        "horizontal_rebars",
                        "vertical_rebars",
                    ],
                }),
                ("状态控制", {"fields": ["success", "message"]}),
            ]
        else:
            fieldsets = ("状态控制", {"fields": ["success", "message"]})
        return fieldsets

    @admin.display(description="别名")
    def remark_name(self, obj: WallDetailedResult):
        if obj.wall:
            return obj.wall.remark_name
        else:
            return None

    remark_name.short_description = "别名"