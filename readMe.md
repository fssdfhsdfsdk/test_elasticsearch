
```
docker-compose up -d
# 等待30秒后验证
curl http://localhost:9200          # 应返回ES版本信息
open http://localhost:5601          # 访问Kibana（Dev Tools路径：Stack Management > Dev Tools）
```

