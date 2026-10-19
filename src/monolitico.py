import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
 
def obtener_dato_de_prueba(pregunta):
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"API Key: {api_key}")  # Agrega esta
    modelo = "gemini-3.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    
    body = {
        "contents": [
            {"parts": [{"text": pregunta}]}
        ]
    }
    
    respuesta = requests.post(url, json=body)
    datos = respuesta.json()
    return datos["candidates"][0]["content"]["parts"][0]["text"]

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))