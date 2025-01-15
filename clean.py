import json
import re
from datetime import datetime

# 敏感词列表及替换方式
SENSITIVE_WORDS = ["习近平", "李克强", "李强"]
REPLACEMENT = "***"

def load_json(filename):
    """加载 JSON 文件"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"成功加载数据，共 {len(data)} 条记录。")
        return data
    except Exception as e:
        print(f"加载 JSON 文件失败：{e}")
        return []

def replace_sensitive_words(text, sensitive_words, replacement):
    """替换文本中的敏感词"""
    for word in sensitive_words:
        text = text.replace(word, replacement)
    return text

def clean_data(records):
    """清洗数据"""
    cleaned_records = []
    for record in records:
        # 检查字段完整性
        if not all(key in record for key in ["title", "time", "source", "content"]):
            continue

        # 检查是否包含无效占位值
        if (
            record["title"] == "Unknown Title" or
            record["time"] == "Unknown Time" or
            record["source"] == "Unknown Source" or
            record["content"] == "Failed to extract content"
        ):
            continue

        # 替换敏感词
        record["title"] = replace_sensitive_words(record["title"], SENSITIVE_WORDS, REPLACEMENT)
        record["content"] = replace_sensitive_words(record["content"], SENSITIVE_WORDS, REPLACEMENT)

        # 标题有效性检查
        title = record["title"]
        if len(title) < 5 or re.search(r"(无效|错误|测试)", title, re.IGNORECASE):
            continue

        # 时间格式校验
        time = record["time"]
        try:
            datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue  # 跳过时间格式错误的数据

        # 来源检查
        source = record["source"]
        if not source or len(source) < 3:  # 来源为空或过短
            continue

        # 正文清洗和有效性检查
        content = record["content"]
        content = re.sub(r"\s+", " ", content).strip()  # 清理多余空格
        if len(content) < 50:  # 正文过短
            continue

        # 去除正文中不需要的内容（如广告语）
        content = re.sub(r"分享到.*$", "", content)

        # 清洗后的数据
        cleaned_record = {
            "title": title.strip(),
            "time": time.strip(),
            "source": source.strip(),
            "content": content.strip(),
        }
        cleaned_records.append(cleaned_record)

    return cleaned_records

def remove_duplicates(records):
    """去重处理"""
    seen_titles = set()
    unique_records = []

    for record in records:
        if record["title"] not in seen_titles:
            seen_titles.add(record["title"])
            unique_records.append(record)

    return unique_records

def save_json(data, filename):
    """保存数据到 JSON 文件"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"数据已成功保存至 {filename}，共 {len(data)} 条记录。")
    except Exception as e:
        print(f"保存 JSON 文件失败：{e}")

def main():
    # 输入和输出文件路径
    input_filename = "output/country.json"
    output_filename = "output/cleaned_country.json"

    # Step 1: 加载数据
    data = load_json(input_filename)
    if not data:
        print("未能加载数据，清洗流程终止。")
        return

    # Step 2: 数据清洗
    cleaned_data = clean_data(data)

    # Step 3: 去重处理
    deduplicated_data = remove_duplicates(cleaned_data)

    # Step 4: 保存清洗后的数据
    save_json(deduplicated_data, output_filename)

if __name__ == "__main__":
    main()