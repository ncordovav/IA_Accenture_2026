# ---------- Matriz de riesgos y deteccion de casos en el limite
MIS_RIESGOS = [
    {
        "riesgo": "Filtracion de RUT o datos personales en logs de consulta ciudadana",
        "probabilidad": 4,
        "impacto": 5,
        "mitigacion": (
            "Redaccion/huella en logs en vez de contenido libre + control de acceso "
            "a trazas de auditoria (Bloque 31)"
        ),
    },
    {
        "riesgo": "Inyeccion de prompt via texto recuperado de ficha o documento externo",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Filtro de patrones que descarta sospechosos, usa solo documentos limpios, "
            "marca revision_humana_requerida y deriva a revision humana (Bloque 31)"
        ),
    },
    {
        "riesgo": "Respuesta con información desactualizada de oficinas por chunk no reindexado",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": (
            "Reindexacion incremental con ids explicitos por tramite + validacion humana "
            "antes de publicar cambios (Bloque 25)"
        ),
    },
    {
        "riesgo": "Cambios no validados en prompts o instrucciones del sistema",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Control de version/huella + aprobacion humana con interrupt()/Command "
            "y segundo revisor antes de activar en produccion (Bloque 32)"
        ),
    },
    {
        "riesgo": "Cambio o deprecacion de modelo de embeddings sin reindexar base vectorial",
        "probabilidad": 2,
        "impacto": 4,
        "mitigacion": (
            "Revision periodica de documentacion, verificacion de version del modelo "
            "y reindexacion limpia del indice si cambia (Bloque 28)"
        ),
    },
]


def puntaje_riesgo(probabilidad: int, impacto: int) -> int:
    return probabilidad * impacto


def categoria_riesgo(puntaje: int) -> str:
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 5:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad: int, impacto: int) -> bool:
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto),
        (probabilidad - 1, impacto),
        (probabilidad, impacto + 1),
        (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False


def evaluar_riesgos(riesgos: list[dict]) -> list[dict]:
    print("--- matriz de riesgos ---")
    for r in riesgos:
        r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
        r["categoria"] = categoria_riesgo(r["puntaje"])
        r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])

    for r in sorted(riesgos, key=lambda x: -x["puntaje"]):
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']}")
        print(f"           Mitigacion: {r['mitigacion']}")

    print("--- revision con otra persona (casos en el limite) ---")
    for r in riesgos:
        if r["al_limite"]:
            print(f"revisar con otra persona: {r['riesgo']}")
            # print(f"           Mitigacion: {r['mitigacion']}")

    return riesgos


if __name__ == "__main__":
    evaluar_riesgos(MIS_RIESGOS)
