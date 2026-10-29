from collections import Counter
import re
from cliente import consultar_modelo


def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    if not isinstance(texto, str):
        raise ValueError("El argumento debe ser una cadena de texto.")
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()


def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token."""
    return Counter(tokens)


def procesar_texto(texto: str) -> list[str]:
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)


if __name__ == "__main__":

    dict_consulta = {
        "¿Qué es el sistema binario?": "El sistema binario es un sistema de numeración en base 2 que utiliza solo dos dígitos: 0 y 1.",
        "¿Para qué se utiliza el test de Turing?": "El test de Turing se utiliza para evaluar si una máquina es capaz de exhibir un comportamiento inteligente indistinguible del de un ser humano.",
        "¿Qué representa un byte?": "Un byte representa una unidad de información que generalmente consta de 8 bits.",
    }

    system_instruction = "Resume la respuesta en máximo 200 caracteres"

    for contador in range(3):
        consulta = list(dict_consulta.keys())[contador]
        referencia = dict_consulta[consulta]
        respuesta = consultar_modelo(consulta, system_instruction)

        # Texto crudo
        crudo_ref = referencia.split()
        crudo_resp = respuesta.split()
        comunes_crudo = set(crudo_ref) & set(crudo_resp)
        pct_crudo = len(comunes_crudo) / len(set(crudo_ref))

        # Texto procesado
        tokens_ref = procesar_texto(referencia)
        tokens_resp = procesar_texto(respuesta)
        comunes = set(tokens_ref) & set(tokens_resp)
        pct_proc = len(comunes) / len(set(tokens_ref))

        print(f"[Caso {contador+1}] Consulta: {consulta}\n")

        print(f"[Caso {contador+1}] Referencia: {referencia}\n")

        print(f"[Caso {contador+1}] Respuesta: {respuesta}\n")

        print(f"[Caso {contador+1}] Coincidencia texto crudo: {pct_crudo:.1%}")

        print(f"[Caso {contador+1}] Coincidencia texto procesado: {pct_proc:.1%}\n")

        print(160 * "*")
