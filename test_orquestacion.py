import pytest
from unittest.mock import MagicMock
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage
from enrutamiento import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
    procesar_mensaje_seguro,
)


def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    # Se define la respuesta esperada en AIMessage
    respuesta_mock = AIMessage(content=" Queja \n")

    # Se configura tanto la llamada directa __call__ como el método .invoke()
    modelo_falso.return_value = respuesta_mock
    modelo_falso.invoke.return_value = respuesta_mock

    # Se envía 'texto' para coincidir con la variable de la plantilla
    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"texto": "algo salió mal"}
    )

    assert resultado == "queja"


def test_enrutamiento_va_a_cadena_queja():
    """Que un mensaje clasificado como 'queja' ejecuta 'cadena_queja', no cualquier otra ruta."""
    cadena_pregunta = RunnableLambda(lambda x: "Ruta Pregunta")
    cadena_queja = RunnableLambda(lambda x: "Ruta Queja")
    cadena_sugerencia = RunnableLambda(lambda x: "Ruta Sugerencia")

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta),
        (lambda x: x["categoria"] == "queja", cadena_queja),
        cadena_sugerencia,
    )

    enrutador = (
        RunnablePassthrough.assign(categoria=lambda x: x["clasificacion"]) | bifurcacion
    )

    resultado = enrutador.invoke(
        {"texto": "la plataforma está caída", "clasificacion": "queja"}
    )
    assert resultado == "Ruta Queja"


def test_enrutamiento_va_a_cadena_pregunta():
    """Que un mensaje clasificado como 'pregunta' ejecuta 'cadena_pregunta'."""
    cadena_pregunta = RunnableLambda(lambda x: "Ruta Pregunta")
    cadena_queja = RunnableLambda(lambda x: "Ruta Queja")
    cadena_sugerencia = RunnableLambda(lambda x: "Ruta Sugerencia")

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta),
        (lambda x: x["categoria"] == "queja", cadena_queja),
        cadena_sugerencia,
    )

    enrutador = (
        RunnablePassthrough.assign(categoria=lambda x: x["clasificacion"]) | bifurcacion
    )

    resultado = enrutador.invoke(
        {"texto": "¿dónde queda la oficina?", "clasificacion": "pregunta"}
    )
    assert resultado == "Ruta Pregunta"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    """Que una categoría que ninguna condición reconoce cae en la ruta por defecto, sin lanzar ningún error."""
    cadena_pregunta = RunnableLambda(lambda x: "Ruta Pregunta")
    cadena_queja = RunnableLambda(lambda x: "Ruta Queja")
    cadena_sugerencia = RunnableLambda(lambda x: "Ruta Sugerencia")

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta),
        (lambda x: x["categoria"] == "queja", cadena_queja),
        cadena_sugerencia,  # Ruta por defecto (catch-all)
    )

    enrutador = (
        RunnablePassthrough.assign(categoria=lambda x: x["clasificacion"]) | bifurcacion
    )

    # Categoría inesperada devuelta por el LLM
    resultado = enrutador.invoke(
        {"texto": "algo aleatorio", "clasificacion": "categoria_inventada"}
    )
    assert resultado == "Ruta Sugerencia"


def test_cadena_queja_usa_fallback_ante_fallo_del_modelo():
    def fallar_a_proposito(x):
        raise Exception("Error de red simulado")
        respuesta_generica = RunnableLambda(lambda x: "respuesta de respaldo")
        cadena_rota = RunnableLambda(fallar_a_proposito)
        cadena_segura = cadena_rota.with_fallbacks([respuesta_generica])
        resultado = cadena_segura.invoke({"mensaje": "algo"})
        assert resultado == "respuesta de respaldo"


def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")
    cadena_falsa = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
    )
    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")
    assert "no pudimos procesar" in resultado.lower()
