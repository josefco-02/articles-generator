import json
import qdrant
import gemini
import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.environ.get('MONGODB_URI')

client = MongoClient(MONGODB_URI)
db = client["tfg_db"]
articles = db["articles"]


def generate_and_insert_mongodb(category_queries, category_name):
    """
    Procesa artículos de una categoría específica y los inserta en MongoDB

    Args:
        category_articles: Lista de artículos de la categoría
        category_name: Nombre de la categoría (str)
    """
    db_data = []

    for query in category_queries:
        response = qdrant.search_points_semantically(query)
        qdrant_data = qdrant.get_texts_and_urls(response)
        generated_article_response = gemini.generate_article(qdrant_data.get("texts", []))
        try:
            article_payload = json.loads(generated_article_response)
        except json.JSONDecodeError:
            continue
        article_payload["urls"] = qdrant_data.get("urls", [])
        article_payload["category"] = category_name
        article_payload["created_at"] = datetime.datetime.now(datetime.timezone.utc)
        db_data.append(article_payload)

    if db_data:
        articles.insert_many(db_data)
        print(f"Artículos de la categoría '{category_name}' insertados en MongoDB.")


def main():
    # Definimos las fuentes y categorías
    fuentes = {
        "https://www.elmundo.es/": {
            "internacional": "internacional",
            "espana": "politica",
            "deportes": "deportes",
            # "tecnologia": "tecnologia",   # Comentado en tu versión
            "economia": "economia"
        },
        "https://elpais.com/": {
            "internacional/": "internacional",
            "espana/": "politica",
            "deportes/": "deportes",
            "tecnologia/": "tecnologia",
            "economia/": "economia"
        },
        "https://www.lavanguardia.com/": {
            "internacional": "internacional",
            "politica": "politica",
            "deportes": "deportes",
            "tecnologia": "tecnologia",
            "economia": "economia"
        }
    }

    # Poblar Qdrant en bucle
    for base_url, secciones in fuentes.items():
        for path, categoria in secciones.items():
            qdrant.populate_qdrant(
                url=f"{base_url}{path}",
                language="es",
                category=categoria
            )

    # Obtener los artículos más relevantes
    most_relevant = gemini.most_relevant_articles()

    # Categorías a procesar
    categorias = ["internacional", "politica", "deportes", "tecnologia", "economia"]

    # Procesar y guardar artículos en MongoDB
    for categoria in categorias:
        articulos = most_relevant.get(categoria, [])
        generate_and_insert_mongodb(articulos, categoria)

if __name__ == "__main__":
    main()