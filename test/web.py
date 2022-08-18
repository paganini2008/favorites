'''
Created on 2021年10月21日

@author: fengyan
'''
import json
from flask import Flask, request, render_template, Markup, jsonify
from es import EsSearcher
from es import EsIndexer

app = Flask(__name__)
es_searcher = EsSearcher()
es_indexer = EsIndexer()


@app.route('/ping')
def ping():
    r = {'code':1}
    q = request.args['q']
    if q:
        r['q'] = q
    return jsonify(r)


@app.route('/')
def index():
    return render_template('search.html')


@app.route('/search', methods=['POST'])
def search_post():
    keyword = request.form['keyword']
    data_list = es_searcher.search(keyword)
    return render_template('result.html', dataList=data_list)


@app.route('/search', methods=['GET'])
def search():
    keyword = request.args['q']
    data_list = es_searcher.search(keyword)
    return render_template('result.html', dataList=data_list)


@app.route('/recreate_all', methods=['GET'])
def recreate_all_indexes():
    es_indexer.recreate_all_indexes()
    return jsonify({'code': 1})

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15000, debug=True)
    pass
