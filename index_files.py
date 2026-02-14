# index_files.py (修复版)
from elasticsearch import Elasticsearch
from pathlib import Path
import hashlib, time

# ✅ 修复1: 创建客户端时必须显式关闭 SSL 验证（即使 HTTP 也需要）
es = Elasticsearch(
    ["http://localhost:9200"],
    verify_certs=False,  # 关键！ES 8.x 客户端默认尝试 HTTPS
    request_timeout=30
)

INDEX_NAME = "custom_documents"

# ✅ 修复2: ES 8.x 创建索引时 body 参数已废弃，改用 mappings/settings
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(
        index=INDEX_NAME,
        settings={
            "analysis": {
                "analyzer": {
                    "my_analyzer": {
                        "type": "custom",
                        #"tokenizer": "ik_max_word",  # 需提前安装IK插件（见附录）
                        "tokenizer": "standard",  # 暂用标准分词（IK 需额外安装）
                        "filter": ["lowercase"]
                    }
                }
            }
        },
        mappings={
            "properties": {
                "content": {"type": "text", "analyzer": "my_analyzer"},
                "filename": {"type": "keyword"},
                "path": {"type": "keyword"},
                "last_modified": {"type": "date"},
                "file_hash": {"type": "keyword"}
            }
        }
    )

def index_file(file_path: Path):
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ 读取文件失败 {file_path}: {e}")
        return False
    
    file_hash = hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()
    
    # 检查重复（基于内容哈希）
    resp = es.search(
        index=INDEX_NAME,
        query={"term": {"file_hash": file_hash}},
        size=1
    )
    if resp['hits']['total']['value'] > 0:
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

# 批量索引
docs_dir = Path("/workspace/docs")  # ✅ 请先创建此目录并放入测试文件
docs_dir.mkdir(exist_ok=True)

indexed = 0
for file in docs_dir.rglob("*"):
    if file.is_file() and file.suffix in {".txt", ".md", ".log"}:
        if index_file(file):
            print(f"✓ 索引: {file.name}")
            indexed += 1

print(f"\n✅ 完成! 共索引 {indexed} 个文件")