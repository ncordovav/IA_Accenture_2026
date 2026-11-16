corpus = [
    "El documento describe la arquitectura, componentes, herramientas, controles de seguridad "
    "y funciones de un agente conversacional con LangChain y gemini-3.1-flash-lite.",
    "El código utiliza dos diccionarios globales para simular fuentes de datos externas: "
    "ESTADOS y OFICINAS_CHILEATIENDE_RM.",
    "La herramienta generar_reembolso_membresia ejecuta la devolución monetaria tras obtener "
    "aprobación humana explícita.",
    "Las trazas se revisan a diario para detectar alucinaciones, desvíos del prompt, mal uso de herramientas "
    " o fugas de contexto."
    "Ante un comportamiento inesperado, se deben contener acciones críticas, aislar y reiniciar la sesión, "
    "auditar trazas y diagnosticar.",
]

splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
chunks = splitter.create_documents(corpus)

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="vectorstore/",
)

print(f"Indexados {len(chunks)} chunks en vectorstore/")
