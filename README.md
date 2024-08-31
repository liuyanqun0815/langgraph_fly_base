

## 基于langgraph构建工作流
[大模型学习记录](https://juejin.cn/column/7379059739118878732)

### 方案设计:

![langchain.drawio.png](docs%2Flangchain_all.drawio.png)

**项目使用的web框架：django**

**日志框架：logging**

**langchain监控框架：langsimith**

## 知识库页面
项目启动成功
访问地址：http://127.0.0.1:8000/kb/upload_file
![kb_page.png](docs%2Fkb_page.png)

## **工作流**：
方案里面的敏感词汇考虑到相对独立，没有设计到工作流中，信息脱敏只对信息收集阶段进行脱敏，其他阶段不脱敏
![grap.png](docs%2Fgrap.png)

#### 产品推荐子链

![recommend.png](docs%2Frecommend.png)

项目目前开发过程中,每天都会进行更新
# 数据库选择
向量数据库选择困难症，对比了活跃度比较高或者易用的数据库(drant,milvus,weaviate,faiss)，最终选择milvus,详细介绍见[向量数据库浅谈](https://juejin.cn/post/7388096340503707688)


milvus可视化页面![img_1.png](docs%2Fimg_1.png)

**milvus使用分区键来区分每个文件**，检索的时候通过分区键进行过滤，提高检索效率


后续继续会集成drant和weaviate

## [推荐系统](https://juejin.cn/post/7402137644372344844)
基于内容推荐的算法，通过向量检索相似度方式获取推荐结果。

我们提取用户多维度的喜好标签和物品多维度的标签进行向量化进行存储， 特征向量化常用稀疏向量模型（SPLADE）进行。

另外也可以同时用稠密向量，使用混合检索，对查询的结果重排序权重稀疏向量大些

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
docker-compose -f milvus-standalone-docker-compose.yml -p fly up -d
```
9. 启动项目\
`python manage.py runserver`


## 更新日志：
```
1. 2024-06-17: 添加支持xlsx格式文件导入，导入QA文档
2. 2024-06-18: 添加向量数据库支持（qdrant，docker部署）
3. 2024-07-28: 添加milvus支持，docker部署
4. 2024-08-07: milvus支持混合检索（稠密向量检索+稀疏向量检索-Splade）
5. 2024-08-09: 问题分类节点重构，信息脱敏节点重构
6. 2024-08-27: milvus支持分区键过滤，解决不同文件（内容类似）上传知识库，相似度检索内容交叉污染的问题
7. 2024-08-29: 添加知识库页面，实现创建知识库，上传文件，检索文件等基础功能
8. 2024-08-31: 添加聊天页面，实现智能贷款客服聊天，支持多轮对话
```
## 文章

[向量检索引擎：Milvus](https://developer.baidu.com/article/detail.html?id=1227320)

[推荐系统常见问题分析](https://cloud.tencent.com/developer/techpedia/1764)