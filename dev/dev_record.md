


```
➜  /workspace git:(master) docker ps
CONTAINER ID   IMAGE                                                  COMMAND                  CREATED          STATUS                    PORTS                                                                                  NAMES
5269a5f6ae53   docker.elastic.co/kibana/kibana:8.11.0                 "/bin/tini -- /usr/l…"   23 seconds ago   Up 10 seconds             0.0.0.0:5601->5601/tcp, :::5601->5601/tcp                                              kibana
bc25087c87e4   docker.elastic.co/elasticsearch/elasticsearch:8.11.0   "/bin/tini -- /usr/l…"   27 seconds ago   Up 21 seconds (healthy)   0.0.0.0:9200->9200/tcp, :::9200->9200/tcp, 0.0.0.0:9300->9300/tcp, :::9300->9300/tcp   es-node


➜  /workspace git:(master) curl http://localhost:9200
{
  "name" : "bc25087c87e4",
  "cluster_name" : "docker-cluster",
  "cluster_uuid" : "CRg92QQ1RqydolT6W1_3Xg",
  "version" : {
    "number" : "8.11.0",
    "build_flavor" : "default",
    "build_type" : "docker",
    "build_hash" : "d9ec3fa628c7b0ba3d25692e277ba26814820b20",
    "build_date" : "2023-11-04T10:04:57.184859352Z",
    "build_snapshot" : false,
    "lucene_version" : "9.8.0",
    "minimum_wire_compatibility_version" : "7.17.0",
    "minimum_index_compatibility_version" : "7.0.0"
  },
  "tagline" : "You Know, for Search"
}
➜  /workspace git:(master) 
```


# a 15M novel index 

```
GET /custom_documents/_stats/docs,store
```

```
{
  "_shards": {
    "total": 2,
    "successful": 1,
    "failed": 0
  },
  "_all": {
    "primaries": {
      "docs": {
        "count": 1,
        "deleted": 0
      },
      "store": {
        "size_in_bytes": 17065028,
        "total_data_set_size_in_bytes": 17065028,
        "reserved_in_bytes": 0
      }
    },
    "total": {
      "docs": {
        "count": 1,
        "deleted": 0
      },
      "store": {
        "size_in_bytes": 17065028,
        "total_data_set_size_in_bytes": 17065028,
        "reserved_in_bytes": 0
      }
    }
  },
  "indices": {
    "custom_documents": {
      "uuid": "kXqCo1fvS-SyRyyoO8rfLw",
      "health": "yellow",
      "status": "open",
      "primaries": {
        "docs": {
          "count": 1,
          "deleted": 0
        },
        "store": {
          "size_in_bytes": 17065028,
          "total_data_set_size_in_bytes": 17065028,
          "reserved_in_bytes": 0
        }
      },
      "total": {
        "docs": {
          "count": 1,
          "deleted": 0
        },
        "store": {
          "size_in_bytes": 17065028,
          "total_data_set_size_in_bytes": 17065028,
          "reserved_in_bytes": 0
        }
      }
    }
  }
}
```