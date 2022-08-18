'''
Created on 2021年10月21日

@author: fengyan
'''
import configparser
import datetime
import time
import json
import logging
import os

from elasticsearch import Elasticsearch

from common import DbUtil
from common import HttpUtil

cf = configparser.ConfigParser()
home_path = os.path.abspath('.')
config_path = os.path.join(home_path, "config", "fav.ini")
cf.read(config_path)

es_index_name = cf.get('es', 'index_name')
es_cluster_name = cf.get('es', 'cluster_name')
es_host = cf.get('es', 'host')
es_port = cf.getint('es', 'port')
es_user = cf.get('es', 'user')
es_password = cf.get('es', 'password')
watching_path = cf.get('exp', 'watching_path')

es_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties":{
                "id":{
                    "type": "integer",
                    "index": False,
                    "store": True
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                    "term_vector": "with_positions_offsets_payloads",
                    "index": True,
                    "store": True
                },
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word",
                    "search_analyzer": "ik_smart",
                    "term_vector": "with_positions_offsets_payloads",
                    "index": True,
                    "store": True
                },
                "url": {
                    "type": "keyword",
                    "index": True,
                    "store": True
                },
                "source_file": {
                    "type": "keyword",
                    "index": True,
                    "store": True
                },
                "created":{
                    "type": "date",
                    "index": False,
                    "store": True
                }
            }
        }
    }

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class EsIndexer:
    
    def __init__(self):
        self.client = Elasticsearch(cluster=es_cluster_name, host=es_host, port=es_port, http_auth=(es_user, es_password))
        pass
    
    def check_indices_exists(self):
        if self.client.indices.exists(index=es_index_name) == False:
            raise RuntimeError('')
    
    def delete_indices(self):
        if self.client.indices.exists(index=es_index_name):
            self.client.indices.delete(index=es_index_name)
        
    def create_indices(self):
        if self.client.indices.exists(index=es_index_name) == False:
            self.client.indices.create(index=es_index_name, body=es_body)
            logging.info("Index name '%s' is created" % es_index_name)
    
    def delete_index_by_source_file(self, source_file):
        self.check_indices_exists()
        if self.get_index_count() > 0:
            query = {'query': {'term': {'source_file': source_file}}}
            self.client.delete_by_query(index=es_index_name, body=query)
            logging.info("Index for source_file '%s' is deleted" % source_file)
            
    def create_index(self, data):
        self.check_indices_exists()
        data['created'] = datetime.datetime.now()
        self.client.index(index=es_index_name, doc_type="_doc", body=json.dumps(data, cls=JsonDateEncoder))
        logging.info("[title: %s, url: %s] is indexed" % (data['title'], data['url']))
        
    def get_index_count(self):
        self.check_indices_exists()
        query = {'query': {'match_all': {}}}
        return self.client.count(index=es_index_name, body=query)['count']
        
    def delete_all_index(self):
        self.check_indices_exists()
        query = {'query': {'match_all': {}}}
        self.client.delete_by_query(index=es_index_name, body=query)
        logging.info("All indexes are deleted")
        
    def recreate_all_indexes(self):
        self.delete_all_index()
        sql = 'select count(*) from fav_page'
        data = DbUtil.execute_query_one(sql, [])
        db_rows = list(data.values())[0]
        if db_rows > 0:
            sql = 'select * from fav_page'
            DbUtil.execute_query(sql, [], self.callback)
            ex_rows = self.get_index_count()
            return (db_rows, ex_rows)
        return (0, 0)
    
    def callback(self, row):
        href = row['url']
        content = HttpUtil.extract_html_content(href)
        if content: 
            data = row.copy()
            data['content'] = str(content).strip().replace('\r', '').replace('\n', '').replace('\t', ' ')
            self.create_index(data)
        pass


class JsonDateEncoder(json.JSONEncoder): 

    def default(self, obj): 
        if isinstance(obj, datetime.datetime): 
            return obj.isoformat()  
        elif isinstance(obj, datetime.date): 
            return obj.strftime("%Y-%m-%d")
        else: 
            return json.JSONEncoder.default(self, obj)


class EsSearcher:
    
    def __init__(self):
        self.client = Elasticsearch(cluster=es_cluster_name, host=es_host, port=es_port, http_auth=(es_user, es_password))
        pass
    
    def search(self, keyword):
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match": {
                                "title": keyword,
                            },
                        },
                        {
                            "match": {
                                "content": keyword,
                            },
                        },
                    ]
                }
            },
            "highlight": {
                "pre_tags": ['<font color="red">'],
                "post_tags": ['</font>'],
                "fields": {
                    "title": {
                        "type": "fvh",
                        "number_of_fragments": 3,
                        "fragment_size": 210
                    },
                    "content": {
                        "type": "fvh",
                        "number_of_fragments": 3,
                        "fragment_size": 210
                    }
                }
            }
        }
        res = self.client.search(index=es_index_name, size=20, body=body)
        return self._foreach(res)
    
    def _foreach(self, res):
        data_list = []
        doc = res['hits']['hits']
        if len(doc):
            for item in doc:
                source = item['_source']
                highlight = item['highlight']
                try:
                    title = highlight['title'][0]
                except:
                    title = source['title']
                data_list.append({
                    "title": title,
                    "content": highlight['content'][0],
                    "url": source['url'],
                    "created": source['created']
                })
        return data_list


def test(keyword):
    start_time = int(round(time.time() * 1000))
    es_searcher = EsSearcher()
    data_list = es_searcher.search(keyword)
    for data in data_list:
        print(data)
    end_time = int(round(time.time() * 1000))
    print('Take: %s (ms)' % (end_time - start_time))
    
def count():
    start_time = int(round(time.time() * 1000))
    es_indexer = EsIndexer()
    count = es_indexer.get_index_count()
    end_time = int(round(time.time() * 1000))
    print(count)
    print('Take: %s (ms)' % (end_time - start_time))

def delete_index(source_file):
    start_time = int(round(time.time() * 1000))
    es_indexer = EsIndexer()
    es_indexer.delete_index_by_source_file(source_file)
    end_time = int(round(time.time() * 1000))
    print('Take: %s (ms)' % (end_time - start_time))

def clean():
    start_time = int(round(time.time() * 1000))
    es_indexer = EsIndexer()
    es_indexer.delete_indices()
    end_time = int(round(time.time() * 1000))
    print('Take: %s (ms)' % (end_time - start_time))

    
def recreate_all():
    start_time = int(round(time.time() * 1000))
    es_indexer = EsIndexer()
    total = es_indexer.recreate_all_indexes()
    end_time = int(round(time.time() * 1000))
    print('Total: %s, Take: %s (ms)' % (total, end_time - start_time))

if __name__ == '__main__':
    # test('SpringBoot')
    #recreate_all()
    # clean()
    # count()
    # delete_index('bookmarks_2021_10_22.html')
    pass
