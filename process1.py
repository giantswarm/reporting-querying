import os
import json
import datetime
from elasticsearch import Elasticsearch


host, processing_index = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSING'].rsplit('/', 1)
_, alert_index = os.environ['ELASTICSEARCH_INDEX_URL_ALERTS'].rsplit('/', 1)
es = Elasticsearch([host])


with open('/usr/src/app/queries.json') as f:
  rules = json.load(f)

  datestring = datetime.datetime.now().strftime("%y-%m-%d")
  data = {
    'date': datestring,
    'items': []
  }
  for rule in rules['list']:
    print("Query %s" % rule['query'])
    query = json.loads(rule['query'])
    res = es.search(index=processing_index, body={"query": query})
    print("Got %d alerts for alert %s:" % (res['hits']['total'], rule['name']))

    rule_alerts = {
      'name': rule['name'],
      'description': rule['description'],
      'severity': rule['severity'],
      'alerts': rule['description']
    }
    for doc in res['hits']['hits']:
      rule_alerts['alerts'].append(doc["_source"])

  res = es.index(index=alert_index, doc_type='_doc', id=datestring, body=data)
