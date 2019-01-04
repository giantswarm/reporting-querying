import os
import json
import datetime
from elasticsearch import Elasticsearch


host, processing_index = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSING'].rsplit('/', 1)
_, alert_index = os.environ['ELASTICSEARCH_INDEX_URL_ALERTS'].rsplit('/', 1)
es = Elasticsearch([host])


with open('/usr/src/app/queries.json') as f:
  rules = json.load(f)
  for rule in rules['list']:
    print("Query %s" % rule['query'])
    query = json.loads(rule['query'])
    res = es.search(index=processing_index, body={"query": query})
    print("Got %d Hits:" % res['hits']['total'])

    if res['hits']['total'] > 0:
      print("Rule %s:" % rule['name'])

    for doc in res['hits']['hits']:
      item = doc["_source"]
      item['description'] = rule['description']
      item['severity'] = rule['severity']
      if '_lasttime_processed' not in item:
        item['_lasttime_processed'] = datetime.datetime.now()
      if 'kind' in item:
        esID = item['metadata']['uid'] + '-' + rule['name']
        res = es.index(index=alert_index, doc_type='_doc', id=esID, body=item)
        print("  Object %s matched" % item['metadata']['name'])
