import requests
import os
from dotenv import load_dotenv

load_dotenv()

HF_API_URL = os.environ.get('HF_API_URL')
HF_API_KEY = os.environ.get('HF_API_KEY')

# Si se quiere hacer el embedding de una query se debe añadir antes una oración con la instrucción que describe la tarea p.ej. "Given a web search query, retrieve relevant passages that answer the query \n Query: how much protein should a female eat
# Retrieve semantically similar text.
def get_detailed_instruct(query, task_description = "Given a web search query, retrieve relevant passages related to the query"):
    return f'Instruct: {task_description}\nQuery:{query}'

# Obtiene el embedding de un texto utilizando la API de Hugging Face
def get_embedding(textInput):

    if not textInput:
        raise ValueError("textInput no puede estar vacío")

    payload = {
        "inputs": textInput,
        "parameters":
            {
                "normalize_embeddings": True
            }
    }
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Lanza error si status_code >= 400
        return response.json()
    
    except requests.Timeout:
        print("Error: la solicitud a HuggingFace tardó demasiado.")
    except requests.RequestException as e:
        print(f"Error en la solicitud: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

    return None

# Obtiene los embeddings de un lote de textos (fragmentos de texto) utilizando la API de Hugging Face
def get_embeddings_batch(texts):

    if not texts:
        raise ValueError("texts debe ser una lista no vacía de strings")

    payload = {
        "inputs": texts,
        "parameters": {
            "normalize_embeddings": True
        }
    }

    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Lanza error si status_code >= 400
        return response.json()
    
    except requests.Timeout:
        print("Error: la solicitud a HuggingFace tardó demasiado.")
    except requests.RequestException as e:
        print(f"Error en la solicitud: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

    return [None] * len(texts)
