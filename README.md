# favorites

A small and exquisite bookmark management application. You can export your favorite web pages from bookmark management of any browser and put it in a directory monitored by the application. The file watchdog will load the file and output all links to <code>Mysql</code> database, finally creating indexes by <code>Elasticsearch</code>.




## Tech Stack

* Python3
* Flask
* Requests
* BeautifulSoup
* Pymysql
* ElasticSearch




## How to Work?

``` mermaid
flowchart TD
   u("BookMark Management")-->|"Export as a File"|a("BookMark File")
   a("BookMark File")-->|"Save"|b("Directory")
   b("Directory")-->c("Watchdog")
   c("Watchdog")-->|"Change Notify"|d("FileChangeEventHandler")
   d("FileChangeEventHandler")-->|"Analyse File and Save Link"|e("Mysql")
   e("Mysql")-->|"Create Index"|f("ElasticSearch")
   
```


## Run

``` log
favorites
├── README.md
├── test
   ├── config
   │   └── fav.ini
   ├── templates
   │   ├── hello.html
   │   ├── layout.html
   │   ├── result.html
   │   └── search.html
   ├── common.py
   ├── es.py
   ├── fav_exp.py
   └── web.py
```


* **Start directory watchdog:** 
  
  ``` 
  python fav_exp.py
  ```
  
  
  
* **Start web appalication to search by keyword:**
  
  ```
  python web.py 
  ```
  
  
