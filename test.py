from elasticsearch import Elasticsearch

# 连接到 Elasticsearch
es = Elasticsearch("http://localhost:9200")

# 测试连接
if es.ping():
    print("Elasticsearch is connected!")
else:
    print("Failed to connect to Elasticsearch.")

# 测试创建索引
INDEX_NAME = "test_index"
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME)
    print(f"Index '{INDEX_NAME}' created.")
else:
    print(f"Index '{INDEX_NAME}' already exists.")

# 测试插入数据
doc = {"test": "data"}
es.index(index=INDEX_NAME, id=1, body=doc)
print("Data inserted:", es.get(index=INDEX_NAME, id=1))