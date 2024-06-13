from sale_app.models import Product


def get_product_info():
    data = Product.objects.all()
    data_list = list(data.values())  # 使用values()获取字典形式的数据
    # 获取list部分参数，拼成str
    product_str = ""
    for i in range(len(data_list)):
        product_str += "产品名称："+str(data_list[i].get("product_name")) + "\n产品信息：" + str(data_list[i].get("product_info")) + "\n"

    print(product_str)
    return product_str




