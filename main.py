import json
from google.genai import errors
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

def safe_most_relevant_articles(retries=3):
    """
    Llama a gemini.most_relevant_articles con reintentos en caso de fallo.
    Si después de los reintentos no se obtiene una respuesta válida, lanza RuntimeError.
    """
    for attempt in range(1, retries + 1):
        try:
            result = gemini.most_relevant_articles()
            if result:
                return result
            else:
                print(f"Respuesta vacía o inválida en most_relevant_articles (intento {attempt}/{retries})")
        except Exception as e:
            print(f"Error en most_relevant_articles (intento {attempt}/{retries}): {e}")

    # si llegamos aquí, todos los intentos fallaron
    raise RuntimeError("No se ha podido obtener una respuesta válida de most_relevant_articles después de varios intentos.")

def safe_generate_article(texts, language="español", retries=3):
    """
    Llama a gemini.generate_article con reintentos en caso de error de servidor.
    """
    for attempt in range(1, retries + 1):
        try:
            return gemini.generate_article(texts, language)
        except errors.ServerError as e:
            print(f"Error en Gemini (intento {attempt}/{retries}): {e}")
        except Exception as e:
            print(f"Error inesperado en generate_article: {e}")
            break
    return None

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
        languages = ["español", "inglés"]
        for language in languages:
            generated_article_response = safe_generate_article(qdrant_data.get("texts", []), language)

            if not generated_article_response:
                print(f"Error al generar el artículo '{query}': No se recibió respuesta válida.")
                continue

            try:
                article_payload = json.loads(generated_article_response)
            except Exception as e:
                print(f"Error al generar o parsear el artículo '{query}': {e}")
                continue

            article_payload["urls"] = qdrant_data.get("urls", [])
            article_payload["category"] = category_name
            article_payload["created_at"] = datetime.datetime.now(datetime.timezone.utc)
            db_data.append(article_payload)

    if db_data:
        articles.insert_many(db_data)
        print(f"Artículos de la categoría '{category_name}' insertados en MongoDB.")


def main():

    qdrant.delete_all_points()

    fuentes = {
        "https://www.elmundo.es/": {
            "internacional": "internacional",
            "espana": "politica",
            "deportes": "deportes",
            "economia": "economia"
        },
        "https://elpais.com/": {
            "internacional/": "internacional",
            "espana/": "politica",
            "sociedad/": "sociedad",
            "deportes/": "deportes",
            "tecnologia/": "tecnologia",
            "economia/": "economia"
        },
        "https://www.lavanguardia.com/": {
            "internacional": "internacional",
            "politica": "politica",
            "vida": "sociedad",
            "deportes": "deportes",
            "tecnologia": "tecnologia",
            "economia": "economia"
        },
        "https://www.abc.es/": {
            "internacional/": "internacional",
            "espana/": "politica",
            "sociedad/": "sociedad",
            "deportes/": "deportes",
            "tecnologia/": "tecnologia",
            "economia/": "economia"
        },
        "https://www.larazon.es/": {
            "internacional/": "internacional",
            "espana/": "politica",
            "sociedad/": "sociedad",
            "deportes/": "deportes",
            "tecnologia/": "tecnologia",
            "economia/": "economia"
        }
    }

    for base_url, secciones in fuentes.items():
        for path, categoria in secciones.items():
            qdrant.populate_qdrant(
                url=f"{base_url}{path}",
                language="es",
                category=categoria
            )

    most_relevant = safe_most_relevant_articles()

    categorias = ["economia", "tecnologia", "deportes", "sociedad", "politica", "internacional"]

    for categoria in categorias:
        articulos = most_relevant.get(categoria, [])
        generate_and_insert_mongodb(articulos, categoria)

if __name__ == "__main__":
    main()