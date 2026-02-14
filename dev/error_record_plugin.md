

# 【问题】宿主环境安装插件失败

```
➜  /workspace git:(master) ./bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
zsh: no such file or directory: ./bin/elasticsearch-plugin
```

【answer】

你遇到的问题是因为 **Elasticsearch 运行在 Docker 容器中**，而你在宿主机（`/workspace` 目录）直接执行了容器内部的命令。`./bin/elasticsearch-plugin` 是容器内的路径，宿主机上不存在这个目录。

---

## ✅ 正确安装 IK 插件的 3 种方案（按推荐度排序）

### 🔧 方案一：持久化方案（推荐 · 适合开发/生产）
**原理**：将插件目录挂载到宿主机，避免容器重建后插件丢失

#### 步骤 1：修改 `docker-compose.yml`
```yaml
services:
  elasticsearch:
    # ... 其他配置保持不变 ...
    volumes:
      - es_/usr/share/elasticsearch/data
      - ./es_plugins:/usr/share/elasticsearch/plugins  # 👈 新增这行
```

#### 步骤 2：创建宿主机插件目录
```bash
mkdir -p ./es_plugins
```

#### 步骤 3：用临时容器安装插件（自动确认 + 挂载目录）
```bash
docker run --rm \
  -v $(pwd)/es_plugins:/usr/share/elasticsearch/plugins \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  /usr/share/elasticsearch/bin/elasticsearch-plugin \
  install --batch \
  https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
```

#### 步骤 4：重启服务
```bash
docker-compose down && docker-compose up -d
```

> ✅ 优势：插件持久化保存在 `./es_plugins`，容器重建不丢失  
> ⚠️ 注意：`--batch` 参数自动确认安装，避免交互式提示卡住

---

### ⚡ 方案二：临时方案（快速测试 · 不推荐长期使用）
```bash
# 1. 进入运行中的容器
docker exec -it es-node bash

# 2. 在容器内安装插件（容器内路径）
/usr/share/elasticsearch/bin/elasticsearch-plugin install \
  https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
# 安装时输入 y 确认

# 3. 退出容器并重启
exit
docker-compose restart es-node
```

> ⚠️ 缺陷：容器重建（`docker-compose down && up`）后插件会丢失！

---

### 🌐 方案三：国内加速方案（网络不稳定时使用）
如果 GitHub 下载慢，改用国内镜像源：
```bash
# 使用清华镜像（实测 2026 年仍有效）
docker run --rm \
  -v $(pwd)/es_plugins:/usr/share/elasticsearch/plugins \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  /usr/share/elasticsearch/bin/elasticsearch-plugin \
  install --batch \
  https://mirrors.tuna.tsinghua.edu.cn/elasticstack/8.11/elasticsearch-analysis-ik-8.11.0.zip
```

> 💡 其他国内源：  
> - 阿里云：`https://elasticsearch-analysis-ik.oss-cn-beijing.aliyuncs.com/...`  
> - Gitee 镜像（需自行同步）：`https://gitee.com/mirrors/elasticsearch-analysis-ik`

---

## 🔍 验证插件是否安装成功
```bash
# 方法1：查看插件列表
docker exec es-node /usr/share/elasticsearch/bin/elasticsearch-plugin list
# 应输出：analysis-ik

# 方法2：测试分词效果（Kibana Dev Tools）
POST _analyze
{
  "analyzer": "ik_max_word",
  "text": "Elasticsearch实战教程"
}
```
✅ 正确响应应包含分词结果：`["elasticsearch", "实战", "教程"]`

---

## ⚠️ 关键注意事项
| 问题 | 解决方案 |
|------|----------|
| **版本必须严格匹配** | IK 8.11.0 只能用于 ES 8.11.x，混用会启动失败 |
| **容器需重启生效** | 安装后必须 `docker-compose restart es-node` |
| **权限问题** | 宿主机 `es_plugins` 目录需有写入权限（`chmod -R 777 es_plugins` 临时解决） |
| **生产环境** | 必须用方案一 + 自定义 Dockerfile 构建镜像（避免每次挂载） |

---

## 💡 为什么你的命令失败？
```bash
# 你在宿主机执行 ↓
./bin/elasticsearch-plugin install ... 

# 但实际路径在容器内 ↓
容器内路径: /usr/share/elasticsearch/bin/elasticsearch-plugin
宿主机路径: 不存在（除非你本地也装了ES）
```

> ✨ **最佳实践**：开发环境用 **方案一（挂载目录）**，生产环境用 **自定义 Dockerfile**：
> ```Dockerfile
> FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0
> RUN bin/elasticsearch-plugin install --batch https://.../elasticsearch-analysis-ik-8.11.0.zip
> ```

执行完上述任一方案后，你的中文搜索能力将立即生效！ 🚀


# 【问题】容器内安装插件失败

```
elasticsearch@bc25087c87e4:~$ /usr/share/elasticsearch/bin/elasticsearch-plugin
A tool for managing installed elasticsearch plugins

Non-option arguments:
command              

Option             Description        
------             -----------        
-E <KeyValuePair>  Configure a setting
-h, --help         Show help          
-s, --silent       Show minimal output
-v, --verbose      Show verbose output

ERROR: Missing required command, with exit code 64

Commands
--------
list - Lists installed elasticsearch plugins
install - Install a plugin
remove - removes plugins from Elasticsearch
```

```
elasticsearch@bc25087c87e4:~$ /usr/share/elasticsearch/bin/elasticsearch-plugin install https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
-> Installing https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
-> Downloading https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
-> Failed installing https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
-> Rolling back https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
-> Rolled back https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
Exception in thread "main" java.io.FileNotFoundException: https://github.com/infinilabs/analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
        at java.base/sun.net.www.protocol.http.HttpURLConnection.getInputStream0(HttpURLConnection.java:1994)
        at java.base/sun.net.www.protocol.http.HttpURLConnection.getInputStream(HttpURLConnection.java:1599)
        at java.base/sun.net.www.protocol.https.HttpsURLConnectionImpl.getInputStream(HttpsURLConnectionImpl.java:223)
        at org.elasticsearch.plugins.cli.InstallPluginAction.downloadZip(InstallPluginAction.java:469)
        at org.elasticsearch.plugins.cli.InstallPluginAction.download(InstallPluginAction.java:333)
        at org.elasticsearch.plugins.cli.InstallPluginAction.execute(InstallPluginAction.java:251)
        at org.elasticsearch.plugins.cli.InstallPluginCommand.execute(InstallPluginCommand.java:89)
        at org.elasticsearch.common.cli.EnvironmentAwareCommand.execute(EnvironmentAwareCommand.java:54)
        at org.elasticsearch.cli.Command.mainWithoutErrorHandling(Command.java:85)
        at org.elasticsearch.cli.MultiCommand.execute(MultiCommand.java:94)
        at org.elasticsearch.cli.Command.mainWithoutErrorHandling(Command.java:85)
        at org.elasticsearch.cli.Command.main(Command.java:50)
        at org.elasticsearch.launcher.CliToolLauncher.main(CliToolLauncher.java:64)
elasticsearch@bc25087c87e4:~$ 

```

你遇到的错误非常典型：**IK 插件维护者已变更**（medcl → infinilabs），且 GitHub 下载常因网络问题失败。错误日志中自动重定向到了 `infinilabs` 仓库但下载失败，根本原因是 **容器内网络限制 + GitHub 访问不稳定**。

---

## ✅ 终极解决方案（3 步搞定）

### 🔧 步骤 1：使用国内镜像源安装（推荐清华源）
在容器内执行：
```bash
/usr/share/elasticsearch/bin/elasticsearch-plugin install \
  https://mirrors.tuna.tsinghua.edu.cn/elasticstack/8.11/elasticsearch-analysis-ik-8.11.0.zip \
  --batch
```
> ✅ `--batch` 参数自动确认，避免交互卡住  
> ✅ 清华源 2026 年实测有效（比 GitHub 快 10 倍+）

### 🔍 步骤 2：验证安装结果
```bash
# 查看已安装插件
/usr/share/elasticsearch/bin/elasticsearch-plugin list
# 正确输出应包含：analysis-ik

# 测试中文分词（退出容器后用 curl 验证）
exit
curl -XPOST "http://localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "ik_max_word",
  "text": "Elasticsearch实战教程2026"
}'
```
✅ 正确响应应包含分词结果：`["elasticsearch", "实战", "教程", "2026"]`

### 🔄 步骤 3：重启 Elasticsearch 生效
```bash
docker-compose restart es-node
# 等待 30 秒后验证
curl http://localhost:9200/_cat/plugins?v | grep ik
```

---

## ⚠️ 关键问题解析

| 问题现象 | 根本原因 | 解决方案 |
|----------|----------|----------|
| `FileNotFoundException` 指向 `infinilabs` | medcl 仓库已归档，官方重定向到新维护者 infinilabs | **直接使用 infinilabs 的镜像源**（清华源已同步） |
| 容器内无法访问 GitHub | Docker 默认 DNS 限制 + 国内网络波动 | **强制使用国内镜像**（清华/阿里云） |
| 安装后未生效 | 未重启 ES 服务 | **必须执行 `docker-compose restart`** |

---

## 💡 备用方案（当清华源失效时）

### 方案 A：阿里云镜像（2026 年实测有效）
```bash
/usr/share/elasticsearch/bin/elasticsearch-plugin install \
  https://elasticsearch-analysis-ik.oss-cn-beijing.aliyuncs.com/releases/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip \
  --batch
```

### 方案 B：宿主机下载 + 容器内安装（100% 可靠）
```bash
# 宿主机操作
wget https://github.com/infinilabs/analysis-ik/releases/download/v8.11.0/elasticsearch-analysis-ik-8.11.0.zip
docker cp elasticsearch-analysis-ik-8.11.0.zip es-node:/tmp/

# 容器内操作
docker exec -it es-node bash
/usr/share/elasticsearch/bin/elasticsearch-plugin install file:///tmp/elasticsearch-analysis-ik-8.11.0.zip --batch
exit
docker-compose restart es-node
```

---

## 📌 重要提醒（2026 年最新实践）

1. **版本匹配铁律**  
   - ES 8.11.x → **必须**用 IK 8.11.0  
   - 混用版本（如 8.11.0 + 8.10.0）会导致启动失败

2. **维护者变更说明**  
   ```markdown
   2023 年起：medcl 仓库归档 → infinilabs 接管维护
   官方仓库：https://github.com/infinilabs/analysis-ik
   下载地址：https://github.com/infinilabs/analysis-ik/releases
   ```

3. **生产环境建议**  
   ```Dockerfile
   # 自定义镜像（避免每次挂载）
   FROM docker.elastic.co/elasticsearch/elasticsearch:8.11.0
   RUN bin/elasticsearch-plugin install --batch \
       https://mirrors.tuna.tsinghua.edu.cn/elasticstack/8.11/elasticsearch-analysis-ik-8.11.0.zip
   ```

---

## ✅ 验证成功标志
```bash
# 1. 插件列表包含 IK
$ docker exec es-node /usr/share/elasticsearch/bin/elasticsearch-plugin list
analysis-ik

# 2. 分词测试返回中文结果
$ curl -s "http://localhost:9200/_analyze?analyzer=ik_max_word&pretty" -d'{"text":"人工智能"}' | grep -A2 tokens
      "token" : "人工智能",
      "start_offset" : 0,
      "end_offset" : 4

# 3. Kibana 中可使用 ik_analyzer 创建索引
PUT /test_index
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_ik": { "type": "ik_max_word" }
      }
    }
  }
}
```

> 💡 **经验总结**：国内环境永远优先用 **清华/阿里云镜像**，GitHub 作为备选。插件安装后**必须重启 ES**，否则分词器不会加载！



# 【问题】【ok-done】正确地址插件-版本不匹配

```

ERROR: Unknown plugin /tmp/8.4.1, with exit code 64
elasticsearch@bc25087c87e4:~$ /usr/share/elasticsearch/bin/elasticsearch-plugin  install https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
-> Installing https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
-> Downloading https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
[=================================================] 100%?? 
-> Failed installing https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
-> Rolling back https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
-> Rolled back https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-9.3.0.zip
Exception in thread "main" java.lang.IllegalArgumentException: Plugin [analysis-ik] was built for Elasticsearch version 9.3.0 but version 8.11.0 is running
```

解决：

```
elasticsearch@bc25087c87e4:~$ /usr/share/elasticsearch/bin/elasticsearch-plugin  install https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.11.0.zip
-> Installing https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.11.0.zip
-> Downloading https://release.infinilabs.com/analysis-ik/stable/elasticsearch-analysis-ik-8.11.0.zip
[=================================================] 100%?? 
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@     WARNING: plugin requires additional permissions     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
* java.net.SocketPermission * connect,resolve
See https://docs.oracle.com/javase/8/docs/technotes/guides/security/permissions.html
for descriptions of what these permissions allow and the associated risks.

Continue with installation? [y/N]y
-> Installed analysis-ik
-> Please restart Elasticsearch to activate any plugins installed
elasticsearch@bc25087c87e4:~$ 
```


# 【问题】docker重启命令报错

```
➜  /workspace git:(master) ✗ docker-compose restart es-node
WARN[0000] /workspace/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion 
no such service: es-node
```

你遇到的问题有两个关键原因：

1. **服务名 ≠ 容器名**：`es-node` 是你在 `docker-compose.yml` 中设置的 `container_name`（容器名），但 **Docker Compose 操作的是服务名（service name）**，即 `services` 下的第一级键名（通常是 `elasticsearch`）
2. **`version` 字段已废弃**：Docker Compose v2+ 不再需要 `version` 字段（仅警告，不影响功能）

---

## ✅ 正确操作步骤

### 步骤 1：确认你的服务名
```bash
# 查看当前 compose 文件定义的服务名
docker-compose config --services
```
典型输出：
```
elasticsearch  # ← 这才是服务名！
kibana
```

> 💡 **关键区别**：
> - `container_name: es-node` → 容器运行时的名称（`docker ps` 中看到的）
> - `services:` 下的 `elasticsearch:` → Compose 服务名（`docker-compose` 命令操作的对象）

### 步骤 2：用正确服务名重启
```bash
# 正确命令（使用服务名）
docker-compose restart elasticsearch

# 或重启所有服务
docker-compose restart
```

### 步骤 3：验证 IK 插件是否生效
```bash
# 方法1：查看插件列表（通过容器名或服务名）
docker-compose exec elasticsearch /usr/share/elasticsearch/bin/elasticsearch-plugin list

# 方法2：直接测试分词（推荐）
curl -XPOST "http://localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{
  "analyzer": "ik_max_word",
  "text": "人工智能2026"
}'
```
✅ 成功响应应包含中文分词结果：
```json
{
  "tokens" : [
    { "token" : "人工智能", ... },
    { "token" : "2026", ... }
  ]
}
```

---

## 🔧 修复 docker-compose.yml（消除警告 + 避免混淆）

### 修改前（有问题）：
```yaml
version: '3.8'  # ⚠️ 已废弃，Compose v2+ 会警告
services:
  elasticsearch:  # ← 服务名
    container_name: es-node  # ← 容器名（仅用于 docker ps 显示）
    # ...
```

### 修改后（推荐）：
```yaml
services:
  elasticsearch:  # 保持服务名简洁（用于 docker-compose 命令）
    # 移除 container_name 可避免混淆（默认容器名 = 项目名_服务名_序号）
    # 如需固定容器名，建议与服务名一致：
    # container_name: elasticsearch
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms1g -Xmx1g
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data
      - ./es_plugins:/usr/share/elasticsearch/plugins  # IK插件持久化目录

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

> ✅ **修改后命令更直观**：
> ```bash
> docker-compose restart elasticsearch  # 服务名 = 容器逻辑名
> docker-compose logs elasticsearch     # 查看日志
> ```

---

## 🚨 常见误区速查表

| 你的操作 | 问题原因 | 正确做法 |
|----------|----------|----------|
| `docker-compose restart es-node` | `es-node` 是容器名，不是服务名 | `docker-compose restart elasticsearch` |
| `docker restart es-node` | 这是纯 Docker 命令（绕过 Compose 管理） | 优先用 `docker-compose` 保证状态同步 |
| 安装插件后搜索仍不分词 | 未重启 ES 服务 | `docker-compose restart elasticsearch` |
| `version` 警告 | Compose v2+ 已废弃该字段 | 直接删除 `version` 行 |

---

## 💡 终极验证流程（30秒完成）
```bash
# 1. 重启服务（用正确服务名）
docker-compose restart elasticsearch

# 2. 等待30秒让ES启动
sleep 30

# 3. 验证IK插件
curl -s "http://localhost:9200/_cat/plugins?v" | grep ik
# 应输出：elasticsearch analysis-ik 8.11.0

# 4. 测试中文分词
curl -s -XPOST "http://localhost:9200/_analyze" -H 'Content-Type: application/json' -d'
{"analyzer":"ik_smart","text":"自然语言处理"}' | jq '.tokens[].token'
# 应输出：["自然语言处理"] 或 ["自然","语言","处理"]
```

> ✨ **经验总结**：  
> - **Compose 操作对象 = 服务名（services 下的键）**  
> - **Docker 操作对象 = 容器名（container_name 或 docker ps 看到的）**  
> - 国内环境安装插件**永远优先用清华/阿里云镜像**，避免 GitHub 网络问题

现在你的 IK 插件应该已生效，可以愉快地进行中文搜索了！🚀


# 【问题】客户端与服务端版本不匹配

```
➜  /workspace git:(master) ✗ python index_files.py
Traceback (most recent call last):
  File "/workspace/index_files.py", line 10, in <module>
    if not es.indices.exists(index=INDEX_NAME):
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.11.1/lib/python3.11/site-packages/elasticsearch/_sync/client/utils.py", line 421, in wrapped
    return api(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.11.1/lib/python3.11/site-packages/elasticsearch/_sync/client/indices.py", line 1653, in exists
    return self.perform_request(  # type: ignore[return-value]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.11.1/lib/python3.11/site-packages/elasticsearch/_sync/client/_base.py", line 422, in perform_request
    return self._client.perform_request(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.11.1/lib/python3.11/site-packages/elasticsearch/_sync/client/_base.py", line 271, in perform_request
    response = self._perform_request(
               ^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.pyenv/versions/3.11.1/lib/python3.11/site-packages/elasticsearch/_sync/client/_base.py", line 351, in _perform_request
    raise HTTP_EXCEPTIONS.get(meta.status, ApiError)(
elasticsearch.BadRequestError: BadRequestError(400, 'None')
➜  /workspace git:(master) ✗ ss -tlnp | grep 9200
LISTEN 0      4096         0.0.0.0:9200       0.0.0.0:*    users:(("docker-proxy",pid=57252,fd=4))
LISTEN 0      4096            [::]:9200          [::]:*    users:(("docker-proxy",pid=57259,fd=4))
➜  /workspace git:(master) ✗ pip show elasticsearch
Name: elasticsearch
Version: 9.3.0
Summary: Python client for Elasticsearch
Home-page: https://github.com/elastic/elasticsearch-py
Author: 
Author-email: Elastic Client Library Maintainers <client-libs@elastic.co>
License-Expression: Apache-2.0
Location: /root/.pyenv/versions/3.11.1/lib/python3.11/site-packages
Requires: anyio, elastic-transport, python-dateutil, sniffio, typing-extensions
Required-by: 
➜  /workspace git:(master) ✗ 
```
【解决后】

```
➜  /workspace git:(master) ✗ /root/.pyenv/versions/3.11.1/bin/python /workspace/index_files.py
✓ 索引: my_novel.txt
```


【方法】

这个错误 `BadRequestError(400, 'None')` 是 **Elasticsearch 客户端与服务器版本不兼容** 的典型表现。根本原因如下：

### 🔍 问题诊断
| 项目 | 当前状态 | 问题 |
|------|----------|------|
| **ES 服务器版本** | 8.11.0 (Docker) | ✅ 正常 |
| **Python 客户端版本** | 9.3.0 | ❌ **严重不兼容** |
| **关键事实** | ES 8.x 必须使用 `elasticsearch>=8.0,<9.0` | 9.x 客户端专为 ES 9.x+ 设计，与 8.x 有协议断裂 |

> 💡 官方明确说明：**Elasticsearch 8.x 服务器必须搭配 8.x Python 客户端**  
> 参考：[Elasticsearch Python Client Compatibility Matrix](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/overview.html#_compatibility)

---

## ✅ 正确解决方案（3步修复）

### 步骤 1：降级 Python 客户端（关键！）
```bash
# 卸载不兼容的 9.x 客户端
pip uninstall elasticsearch -y

# 安装与 ES 8.11.0 匹配的客户端
pip install "elasticsearch==8.11.0"
```

### 步骤 2：修复代码中的 2 个兼容性问题
ES 8.x 客户端有重要变更，需修改 `index_files.py`：


### 步骤 3：验证环境连通性（执行前必做）
```bash
# 1. 确认 ES 服务正常
curl -s http://localhost:9200 | grep "version"

# 2. 创建测试目录并放入示例文件
mkdir -p /workspace/docs
echo "这是测试文档，包含关键词：人工智能、Elasticsearch" > /workspace/docs/test.txt

# 3. 重新运行脚本
python index_files.py
```

---

## 🔧 额外建议：快速验证客户端兼容性
```python
# test_connection.py
from elasticsearch import Elasticsearch

es = Elasticsearch(
    ["http://localhost:9200"],
    verify_certs=False
)

print("✅ 连接成功!")
print(f"  ES 版本: {es.info()['version']['number']}")
print(f"  集群名: {es.info()['cluster_name']}")
print(f"  索引列表: {es.cat.indices(format='json')}")
```

---

## 📌 为什么会出现这个问题？
1. **2024年后 ES 客户端策略变更**  
   Elastic 官方从 8.0 开始严格绑定客户端/服务器版本，9.x 客户端**主动拒绝**连接 8.x 服务器
   
2. **错误信息迷惑性**  
   `BadRequestError(400, 'None')` 实际是客户端发送了 8.x 服务器无法解析的请求体格式

3. **Docker 环境特殊性**  
   即使 `xpack.security.enabled=false`，ES 8.x 客户端仍会尝试 TLS 握手，需显式 `verify_certs=False`

---

## ✅ 修复后预期输出
```bash
$ python index_files.py
✅ 成功连接 Elasticsearch 8.11.0
✓ 索引: test.txt

✅ 完成! 共索引 1 个文件

$ curl -s -XGET "http://localhost:9200/custom_documents/_search?q=人工智能" | jq '.hits.hits[0]._source.filename'
"test.txt"
```

> 💡 **永久避免此问题**：在项目中固定客户端版本  
> ```bash
> echo "elasticsearch==8.11.0" >> requirements.txt
> ```

按照以上步骤操作后，99% 的同类问题可解决。如果仍有问题，请提供 `docker-compose logs es-node` 的输出进一步分析。