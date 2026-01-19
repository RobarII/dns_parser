import sys
import json
import subprocess
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_USERNAME = "admin"
MONGO_PASSWORD = "secret"


def is_docker_running() -> bool:
    """Проверяет, что докер запущен"""
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def container_exists(name: str) -> bool:
    """Проверяет, существует ли контейнер"""
    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={name}"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def start_mongodb():
    """Запускает существующий контейнер mongodb или создаёт новый"""
    container_name = "mongodb"

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
            "-p", "27017:27017",
            "-e", "MONGO_INITDB_ROOT_USERNAME=admin",
            "-e", "MONGO_INITDB_ROOT_PASSWORD=secret",
            "mongo:latest"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка создания контейнера: {result.stderr}")
            sys.exit(1)


def create_connection():
    """Создает подключение к MongoDB и возвращает коллекцию"""
    global MONGO_HOST, MONGO_PORT, MONGO_USERNAME, MONGO_PASSWORD
    connection_string = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/?authSource=admin"
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
    except ConnectionFailure as e:
        print(f"Ошибка подключения: {e}")
        exit(1)
    db = client["tech_analytics"]
    collection = db["products"]

    return collection


def insert_data(document):
    """Вставляет значения"""
    collection = create_connection()
    collection.insert_one(document)
    print('Документ вставлен успешно.')


def show_data():
    """Просмотр вставленных документов"""
    collection = create_connection()
    documents = collection.find()
    for doc in documents:
        print(doc)
    print(f'Количество документов: {collection.count_documents({})}')


def clear_data():
    """Полностью очистить бд"""
    collection = create_connection()
    collection.delete_many({})
    print("Документы успешно удалены.")


def check_data(url: str):
    """
    Проверяет, есть ли товар в бд по url
    Если продукт есть в бд: return False
    Если продукта нет в бд: return True
    """
    collection = create_connection()
    exists = collection.find_one({"Ссылка": url.strip()})
    if exists:
        return False
    else:
        return True


def export_data(filename="products.json"):
    """Записывает все документы в JSON файл без _id"""
    collection = create_connection()
    documents = []
    for doc in collection.find({}):
        doc.pop('_id', None)
        documents.append(doc)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=4)
    print(f"Сохранено {len(documents)} документов в '{filename}'")


def import_data(file_path: str):
    """Импортирует данные из json файла."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    collection = create_connection()
    collection.insert_many(data)
    print(f"Импортировано {len(data)} документов за один запрос.")


if __name__ == '__main__':
    clear_data()
    import_data("database/products.json")