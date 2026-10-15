import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# Se sube dos niveles desde 'src' para llegar a la raíz 'plantilla-repositorio-base' donde está el .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
#load_dotenv()
 
def obtener_dato_de_prueba(pregunta):
    api_key = os.getenv("API_KEY")
    modelo = "gemini-3.8-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    
    body = {
        "contents": [
            {"parts": [{"text": pregunta}]}
        ]
    }
    
    respuesta = requests.post(url, json=body)
    datos = respuesta.json()
    
    if "error" in datos:
        return f"Error devuelto por Google: {datos['error']}"
        
    return datos["candidates"][0]["content"]["parts"][0]["text"]

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))