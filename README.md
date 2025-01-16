# Intelligent Policy Assistant

## 🌟 Introduction
This project implements an intelligent policy assistant system based on AI, providing accurate and professional policy answers. It integrates ZhipuAI for response generation, Elasticsearch for document retrieval, and text2vec for embedding-based search.

## 🛠️ Prerequisites
- **Elasticsearch**: Make sure Elasticsearch is installed and running ([Official Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/index.html))
- **ZhipuAI API Key**: Configure in ``text2vec_elastic_main.py``:
    ```python
    api_key = "your_api_key"  # Replace with your ZhipuAI API Key
    ```
- **Policy Data**: Place policy data (JSON format) in `output/` folder (default: ```cleaned_policy.json```)

## 📦 Installation & Usage
1. Install dependencies
     ```bash
     pip install -r requirements.txt
     ```

2. Run application
     ```bash
     python text2vec_elastic_main.py
     ```

3. Access interface at `http://localhost:7860`

4. (Optional) Before running the application, execute the following script to crawl data and save to `output/`:
    ```bash
    `python crawler_from_index.py`
    ```
    
5. (Optional) Please note that the model **GanymedeNil/text2vec-large-chinese** also needs to be downloaded in advance for proper embedding-based search.


## ⚠️ Important Notes
- Ensure Elasticsearch is running and configured correctly
- Verify your ZhipuAI API key is valid
