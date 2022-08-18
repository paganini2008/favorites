# favorites

A small and exquisite Bookmark management application that collects your favorite webpage and provides search the content you want by keyword




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
  
  
