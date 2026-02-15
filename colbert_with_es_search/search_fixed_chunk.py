import os
import sys
import argparse
import time
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import CrossEncoder

ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = 9200
INDEX_NAME = "novel_index"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

es = Elasticsearch(f"http://{ES_HOST}:{ES_PORT}")
print(f"Loading Model {RERANK_MODEL_NAME} on CPU...", file=sys.stderr)
reranker = CrossEncoder(RERANK_MODEL_NAME, device="cpu")


def read_and_chunk_file(filepath, chunk_size=300, overlap=50):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        return []

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read().replace("\n", "")

    chunks = []
    filename = os.path.basename(filepath)

    for i in range(0, len(text), chunk_size - overlap):
        segment = text[i : i + chunk_size]
        if len(segment) < 20:
            continue
        chunks.append(
            {
                "_index": INDEX_NAME,
                "_source": {"content": segment, "novel": filename, "offset": i},
            }
        )
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


def index_novel(filepath):
    if not wait_for_es():
        print("Failed to connect to Elasticsearch.")
        return

    if not es.indices.exists(index=INDEX_NAME):
        es.indices.create(
            index=INDEX_NAME,
            body={
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "content": {"type": "text", "analyzer": "standard"},
                        "novel": {"type": "keyword"},
                    }
                },
            },
        )
        print("Index created.")

    print(f"Processing {filepath}...")
    actions = read_and_chunk_file(filepath)

    if actions:
        success, _ = helpers.bulk(es, actions)
        print(f"Indexed {success} chunks from {filepath}.")
        es.indices.refresh(index=INDEX_NAME)
    else:
        print("No content to index.")


def search(query, top_k_recall=75, top_k_final=8):
    if not wait_for_es():
        print("Failed to connect to Elasticsearch.")
        return

    resp = es.search(
        index=INDEX_NAME,
        body={
            "size": top_k_recall,
            "query": {"match": {"content": query}},
            "_source": ["content", "novel", "offset"],
        },
    )

    hits = resp["hits"]["hits"]
    if not hits:
        print("No results found in recall phase.")
        return

    recall_results = []
    cross_inp = []

    for hit in hits:
        content = hit["_source"]["content"]
        recall_results.append(hit["_source"])
        cross_inp.append([query, content])

    scores = reranker.predict(cross_inp)

    ranked_hits = sorted(zip(recall_results, scores), key=lambda x: x[1], reverse=True)

    print(f"\n====== Search Results for: '{query}' ======")
    for i, (doc, score) in enumerate(ranked_hits[:top_k_final]):
        print(f"\n[Rank {i + 1}] Score: {score:.4f} | Novel: {doc['novel']}")
        print(f"Content: ...{doc['content']}...")
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
        choices=["index", "search", "list", "clear"],
        required=True,
        help="Mode: index, search, list, or clear",
    )
    parser.add_argument("--file", help="File path for indexing")
    parser.add_argument("--query", help="Query string for searching")
    parser.add_argument(
        "--top-k", type=int, default=5, help="Number of final results to return"
    )

    args = parser.parse_args()

    if args.mode == "index":
        if not args.file:
            print("Please provide --file for indexing.")
        else:
            index_novel(args.file)
    elif args.mode == "search":
        if not args.query:
            print("Please provide --query for searching.")
        else:
            search(args.query, top_k_final=args.top_k)
    elif args.mode == "list":
        list_indexed_novels()
    elif args.mode == "clear":
        clear_index()
