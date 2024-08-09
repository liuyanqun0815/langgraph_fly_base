# 假设项目根目录包含特定的文件或目录，例如 'manage.py' 或 'README.md'
import os


def find_project_root(start_path):
    path = start_path
    while not os.path.exists(os.path.join(path, 'manage.py')):  # 根据你的项目特征修改条件
        path = os.path.dirname(path)
        if path == os.path.dirname(path):  # 检查是否已经到达文件系统的根目录
            return None
    return path