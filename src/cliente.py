import os
import requests
from dotenv import load_dotenv
import re
import time
from typing import Callable, Any

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-3.6-flash:generateContent?key={GEMINI_API_KEY}"
)
headers = {"Content-Type": "application/json"}


def validar_pregunta(pregunta):
    for signo in [".", ",", ";", "!", "¡", "?", "¿", '"']:
        pregunta = pregunta.replace(signo, "")
    palabras = pregunta.split()
    largo_valido_palabra = any(len(p) > 2 for p in palabras)

    if not pregunta or pregunta.strip() == "":
        raise ValueError("Error! La pregunta no puede estar vacía.")
    elif pregunta.isnumeric():
        raise ValueError("Error! La pregunta no puede ser solo un número.")
    elif pregunta.isalpha() and len(pregunta.split()) == 1:
        raise ValueError("Error! La pregunta debe tener al menos 2 palabras.")
    elif re.search(r"\b(?=[a-zA-Z]*\d)(?=\d*[a-zA-Z])[a-zA-Z\d]+\b", pregunta):
        raise ValueError(
            "Error! La pregunta no puede contener palabras que mezclen números y"
            " letras."
        )
    elif len(pregunta.split()) > 1 and any(len(palabra) > 23 for palabra in palabras):
        raise ValueError("Error! Has ingresado una palabra demasiado larga.")
    elif not largo_valido_palabra:
        raise ValueError(
            "Error! La pregunta debe contener al menos una palabra con más de 2"
            " caracteres."
        )
    else:
        return True


def construir_peticion(pregunta, system_instruction, response_schema=None):
    if validar_pregunta(pregunta):
        # api_key = os.getenv("GEMINI_API_KEY")
        # modelo = "gemini-3.6-flash"
        # url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        body = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": pregunta}]}],
        }
        if response_schema is not None:
            body["generationConfig"] = {
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            }
        return body


def enviar_peticion(cuerpo):
    try:
        # print(f"Enviando petición a {URL} con cuerpo: {cuerpo}")
        respuesta = requests.post(URL, json=cuerpo, headers=headers, timeout=10)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        raise TimeoutError("No se pudo contactar al proveedor. Puede ser momentáneo.")
    if respuesta.status_code in (401, 403):
        # print(f"Error de autenticación: {respuesta.status_code} - {respuesta.text}")
        raise ValueError("Credencial inválida o sin permiso. Revisa tu GEMINI_API_KEY.")
    if respuesta.status_code == 429 or respuesta.status_code >= 500:
        raise TimeoutError(
            "El proveedor no pudo procesar la petición. Hay que esperar y reintentar."
        )
    #
    # print(respuesta.raise_for_status())
    return respuesta.json()


def extraer_texto(datos):
    if "error" in datos:
        raise RuntimeError(f"Error devuelto por la API: {datos['error']}")
    candidates = datos.get("candidates", [])
    if not candidates:
        raise RuntimeError("La API no devolvió candidatos o hubo un bloqueo.")
    try:
        return candidates[0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError(
            "La respuesta no trae el texto generado en el lugar esperado."
        )


def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_segundos: int = 2,
) -> Any:
    for intento in range(1, intentos + 1):
        try:
            return funcion()
            # answer = funcion()
            # print(f"Respuesta obtenida en el intento {intento}: {answer}")
            # return answer
        except TimeoutError:
            if intento == intentos:
                raise

            print(
                f"Intento {intento} de {intentos} falló por límite de uso. Reintentando..."
            )
            time.sleep(espera_segundos)


def consultar_modelo(
    pregunta: str,
    system_instruction: str = "",
) -> str:
    cuerpo = construir_peticion(pregunta, system_instruction)
    try:
        respuesta = con_reintento(lambda: enviar_peticion(cuerpo))
    except TimeoutError:
        raise RuntimeError(
            "El servicio no respondió tras varios intentos. Intenta más tarde."
        )
    return extraer_texto(respuesta)


if __name__ == "__main__":

    try:
        respuesta = consultar_modelo("¿Cuál es la capital de Chile?")
        print(respuesta)
    except ValueError as error:
        print(f"Error de configuración: {error}")
    except RuntimeError as error:
        print(error)
