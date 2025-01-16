import os
import json
import gradio as gr
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from text2vec import SentenceModel
from langchain.schema import Document
from zhipuai import ZhipuAI
import urllib3

# 忽略 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Elasticsearch 索引名
ES_INDEX = "policy_knowledge_base"

class ChatbotWithRAG:
    def __init__(self, json_path, api_key):
        # 初始化 ZhipuAI 客户端
        self.client = ZhipuAI(api_key=api_key)

        # 初始化 Elasticsearch 客户端
        self.es = Elasticsearch(
            "https://localhost:9200",
            basic_auth=("elastic", "elastic_password"),  # 替换为你的认证信息
            verify_certs=False  # 忽略证书验证
        )
        if not self.es.ping():
            raise ConnectionError("无法连接到 Elasticsearch，请检查服务是否启动。")

        # 初始化嵌入模型
        self.embedding_model = SentenceModel("GanymedeNil/text2vec-large-chinese")

        # 创建或检查 Elasticsearch 索引
        self._initialize_index()

        # 加载 JSON 数据并存储到 Elasticsearch
        self._load_json_to_es(json_path)

        # 初始化对话历史
        self.conversation_history = ""

    def _initialize_index(self):
        """初始化 Elasticsearch 索引"""
        if not self.es.indices.exists(index=ES_INDEX):
            print(f"创建索引 '{ES_INDEX}'...")
            self.es.indices.create(index=ES_INDEX, body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text"},
                        "time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"},
                        "source": {"type": "text"},
                        "content": {"type": "text"},
                        "embedding": {"type": "dense_vector", "dims": 1024}  # 嵌入向量维度调整为 1024
                    }
                }
            })
            print(f"索引 '{ES_INDEX}' 创建成功。")
        else:
            print(f"索引 '{ES_INDEX}' 已存在。")
            # 检查索引映射是否符合预期
            mapping = self.es.indices.get_mapping(index=ES_INDEX)
            dims = mapping[ES_INDEX]["mappings"]["properties"]["embedding"]["dims"]
            if dims != 1024:
                raise ValueError(f"索引 '{ES_INDEX}' 的嵌入维度为 {dims}，而不是预期的 1024，请删除后重新创建。")

    def _load_json_to_es(self, json_path):
        """加载 JSON 数据到 Elasticsearch"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        actions = []
        for record in data:
            try:
                # 生成嵌入向量
                content = f"标题: {record['title']}\n时间: {record['time']}\n来源: {record['source']}\n内容: {record['content']}"
                embedding = self.embedding_model.encode(content)

                if len(embedding) != 1024:
                    print(f"跳过记录，嵌入维度不匹配: {record['title']}")
                    continue

                # 准备插入文档
                actions.append({
                    "_index": ES_INDEX,
                    "_source": {
                        "title": record["title"],
                        "time": record["time"],
                        "source": record["source"],
                        "content": record["content"],
                        "embedding": embedding.tolist()
                    }
                })
            except Exception as e:
                print(f"Error processing record: {record.get('title', '未知标题')}. Error: {e}")

        # 批量插入数据
        if actions:
            try:
                bulk(self.es, actions, chunk_size=50)
                print(f"{len(actions)} 条数据已成功插入到索引 '{ES_INDEX}'。")
            except Exception as e:
                print(f"批量插入失败: {e}")
        else:
            print("没有数据插入到 Elasticsearch，请检查输入文件。")

    def retrieve_documents(self, query):
        """
        使用 Elasticsearch 检索相关文档
        """
        # 生成查询嵌入向量
        query_embedding = self.embedding_model.encode(query)

        # 构建查询脚本
        script_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding.tolist()}
                }
            }
        }

        # 执行查询
        response = self.es.search(index=ES_INDEX, body={"size": 5, "query": script_query})
        docs = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            docs.append(Document(
                page_content=f"标题: {source['title']}\n时间: {source['time']}\n来源: {source['source']}\n内容: {source['content']}",
                metadata={"title": source["title"], "time": source["time"], "source": source["source"]}
            ))
        return docs

    def generate_response(self, query):
        """
        生成回答：结合检索到的文档内容调用 ChatGLM 接口
        """
        # 检索相关文档
        relevant_docs = self.retrieve_documents(query)
        context = "\n".join([doc.page_content for doc in relevant_docs])

        # 构造上下文与用户问题
        prompt = (
            f"以下是政务领域的相关信息：\n{context}\n\n"
            f"用户的问题是：{query}\n"
            "请基于上述内容提供准确、简洁的回答。"
        )

        # 调用 ChatGLM 接口
        response = self.client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个政务领域的智能助手，擅长回答政策问题。"},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def get_response(self, user_input):
        """
        为 Gradio 创建的函数，获取用户输入并返回机器人的响应。
        """
        response = self.generate_response(user_input)
        # 更新对话历史
        self.conversation_history += f"你: {user_input}\nChatbot: {response}\n"
        return self.conversation_history


if __name__ == "__main__":
    # 知识库 JSON 文件路径
    json_file = "output/cleaned_policy.json"  # 替换为实际路径
    api_key = "your_api_key"  # 替换为你的 ZhipuAI API Key
    bot = ChatbotWithRAG(json_file, api_key)

    # 定义 Gradio 界面
    interface = gr.Blocks()

    with interface:
        with gr.Row():
            gr.Markdown("<h1 style='text-align: center; color: #4CAF50;'>广东省科技厅政务智能客服</h1>")
        with gr.Row():
            gr.Markdown(
                """
                <p style="text-align: center; font-size: 1.2em;">
                欢迎使用广东省科技厅政务智能客服系统。本系统基于最新的人工智能技术，提供准确、专业的政策解答。
                </p>
                """)
        with gr.Row():
            with gr.Column(scale=1):
                user_input = gr.Textbox(
                    label="请输入您的问题",
                    placeholder="例如：广东省最新的科技计划政策是什么？",
                    lines=2,
                )
            with gr.Column(scale=1):
                submit_button = gr.Button("提交")

        with gr.Row():
            output_text = gr.Textbox(
                label="回复",
                lines=10,
                interactive=False,
            )

        submit_button.click(bot.get_response, inputs=user_input, outputs=output_text)

    interface.launch()