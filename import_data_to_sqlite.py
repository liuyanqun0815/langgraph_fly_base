import json
import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# 设置Django环境变量
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fly_base.settings")
application = get_wsgi_application()

# 加载JSON数据
def load_data(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data


# 导入数据到模型
from sale_app.models import Product

def import_data(data):
    for item in data:
        # 创建模型实例并保存到数据库
        Product.objects.create(**item)


BASE_DIR = Path(__file__).resolve().parent.parent


# 主函数
def main():
    # 构建数据文件的路径
    data_file_path = 'sale_app/migrations/init_sqllite.json'
    # 加载数据
    data = load_data(data_file_path)
    # 导入数据
    import_data(data)


if __name__ == '__main__':
    main()