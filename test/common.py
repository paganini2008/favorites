# -*- coding: utf-8 -*-
import configparser
import os
import sys

from bs4 import BeautifulSoup
import chardet
from dbutils.pooled_db import PooledDB
import pymysql
import requests


cf = configparser.ConfigParser()
home_path = os.path.abspath('.')
config_path = os.path.join(home_path, "config", "fav.ini")
cf.read(config_path)

host = cf.get('mysql', 'host')
port = cf.getint('mysql', 'port')
db = cf.get('mysql', 'db')
user = cf.get('mysql', 'user')
password = cf.get('mysql', 'password')

headers = {
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
            'Accept':'*/*',
            'Accept-Encoding': 'gzip, deflate, sdch'
          }

        
class HttpUtil:
    
    @staticmethod
    def extract_html_content(url):
        try:
            r = requests.get(url, timeout=(10, 50), headers=headers)
            encoding = r.apparent_encoding
            if encoding is None:
                encoding = sys.getdefaultencoding()
            html = str(r.content, encoding)
        except:
            html = ''
        if html is None or len(html) == 0:
            return
        soup = BeautifulSoup(html, "lxml")
        body = soup.find('body');
        if body is None:
            return None
        return body.text


class DbUtil:
    
    pool = PooledDB(pymysql, maxconnections=10, host=host, user=user,
                passwd=password, db=db, port=port, charset="utf8")

    @staticmethod
    def get_connection():
        return DbUtil.pool.connection()

    @staticmethod
    def execute_insert(sql, values):
        new_id = 0
        db = DbUtil.get_connection()
        cs = None
        try:
            cs = db.cursor()
            cs.execute(sql, values)
            new_id = cs.lastrowid
            db.commit()
            return new_id
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if cs:
                cs.close()
            db.close()
    
    @staticmethod
    def execute_update(sql, values):
        db = DbUtil.get_connection()
        cs = None
        try:
            cs = db.cursor()
            rows = cs.execute(sql, values)
            db.commit()
            return rows
        except Exception as e:
            db.rollback()
            raise e
        finally:
            if cs:
                cs.close()
            db.close()
            
    @staticmethod
    def execute_query_one(sql, values):
        db = DbUtil.get_connection()
        cs = None
        try:
            cs = db.cursor(pymysql.cursors.DictCursor)
            cs.execute(sql, values)
            return cs.fetchone()
        finally:
            if cs:
                cs.close()
            db.close()
    
    @staticmethod
    def execute_query(sql, values, callback):
        db = DbUtil.get_connection()
        cs = None
        try:
            cs = db.cursor(pymysql.cursors.DictCursor)
            cs.execute(sql, values)
            while 1:
                row = cs.fetchone()
                if row is None:
                    break
                callback(row)
        finally:
            if cs:
                cs.close()
            db.close()


def callback(data):
    print(data)


if __name__ == '__main__':
    url = 'https://os.51cto.com/art/202011/631053.htm'
    print(HttpUtil.extract_html_content(url))
    pass
    
