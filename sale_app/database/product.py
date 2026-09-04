from config import recommend_collection_name
from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
from sale_app.database.session import get_db_session
from sale_app.database.sqlalchemy_models import Product

logger = Logger("fly_base")


def get_product_info(user_info: str):
    product_str = ""
    logger.info(f"提取用户信息:{user_info}")
    if user_info in "暂无用户信息":
        with get_db_session() as session:
            products = session.query(Product).all()
            for p in products:
                product_str += f"产品名称：{p.product_name}\n产品信息：{p.product_info}\n"
    else:
        product_str = KBService.hybrid_search(user_info, recommend_collection_name())
    return product_str
