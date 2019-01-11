import os
import json
import datetime
from elasticsearch import Elasticsearch


host, processing_index = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSING'].rsplit('/', 1)
_, alert_index = os.environ['ELASTICSEARCH_INDEX_URL_ALERTS'].rsplit('/', 1)
es = Elasticsearch([host])


with open('./queries.json') as f:
  rules = json.load(f)

  datestring = datetime.datetime.now().strftime("%y-%m-%d")
  data = {
    'date': datestring,
    'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    'items': []
  }
  for rule in rules['list']:
    query = json.loads(rule['query'])
    res = es.search(index=processing_index, body={"query": query})
    print("Got %d alerts for alert %s" % (res['hits']['total'], rule['name']))

    rule_alerts = {
      'name': rule['name'],
      'description': rule['description'],
      'severity': rule['severity'],
      'resources': []
    }
    for doc in res['hits']['hits']:
      rule_alerts['resources'].append({
        'pod': doc["_source"]["metadata"]["name"],
        'namespace': doc["_source"]["metadata"]["namespace"]
      })

    data['items'].append(rule_alerts)

  res = es.index(index=alert_index, doc_type='_doc', id=datestring, body=data)
  print(data)
