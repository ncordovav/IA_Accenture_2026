from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmación con su número entre corchetes, como [1]. Si el contexto no \
contiene la información exacta para responder, responde únicamente: \
'No dispongo de información suficiente en la base de conocimientos para responder esta consulta' \
y no agregues nada más.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def formatear_contexto(chunks_recuperados):
    """Arma un bloque de contexto numerado para el prompt, y un mapa
    numero -> fuente para reconstruir la cita despues."""
    lineas = []
    citas = {}
    for i, doc in enumerate(chunks_recuperados, start=1):
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente
    contexto = "\n\n".join(lineas)
    return contexto, citas


def construir_prompt(pregunta, persist_directory, k=3):
    """Recupera los k chunks mas relevantes para la pregunta y arma
    el prompt
    dinmáico con contexto numerado, listo para pasarle al modelo."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(
        persist_directory=persist_directory, embedding_function=embeddings
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})

    chunks_recuperados = retriever.invoke(pregunta)
    contexto, citas = formatear_contexto(chunks_recuperados)
    prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)
    return prompt, citas


if __name__ == "__main__":

    preguntas = [
        "¿Cuál es el objetivo del agente?",
        "¿Cómo se simulan las fuentes de datos externas?",
        "¿En qué consiste generar reembolso?",
    ]

    for pregunta in preguntas:
        prompt, citas = construir_prompt(
            pregunta,
            persist_directory="vectorstore/",
        )
        print(prompt)
        print(citas)

    # Pregunta totalmente fuera del alcance de tu corpus
    pregunta_prueba = "¿Cuál es la capital de Francia y cuántos habitantes tiene?"
    print("\n" + 60 * "-")
    print("-- PREGUNTA FUERA DEL ALCANCE DEL CORPUS --")
    print(pregunta_prueba)
    print(60 * "-")

    # Construir el prompt con la base vectorial existente
    prompt, citas = construir_prompt(
        pregunta_prueba,
        persist_directory="vectorstore/",
    )

    # 2. Inicializar el modelo de chat de Gemini y enviarle el prompt
    modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    respuesta = modelo.invoke(prompt)

    print("--- PROMPT ENVIADO AL MODELO ---")
    print(prompt)
    print("-" * 40)
    print("\n--- RESPUESTA DEL MODELO ---")
    print(respuesta.content)
