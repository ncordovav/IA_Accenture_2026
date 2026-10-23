import os
import requests
import re
from dotenv import load_dotenv

load_dotenv()

def calcular_costo(datos, precio_entrada, precio_salida):
    tokens_entrada = datos["usageMetadata"]["promptTokenCount"]
    tokens_salida = datos["usageMetadata"]["candidatesTokenCount"]
    costo_entrada = tokens_entrada * precio_entrada
    costo_salida = tokens_salida * precio_salida
    costo_total = costo_entrada + costo_salida
    return costo_total


def validar_pregunta(pregunta):

    for signo in [".", ",", ",", ";", "!", "¡", "?", "¿", '"']:
        pregunta = pregunta.replace(signo, "")

    palabras = pregunta.split()
    
    largo_valido_palabra = any(len(p) > 2 for p in palabras)

    if not pregunta or pregunta.strip() == "":
        raise ValueError("La pregunta debe ser una cadena de texto.")
    
    elif pregunta.isnumeric():
        raise ValueError("La pregunta no puede ser solo un número.")
    
    elif pregunta.isalpha() and len(pregunta.split()) == 1:
        raise ValueError("La pregunta debe tener al menos 2 palabras.")

    elif re.search(r'\b(?=[a-zA-Z]*\d)(?=\d*[a-zA-Z])[a-zA-Z\d]+\b', pregunta):
        raise ValueError("La pregunta no puede contener palabras que mezclen números y letras.")

    elif len(pregunta.split()) > 1 and any(len(palabra) > 23 for palabra in palabras):
        # La palabra más larga en español tiene 23 caracteres, por lo que se considera un límite razonable. 
        raise ValueError("Has ingresado una palabra demasiado larga.")
    
    elif not largo_valido_palabra:
        raise ValueError("La pregunta debe contener al menos una palabra con más de 2 caracteres.")
    
    else:
        return True


def construir_peticion(pregunta):
    if validar_pregunta(pregunta):
        api_key = os.getenv("GEMINI_API_KEY")
        modelo = "gemini-3.5-flash-lite"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        body = {
                
            "contents": [
                {"parts": [{"text": pregunta}]}
            ]
            }
        return url, body


def enviar_peticion(url, body):
    try:
        respuesta = requests.post(url, json=body)
    #    respuesta.raise_for_status()  # Lanza un error si la respuesta HTTP no es 200
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta nuevamente en unos momentos.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")
    #except Exception as e:
    #    print(f"Error inesperado al procesar la respuesta: {e}")


def extraer_texto(datos):
    try:
        print("Tokens prompt:", datos["usageMetadata"]["promptTokenCount"])
        print("Tokens candidates:", datos["usageMetadata"]["candidatesTokenCount"])
        print("Tokens total:", datos["usageMetadata"]["totalTokenCount"])
        return datos["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")


def obtener_dato_de_prueba(pregunta):
    try:
        url, body = construir_peticion(pregunta)
        datos = enviar_peticion(url, body)
        costo = calcular_costo(datos, 0.0000003, 0.0000025)
        print(f"Costo estimado de la petición: {costo}")
        return extraer_texto(datos)
    except KeyError as e:
        print(f"Error al extraer el dato de prueba: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
       
        return None


if __name__ == "__main__":
    pregunta = input("Introduce tu pregunta: ")
    try:
        resultado = obtener_dato_de_prueba(pregunta)
        if resultado is not None:
            print(resultado)
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)
