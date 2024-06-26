

## 基于langgraph构建工作流

### 方案设计:

![langchain.drawio.png](docs%2Flangchain.drawio.png)

**项目使用的web框架：django**

**日志框架：logging**

**langchain监控框架：langsimith**

## **工作流**：
方案里面的敏感词汇和信息脱敏考虑到相对独立，没有设计到工作流中
![grap.png](docs%2Fgrap.png)

#### 产品推荐子链

![recommend.png](docs%2Frecommend.png)

项目目前开发过程中,每天都会进行更新

## 步骤:
1. 创建项目
2. 创建虚拟环境
3. 克隆项目
4. pip install -r requirements
如果按照fasttext失败,手动安装
5. pip install /load_model/fasttext_wheel-0.9.2-cp311-cp311-win_amd64.whl
6. 数据库表迁移\
`python manage.py makemigrations sale_app`\
`python manage.py migrate sale_app`
7. 默认数据导入\
`python import_data_to_sqlite.py`
8. 向量数据库创建(通过docker启动)\
进入到docker目录下 \
```shell
cd docker
docker-compose -f docker-compose.qdrant.yaml -p fly up -d
```
9. 启动项目\
`python manage.py runserver`


## 更新日志：
1. 2024-06-17: 添加支持xlsx格式文件导入，导入QA文档
2. 2024-06-18: 添加向量数据库支持（qdrant，docker部署）