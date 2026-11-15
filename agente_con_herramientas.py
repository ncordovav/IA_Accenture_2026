from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

load_dotenv()

modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")


@tool
def consultar_estado_cedula_pasaporte(run: str) -> str:
    """Consulta si la cédula de identidad o pasaporte
    está listo para retiro en las oficinas del Registro
    Civil en Santiago. Usar cuando el usuario pregunta
    si su documento de identidad ya está disponible."""

    # Simulación de registros de documentos
    registros = {
        "9.874.229-8": "Cédula lista para retiro en la oficina de Santiago Centro (Huérfanos).",
        "98.765.432-1": "Pasaporte en proceso de impresión y validación.",
    }

    return registros.get(
        run, "No se encontraron solicitudes vigentes para el RUN ingresado."
    )


@tool
def calcular_permiso_circulacion(patente: str, avaluo_fiscal: int) -> str:
    """Calcula el valor aproximado del Permiso de Circulación
    vehicular para una municipalidad de la Región Metropolitana
    en base al avaluo fiscal del vehículo. Usar cuando
    el usuario pregunta cuánto debe pagar por su permiso."""

    # Cálculo simulado estándar (ej: aprox 4.5% del avalúo fiscal)
    if avaluo_fiscal <= 0:
        return "El avalúo fiscal ingresado no es válido."

    valor_permiso = avaluo_fiscal * 0.045

    return f"El valor estimado del Permiso de Circulación para el vehículo patente {patente.upper()} es de ${valor_permiso:,.0f} CLP (sujeto a variaciones según multas o tasación oficial del SII)."


herramientas = [consultar_estado_cedula_pasaporte, calcular_permiso_circulacion]

prompt_agente = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente que responde preguntas "
            "usando las herramientas disponibles cuando "
            "las necesites.",
        ),
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

ejecutor_agente = AgentExecutor(
    agent=agente, tools=herramientas, verbose=True, return_intermediate_steps=True
)


if __name__ == "__main__":

    resultado = ejecutor_agente.invoke(
        {
            "entrada": "Necesito saber si mi cédula está lista para retiro, mi RUN es 9.874.229-8."
        }
    )

    print(f"Herramienta usada: {resultado["intermediate_steps"][0][0].tool}")

    print(resultado["output"])

    resultado = ejecutor_agente.invoke(
        {
            "entrada": (
                "¿Cuánto debo pagar por el permiso de circulación de mi auto, "
                "patente AB123CD, con avalúo fiscal de 5.000.000?"
            )
        }
    )
    print(f"Herramienta usada: {resultado["intermediate_steps"][0][0].tool}")

    print(resultado["output"])

    # Qué pasa si alguna entrada no tiene respuesta en las tools definidas
    resultado = ejecutor_agente.invoke({"entrada": "¿Qué es LangChain?"})

    print(f"Herramienta usada: {resultado["intermediate_steps"]}")

    print(resultado["output"])
