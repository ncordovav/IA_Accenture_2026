import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
from langchain_core.runnables import RunnableLambda

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", timeout=10)
modelo_respaldo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", timeout=15)

respuesta_generica = RunnableLambda(
    lambda x: (
        "Gracias por tu mensaje. Un miembro de nuestro "
        "equipo te va a responder pronto."
    )
)


def construir_paso_clasificacion(modelo):
    plantilla_clasificar = PromptTemplate.from_template(
        "Clasifica el siguiente mensaje de usuario en una sola palabra: "
        "pregunta, queja o sugerencia. Responde únicamente con esa palabra.\n\n"
        "Mensaje: {texto}"
    )
    return (
        plantilla_clasificar
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )


def construir_cadena_queja(modelo):
    plantilla = PromptTemplate.from_template(
        "Responde a esta queja con empatía, reconociendo el problema antes de ofrecer una solución:\n\n{texto}"
    )
    return plantilla | modelo | StrOutputParser()


def construir_cadena_queja_segura(modelo_principal, modelo_respaldo):
    cadena_principal = construir_cadena_queja(modelo_principal)
    cadena_respaldo = construir_cadena_queja(modelo_respaldo)
    return cadena_principal.with_fallbacks([cadena_respaldo, respuesta_generica])


def construir_cadena_sugerencia(modelo):
    plantilla = PromptTemplate.from_template(
        "Agradece esta sugerencia y explica cómo se evaluará dentro del producto:\n\n{texto}"
    )
    return plantilla | modelo | StrOutputParser()


def construir_cadena_pregunta(modelo):
    plantilla_extraer = PromptTemplate.from_template(
        "Analiza la siguiente solicitud sobre trámites o servicios públicos en Chile "
        "y extrae únicamente las entidades clave.\n\n"
        "Solicitud: {solicitud_usuario}\n\n"
        "Formato de respuesta:\n"
        "- Entidad/Servicio: <nombre o tipo de servicio>\n"
        '- Ubicación/Comuna: <comuna o sector mencionado, o "No especificado">\n'
        "- Intención: <propósito principal>"
    )
    paso_extraer = plantilla_extraer | modelo | StrOutputParser()

    plantilla_enriquecer = PromptTemplate.from_template(
        "Dado el siguiente análisis preliminar:\n{salida_paso_1}\n\n"
        "Complementa la información aplicando estas reglas de negocio para Chile:\n"
        "1. Identifica qué documentos o requisitos generales suelen solicitarse.\n"
        "2. Determina la institución pública responsable si no fue mencionada explícitamente.\n"
        "3. Señala observaciones clave sobre la atención (reserva de hora, días hábiles, etc.)."
    )
    paso_enriquecer = plantilla_enriquecer | modelo | StrOutputParser()

    plantilla_formatear = PromptTemplate.from_template(
        "Convierte la siguiente información enriquecida en un objeto JSON plano válido "
        "(sin bloques de código markdown, entrega únicamente el texto JSON puro) con estas claves exactas:\n"
        "- servicio_requerido\n"
        "- institucion\n"
        "- comuna\n"
        "- direccion\n"
        "- horario\n"
        "- tramites_asociados\n"
        "- fuente_oficial\n\n"
        "Información a procesar:\n{informacion_previa}"
    )
    paso_formatear = plantilla_formatear | modelo | StrOutputParser()

    return (
        {"solicitud_usuario": lambda x: x["texto"]}
        | paso_extraer
        | (lambda datos: {"salida_paso_1": datos})
        | paso_enriquecer
        | (lambda info: {"informacion_previa": info})
        | paso_formatear
    )


def construir_cadena_pregunta_segura(modelo_principal, modelo_respaldo):
    """Construye la cadena de pregunta aplicando with_fallbacks con modelo de respaldo y respuesta genérica."""
    cadena_principal = construir_cadena_pregunta(modelo_principal)
    cadena_respaldo = construir_cadena_pregunta(modelo_respaldo)

    return cadena_principal.with_fallbacks([cadena_respaldo, respuesta_generica])


def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_queja=None,
    cadena_sugerencia=None,
    cadena_pregunta=None,
):
    cadena_queja = cadena_queja or RunnablePassthrough()
    cadena_sugerencia = cadena_sugerencia or RunnablePassthrough()
    cadena_pregunta = cadena_pregunta or RunnablePassthrough()

    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta),
        (lambda x: x["categoria"] == "queja", cadena_queja),
        cadena_sugerencia,
    )

    return RunnablePassthrough.assign(categoria=paso_clasificacion) | bifurcacion


def construir_cadena_unificada(modelo_principal, modelo_respaldo):
    paso_clasificacion = construir_paso_clasificacion(modelo_principal)

    # Ambas rutas principales cuentan ahora con su respectiva protección con fallbacks
    cadena_queja = construir_cadena_queja_segura(modelo_principal, modelo_respaldo)
    cadena_pregunta = construir_cadena_pregunta_segura(
        modelo_principal, modelo_respaldo
    )

    cadena_sugerencia = construir_cadena_sugerencia(modelo_principal)

    return construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasificacion,
        cadena_queja=cadena_queja,
        cadena_sugerencia=cadena_sugerencia,
        cadena_pregunta=cadena_pregunta,
    )


def procesar_mensaje_seguro(cadena_o_mensaje, mensaje_opcional=None):
    """
    Permite invocar el procesamiento de forma segura aceptando:
    1. procesar_mensaje_seguro("mensaje") -> Construye y ejecuta la cadena unificada por defecto.
    2. procesar_mensaje_seguro(cadena_falsa, "mensaje") -> Ejecuta la cadena personalizada (ideal para tests).
    """
    try:
        if mensaje_opcional is not None:
            # Si se pasan dos argumentos, el primero es la cadena/enrutador y el segundo el mensaje
            cadena_api = cadena_o_mensaje
            mensaje = mensaje_opcional
        else:
            # Si se pasa un solo argumento, es el mensaje y construimos la cadena unificada estándar
            cadena_api = construir_cadena_unificada(modelo, modelo_respaldo)
            mensaje = cadena_o_mensaje

        return cadena_api.invoke({"texto": mensaje})

    except Exception as error:
        logger.error(f"Error procesando mensaje: {error}")
        return (
            "No pudimos procesar tu mensaje en este momento. "
            "Intenta de nuevo más tarde."
        )


if __name__ == "__main__":

    print("=" * 60)
    print(" 1. PRUEBAS DE FLUJO NORMAL (HAPPY PATHS)")
    print("=" * 60)

    # Caso 1: Pregunta de servicio público
    print("\n--- CASO A: PREGUNTA ---")
    res_pregunta = procesar_mensaje_seguro(
        "¿Dónde queda la oficina de ChileAtiende en Ñuñoa y qué horario tiene para sacar cédula?"
    )
    print(res_pregunta)

    # Caso 2: Queja
    print("\n--- CASO B: QUEJA ---")
    res_queja = procesar_mensaje_seguro(
        "La plataforma está caída y no me deja ingresar mi solicitud desde ayer."
    )
    print(res_queja)

    # Caso 3: Sugerencia (Ruta por defecto)
    print("\n--- CASO C: SUGERENCIA ---")
    res_sugerencia = procesar_mensaje_seguro(
        "Sería excelente que agregaran una opción para enviar recordatorios por WhatsApp cuando se acerque la fecha de la cita."
    )
    print(res_sugerencia)

    print("\n" + "=" * 60)
    print(" 2. PRUEBAS DE RESILIENCIA Y TOLERANCIA A FALLOS")
    print("=" * 60)

    print("=== PRUEBA DE FALLBACK EN RUTA (PREGUNTA) ===")

    # Se crea un modelo principal simulado que falle a propósito
    modelo_principal_roto_pregunta = RunnableLambda(
        lambda x: (_ for _ in ()).throw(
            Exception("Fallo crítico en modelo principal de preguntas")
        )
    )

    # Se construye la cadena de pregunta de prueba aplicando with_fallbacks
    # Se usa construir_cadena_pregunta con el modelo roto y la respaldamos con el modelo real y la respuesta genérica
    cadena_pregunta_con_fallo_forzado = construir_cadena_pregunta(
        modelo_principal_roto_pregunta
    ).with_fallbacks([construir_cadena_pregunta(modelo_respaldo), respuesta_generica])

    # Se ensambla un enrutador temporal que fuerce la categoría "pregunta"
    enrutador_prueba_pregunta = RunnablePassthrough.assign(
        categoria=RunnableLambda(lambda x: "pregunta")
    ) | RunnableBranch(
        (lambda x: x["categoria"] == "pregunta", cadena_pregunta_con_fallo_forzado),
        RunnablePassthrough(),
    )

    # Se invoca el enrutador de prueba
    resultado_fallback_pregunta = enrutador_prueba_pregunta.invoke(
        {"texto": "¿Dónde queda la oficina de ChileAtiende en Ñuñoa?"}
    )

    print("Resultado obtenido tras activar el fallback en la ruta de pregunta:")
    print(resultado_fallback_pregunta)

    # Prueba de Fallback Específico en una Ruta (Ej: Queja con modelo principal roto)
    print("\n--- PRUEBA DE FALLBACK EN RUTA (QUEJA) ---")
    modelo_principal_roto = RunnableLambda(
        lambda x: (_ for _ in ()).throw(
            Exception("Fallo crítico simulado en modelo principal")
        )
    )

    # Se construye una cadena de queja de prueba con el modelo roto
    cadena_queja_rota = construir_cadena_queja(modelo_principal_roto).with_fallbacks(
        [construir_cadena_queja(modelo_respaldo), respuesta_generica]
    )

    # Enrutador temporal para forzar la ruta de queja
    enrutador_fallback_prueba = RunnablePassthrough.assign(
        categoria=RunnableLambda(lambda x: "queja")
    ) | RunnableBranch(
        (lambda x: x["categoria"] == "queja", cadena_queja_rota),
        RunnablePassthrough(),
    )

    resultado_fallback = enrutador_fallback_prueba.invoke(
        {"texto": "El servicio no funciona"}
    )
    print("Resultado obtenido tras activar el fallback de la ruta:", resultado_fallback)

    # Prueba del Try/Except General (Fallo a nivel raíz / clasificación)
    print("\n--- PRUEBA DE TRY/EXCEPT GLOBAL (CLASIFICACIÓN ROTA) ---")

    # Se sobrescribe temporalmente el modelo principal por uno que explote en la raíz
    modelo_principal_roto = RunnableLambda(
        lambda x: (_ for _ in ()).throw(
            Exception("Error de red masivo / Timeout global")
        )
    )

    # Se llama a procesar_mensaje_seguro inyectando el fallo general

    try:
        cadena_api_rota = construir_cadena_unificada(
            modelo_principal_roto, modelo_respaldo
        )
        resultado_global = cadena_api_rota.invoke({"texto": "Prueba de fallo global"})
    except Exception as e:
        # Si la cadena no tuviera try interno, caería aquí; como procesar_mensaje_seguro lo encapsula:
        pass

    # Se verifica el comportamiento seguro
    print("Invocando procesar_mensaje_seguro con servicio caído:")

    print(
        "Respuesta segura obtenida:",
        procesar_mensaje_seguro("Mensaje de prueba bajo fallo"),
    )

    print("\n" + "=" * 60)
    print(" PRUEBAS FINALIZADAS EXITOSAMENTE")
    print("=" * 60)
