# relationship_analyzer.py
from elasticsearch import Elasticsearch
from collections import defaultdict
import networkx as nx  # 用于图谱计算

es = Elasticsearch("http://localhost:9200")

# 获取所有含人物的段落
query = {
  "query": {
    "bool": {
      "must": { "exists": { "field": "characters" } },
      "filter": { "script": { "script": "doc['characters'].size() > 1" } }  # 至少2人同现
    }
  },
  "size": 10000,
  "_source": ["characters", "chapter"]
}

resp = es.search(index="novel_segments", body=query)
co_occurrence = defaultdict(int)
chapter_cooccurrence = defaultdict(lambda: defaultdict(int))

for hit in resp['hits']['hits']:
    chars = hit['_source']['characters']
    chapter = hit['_source']['chapter']
    
    # 无序对：避免(A,B)和(B,A)重复计数
    for i in range(len(chars)):
        for j in range(i+1, len(chars)):
            pair = tuple(sorted([chars[i], chars[j]]))
            co_occurrence[pair] += 1
            chapter_cooccurrence[chapter][pair] += 1

# 输出Top10关系
top_relations = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:10]
print("人物关系强度（共现次数）:")
for (char1, char2), count in top_relations:
    print(f"{char1} ↔ {char2}: {count}次")


