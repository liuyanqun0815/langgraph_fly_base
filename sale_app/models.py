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
