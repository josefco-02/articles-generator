from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()


GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')


def limpiar_y_parsear_json(raw_text):
    if raw_text.startswith('```json') and raw_text.endswith('```'):
        raw_text = raw_text[7:-3].strip()
    
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("Error al parsear JSON:", e)
        return None

    return data


def most_relevant_articles():
    client = genai.Client(
        api_key=GEMINI_API_KEY,
    )

    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text='Actúa como un agregador de noticias actualizado. Devuélveme las 5 noticias más relevantes del día de hoy en periódicos de España para cada una de las siguientes categorías: Internacional, Política, Economía, Deportes y Tecnología. Para cada noticia, proporciona únicamente un breve texto descriptivo que pueda servir como búsqueda semántica representativa del contenido de la noticia y que me ayude a buscar noticias relacionadas. Organiza toda la salida exclusivamente en formato JSON, sin saltos de línea, donde cada categoría sea una clave (en minúsculas y sin tildes) que contenga un array de 5 textos semánticos. No añadas explicaciones, texto fuera del JSON ni ningún tipo de número, enlace, fuente o referencia entre corchetes, paréntesis o de ningún tipo. Solo un JSON con el texto limpio'),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        response_mime_type="text/plain",
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    # print(response.text)
    return limpiar_y_parsear_json(response.text)

def generate_article(texts):
    client = genai.Client(
        api_key=GEMINI_API_KEY,
    )

    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=(f'Actúa como un periodista profesional especializado en redacción para medios digitales. Voy a proporcionarte una lista de fragmentos de texto extraídos de diferentes artículos periodísticos. La mayoría estarán relacionados con un mismo tema, pero puede que algunos no tengan ninguna relación con el tema principal. Tu tarea es: 1. Analizar todos los fragmentos y detectar el tema central, ignorando por completo cualquier fragmento irrelevante o no relacionado. 2. Redactar un artículo periodístico original de aproximadamente 800 palabras basado únicamente en los fragmentos relevantes y el tema principal detectado. 3. El artículo debe mantener un tono informativo, imparcial y claro, siguiendo el estilo de un periódico online. Determina también: 1. Título. 2. Una breve descripción/resumen para poner bajo el título. 3. Categoría a la que pertenece el artículo entre estas: internacional, politica, economia, deportes y tecnologia (en minúsculas y sin tildes) teniendo en cuenta que los fragmentos provienen de periódicos nacionales correspondientes al idioma en el que están redactados. 4. Idioma (en código ISO 639-1). Los fragmentos de texto con los que tienes que trabajar son los siguientes: {texts}')),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["title", "summary", "body", "language", "category"],
            properties = {
                "title": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "summary": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "body": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "language": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
                "category": genai.types.Schema(
                    type = genai.types.Type.STRING,
                ),
            },
        ),
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text
