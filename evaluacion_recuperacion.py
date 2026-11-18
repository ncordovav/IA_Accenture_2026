from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from datetime import datetime


# Cargar variables de entorno
 
load_dotenv()

# --- CONFIGURACIÓN Y DATOS ---

K = 3  # cuántos chunks recupera el retriever y cuántos evalúa la función


casos_evaluacion = [
    {
        "pregunta": "cual es el objetivo del agente",
        "ids_relevantes" : {"doc0"},
    },
    {
        "pregunta": "al agente da soporte a nivel nacional",
        "ids_relevantes" : {"doc0"},
    },
    {
        "pregunta": "el agente incluye servicios privados",
        "ids_relevantes" : {"doc0"},
    },
    {
        "pregunta": "el agente entrega información de las estaciones de Metro",
        "ids_relevantes" : set(),
    },
    {
        "pregunta": "el agente esta conectado a fuentes de datos externas",
        "ids_relevantes" : {"doc1"},
    },
        {
        "pregunta": "como se simulan las fuentes de datos externas ",
        "ids_relevantes" : {"doc1"},
    },    
        {
        "pregunta": "cuales son los nombres de las estructuras usadas para simular las fuentes de datos externas",
        "ids_relevantes" : {"doc1"},
    },  
        {
        "pregunta": "el agente considera dentro de las interacciones la devolucion de dinero",
        "ids_relevantes" : {"doc2"}
    },
        {
        "pregunta": "por que concepto se podria generar la devolucion de dinero y como se llama la funcion",
        "ids_relevantes" : {"doc2"},
    },
        {
        "pregunta": "el generar reembolso se ejecuta en forma automática",
        "ids_relevantes" : {"doc2"},
    },
        {
        "pregunta": "que se registra en las trazas",
        "ids_relevantes" : {"doc3"},
    },
        {
        "pregunta": "que se busca detectar en las trazas",
        "ids_relevantes" : {"doc3"},
    },
        {
        "pregunta": "con que frecuencia se sugiere la revision de trazas",
        "ids_relevantes" : {"doc3"},
    },
        {
        "pregunta": "en que consiste el calculo del permiso de circulacion",
        "ids_relevantes" : {"doc4"},
    },
        {
        "pregunta": "que informacion se requiere para solicitar el calculo del permiso de circulacion",
        "ids_relevantes" : {"doc4"},
    },
        {
        "pregunta": "el valor calculado para el permiso de circulacion es definitivo o solo referencial",
        "ids_relevantes" : {"doc4"},
    },        
]
 
 
 
def precision_at_k(ids_recuperados, ids_relevantes):
	"""Fraccion de los ids recuperados que son relevantes (0.0 si no hay ninguno)."""
	if not ids_recuperados:
		return 0.0
	acertados = [i for i in ids_recuperados if i in ids_relevantes]
	return len(acertados) / len(ids_recuperados)
 
 
def recall_at_k(ids_recuperados, ids_relevantes):
	"""Fraccion de los ids relevantes que se recuperaron (None si el caso no tiene ninguno)."""
	if not ids_relevantes:
		return None
	acertados = [i for i in ids_recuperados if i in ids_relevantes]
	return len(acertados) / len(ids_relevantes)
 
 
def promediar(valores):
	"""Promedio que ignora los None y evita dividir por cero."""
	validos = [v for v in valores if v is not None]
	return sum(validos) / len(validos) if validos else 0.0
 
 
def evaluar_recuperacion(retriever, casos, k=3):
	"""Corre cada caso contra el retriever real y promedia precision y recall."""
	resultados = []
	for caso in casos:
		chunks = retriever.invoke(caso["pregunta"])
		ids_recuperados = [c.id for c in chunks][:k]
		p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
		r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
		resultados.append({"pregunta": caso["pregunta"], "precision": p, "recall": r})
 
	precision_promedio = promediar(x["precision"] for x in resultados)
	recall_promedio = promediar(x["recall"] for x in resultados)
	return resultados, precision_promedio, recall_promedio

 


if __name__ == "__main__":

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    vectorstore = Chroma(persist_directory="vectorstore/", embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": K})
    
    resultados, precision_promedio, recall_promedio = evaluar_recuperacion(
        retriever, casos_evaluacion, k=K
    )

    # Imprimir en consola

    for r in resultados:
        recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
        print(f"{r['precision']:.2f}  {recall_txt}  {r['pregunta']}")
    print(f"\npromedio -> precision: {precision_promedio:.3f}  recall: {recall_promedio:.3f}")

    # Guardar en archivo

    with open("resultados_evaluacion.txt", "a", encoding="utf-8") as archivo:
        fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        archivo.write(f"\nFecha y hora: {fecha_hora_actual}\n")
        archivo.write(f"Configuracion: k={K}, chunk_size=200, chunk_overlap=30\n\n")
        for r in resultados:
            recall_txt = "n/a" if r["recall"] is None else f"{r['recall']:.2f}"
            archivo.write(f"{r['precision']:.2f}  {recall_txt}  {r['pregunta']}\n")
        archivo.write(
            f"\npromedio -> precision: {precision_promedio:.3f}  recall: {recall_promedio:.3f}\n"
        )
		
    print("Resultados guardados en resultados_evaluacion.txt")

