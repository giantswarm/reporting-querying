import os
import json
import datetime
from elasticsearch import Elasticsearch

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
RULES_FILE = './queries.json'
TODAY_INDEX = datetime.datetime.now().strftime("%y-%m-%d")
ALERTS_HISTORY_DAYS = os.environ['DAYS_HISTORY']
host, INDEX_PROCESSOR = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSOR'].rsplit('/', 1)
_, INDEX_ALERTS = os.environ['ELASTICSEARCH_INDEX_URL_ALERTS'].rsplit('/', 1)
es = Elasticsearch([host])

def get_alerts(rules):
  alerts = []
  for rule in rules['list']:
    alerts += get_alert(rule)

  return alerts

def get_alert(rule):
  alerts = []
  alert = {
    'date': TODAY_INDEX,
    'timestamp': TIMESTAMP,
    'name': rule['name'],
    'description': rule['description'],
    'severity': rule['severity'],
    'pod': '',
    'namespace': ''
  }

  query = json.loads(rule['query'])
  docs = search_alerts(query)
  print("Got %d alerts for rule %s" % (len(alerts), rule['name']))
  for doc in docs:
    alert['pod'] = doc["_source"]["metadata"]["name"]
    alert['namespace'] = doc["_source"]["metadata"]["namespace"]
    alerts.append(alert)

  return alerts

def search_alerts(query):
  res = es.search(index=INDEX_PROCESSOR, body={"query": query})

  return res['hits']['hits']

def save_alerts(alerts):
  for alert in alerts:
    print('saving alert %s' % alert)
    res = es.index(index=INDEX_ALERTS, doc_type='_doc', body=alert)
    print(res)

def delete_proccesed_index():
  expr_date = "now-" + ALERTS_HISTORY_DAYS + "d"
  query = {
    "query": {
      "bool": {
        "must": {
          "match_all": {}
        },
        "filter": {
          "range": { "@timestamp" : { "lt" : expr_date }}
        }
      }
    }
  }
  es.delete_by_query(index=INDEX_PROCESSOR, body={"query": query} ,ignore=[400, 404])
  print('Old alerts removed')

def delete_old_alerts():
    es.indices.delete(index=INDEX_PROCESSOR, ignore=[400, 404])
    print('Processor index deleted')

def exist_processor_index():
  if not es.indices.exists(index=INDEX_PROCESSOR):
    print("Index %s not found, skipping the querying" % INDEX_PROCESSOR)
    quit()

def main():
  exist_processor_index()

  with open(RULES_FILE) as f:
    rules = json.load(f)

    alerts = get_alerts(rules)
    save_alerts(alerts)
    delete_proccesed_index()
    delete_old_alerts()
 
if __name__ == "__main__":
	main()