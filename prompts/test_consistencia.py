import requests
import json
import os
import re
import time

from dotenv import load_dotenv
load_dotenv()


def parsear_respuesta_json(texto):
  texto_limpio = texto.strip()
  texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
  texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
  try:
    return json.loads(texto_limpio)
  except json.JSONDecodeError:
    raise ValueError("La respuesta del modelo no es JSON válido.")


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
  elif len(pregunta.split()) > 1 and any(
      len(palabra) > 23 for palabra in palabras
  ):
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
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": pregunta}]}],
    }
    if response_schema is not None:
      body["generationConfig"] = {
          "responseMimeType": "application/json",
          "responseSchema": response_schema,
      }
    return url, body


def enviar_peticion(url, body):
  try:
    inicio = time.time()
    respuesta = requests.post(url, json=body)
    #print(f"Duración de la petición: {time.time() - inicio:.2f} segundos")
  except requests.exceptions.ConnectionError:
    raise RuntimeError("No se pudo conectar con el servicio.")
  try:
    return respuesta.json()
  except requests.exceptions.JSONDecodeError:
    raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")


def extraer_texto(datos):
  if "error" in datos:
    raise RuntimeError(f"Error devuelto por la API: {datos['error']}")
  candidates = datos.get("candidates", [])
  if not candidates:
    raise RuntimeError("La API no devolvió candidatos o hubo un bloqueo.")
  try:
    return candidates[0]["content"]["parts"][0]["text"]
  except (KeyError, IndexError):
    raise RuntimeError("La respuesta no trae el texto generado en el lugar esperado.")


if __name__ == "__main__":

  registro = {}

  # Obtener la ruta absoluta del directorio actual (prompts/)
  directorio_actual = os.path.dirname(os.path.abspath(__file__))

  # Construir la ruta hacia banco.json
  ruta_banco = os.path.join(directorio_actual, "banco.json")

  # Leer y cargar el archivo JSON
  with open(ruta_banco, "r", encoding="utf-8") as archivo:
    banco_de_prompts = json.load(archivo)

  for prompt in banco_de_prompts:
    exitos = 0
    intentos = 3

    for intento in range(intentos):
      try:
        # Construir la petición
        url, body = construir_peticion(
            prompt["ejemplo_usuario"],
            prompt["system_instruction"],
            prompt.get("response_schema"),
        )

        # Enviar petición y extraer texto
        respuesta = enviar_peticion(url, body)
        texto = extraer_texto(respuesta)

        # Parsear y validar que contenga las claves esperadas
        datos = parsear_respuesta_json(texto)
        if all(clave in datos for clave in prompt["claves_esperadas"]):
          exitos += 1
          
      except Exception as error:
        print(f"[{prompt['nombre']}] Intento {intento + 1} falló: {error}")

      # Backoff exponencial (si aún quedan intentos pendientes)
      if intento < intentos - 1:
        tiempo_espera = 2**intento  
        time.sleep(tiempo_espera)

    # Resumen final por prompt 
    print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas válidas")
    registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}

# Guardar el registro automáticamente en prompts/registro_resultados.json
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_resultados = os.path.join(directorio_actual, "registro_resultados.json")

    with open(ruta_resultados, "w", encoding="utf-8") as archivo:
      json.dump(registro, archivo, indent=2, ensure_ascii=False)

  print(f"\nResultados guardados en: {ruta_resultados}")