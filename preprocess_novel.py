# preprocess_novel.py - 使用 spaCy 中文模型提取人物
import spacy
from elasticsearch import Elasticsearch
from pathlib import Path

# 加载中文NLP模型（首次运行需下载：python -m spacy download zh_core_web_sm）
nlp = spacy.load("zh_core_web_sm") 

# 预定义小说人物词典（避免NLP漏识别）
CHARACTER_DICT = ["林黛玉", "贾宝玉", "薛宝钗", "王熙凤"] 

def extract_characters(text):
    """提取文本中出现的人物（结合词典+NER）"""
    # 方法1：基于预定义词典匹配
    found = [char for char in CHARACTER_DICT if char in text]
    
    # 方法2：NLP实体识别（补充词典未覆盖人物）
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON" and ent.text not in found:
            found.append(ent.text)
    
    return list(set(found))  # 去重

# 索引小说段落（按500字分块）
es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "novel_segments"

if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, body={
        "settings": {
            "analysis": {
                "analyzer": {
                    "novel_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "content": {"type": "text", "analyzer": "novel_analyzer"},
                "chapter": {"type": "integer"},
                "paragraph_start": {"type": "integer"},  # 段落起始位置
                "characters": {  # 关键：人物标签数组
                    "type": "keyword"
                },
                "events": {  # 事件标签（后续用）
                    "type": "keyword"
                }
            }
        }
    })

# 分块索引示例（简化版）
novel_text = Path("dream_of_red_mansion.txt").read_text(encoding="utf-8")
chunk_size = 500

for i in range(0, len(novel_text), chunk_size):
    chunk = novel_text[i:i+chunk_size]
    chars = extract_characters(chunk)
    
    es.index(index=INDEX_NAME, document={
        "content": chunk,
        "chapter": i // 10000 + 1,  # 简化章节计算
        "paragraph_start": i,
        "characters": chars,
        "events": []  # 后续补充
    })