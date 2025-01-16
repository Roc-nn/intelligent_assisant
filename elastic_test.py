from elasticsearch import Elasticsearch
import json
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 替换你的用户名和密码
es = Elasticsearch(
    "https://localhost:9200",
    basic_auth=("elastic", "xvVyiK=ox15Tcbv8m28t"),
    verify_certs=False  # 临时忽略 SSL 验证
)

if es.ping():
    print("Successfully connected to Elasticsearch!")
else:
    print("Failed to connect to Elasticsearch.")

INDEX_NAME = "policy_knowledge_base"

# 1. 检查索引是否存在
if not es.indices.exists(index=INDEX_NAME):
    print(f"Index '{INDEX_NAME}' does not exist. Creating it...")
    
    # 创建索引时，将时间字段的格式指定为支持的日期格式
    es.indices.create(index=INDEX_NAME, body={
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"},
                "source": {"type": "text"},
                "content": {"type": "text"}
            }
        }
    })
    print(f"Index '{INDEX_NAME}' created.")
else:
    print(f"Index '{INDEX_NAME}' already exists.")

# 2. 插入数据
print("Inserting data into the index...")
with open("output/cleaned_policy.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for record in data:
    try:
        # 转换时间格式为 Elasticsearch 支持的格式
        if "time" in record and record["time"]:
            record["time"] = datetime.strptime(record["time"], "%Y-%m-%d %H:%M:%S").isoformat()
        else:
            record["time"] = None  # 如果时间字段为空，设置为 None

        # 插入数据
        es.index(index=INDEX_NAME, body={
            "title": record["title"],
            "time": record["time"],
            "source": record["source"],
            "content": record["content"]
        })
    except Exception as e:
        print(f"Error inserting record: {record['title']}. Error: {e}")
print("Data insertion complete.")

# 3. 测试检索
print("Testing retrieval...")
query = {
    "query": {
        "match": {
            "content": "香港"  # 修改为你希望检索的关键词
        }
    }
}

response = es.search(index=INDEX_NAME, body=query)
print("Search results:")
for hit in response["hits"]["hits"]:
    print(f"Score: {hit['_score']}, Title: {hit['_source']['title']}")