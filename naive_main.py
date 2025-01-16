import gradio as gr
from zhipuai import ZhipuAI

class SimpleChatbot:
    def __init__(self, api_key):
        # 初始化 ZhipuAI 客户端
        self.client = ZhipuAI(api_key=api_key)
        # 初始化对话历史
        self.conversation_history = []

    def generate_response(self, user_input):
        """
        调用 ZhipuAI API 直接生成回答
        """
        # 构造对话上下文
        self.conversation_history.append({"role": "user", "content": user_input})

        # 调用 ChatGLM 接口
        response = self.client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个政务领域的智能助手，擅长回答政策问题。"},
                *self.conversation_history,
            ],
        )
        # 获取回复内容
        reply = response.choices[0].message.content
        # 更新对话历史
        self.conversation_history.append({"role": "assistant", "content": reply})

        return reply

if __name__ == "__main__":
    api_key = "your_api_key"  # 替换为你的 ZhipuAI API Key
    chatbot = SimpleChatbot(api_key)

    # 定义 Gradio 界面
    interface = gr.Blocks()

    with interface:
        with gr.Row():
            gr.Markdown("<h1 style='text-align: center; color: #0000FF;'>广东省科技厅政务客服</h1>")
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

        def process_input(user_input):
            return chatbot.generate_response(user_input)

        submit_button.click(process_input, inputs=user_input, outputs=output_text)

    interface.launch()