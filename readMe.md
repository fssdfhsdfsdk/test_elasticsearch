
```
docker-compose up -d
# 等待30秒后验证
curl http://localhost:9200          # 应返回ES版本信息
open http://localhost:5601          # 访问Kibana（Dev Tools路径：Stack Management > Dev Tools）
```

```
python colbert_search.py --mode index --file  ./data/dream_of_red_mansion_ch01_to_ch10.txt
python colbert_search.py --mode search --query "王熙凤出场有什么特点" 
python colbert_search.py --mode search --query "林黛玉去世" 
python colbert_search.py --mode clear

python colbert2.py --mode index-window --window-size 2 --file dpcq.txt 
python colbert2.py --mode search-window --window-size 2 --query "王熙凤出场"
```


```
curl -X GET "http://localhost:9200/custom_documents/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "content": "mc_name"
      }
    },
    "_source": ["filename", "path"],
  "highlight": {
    "fields": {
      "content": {
        "max_analyzed_offset": 60000
      }
    }
  }
  }' | jq '.' 
```