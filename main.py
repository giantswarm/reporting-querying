import os
import json
import datetime
from elasticsearch import Elasticsearch

RULES_FILE = './queries.json'
TODAY_INDEX = datetime.datetime.now().strftime("%y-%m-%d")
ALERTS_HISTORY_DAYS = os.environ['DAYS_HISTORY']
host, INDEX_PROCESSOR = os.environ['ELASTICSEARCH_INDEX_URL_PROCESSOR'].rsplit('/', 1)
_, INDEX_ALERTS = os.environ['ELASTICSEARCH_INDEX_URL_ALERTS'].rsplit('/', 1)
es = Elasticsearch([host])

def get_alerts(rules):
  alerts = {
    'date': TODAY_INDEX,
    'timestamp': datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    'items': []
  }
  for rule in rules['list']:
    rule_alerts = get_alert(rule)
    alerts['items'].append(rule_alerts)

  return alerts

def get_alert(rule):
  rule_alerts = {
    'name': rule['name'],
    'description': rule['description'],
    'severity': rule['severity'],
    'resources': []
  }

  query = json.loads(rule['query'])
  alerts = search_alerts(query)
  print("Got %d alerts for alert %s" % (len(alerts), rule['name']))
  for alert in alerts:
    rule_alerts['resources'].append({
      'pod': alert["_source"]["metadata"]["name"],
      'namespace': alert["_source"]["metadata"]["namespace"]
    })

  return rule_alerts

def search_alerts(query):
  res = es.search(index=INDEX_PROCESSOR, body={"query": query})

  return res['hits']['hits']

def save_alerts(alerts):
  res = es.index(index=INDEX_ALERTS, doc_type='_doc', id=TODAY_INDEX, body=alerts)
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