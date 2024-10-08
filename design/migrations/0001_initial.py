# Generated by Django 4.2.16 on 2024-09-23 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WallDetailedData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "project_num",
                    models.CharField(
                        blank=True,
                        help_text="下层结构计算需要该参数",
                        max_length=32,
                        null=True,
                        verbose_name="项目编号",
                    ),
                ),
                (
                    "shear_wall_num",
                    models.CharField(
                        blank=True,
                        help_text="下层结构计算需要该参数",
                        max_length=32,
                        null=True,
                        verbose_name="剪力墙编号",
                    ),
                ),
                (
                    "rebar_name",
                    models.CharField(
                        choices=[
                            ["HPB300", "HPB300"],
                            ["HRB335", "HRB335"],
                            ["HRBF335", "HRBF335"],
                            ["HRB400", "HRB400"],
                            ["HRBF400", "HRBF400"],
                            ["RRB400", "RRB400"],
                            ["HRB500", "HRB500"],
                            ["HRBF500", "HRBF500"],
                        ],
                        default="HPB300",
                        max_length=32,
                        verbose_name="钢筋等级",
                    ),
                ),
                (
                    "concrete_grade",
                    models.IntegerField(
                        choices=[
                            [30, "C30"],
                            [35, "C35"],
                            [40, "C40"],
                            [45, "C45"],
                            [50, "C50"],
                        ],
                        default=30,
                        verbose_name="混凝土等级",
                    ),
                ),
                (
                    "protective_layer_thickness",
                    models.IntegerField(default=20, verbose_name="保护层厚度 c(mm)"),
                ),
            ],
        ),
    ]
