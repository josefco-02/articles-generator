import datetime
import requests
import scraper
import embeddings
import uuid
import os
from dotenv import load_dotenv

load_dotenv()


QDRANT_API_URL = os.environ.get('QDRANT_API_URL')
QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY')

def delete_all_points():
    headers = {
        "Authorization": f"Bearer {QDRANT_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "filter": {
            "must": []
        }
    }
    
    try:
        response = requests.post(
            f"{QDRANT_API_URL}/collections/articles/points/delete",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print("Todos los puntos han sido eliminados.")
    except requests.RequestException as e:
        print(f"Error al eliminar puntos en Qdrant: {e}")

def get_id(text):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, text))

def upsert_points(points_batch):
    ids = [get_id(p["text"]) for p in points_batch]
    duplicates = [id for id in set(ids) if ids.count(id) > 1]
    if duplicates:
        print("IDs duplicados detectados:", duplicates)
        
    current_datetime = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "points": [
            {
                "id": get_id(point["text"]),
                "vector": point["embedding"],
                "payload": {
                    "text": point["text"],
                    "url": point["url"],
                    "language": point["language"],
                    "category": point["category"],
                    "datetime": current_datetime.isoformat(),
                }
            }
            for point in points_batch
        ]
    }

    headers = {
        "Authorization": f"Bearer {QDRANT_API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.put(
            f"{QDRANT_API_URL}/collections/articles/points",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        print(f"Insertados {len(points_batch)} puntos correctamente.")
    except requests.RequestException as e:
        print(f"Error al insertar puntos en Qdrant: {e}")


def batch_embedding_and_upsert(fragments, batch_size=30):
    for i in range(0, len(fragments), batch_size):
        batch = fragments[i:i + batch_size]
        texts = [f["text"] for f in batch]
        embeddings_batch = embeddings.get_embeddings_batch(texts)

        batch_points = []
        for frag, emb in zip(batch, embeddings_batch):
            if emb:
                batch_points.append({
                    "text": frag.get("text", ""),
                    "embedding": emb,
                    "url": frag.get("url", ""),
                    "language": frag.get("language", "es"),
                    "category": frag.get("category", "general")
                })

        if batch_points:
            upsert_points(batch_points)

def search_points_by_vector(vector):
    headers = {
        "Authorization": f"Bearer {QDRANT_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{QDRANT_API_URL}/collections/articles/points/query",
            headers=headers,
            json={
                "limit": 9,
                "with_payload": True,
                "query": vector
            },
        )
        response.raise_for_status()
        return response.json().get("result", [])
    except requests.RequestException as e:
        print(f"Error en busqueda de Qdrant: {e}")
    
    return []

def search_points_semantically(search_query: str):
    embedding = embeddings.get_embedding(embeddings.get_detailed_instruct(search_query))
    return search_points_by_vector(embedding)

def get_texts_and_urls(response):
    points = response["points"]

    texts = []
    urls_set = set()

    for point in points:
        payload = point.get("payload", {})
        
        text = payload.get("text")
        url = payload.get("url")
        
        if text:
            texts.append(text)
        if url:
            urls_set.add(url)

    urls = list(urls_set)

    qdrant_data = {
        "texts": texts,
        "urls": urls
    }

    return qdrant_data

def populate_qdrant(url, language, category):
    print(f"Recopilando enlaces de artículos de {url}...")
    articles_urls = scraper.get_main_article_links(url)
    print(articles_urls)

    fragments = scraper.collect_fragments_from_articles(articles_urls, language=language, category=category)

    if fragments:
        print(f"Generando embeddings para {len(fragments)} fragmentos...")
        batch_embedding_and_upsert(fragments)
    else:
        print("No se encontraron fragmentos para procesar.")