import os
import requests
from dotenv import load_dotenv
from cprint import cprint
import re
import json

load_dotenv()


def armar_peticion(
    pregunta: str, system_instruction: str, response_schema: dict = None
) -> tuple[str, dict]:
    if type(pregunta) != str:
        raise ValueError("La pregunta debe ser una cadena de texto.")
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = "gemini-3.5-flash-lite"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": [{"text": pregunta}]}],
    }
    if response_schema:
        body["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema,
        }
    return url, body


def extraer_texto(datos: dict) -> str:
    cprint.ok("Tokens prompt:", datos["usageMetadata"]["promptTokenCount"])
    cprint.ok("Tokens candidates:", datos["usageMetadata"]["candidatesTokenCount"])
    cprint.ok("Tokens total:", datos["usageMetadata"]["totalTokenCount"])
    return datos["candidates"][0]["content"]["parts"][0]["text"]
