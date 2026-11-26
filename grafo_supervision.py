from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    return {}


def supervisar(estado: EstadoDespliegue):
    decision = interrupt(
        {
            "motivo": "aprobar nueva version de prompt en produccion",
            "huella_propuesta": estado["huella_nueva"],
        }
    )
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print("version", estado["huella_nueva"], "activada")
    else:
        print("version", estado["huella_nueva"], "rechazada, se mantiene la anterior")
    return {}


grafo = StateGraph(EstadoDespliegue)
grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

app_despliegue = grafo.compile(checkpointer=InMemorySaver())

# Reemplaza esta huella por la obtenida en registro_prompts.py:
huella = "dbbedda0c8ea"

# 1) Dejar pausado y luego aprobar
config_aprobacion = {"configurable": {"thread_id": "despliegue-stgo-aprobar-1"}}
pausa = app_despliegue.invoke(
    {"huella_nueva": huella, "aprobado": False}, config=config_aprobacion
)
print("1) tras invocar:", pausa)
print("2) pendiente:", app_despliegue.get_state(config_aprobacion).interrupts[0].value)

res_aprobado = app_despliegue.invoke(Command(resume=True), config=config_aprobacion)
print("3) tras aprobar:", res_aprobado)

# 2) Rechazar con un thread_id distinto
config_rechazo = {"configurable": {"thread_id": "despliegue-stgo-rechazar-1"}}
app_despliegue.invoke(
    {"huella_nueva": huella, "aprobado": False}, config=config_rechazo
)
res_rechazado = app_despliegue.invoke(Command(resume=False), config=config_rechazo)
print("4) tras rechazar:", res_rechazado)
