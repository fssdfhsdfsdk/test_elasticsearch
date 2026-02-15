import os
import sys
import argparse
import time
import re
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import CrossEncoder, SentenceTransformer

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = 9200
INDEX_NAME = "novel_index"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")
print(f"Loading Model {RERANK_MODEL_NAME} on CPU...", file=sys.stderr)
reranker = CrossEncoder(RERANK_MODEL_NAME, device="cpu")
bi_reranker = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device="cpu")


def split_into_sentences(text):
    sentence_delimiters = r"[。！？；\n]+"
    sentences = re.split(sentence_delimiters, text)
    return [s.strip() for s in sentences if s.strip()]


def read_and_chunk_file(filepath, chunk_size=300, overlap=50, window_size=0):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read().replace("\n", "")

    sentences = split_into_sentences(text)
    filename = os.path.basename(filepath)

    sentence_offsets = []
    if window_size > 0:
        pos = 0
        for s in sentences:
            s_pos = text.find(s, pos)
            if s_pos == -1:
                s_pos = pos
            sentence_offsets.append((s_pos, s_pos + len(s)))
            pos = s_pos + len(s)

    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        segment = text[i : i + chunk_size]
        if len(segment) < 20:
            continue

        doc = {"content": segment, "novel": filename, "offset": i}

        if window_size > 0:
            chunk_end = i + chunk_size
            sent_indices = []
            for idx, (s_start, s_end) in enumerate(sentence_offsets):
                if s_start < chunk_end and s_end > i:
                    sent_indices.append(idx)

            if sent_indices:
                start_idx = max(0, sent_indices[0] - window_size)
                end_idx = min(len(sentences), sent_indices[-1] + window_size + 1)
                window_sentences = sentences[start_idx:end_idx]
                doc["window_content"] = "".join(window_sentences)

        chunks.append({"_index": INDEX_NAME, "_source": doc})

    return chunks


def wait_for_es(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            if es.ping():
                print("Elasticsearch is ready!")
                return True
        except Exception:
            pass
        print(f"Waiting for Elasticsearch... ({i + 1}/{max_retries})")
        time.sleep(delay)
    return False


def index_novel(filepath, use_window=False, window_size=2):
    if not wait_for_es():
        print("Failed to connect to Elasticsearch.")
        return

    mappings = {
        "properties": {
            "content": {"type": "text", "analyzer": "standard"},
            "novel": {"type": "keyword"},
        }
    }

    if use_window:
        mappings["properties"]["window_content"] = {
            "type": "text",
            "analyzer": "standard",
        }

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": mappings,
            },
        )
        print("Index created.")

    print(f"Processing {filepath}...")

    actions = read_and_chunk_file(
        filepath, window_size=window_size if use_window else 0
    )
    index_type = "window" if use_window else "chunk"

    if actions:
        success, _ = helpers.bulk(es, actions)
        print(f"Indexed {success} {index_type}s from {filepath}.")
        es.indices.refresh(index=INDEX_NAME)
    else:
        print("No content to index.")


def search(query, top_k_recall=50, top_k_final=5, use_window=False):
    if not wait_for_es():
        print("Failed to connect to Elasticsearch.")
        return

    source_fields = ["content", "novel", "offset"]
    if use_window:
        source_fields.append("window_content")

    resp = es.search(
        index=INDEX_NAME,
        body={
            "size": top_k_recall,
            "query": {"match": {"content": query}},
            "_source": source_fields,
        },
    )

    hits = resp["hits"]["hits"]
    if not hits:
        print("No results found in recall phase.")
        return

    recall_results = []
    cross_inp = []

    total_hits = resp['hits']['total']['value']
    print(f"Total hits from search: {total_hits}")

    # Step 1: 准备rerank输入 - 始终用短content（不用window_content，太大）
    for hit in hits:
        source = hit["_source"]
        recall_results.append(source)
        # 用短content做rerank，不用合并后的window_content
        cross_inp.append([query, source["content"]])

    # Step 2: Cross-Encoder rerank on SHORT content
    scores = reranker.predict(cross_inp)

    # Step 3: 按分数排序
    ranked_hits = sorted(zip(recall_results, scores), key=lambda x: x[1], reverse=True)


    print(f"Reranked hits: {len(ranked_hits)}")

    # Step 4: 输出top-k，window模式下用window_content
    print(f"\n====== Search Results for: '{query}' ======")
    for i, (doc, score) in enumerate(ranked_hits[:top_k_final]):
        # window模式：输出window_content；普通模式：输出content
        display_content = doc.get("window_content") or doc["content"]

        # 调试：同时显示短content用于对比
        if use_window and "window_content" in doc:
            print(f"\n[Rank {i + 1}] Score: {score:.4f} | Novel: {doc['novel']}")
            print(f"  (short) ...{doc['content']}...")
            print(f"  (window) ...{display_content}...")
        else:
            print(f"\n[Rank {i + 1}] Score: {score:.4f} | Novel: {doc['novel']}")
            print(f"Content: ...{display_content}...")
        print("-" * 60)


def list_indexed_novels():
    if not wait_for_es():
        return

    if not es.indices.exists(index=INDEX_NAME):
        print("No index exists.")
        return

    resp = es.search(
        index=INDEX_NAME,
        body={
            "size": 0,
            "aggs": {"novels": {"terms": {"field": "novel", "size": 100}}},
        },
    )

    buckets = resp["aggregations"]["novels"]["buckets"]
    if not buckets:
        print("No novels indexed.")
        return

    print("=== Indexed Novels ===")
    for bucket in buckets:
        print(f"- {bucket['key']}: {bucket['doc_count']} chunks")


def clear_index():
    if not wait_for_es():
        return

    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Index {INDEX_NAME} deleted.")
    else:
        print(f"Index {INDEX_NAME} does not exist.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["index", "index-window", "search", "search-window", "list", "clear"],
        required=True,
        help="Mode: index, index-window, search, search-window, list, or clear",
    )
    parser.add_argument("--file", help="File path for indexing")
    parser.add_argument("--query", help="Query string for searching")
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of final results to return"
    )
    parser.add_argument(
        "--top-k-recall",
        type=int,
        default=50,
        help="Number of results to recall from BM25 (default: 50)",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=2,
        help="Number of sentences before/after for window context (default: 2)",
    )

    args = parser.parse_args()

    if args.mode == "index":
        if not args.file:
            print("Please provide --file for indexing.")
        else:
            index_novel(args.file, use_window=False)
    elif args.mode == "index-window":
        if not args.file:
            print("Please provide --file for indexing.")
        else:
            index_novel(args.file, use_window=True, window_size=args.window_size)
    elif args.mode == "search":
        if not args.query:
            print("Please provide --query for searching.")
        else:
            search(
                args.query,
                top_k_recall=args.top_k_recall,
                top_k_final=args.top_k,
                use_window=False,
            )
    elif args.mode == "search-window":
        if not args.query:
            print("Please provide --query for searching.")
        else:
            search(
                args.query,
                top_k_recall=args.top_k_recall,
                top_k_final=args.top_k,
                use_window=True,
            )
    elif args.mode == "list":
        list_indexed_novels()
    elif args.mode == "clear":
        clear_index()
