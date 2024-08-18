from config import recommend_collection_name
from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
from sale_app.models import Product

logger = Logger("fly_base")


def get_product_info(user_info: str):
    product_str = ""
    logger.info(f"提取用户信息:{user_info}")
    if user_info in "暂无用户信息":
        data = Product.objects.all()
        data_list = list(data.values())  # 使用values()获取字典形式的数据
        # 获取list部分参数，拼成str
        for i in range(len(data_list)):
            product_str += "产品名称：" + str(data_list[i].get("product_name")) + "\n产品信息：" + str(
                data_list[i].get("product_info")) + "\n"
    else:
        # 查询推荐向量数据库,暂定使用默认的集合
        product_str = KBService.hybrid_search(user_info, recommend_collection_name())
    print(product_str)
    return product_str
