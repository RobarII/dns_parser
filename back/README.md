# DNS-parser-with-analysis
## Описание
Парсер сайта магазина DNS, с анализом товаров и их комментариев.
Все данные, которые парсятся, будут записаны в Docker контейнер MongoDB, а после очищены и перенесены в CouchDB.
Далее из CouchDB будут созданы 3 parquet файла для анализа при помощи Dask.
## Стек
1. Python 3.14
2. BeautifulSoup4, undetected-chromedriver, selenium
3. dask
4. FastAPI, uvicorn, httpx
5. pymongo, couchdb
6. pyarrow
7. transformers, torch
## Установка и запуск
1. Создайте окружение в главной директории
```commandline
python -m venv venv
```
2. Установите зависимости
```commandline
python install -r requirements.txt
```
3. Скачайте Docker Desktop вместе с образами MongoDB и CouchDB
4. Для работы с ИИ необходимо зайти в папку model/models, запустить bash и выполнить клонирование репозитория
```bash
git clone https://huggingface.co/Qwen/Qwen3-0.6B
```
5. Запустить main.py
```commandline
python main.py
```
## Источники
Источники, которые помогли в разработке:
1. На чём основан парсер: https://github.com/kireev20000/DNS-Shop-Parser
2. Использованная модель: https://huggingface.co/Qwen/Qwen3-0.6B