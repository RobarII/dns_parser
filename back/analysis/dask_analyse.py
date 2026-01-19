import re
import os
from typing import Optional, Any, Dict, List
from datetime import datetime
from functools import lru_cache
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


def extract_base_model(name: str) -> str:
    """Извлекает базовую модель из названия, убирая спецификации."""
    if not isinstance(name, str):
        return "Неизвестно"

    name = re.sub(r'\([^)]*\)', '', name)
    words = name.strip().split()
    base = []
    spec_patterns = ['/', 'гб', 'gb', 'ram', 'rom', 'мб', 'mb', 'tb', 'тб', 'ghz', 'ггц']

    for w in words:
        if any(spec in w.lower() for spec in spec_patterns):
            break
        if w.isdigit() and base:
            break
        base.append(w)

    return " ".join(base) if base else name.strip()


def extract_brand_from_model_or_name(row: Series) -> str:
    """Извлекает бренд как первое слово из 'Модель' в характеристиках или 'Наименование'."""
    char = row.get("Характеристики", {})

    if isinstance(char, dict):
        model = char.get("Модель")
        if isinstance(model, str) and model.strip():
            return model.strip().split()[0]

    name = row.get("Наименование", "")
    if isinstance(name, str) and name.strip():
        return name.split()[0]

    return "Неизвестно"


def extract_year(char: dict) -> Optional[int]:
    """Извлекает год релиза."""
    val = char.get("Год релиза", "")
    return int(val) if isinstance(val, str) and val.isdigit() else None


def normalize_char(x: Any) -> Dict[str, Any]:
    """Приводит характеристики к dict даже при None/str/bool."""
    return x if isinstance(x, dict) else {}


def convert_numpy_types_in_list(lst: List[Dict]) -> List[Dict]:
    """Конвертирует numpy-типы в стандартные Python-типы."""
    result = []
    for item in lst:
        clean_item = {}
        for k, v in item.items():
            if isinstance(v, (np.integer, np.int64, np.int32)):
                clean_item[k] = int(v)
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                clean_item[k] = float(v) if not pd.isna(v) else None
            elif pd.isna(v):
                clean_item[k] = None
            else:
                clean_item[k] = v
        result.append(clean_item)
    return result


@lru_cache(maxsize=2)
def load_and_process_data(parquet_path: str = "./data/products.parquet") -> DataFrame:
    """
    Загружает данные из трёх Parquet-файлов и воссоздаёт единый DataFrame.
    """
    base_dir = os.path.dirname(parquet_path)
    products_path = os.path.join(base_dir, "products_main.parquet")
    specs_path = os.path.join(base_dir, "specs.parquet")
    reviews_path = os.path.join(base_dir, "reviews.parquet")

    # Проверка наличия основного файла
    if not os.path.exists(products_path):
        raise FileNotFoundError(f"Файл {products_path} не найден.")

    # Загрузка основной таблицы
    products_df = pd.read_parquet(products_path)

    # Восстановление характеристик
    if os.path.exists(specs_path) and os.path.getsize(specs_path) > 0:
        try:
            specs_df = pd.read_parquet(specs_path)
            char_dict = (
                specs_df.groupby("product_id")
                .apply(lambda x: dict(zip(x["key"], x["value"])))
                .to_dict()
            )
            products_df["Характеристики"] = products_df["id"].map(char_dict).fillna({})
        except Exception as e:
            print(f"Ошибка при загрузке характеристик: {e}")
            products_df["Характеристики"] = [{} for _ in range(len(products_df))]
    else:
        products_df["Характеристики"] = [{} for _ in range(len(products_df))]

    # Восстановление отзывов
    if os.path.exists(reviews_path) and os.path.getsize(reviews_path) > 0:
        try:
            reviews_df = pd.read_parquet(reviews_path)
            reviews_list = (
                reviews_df.groupby("product_id")
                .apply(lambda x: x.drop(columns=["product_id"]).to_dict(orient="records"))
                .to_dict()
            )
            products_df["Отзывы"] = products_df["id"].map(reviews_list).fillna([]).apply(
                lambda x: x if isinstance(x, list) else []
            )
        except Exception as e:
            print(f"Ошибка при загрузке отзывов: {e}")
            products_df["Отзывы"] = [[] for _ in range(len(products_df))]
    else:
        products_df["Отзывы"] = [[] for _ in range(len(products_df))]

    # Преобразования
    products_df["Характеристики"] = products_df["Характеристики"].apply(normalize_char)
    products_df["Рейтинг"] = pd.to_numeric(products_df["Рейтинг"], errors="coerce")
    products_df["Всего_отзывов"] = pd.to_numeric(products_df["Всего_отзывов"], errors="coerce")
    products_df["Цена"] = pd.to_numeric(products_df["Цена"], errors="coerce")

    # Дополнительные поля
    products_df["Базовая_модель"] = products_df["Наименование"].apply(extract_base_model)
    products_df["Бренд"] = products_df.apply(extract_brand_from_model_or_name, axis=1)
    products_df["Год"] = products_df["Характеристики"].apply(extract_year)

    return products_df


def get_info(parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)
    return {
        "total_products": len(pdf),
        "total_reviews": int(pdf["Всего_отзывов"].fillna(0).sum()),
        "last_parsing": datetime.now().isoformat()
    }


def get_count(parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)
    return {
        "category_distribution": pdf["Категория"].value_counts().to_dict(),
        "brand_distribution": pdf["Бренд"].value_counts().to_dict()
    }


def get_avg(param: str, parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)

    if param == "rate":
        agg_data = pdf.dropna(subset=["Рейтинг"])
        col = "Рейтинг"
    elif param == "price":
        agg_data = pdf.dropna(subset=["Цена"])
        col = "Цена"
    else:
        return {"error": "Invalid parameter. Use 'rate' or 'price'"}

    result = {
        f"avg_{param}_by_category": agg_data.groupby("Категория")[col].mean().round(2).to_dict(),
        f"avg_{param}_by_brand": agg_data.groupby("Бренд")[col]
        .mean()
        .sort_values(ascending=False)
        .head(20)
        .round(2)
        .to_dict(),
    }

    if pdf["Год"].notna().any():
        yearly_agg = pdf.dropna(subset=["Год", col]).groupby("Год")[col].mean().round(2).sort_index()
        result[f"avg_{param}_by_year"] = yearly_agg.to_dict()

    return result


def get_rate_devices(parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)
    rated = pdf.dropna(subset=["Рейтинг"]).sort_values("Рейтинг", ascending=False)
    result_list = rated[["id", "Наименование", "Рейтинг", "Всего_отзывов"]] \
        .assign(
        id=lambda x: x["id"].astype(int),
        Рейтинг=lambda x: x["Рейтинг"].round(2),
        Всего_отзывов=lambda x: x["Всего_отзывов"].fillna(0).astype(int)
    ) \
        .to_dict(orient="records")
    return {"devices_by_rating": result_list}


def get_brand_info(brand_name: str, parquet_path: str = "./data/products.parquet") -> dict:
    try:
        pdf = load_and_process_data(parquet_path)
        brand_mask = pdf["Бренд"] == brand_name
        brand_df = pdf[brand_mask].copy()

        if brand_df.empty:
            return {"error": f"Brand '{brand_name}' not found"}

        device_count = int(len(brand_df))
        total_devices = len(pdf)
        share_percent = (device_count / total_devices * 100) if total_devices > 0 else 0.0

        stats = {
            'brand': brand_name,
            "device_count": device_count,
            "avg_rating": float(round(brand_df["Рейтинг"].mean(), 2)),
            "avg_price": float(round(brand_df["Цена"].mean(), 2)),
            "min_price": int(brand_df["Цена"].min()) if not brand_df["Цена"].isna().all() else 0,
            "max_price": int(brand_df["Цена"].max()) if not brand_df["Цена"].isna().all() else 0,
            "share_percent": float(round(share_percent, 2)),
            "total_reviews": int(brand_df["Всего_отзывов"].sum())
        }

        devices_list = (
            brand_df[["id", "Наименование", "Рейтинг", "Всего_отзывов", "Цена"]]
            .assign(
                id=lambda x: x["id"].astype(int),
                Рейтинг=lambda x: x["Рейтинг"].round(2).astype(float),
                Всего_отзывов=lambda x: x["Всего_отзывов"].fillna(0).astype(int),
                Цена=lambda x: x["Цена"].fillna(0).astype(float)
            )
            .to_dict(orient="records")
        )

        stats["devices"] = convert_numpy_types_in_list(devices_list)
        return stats

    except Exception as e:
        print(f"Ошибка в get_brand_info: {e}")
        raise


def get_products_by_category(category_name: str, parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)
    filtered = pdf[pdf["Категория"] == category_name].copy()
    if filtered.empty:
        return {}

    prepared = (
        filtered[["id", "Наименование", "Рейтинг", "Всего_отзывов", "Цена"]]
        .assign(
            id=lambda x: x["id"].astype(int),
            Рейтинг=lambda x: x["Рейтинг"].round(2).astype(float),
            Всего_отзывов=lambda x: x["Всего_отзывов"].fillna(0).astype(int),
            Цена=lambda x: x["Цена"].fillna(0).astype(float)
        )
    )

    records = convert_numpy_types_in_list(prepared.to_dict(orient="records"))
    return {item["id"]: item for item in records}


def get_product_by_id(product_id: int, parquet_path: str = "./data/products.parquet") -> dict:
    pdf = load_and_process_data(parquet_path)

    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return {}

    pdf["id"] = pd.to_numeric(pdf["id"], errors="coerce")
    product_row = pdf[pdf["id"] == product_id]
    if product_row.empty:
        return {}

    record = product_row.iloc[0].to_dict()

    def clean_value(val):
        if val is None:
            return None
        if isinstance(val, (np.integer, np.int64, np.int32)):
            return int(val)
        elif isinstance(val, (np.floating, np.float64, np.float32)):
            return float(val) if not pd.isna(val) else None
        elif isinstance(val, (np.bool_, bool)):
            return bool(val)
        if pd.api.types.is_scalar(val) and pd.isna(val):
            return None
        if isinstance(val, dict):
            return {k: clean_value(v) for k, v in val.items()}
        if isinstance(val, (list, tuple, np.ndarray)):
            val = val.tolist() if isinstance(val, np.ndarray) else val
            return [clean_value(item) for item in val]
        return val

    clean_record = {k: clean_value(v) for k, v in record.items()}
    return clean_record


def get_brands_by_reviews(parquet_path: str = "./data/products.parquet") -> dict:
    """Возвращает топ брендов по общему количеству отзывов."""
    pdf = load_and_process_data(parquet_path)
    reviews_by_brand = (
        pdf.groupby("Бренд")["Всего_отзывов"]
        .sum()
        .fillna(0)
        .astype(int)
        .sort_values(ascending=False)
    )
    return reviews_by_brand.to_dict()
