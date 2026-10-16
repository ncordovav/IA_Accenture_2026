import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Se sube dos niveles desde 'src' para llegar a la raíz 'plantilla-repositorio-base' donde está el .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
#load_dotenv()

def construir_peticion(pregunta):
    api_key = os.getenv("API_KEY")
    modelo = "gemini-3.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
        "contents": [
            {"parts": [{"text": pregunta}]}
        ]
    }
    return url, body

def enviar_peticion(url, body):
     respuesta = requests.post(url, json=body)
     return respuesta.json()

def extraer_texto(datos):
    return datos["candidates"][0]["content"]["parts"][0]["text"]

def obtener_dato_de_prueba(pregunta):
    url, body = construir_peticion(pregunta)
    datos = enviar_peticion(url, body)
    return extraer_texto(datos)

if __name__ == "__main__":
    print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))