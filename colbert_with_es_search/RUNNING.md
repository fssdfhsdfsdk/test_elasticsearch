# 智能小说检索引擎

基于 BM25 召回 + Cross-Encoder 精排的两阶段检索架构。

## 快速开始

### 1. 启动环境

```bash
docker-compose up -d --build
```

### 2. 索引测试数据

```bash
docker exec -it search-app python main.py --mode index --file /app/data/test_novel.txt
```

### 3. 执行搜索

```bash
docker exec -it search-app python main.py --mode search --query "王熙凤出场有什么特点"
```

## 命令说明

| 命令 | 说明 |
|------|------|
| `--mode index --file <path>` | 普通模式索引（滑动窗口） |
| `--mode index-window --file <path>` | 窗口模式索引（chunk + 窗口元数据） |
| `--mode index-window --file <path> --window-size <N>` | 指定窗口大小（默认2） |
| `--mode search --query <query>` | 普通搜索 |
| `--mode search-window --query <query>` | 窗口模式搜索（返回上下文） |
| `--mode list` | 列出已索引的小说 |
| `--mode clear` | 清除索引 |
| `--top-k <N>` | 设置返回结果数量（默认5） |

## 检索模式

### 普通模式（滑动窗口）

索引时按固定字符数切分（300字/块，50字重叠），检索时直接返回匹配的内容块。

```bash
docker exec -it search-app python main.py --mode index --file /app/data/test_novel.txt
docker exec -it search-app python main.py --mode search --query "王熙凤出场"
```

### 窗口模式（chunk + 窗口元数据）

- **索引阶段**：按chunk切分，元数据存储前后N个句子的上下文
- **检索阶段**：在chunk上执行 BM25 + Cross-Encoder 精排
- **后处理**：用元数据中的上下文窗口替换chunk内容，返回更丰富的上下文

```bash
docker exec -it search-app python main.py --mode index-window --file /app/data/test_novel.txt --window-size 2
docker exec -it search-app python main.py --mode search-window --query "王熙凤出场"
```

## 添加红楼梦

将 `红楼梦.txt` 放入 `data/` 目录后执行：

```bash
docker exec -it search-app python main.py --mode index-window --file /app/data/红楼梦.txt
```

搜索示例：
```bash
docker exec -it search-app python main.py --mode search-window --query "黛玉为何要葬花"
docker exec -it search-app python main.py --mode search-window --query "贾宝玉和袭人的关系"
```

## 项目结构

```
.
├── data/                  # 小说文件目录
├── docker-compose.yml     # 环境配置
├── Dockerfile            # Python 应用镜像
├── main.py                # 主程序
└── requirements.txt       # Python 依赖
```

## 测试数据

`data/test_novel.txt` 包含红楼梦人物的测试片段，可用于快速验证系统功能。
