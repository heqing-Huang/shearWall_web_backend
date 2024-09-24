# Generated by Django 4.2.16 on 2024-09-24 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("design", "0003_walldetaileddata_remark_name_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="walldetaileddata",
            options={"verbose_name": "深化设计", "verbose_name_plural": "深化设计"},
        ),
        migrations.AlterModelOptions(
            name="walldetailedresult",
            options={
                "verbose_name": "深化设计结果",
                "verbose_name_plural": "深化设计结果",
            },
        ),
        migrations.AddField(
            model_name="walldetailedresult",
            name="message",
            field=models.CharField(
                blank=True,
                help_text="错误原因",
                max_length=256,
                null=True,
                verbose_name="错误原因",
            ),
        ),
        migrations.AddField(
            model_name="walldetailedresult",
            name="success",
            field=models.BooleanField(
                default=False, help_text="调用计算的状态", verbose_name="计算状态"
            ),
        ),
    ]
