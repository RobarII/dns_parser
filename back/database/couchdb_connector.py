import sys
import os
import re
import subprocess
import hashlib
import couchdb
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from database.mongodb_connector import is_docker_running, container_exists, create_connection


COUCHDB_HOST = "localhost"
COUCHDB_PORT = 5984
COUCHDB_USER = "admin"
COUCHDB_PASSWORD = "secret"
DATABASE_NAME = "tech_analytics"


def start_couchdb():
    """Запускает контейнер CouchDB, если он не запущен"""
    container_name = "couchdb"

    if not is_docker_running():
        print("Docker не запущен. Запустите Docker Desktop.")
        sys.exit(1)

    if container_exists(container_name):
        result = subprocess.run(["docker", "start", container_name], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Не удалось запустить контейнер: {result.stderr}")
            sys.exit(1)
    else:
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", "5984:5984",
            "-e", "COUCHDB_USER=admin",
            "-e", "COUCHDB_PASSWORD=secret",
            "couchdb:latest"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка создания контейнера: {result.stderr}")
            sys.exit(1)


def get_couchdb_server():
    """Возвращает подключение к серверу CouchDB"""
    try:
        server = couchdb.Server(f"http://{COUCHDB_USER}:{COUCHDB_PASSWORD}@{COUCHDB_HOST}:{COUCHDB_PORT}/")
        # Проверка подключения
        server.version()
        return server
    except Exception as e:
        print(f"Ошибка подключения к CouchDB: {e}")
        sys.exit(1)


def get_or_create_database():
    """Возвращает базу данных, создаёт если не существует"""
    server = get_couchdb_server()
    if DATABASE_NAME not in server:
        server.create(DATABASE_NAME)
    return server[DATABASE_NAME]


def clean_text(text: str) -> str:
    """Функция для очистки текста"""
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "\U0001F004-\U0001F0CF"
        "\U0001F170-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub(r'', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[.;,\s]+$', '', text)
    return text.strip()


def remove_empty_reviews(product_data: dict) -> dict:
    """Очищает текст в отзывах и удаляет абсолютно пустые отзывы."""
    if "Отзывы" not in product_data or not isinstance(product_data["Отзывы"], list):
        return product_data

    filtered = []
    for rev in product_data["Отзывы"]:
        if not isinstance(rev, dict):
            continue

        # Очищаем текстовые поля
        pros = clean_text(rev.get("Достоинства", "") or "")
        cons = clean_text(rev.get("Недостатки", "") or "")
        comm = clean_text(rev.get("Комментарий", "") or "")

        # Обновляем отзыв очищенным текстом
        rev["Достоинства"] = pros
        rev["Недостатки"] = cons
        rev["Комментарий"] = comm

        # Сохраняем отзыв, если хотя бы одно поле не пустое
        if pros or cons or comm:
            filtered.append(rev)

    product_data["Отзывы"] = filtered
    product_data["Всего_отзывов"] = len(filtered)
    return product_data


def generate_doc_id(url: str) -> str:
    """Генерирует стабильный ID на основе URL (для избежания дублей)"""
    return "product_data" + hashlib.md5(url.encode()).hexdigest()


def insert_data(document: dict):
    """
    Вставляет документ в CouchDB.
    Если документ с таким URL уже есть — обновляет его.
    """
    url = document.get("Ссылка", "").strip()
    if not url:
        print("Пропущен документ без ссылки.")
        return

    db = get_or_create_database()
    doc_id = generate_doc_id(url)

    # Очищаем пустые отзывы
    cleaned_doc = remove_empty_reviews(document)
    cleaned_doc["_id"] = doc_id  # CouchDB требует _id

    try:
        # Пытаемся получить существующий документ
        existing = db[doc_id]
        # Обновляем данные
        cleaned_doc["_rev"] = existing["_rev"]
        db[doc_id] = cleaned_doc
        print(f"Обновлён существующий документ: {doc_id}")
    except couchdb.ResourceNotFound:
        # Новый документ
        db[doc_id] = cleaned_doc
        print(f"Добавлен новый документ: {doc_id}")


def show_data():
    """Показывает все документы в базе"""
    db = get_or_create_database()
    count = 0
    for doc_id in db:
        doc = db[doc_id]
        print(doc)
        count += 1
    print(f'Количество документов: {count}')


def clear_data():
    """Полностью очищает базу данных"""
    server = get_couchdb_server()
    if DATABASE_NAME in server:
        del server[DATABASE_NAME]
    print("База данных очищена.")


def mongo_to_couch():
    """Создает соединение и перебрасывает данные между Mongo и Couch"""
    # Вытаскиваем данные из MongoDB
    mongo_collection = create_connection()
    mongo_documents = mongo_collection.find()
    # Закидываем документы из Mongo в Couch
    for doc in mongo_documents:
        insert_data(doc)


def fetch_and_save_to_parquet(OUTPUT_DIR='./data'):
    """Основная функция: загрузка → очистка → сохранение."""
    print("Подключение к CouchDB...")
    db = get_or_create_database()

    print("Загрузка всех документов...")
    docs = []
    for doc_id in db:
        doc = db[doc_id]
        # Убираем служебные поля CouchDB
        doc.pop('_id', None)
        doc.pop('_rev', None)
        docs.append(doc)

    if not docs:
        print("Нет данных в CouchDB.")
        return

    print(f"Очистка пустых отзывов у {len(docs)} товаров...")
    cleaned_docs = [remove_empty_reviews(doc) for doc in docs]

    # Добавляем числовой id
    for i, doc in enumerate(cleaned_docs, start=1):
        doc["id"] = i

    df = pd.DataFrame(cleaned_docs)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    product_cols = [
        "id", "Категория", "Наименование", "Цена", "Рейтинг",
        "Ссылка", "Описание", "Всего_отзывов"
    ]
    for col in product_cols:
        if col not in df.columns:
            df[col] = None
    products_df = df[product_cols].copy()
    products_df.to_parquet(os.path.join(OUTPUT_DIR, "products_main.parquet"), index=False)

    specs_records = []
    for _, row in df.iterrows():
        char = row.get("Характеристики", {})
        if isinstance(char, dict):
            for key, value in char.items():
                specs_records.append({
                    "product_id": row["id"],
                    "key": key,
                    "value": str(value) if value is not None else ""
                })

    if specs_records:
        specs_df = pd.DataFrame(specs_records)
        specs_df.to_parquet(os.path.join(OUTPUT_DIR, "specs.parquet"), index=False)
    else:
        schema = pa.schema([
            ("product_id", pa.int64()),
            ("key", pa.string()),
            ("value", pa.string())
        ])
        pq.write_table(pa.table([], schema=schema), os.path.join(OUTPUT_DIR, "specs.parquet"))

    review_records = []
    for _, row in df.iterrows():
        reviews = row.get("Отзывы", [])
        if isinstance(reviews, list):
            for rev in reviews:
                if isinstance(rev, dict):
                    review_records.append({
                        "product_id": row["id"],
                        "Автор": str(rev.get("Автор", "")),
                        "Дата": str(rev.get("Дата", "")),
                        "Реальный покупатель": bool(rev.get("Реальный покупатель", False)),
                        "Общий рейтинг": int(rev.get("Общий рейтинг", 0)),
                        "Срок использования": str(rev.get("Срок использования", "")),
                        "Достоинства": str(rev.get("Достоинства", "")),
                        "Недостатки": str(rev.get("Недостатки", "")),
                        "Комментарий": str(rev.get("Комментарий", ""))
                    })

    if review_records:
        reviews_df = pd.DataFrame(review_records)
        reviews_df.to_parquet(os.path.join(OUTPUT_DIR, "reviews.parquet"), index=False)
    else:
        schema = pa.schema([
            ("product_id", pa.int64()),
            ("Автор", pa.string()),
            ("Дата", pa.string()),
            ("Реальный покупатель", pa.bool_()),
            ("Общий рейтинг", pa.int64()),
            ("Срок использования", pa.string()),
            ("Достоинства", pa.string()),
            ("Недостатки", pa.string()),
            ("Комментарий", pa.string())
        ])
        pq.write_table(pa.table([], schema=schema), os.path.join(OUTPUT_DIR, "reviews.parquet"))

    print(f"Сохранено {len(df)} товаров в {OUTPUT_DIR}/")


if __name__ == '__main__':
    clear_data()
    mongo_to_couch()