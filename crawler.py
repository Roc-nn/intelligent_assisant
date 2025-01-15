import requests
from bs4 import BeautifulSoup
import json
import logging
import os

# 配置日志记录
logging.basicConfig(
    filename='crawler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 目标页面 URL
URL = "https://gdstc.gd.gov.cn/zwgk_n/zcfg/gfwj/content/post_4646913.html"

# JSON 文件保存目录
os.makedirs("output", exist_ok=True)

def fetch_page(url):
    """获取页面内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功
        logging.info(f"成功访问页面：{url}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"访问页面失败：{url}，错误信息：{e}")
        raise

def parse_page(html):
    """解析页面内容"""
    try:
        soup = BeautifulSoup(html, "lxml")

        # 提取标题
        title_element = soup.select_one("h3.zw-title")
        title = title_element.get_text(strip=True) if title_element else "未知标题"

        # 提取时间
        time_element = soup.select_one("span.time")
        time = time_element.get_text(strip=True).replace("时间  :  ", "") if time_element else "未知时间"

        # 提取来源
        source_element = soup.select_one("span.ly")
        source = source_element.get_text(strip=True).replace("来源  :  ", "") if source_element else "未知来源"

        # 提取正文内容
        content_div = soup.select_one("div.zw")
        if content_div:
            content = "\n".join(p.get_text(strip=True) for p in content_div.find_all("p"))
        else:
            content = "正文内容提取失败"

        logging.info(f"成功解析页面内容：标题 - {title}")
        return {
            "标题": title,
            "时间": time,
            "来源": source,
            "内容": content
        }
    except Exception as e:
        logging.error(f"解析页面失败：错误信息：{e}")
        raise

def save_to_json(data, filename):
    """保存数据为 JSON 文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"成功保存数据至文件：{filename}")
    except Exception as e:
        logging.error(f"保存数据失败：{filename}，错误信息：{e}")
        raise

def main():
    try:
        # Step 1: 获取页面内容
        html = fetch_page(URL)

        # Step 2: 解析页面内容
        data = parse_page(html)

        # Step 3: 保存数据为 JSON 文件
        save_to_json(data, "output/policy.json")
    except Exception as e:
        logging.error(f"爬取任务失败：{e}")

if __name__ == "__main__":
    main()