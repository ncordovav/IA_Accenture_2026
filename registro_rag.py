import time
import json
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


@contextmanager
def medir(tiempos, etapa):
    inicio = time.perf_counter()
    yield
    tiempos[etapa] = time.perf_counter() - inicio


def formatear_contexto(chunks_recuperados):
    lineas = []
    for i, doc in enumerate(chunks_recuperados, start=1):
        lineas.append(f"[{i}] {doc.page_content}")
    return "\n\n".join(lineas)


def registrar_consulta(pregunta, k, persist_directory):
    """Corre una consulta RAG real, midiendo tiempo por etapa y tokens reales
    de la respuesta del modelo."""
    tiempos = {}

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    chat_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

    with medir(tiempos, "embed_y_busqueda"):
        vectorstore = Chroma(
            persist_directory=persist_directory, embedding_function=embeddings
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        chunks = retriever.invoke(pregunta)

    contexto = formatear_contexto(chunks)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    with medir(tiempos, "generacion"):
        respuesta = chat_model.invoke(prompt)

    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "tiempos_ms": {etapa: round(s * 1000, 2) for etapa, s in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": dict(respuesta.usage_metadata) if respuesta.usage_metadata else None,
    }
    return registro


if __name__ == "__main__":
    preguntas_prueba = [
        "cual es el objetivo del agente",
        "como se simulan las fuentes de datos externas",
        "por que concepto se podria generar la devolucion de dinero y como se llama la funcion",
    ]

    for pregunta in preguntas_prueba:
        valores_k = [3, 6]
        for k in valores_k:
            registro = registrar_consulta(pregunta, k, persist_directory="vectorstore/")
            print(json.dumps(registro, indent=2, ensure_ascii=False))

            with open("registros_latencia_costo.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(registro, ensure_ascii=False) + "\n")
