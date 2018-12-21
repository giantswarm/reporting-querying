import os
import json
from elasticsearch import Elasticsearch


host, index_agent = os.environ['ELASTICSEARCH_INDEX_URL_AGENT'].rsplit('/', 1)
_, index_processing = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSING'].rsplit('/', 1)
es = Elasticsearch([host])


with open('queries.json') as f:
  queries = json.load(f)
  for query in queries['list']:
    res = es.search(index=index_agent, body={"query": query})
    print("Got %d Hits:" % res['hits']['total'])

    for hit in res['hits']['hits'][0:1]:
        for item in hit["_source"]["items"]:
            print(item["name"])
