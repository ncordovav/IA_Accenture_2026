from datetime import datetime, timezone
import json
import sys
import threading
from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

# Base de datos simulada cédulas y pasaportes
ESTADOS = {
    "9.874.229-8": {
        "actual": (
            "Cédula lista para retiro en la oficina de Santiago Centro"
            " (Huérfanos)."
        ),
        "historial": [
            "documento solicitado en oficina digital",
            "pago y antecedentes aprobados",
            "en proceso de fabricación",
            "despachado y disponible para retiro en oficina de destino",
        ],
    },
    "98.765.432-1": {
        "actual": "Pasaporte en proceso de impresión y validación.",
        "historial": [
            "pasaporte solicitado y citado a captura de datos",
            "captura de huellas y fotografía completada",
            "aprobado por control de calidad",
            "en proceso de impresión y validación",
        ],
    },
}

# Base de datos simulada de oficinas ChileAtiende en la Región Metropolitana por comuna
OFICINAS_CHILEATIENDE_RM = {
    "santiago": [
        {
            "oficina": "Santiago Centro",
            "direccion": "Avenida Libertador Bernardo O'Higgins 1353",
            "horario": "Lunes a Viernes, 08:30 a 14:00 horas",
            "servicios": [
                "Cédulas",
                "Pasaportes",
                "ClaveÚnica",
                "IPS",
                "Registro Civil",
            ],
        },
    ],
    "ñuñoa": [
        {
            "oficina": "Ñuñoa",
            "direccion": "Avenida José Pedro Alessandri 211",
            "horario": "Lunes a Viernes, 08:30 a 14:00 horas",
            "servicios": ["Cédulas", "Pasaportes", "ClaveÚnica", "Registro Civil"],
        }
    ],
    "providencia": [
        {
            "oficina": "Providencia",
            "direccion": "Avenida Holanda 254",
            "horario": "Lunes a Viernes, 08:30 a 14:00 horas",
            "servicios": ["Cédulas", "Pasaportes", "ClaveÚnica", "IPS"],
        }
    ],
    "maipú": [
        {
            "oficina": "Maipú",
            "direccion": "Avenida Los Pajaritos 629",
            "horario": "Lunes a Viernes, 08:30 a 14:00 horas",
            "servicios": [
                "Cédulas",
                "Pasaportes",
                "ClaveÚnica",
                "IPS",
                "Registro Civil",
            ],
        }
    ],
    "puente alto": [
        {
            "oficina": "Puente Alto",
            "direccion": "Santo Domingo 481",
            "horario": "Lunes a Viernes, 08:30 a 14:00 horas",
            "servicios": [
                "Cédulas",
                "Pasaportes",
                "ClaveÚnica",
                "IPS",
                "Registro Civil",
            ],
        }
    ],
}


# Esquema Pydantic y Tools
class ArgumentosConsultaCedulaPasaporte(BaseModel):
  run: str = Field(
      description="RUN del ciudadano para la consulta (ej. 9.874.229-8)."
  )
  incluir_historial: bool = Field(
      default=False,
      description=(
          "Si es True, se debe incluir el historial completo de tramitación."
      ),
  )


@tool(
    "consultar_estado_cedula_pasaporte",
    args_schema=ArgumentosConsultaCedulaPasaporte,
)
def consultar_estado_cedula_pasaporte(
    run: str, incluir_historial: bool = False
) -> str:
  """Consulta si la cédula de identidad o pasaporte

  está listo para retiro en las oficinas del Registro
  Civil en Santiago, con opción de incluir su historial completo.
  """
  doc = ESTADOS.get(run)
  if doc is None:
    return f"No se encontraron solicitudes vigentes para el RUN {run}."

  if not incluir_historial:
    return doc["actual"]

  historial_str = ", ".join(doc["historial"])
  return f"{doc['actual']} (Historial de tramitación: {historial_str})"


class ArgumentosBuscarDocumentacion(BaseModel):
  comuna: str = Field(
      description=(
          "Nombre de la comuna de la Región Metropolitana para buscar las"
          " oficinas de ChileAtiende (ej. 'Santiago', 'Ñuñoa', 'Providencia',"
          " 'Maipú', 'Puente Alto')."
      )
  )


@tool("buscar_documentacion", args_schema=ArgumentosBuscarDocumentacion)
def buscar_documentacion(comuna: str) -> str:
  """Busca información, direcciones, horarios y servicios disponibles de las oficinas

  de ChileAtiende en una comuna específica de la Región Metropolitana.
  """
  comuna_limpia = comuna.strip().lower()
  oficinas = OFICINAS_CHILEATIENDE_RM.get(comuna_limpia)

  if not oficinas:
    comunas_disponibles = ", ".join(
        [c.title() for c in OFICINAS_CHILEATIENDE_RM.keys()]
    )
    return (
        f"No se encontraron registros de oficinas de ChileAtiende para la"
        f" comuna '{comuna}' en la Región Metropolitana. Comunas disponibles en"
        f" la base de datos simulada: {comunas_disponibles}."
    )

  resultado_texto = f"Oficinas de ChileAtiende en la comuna de {comuna.title()} (Región Metropolitana):\n"
  for idx, oficina in enumerate(oficinas, start=1):
    servicios_str = ", ".join(oficina["servicios"])
    resultado_texto += (
        f"\n{idx}. Sucursal: {oficina['oficina']}\n"
        f"   - Dirección: {oficina['direccion']}\n"
        f"   - Horario: {oficina['horario']}\n"
        f"   - Servicios: {servicios_str}\n"
    )

  return resultado_texto


@tool
def calcular_permiso_circulacion(patente: str, avaluo_fiscal) -> str:
  """Calcula el valor aproximado del Permiso de Circulación

  vehicular para una Municipalidad de la Región Metropolitana
  en base al avalúo fiscal del vehículo. Usar cuando
  el usuario pregunta cuánto debe pagar por su permiso (patente).
  """
  try:
    avaluo = float(avaluo_fiscal)
    if avaluo <= 0:
      raise ValueError("El avalúo debe ser mayor a cero.")
    valor_permiso = avaluo * 0.045
    return (
        f"El valor estimado del Permiso de Circulación para el vehículo patente"
        f" {patente.upper()} es de ${valor_permiso:,.0f} CLP (sujeto a"
        f" variaciones según multas o tasación oficial del SII)."
    )
  except (ValueError, TypeError):
    return (
        "El avalúo fiscal ingresado no es válido. Debe ser un número mayor a"
        " cero."
    )


registro_aprobaciones = []


@tool
def calcular_reembolso_membresia(tipo_membresia: str, cantidad_meses: int) -> str:
  """Calcula la devolución por un cargo erróneo de membresía realizado a un cliente.

  Se debe tener en cuenta que los cobros automáticos se realizan el 1° de cada
  mes.
  Utiliza esta herramienta antes de proceder con el reembolso si el cliente
  reporta cobros indebidos de membresía.
  """
  try:
    tipo_membresia = tipo_membresia.lower()
    monto = 15000 if tipo_membresia == "premium" else 10500
    meses = int(cantidad_meses)
    if monto <= 0 or meses <= 0:
      raise ValueError("El monto y los meses deben ser mayores a cero.")

    total_devolucion = monto * meses
    return (
        f"Cálculo de devolución de membresía: Considerando que los cobros se"
        f" ejecutan el 1° de cada mes, se identificaron {meses} mes(es) con"
        f" cobros erróneos de ${monto:,.0f} cada uno. El monto total a"
        f" reembolsar es de ${total_devolucion:,.0f} CLP."
    )
  except (ValueError, TypeError):
    return (
        "Los datos ingresados para el cálculo de la membresía no son válidos."
        " El monto y la cantidad de meses deben ser numéricos y mayores a cero."
    )


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 300) -> bool:
  print(mensaje, end="", flush=True)
  resultado = [False]

  def pedir_entrada():
    try:
      respuesta = sys.stdin.readline()
      if respuesta:
        resultado[0] = respuesta.strip().lower() == "s"
    except Exception:
      pass

  hilo = threading.Thread(target=pedir_entrada)
  hilo.daemon = True
  hilo.start()
  hilo.join(timeout=tiempo_limite_segundos)

  if hilo.is_alive():
    print("\nTiempo de espera agotado.")
    return False

  return resultado[0]


def registrar_aprobacion(
    herramienta: str, argumentos: dict, aprobado: bool
) -> None:
  registro_aprobaciones.append(
      {
          "herramienta": herramienta,
          "argumentos": argumentos,
          "aprobado": aprobado,
          "momento": datetime.now().isoformat(),
      }
  )


@tool
def generar_reembolso_membresia(numero_cliente: str, monto: float) -> str:
  """Genera un reembolso de membresía para un cliente. Acción

  irreversible: requiere aprobación humana antes
  de ejecutarse.
  """
  mensaje = (
      f"El agente quiere reembolsar ${monto} para el cliente {numero_cliente}."
      " ¿Aprobar? (s/n): "
  )
  aprobado = esperar_aprobacion(mensaje)
  registrar_aprobacion(
      herramienta="generar_reembolso",
      argumentos={"numero_cliente": numero_cliente, "monto": monto},
      aprobado=aprobado,
  )

  if not aprobado:
    return "Reembolso no aprobado por el supervisor humano."

  return f"Reembolso de ${monto} generado para el cliente {numero_cliente}."


def normalizar_salida_agente(resultado: dict) -> dict:
  """Convierte la salida del agente a texto plano."""
  salida = resultado.get("output", "")

  if isinstance(salida, list):
    textos = []
    for bloque in salida:
      if isinstance(bloque, dict):
        if bloque.get("type") == "text":
          textos.append(bloque.get("text", ""))
      elif isinstance(bloque, str):
        textos.append(bloque)
    resultado["output"] = "\n".join(textos)

  return resultado


# Almacena los historiales de las distintas sesiones.
historiales = {}


def obtener_historial(session_id: str) -> InMemoryChatMessageHistory:
  """Recupera el historial de una sesión."""
  if session_id not in historiales:
    historiales[session_id] = InMemoryChatMessageHistory()
  return historiales[session_id]


def registrar_traza(
    session_id: str, entrada: str, resultado: dict
) -> None:
  """Guarda una interacción del agente como una línea JSON en trazas_agente.jsonl."""
  registro = {
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "session_id": session_id,
      "entrada": entrada,
      "acciones": [
          {
              "herramienta": accion.tool,
              "argumentos": accion.tool_input,
              "observacion": observacion,
          }
          for accion, observacion in resultado.get("intermediate_steps", [])
      ],
      "respuesta_final": resultado["output"],
  }

  with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
    print("Escribiendo traza en el archivo trazas_agente.jsonl...")
    archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


def reiniciar_sesion(session_id: str) -> None:
  """Limpia el historial de una sesión y registra la acción en trazas_agente.jsonl."""
  historiales.pop(session_id, None)
  
  registro = {
      "timestamp": datetime.now(timezone.utc).isoformat(),
      "session_id": session_id,
      "evento": "reiniciar_sesion",
      "descripcion": f"Historial de la sesión '{session_id}' eliminado y reiniciado.",
  }

  with open("trazas_agente.jsonl", "a", encoding="utf-8") as archivo:
    print(f"Registrando evento de reinicio de sesión en trazas_agente.jsonl...")
    archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

  print(f"[RESET] Historial de la sesión '{session_id}' eliminado y registrado correctamente.")


def crear_agente_con_memoria():
  """Construye el agente, sus herramientas y la memoria conversacional."""
  herramientas = [
      consultar_estado_cedula_pasaporte,
      calcular_permiso_circulacion,
      calcular_reembolso_membresia,
      generar_reembolso_membresia,
      buscar_documentacion,
  ]

  prompt_agente = ChatPromptTemplate.from_messages([
      (
          "system",
          (
              "Eres un asistente de servicios públicos que responde preguntas"
              " usando las herramientas disponibles cuando las necesites. Usa"
              " texto plano sin formato JSON ni Markdown. REGLA OBLIGATORIA:"
              " Cada vez que informes sobre el estado de una cédula, pasaporte o"
              " trámite, DEBES mencionar explícitamente el RUN del usuario en tu"
              " respuesta final."
          ),
      ),
      MessagesPlaceholder("chat_history"),
      ("human", "{entrada}"),
      MessagesPlaceholder("agent_scratchpad"),
  ])

  agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

  ejecutor_agente = AgentExecutor(
      agent=agente, tools=herramientas, verbose=True, return_intermediate_steps=True
  )

  ejecutor_normalizado = ejecutor_agente | RunnableLambda(
      normalizar_salida_agente
  )

  agente_con_memoria = RunnableWithMessageHistory(
      ejecutor_normalizado,
      obtener_historial,
      input_messages_key="entrada",
      history_messages_key="chat_history",
      output_messages_key="output",
  )

  return agente_con_memoria


def imprimir_pasos_intermedios(resultado: dict) -> None:
  """Muestra las herramientas utilizadas por el agente."""
  pasos = resultado.get("intermediate_steps", [])

  if not pasos:
    print("\nEl agente no utilizó herramientas.")
    return

  print("\n--- HERRAMIENTAS UTILIZADAS ---")
  for numero, (accion, observacion) in enumerate(pasos, start=1):
    print(f"Herramienta: {accion.tool}")
    print(f"Argumentos: {accion.tool_input}")
    print(f"Resultado: {observacion}")


def ejecutar_consulta(agente, pregunta, session_id):
  """Envía una consulta, muestra la respuesta y registra la traza."""
  config = {"configurable": {"session_id": session_id}}
  resultado = agente.invoke({"entrada": pregunta}, config)

  print("\n--- CONSULTA ---")
  print(pregunta)

  print("\n--- RESPUESTA DEL AGENTE ---")
  print(resultado["output"])

  imprimir_pasos_intermedios(resultado)
  registrar_traza(session_id, pregunta, resultado)

  return resultado


if __name__ == "__main__":
  print(50 * "=")
  print("   INICIANDO ASISTENTE DE SERVICIOS PÚBLICOS ")
  print(50 * "=")

  agente = crear_agente_con_memoria()

  # Pruebas de consulta utilizando herramientas y memoria
  ejecutar_consulta(
      agente,
      "Necesito saber el estado de mi cédula, mi RUN es 9.874.229-8",
      "session_001",
  )

  ejecutar_consulta(
      agente,
      "Estado de mi pasaporte, RUN 98.765.432-1",
      "session_002",
  )

  ejecutar_consulta(
      agente,
      (
          "Quiero consultar por el valor del permiso de circulación para mi"
          " vehículo patente ABCD123 con un avalúo de 10000000 CLPs"
      ),
      "session_003",
  )

  ejecutar_consulta(
      agente,
      (
          "Hola, me cobraron erróneamente la membresía premium durante 2"
          " meses. Por favor calcula la devolución, para luego solicitar el"
          " reembolso para el cliente C-0145."
      ),
      "session_004",
  )

  # Prueba invocando la herramienta de reembolso a través del agente
  ejecutar_consulta(
      agente,
      "Por favor genera un reembolso de 30000 para el cliente C-0145",
      "session_004",
  )

  ejecutar_consulta(
      agente,
      "¿Dónde queda la oficina de ChileAtiende en Ñuñoa y qué horario tiene?",
      "session_05",
  )

  # Ejemplo de limpieza y registro de reinicio de sesión ante comportamiento inesperado
  reiniciar_sesion("session_001")

  print("\nProceso finalizado. Revisa el archivo 'trazas_agente.jsonl'.")