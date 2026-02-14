# index_files.py
from elasticsearch import Elasticsearch
from pathlib import Path
import hashlib, time

es = Elasticsearch("http://localhost:9200")
INDEX_NAME = "custom_documents"

# 创建索引（含中文分词优化）
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, body={
        "settings": {
            "analysis": {
                "analyzer": {
                    "my_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",  # 需提前安装IK插件（见附录）
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "content": {"type": "text", "analyzer": "my_analyzer"},
                "filename": {"type": "keyword"},
                "path": {"type": "keyword"},
                "last_modified": {"type": "date"},
                "file_hash": {"type": "keyword"}
            }
        }
    })

def index_file(file_path: Path):
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    file_hash = hashlib.md5(content.encode()).hexdigest()
    
    # 避免重复索引（基于内容哈希）
    query = {"query": {"term": {"file_hash": file_hash}}}
    if es.search(index=INDEX_NAME, body=query)['hits']['total']['value'] > 0:
        return False
    
    doc = {
        "content": content,
        "filename": file_path.name,
        "path": str(file_path),
        "last_modified": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(file_path.stat().st_mtime)),
        "file_hash": file_hash,
        "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    es.index(index=INDEX_NAME, document=doc, id=str(file_path))
    return True

# 批量索引目录
for file in Path("/your/docs").rglob("*.txt"):
    if index_file(file):
        print(f"✓ 索引: {file.name}")