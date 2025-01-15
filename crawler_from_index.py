import requests
from bs4 import BeautifulSoup
import json
import logging
import os
import time

# 配置日志记录
logging.basicConfig(
    filename='crawler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 输出文件路径
OUTPUT_DIR = "output"
OUTPUT_FILENAME = os.path.join(OUTPUT_DIR, "country.json")

# 确保输出文件夹存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 如果文件不存在，初始化一个空 JSON 数组
if not os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

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

def parse_index_page(html):
    """解析目录页，提取子页面的链接"""
    try:
        soup = BeautifulSoup(html, "lxml")
        links = []

        # 提取每个子页面链接
        for li in soup.select("ul.list > li"):
            link_tag = li.select_one("a")
            if link_tag:
                link = link_tag["href"]  # 提取链接
                
                # 补全相对路径为绝对路径
                if not link.startswith("http"):
                    link = f"https://gdstc.gd.gov.cn{link}"
                
                links.append(link)

        logging.info(f"成功解析目录页，共找到 {len(links)} 个子页面")
        return links
    except Exception as e:
        logging.error(f"解析目录页失败：错误信息：{e}")
        raise

def parse_detail_page(html):
    """解析子页面内容"""
    try:
        soup = BeautifulSoup(html, "lxml")

        # 提取标题
        title_element = soup.select_one("h3.zw-title")
        title = title_element.get_text(strip=True) if title_element else "Unknown Title"

        # 提取时间
        time_element = soup.select_one("span.time")
        time = time_element.get_text(strip=True).replace("时间  :  ", "") if time_element else "Unknown Time"

        # 提取来源
        source_element = soup.select_one("span.ly")
        source = source_element.get_text(strip=True).replace("来源  :  ", "") if source_element else "Unknown Source"

        # 提取正文内容
        content_div = soup.select_one("div.zw")
        if content_div:
            content = "\n".join(p.get_text(strip=True) for p in content_div.find_all("p"))
        else:
            content = "Failed to extract content"

        logging.info(f"成功解析子页面内容：标题 - {title}")
        return {
            "title": title,
            "time": time,
            "source": source,
            "content": content
        }
    except Exception as e:
        logging.error(f"解析子页面失败：错误信息：{e}")
        raise

def append_to_json_file(data, filename):
    """将数据追加到 JSON 文件"""
    try:
        with open(filename, "r+", encoding="utf-8") as f:
            existing_data = json.load(f)  # 读取现有数据
            existing_data.append(data)  # 追加新数据
            f.seek(0)  # 回到文件开头
            json.dump(existing_data, f, ensure_ascii=False, indent=4)  # 写回文件
        logging.info(f"成功将数据追加到文件：{filename}")
    except Exception as e:
        logging.error(f"追加数据失败：{filename}，错误信息：{e}")
        raise

def main():
    # 目录页 URL（可以手动更改）
    index_url = input("请输入目录页的 URL: ").strip()
    try:
        # Step 1: 获取目录页内容
        index_html = fetch_page(index_url)

        # Step 2: 提取子页面链接
        links = parse_index_page(index_html)

        # Step 3: 遍历子页面链接，爬取详细内容
        for i, link in enumerate(links):
            try:
                logging.info(f"正在处理第 {i+1} 个页面：{link}")
                
                # 获取子页面内容
                detail_html = fetch_page(link)

                # 解析子页面内容
                detail_data = parse_detail_page(detail_html)

                # 过滤掉标题包含“图解”的页面
                if any(keyword in detail_data["title"] for keyword in ["图解", "视频", "媒体"]):
                    logging.info(f"跳过标题包含过滤关键字的页面：{detail_data['title']}")
                    continue

                # 追加到 JSON 文件
                append_to_json_file(detail_data, OUTPUT_FILENAME)

                # 延时以避免过快访问
                time.sleep(1)

            except Exception as e:
                logging.error(f"处理页面失败：{link}，错误信息：{e}")
                continue

        logging.info(f"所有符合条件的页面数据已追加到文件：{OUTPUT_FILENAME}")
    except Exception as e:
        logging.error(f"爬取任务失败：{e}")

if __name__ == "__main__":
    main()