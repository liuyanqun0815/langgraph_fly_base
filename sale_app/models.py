from django.db import models


# Create your models here.
class Product(models.Model):
    id = models.AutoField("主键Id", primary_key=True)  # 产品id
    product_name = models.CharField("产品名称", max_length=16)  # 产品名称
    product_priority = models.IntegerField("产品优先级", default=1)
    product_type = models.IntegerField("产品类型", default=1)  # 产品类型
    product_info = models.CharField("产品信息", max_length=256)  # 产品信息

    def __str__(self):
        print(self.product_name)

    class Meta:
        verbose_name = "产品信息表"


class Datasets(models.Model):
    id = models.AutoField("主键Id", primary_key=True)
    tenant_id = models.IntegerField("租户id", default=1)
    dataset_name = models.CharField("数据集名称", max_length=16)
    dataset_type = models.IntegerField("数据集类型", default=1)
    dataset_info = models.CharField("数据集信息", max_length=256)
    dataset_status = models.IntegerField("数据集状态", default=1)
    embedding_model = models.CharField("embedding模型", max_length=16)
    embedding_model_provider = models.CharField("embedding模型提供商", max_length=16)

    dataset_create_time = models.DateTimeField("数据集创建时间", auto_now_add=True)
    dataset_update_time = models.DateTimeField("数据集更新时间", auto_now=True)

    class Meta:
        verbose_name = "数据集信息表"

    def __str__(self):
        return self.dataset_name
