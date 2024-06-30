# Generated by Django 5.0.6 on 2024-06-12 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sale_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': '产品信息表'},
        ),
        migrations.AlterField(
            model_name='product',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='主键Id'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_info',
            field=models.CharField(max_length=256, verbose_name='产品信息'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_name',
            field=models.CharField(max_length=16, verbose_name='产品名称'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_priority',
            field=models.IntegerField(default=1, verbose_name='产品优先级'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.IntegerField(default=1, verbose_name='产品类型'),
        ),
    ]