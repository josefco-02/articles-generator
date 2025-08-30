import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse


# Devuelve el texto útil completo de un artículo dada su URL
def scrape_article_tag_text(url, min_paragraph_len=100):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Intenta extraer desde <article> si existe
        article = soup.find("article")
        if article:
            paragraphs = article.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        # Filtra y concatena párrafos decentes
        text = "\n".join(
            p.get_text().strip()
            for p in paragraphs
            if len(p.get_text().strip()) > min_paragraph_len  # descarta textos irrelevantes
        )

        return text.strip()

    except Exception as e:
        print(f"Error al scrapear la URL: {e}")
        return ""
    
def scrape_section_tag_text(url, min_paragraph_len=100):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extrae todos los <section> y sus <p>
        sections = soup.find_all("section")
        paragraphs = []
        for section in sections:
            paragraphs.extend(section.find_all("p"))

        # Si no hay <section>, usa todos los <p> del documento
        if not paragraphs:
            paragraphs = soup.find_all("p")

        # Filtra y concatena párrafos decentes
        text = "\n".join(
            p.get_text().strip()
            for p in paragraphs
            if len(p.get_text().strip()) > min_paragraph_len
        )

        return text.strip()

    except Exception as e:
        print(f"Error al scrapear la URL: {e}")
        return ""

# De momento funciona para elmundo, elpais y lavanguardia
# Obtiene los enlaces de los artículos principales de la portada de un periódico, evitando enlaces no deseados
def get_main_article_links(base_url, max_links=15):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"No se pudo acceder a la portada {base_url}: {e}")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")

    articles = soup.find_all("article")

    article_links = []
    seen = set()

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    base_path = parsed_base.path.rstrip("/")  # quitar / final si lo hay

    for article in articles:
        links = article.find_all("a")
        for link in links:
            href = link.get("href")
            if not href or href.startswith(("mailto:", "tel:")):
                continue

            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)

            # Ignorar dominio externo
            if parsed_url.netloc != base_domain:
                continue

            # Mantener solo las URLs dentro de la sección base
            if not parsed_url.path.startswith(base_path):
                continue

            # Quitar fragmento y parámetros
            clean_url = urlunparse(parsed_url._replace(fragment="", query=""))

            if clean_url not in seen:
                seen.add(clean_url)
                article_links.append(clean_url)

            if len(article_links) >= max_links:
                return article_links

    return article_links




def split_text_into_fragments(texto, max_words=340, min_words=80):
    # Dividir el texto en oraciones usando puntuación fuerte.
    sentences = re.split(r'(?<=[.!?])\s+', texto.strip())
    
    fragments = []
    current_fragment = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        word_count = len(sentence_words)

        # Si la oración sola es mayor que el máximo, se añade como fragmento aparte
        if word_count > max_words:
            if current_fragment:
                fragments.append(' '.join(current_fragment))
                current_fragment = []
                current_word_count = 0
            fragments.append(sentence)
        elif current_word_count + word_count <= max_words:
            current_fragment.extend(sentence_words)
            current_word_count += word_count
        else:
            # Si el fragmento actual tiene suficientes palabras, lo guardo y empiezo uno nuevo
            if current_word_count >= min_words:
                fragments.append(' '.join(current_fragment))
                current_fragment = sentence_words
                current_word_count = word_count
            else:
                # Si no cumple mínimo, igual se añade la oración para evitar bucles raros
                current_fragment.extend(sentence_words)
                current_word_count += word_count

    # Añadir lo que quede
    if current_fragment:
        fragments.append(' '.join(current_fragment))

    return fragments

# Combina las funciones de scraping y fragmentación por oraciones y número de palabras para extraer fragmentos de texto de una lista de artículos
def extract_text_fragments(article_urls, language="es", category="general"):
    all_fragments = []
    for url in article_urls:
        if urlparse(url).netloc == "www.larazon.es":
            text = scrape_section_tag_text(url)
        else:
            text = scrape_article_tag_text(url)
        if not text:
            continue
        fragments = split_text_into_fragments(text)
        for fragment in fragments:
            all_fragments.append({"text": fragment, "url": url, "language": language, "category": category})
    return all_fragments