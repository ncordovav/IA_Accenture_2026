import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


load_dotenv()

consulta_usuario = "¿Dónde queda la oficina de ChileAtiende en Ñuñoa y qué horario tiene para sacar cédula?"

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

def construir_cadena(modelo):
    

# 1. Plantilla de extracción 
    plantilla_extraer = PromptTemplate.from_template(
        "Analiza la siguiente solicitud de usuario sobre trámites o servicios públicos "
        "y extrae únicamente las entidades clave presentes en el texto.\n"
        "Solicitud: {solicitud_usuario}\n"
        "Devuelve las entidades en el siguiente formato:\n"
        "- Entidad/Servicio: <nombre o tipo de servicio requerido>\n"
        "- Ubicación/Comuna: <comuna o sector mencionado, o \"No especificado\">\n"
        "- Intención: <propósito del trámite o duda principal>"
    )

    paso_extraer = plantilla_extraer | modelo | StrOutputParser()

    # 2. Plantilla de enriquecimiento 
    plantilla_enriquecer = PromptTemplate.from_template(
        "Dado el siguiente análisis preliminar de una solicitud:\n"
        "{salida_paso_1}\n\n"
        "Complementa la información aplicando las siguientes reglas de negocio:\n"
        "1. Identifica qué documentos o requisitos generales suelen solicitarse para esta Intención/Servicio en Chile.\n"
        "2. Determina la institución pública responsable si no fue mencionada explícitamente.\n"
        "3. Señala observaciones clave sobre la atención (por ejemplo, si requiere reserva previa de hora o si solo atiende días hábiles)."
    )

    paso_enriquecer = plantilla_enriquecer | modelo | StrOutputParser()

    # 3. Plantilla de formateo final 
    plantilla_formatear = PromptTemplate.from_template(
        "Convierte la siguiente información enriquecida en un objeto JSON plano válido "
        "(sin bloques de código markdown, solo el texto plano del JSON) con estas claves exactas:\n"
        "- servicio_requerido:\n"
        "- institucion:\n"
        "- comuna:\n"
        "- direccion:\n"
        "- horario:\n"
        "- tramites_asociados:\n"
        "- fuente_oficial:\n\n"
        "Información a procesar:\n"
        "{informacion_previa}"
    )

    # Se instancia correctamente el parser con StrOutputParser()
    paso_formatear = plantilla_formatear | modelo | StrOutputParser()


    cadena_api = (
        {"solicitud_usuario": lambda x: x["texto"]}
        | paso_extraer
        | (lambda datos: {"salida_paso_1": datos})
        | paso_enriquecer
        | (lambda informacion: {"informacion_previa": informacion})
        | paso_formatear
    )
    return cadena_api

if __name__ == "__main__":
    cadena_api = construir_cadena(modelo)
    resultado = cadena_api.invoke({"texto": consulta_usuario})
    #resultado = cadena_api.invoke({"texto": consulta_usuario})
    print(resultado)


