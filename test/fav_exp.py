# -*- coding: utf-8 -*-
import configparser
import datetime
import logging
import os
import os.path
import time

from bs4 import BeautifulSoup
from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer

from common import DbUtil
from common import HttpUtil
from es import EsIndexer


cf = configparser.ConfigParser()
home_path = os.path.abspath('.')
config_path = os.path.join(home_path, "config", "fav.ini")
cf.read(config_path)

watching_path = cf.get('exp', 'watching_path')
charset = cf.get('exp', 'charset')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

es_indexer = EsIndexer()


class FavFileChangeEventHandler(LoggingEventHandler):

    def on_created(self, event):
        super(LoggingEventHandler, self).on_created(event)
        if os.path.isfile(event.src_path) == False:
            return
        if os.path.exists(event.src_path) == False:
            return;
        logging.info('Create File: ' + event.src_path)       
        with open(event.src_path, 'r', encoding=charset) as f:
            content = f.read()
            if len(content) > 0:
                soup = BeautifulSoup(content, "lxml")
                aList = soup.find_all('a')
                for a in aList:
                    self.save_page(a, event.src_path)
                    
    def on_deleted(self, event):
        super(LoggingEventHandler, self).on_deleted(event)
        source_file = os.path.basename(event.src_path);
        es_indexer.delete_index_by_source_file(source_file)
        sql = 'delete from fav_page where source_file=%s';
        rows = DbUtil.execute_update(sql, [source_file])
        logging.info("%s are deleted" % (rows))

    def on_moved(self, event):
        super(LoggingEventHandler, self).on_moved(event)
        pass

    def on_modified(self, event):
        super(LoggingEventHandler, self).on_modified(event)
        if os.path.isfile(event.src_path) == False:
            return
        if os.path.exists(event.src_path) == False:
            return;
        logging.info('Modify File: ' + event.src_path)
        with open(event.src_path, 'r', encoding='utf8') as f:
            content = f.read()
            if len(content) > 0:
                soup = BeautifulSoup(content, "lxml")
                aList = soup.find_all('a')
                for a in aList:
                    self.save_page(a, event.src_path)

    def save_page(self, a, src_path):
        title = a.string
        if title is None or len(title) == 0:
            title = 'Undefined'
        title = title.strip()
        href = a['href']
        sql = 'select count(*) from fav_page where title=%s and url=%s'
        data = DbUtil.execute_query_one(sql, [title, href])
        if list(data.values())[0] > 0:
            logging.debug("[title: %s, url: %s] exists" % (title, href))
            return
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        sql = 'insert into fav_page (title,url,created,source_file) values (%s,%s,%s,%s)'
        new_id = DbUtil.execute_insert(sql, [title, href, now, os.path.basename(src_path)])
        sql = 'select * from fav_page where id=%s'
        data = DbUtil.execute_query_one(sql, [new_id])
        logging.info("[title: %s, url: %s] handled" % (title, href))
        
        content = HttpUtil.extract_html_content(href)
        if content: 
            data['content'] = str(content).strip().replace('\r', '').replace('\n', '').replace('\t', ' ')
            es_indexer.create_index(data)


def start():
    es_indexer.create_indices()
    event_handler = FavFileChangeEventHandler()
    observer = Observer()
    observer.schedule(event_handler, watching_path, recursive=True)
    observer.start()
    logging.info("Keep watching folder: %s" % (watching_path))
    try:
        while True:
            time.sleep(3)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    print('bye')


if __name__ == '__main__':
    start()
