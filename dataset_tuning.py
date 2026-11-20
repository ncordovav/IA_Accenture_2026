import json
from google.genai import types
from collections import Counter

ejemplos_raw = [
    (
        "¿Cuál es la dirección exacta de la oficina del Registro Civil más cercana en Ñuñoa para sacar carnet?",
        {"categoria": "consulta_direccion", "prioridad": "baja"},
    ),
    (
        "Necesito saber la dirección del CESFAM correcta de mi sector porque el número que se informa no corresponde.",
        {"categoria": "consulta_direccion", "prioridad": "alta"},
    ),
    (
        "¿A qué hora abre ChileAtiende en Santiago Centro hoy viernes y si atienden por orden de llegada?",
        {"categoria": "consulta_horario", "prioridad": "baja"},
    ),
    (
        "¿Cuál es el horario de atención de la Dirección de Tránsito de la municipalidad para renovar permiso de circulación?",
        {"categoria": "consulta_horario", "prioridad": "baja"},
    ),
    (
        "Quiero saber cómo se solicita el cambio de domicilio en el Registro Social de Hogares y cuánto demora el trámite.",
        {"categoria": "consulta_tramite", "prioridad": "media"},
    ),
    (
        "Necesito consultar el trámite para inscribirme en un CESFAM de la comuna después de cambiarme de domicilio.",
        {"categoria": "consulta_tramite", "prioridad": "baja"},
    ),
    (
        "¿Qué documentación debo llevar a ChileAtiende para postular al Bono Bodas de Oro?",
        {"categoria": "consulta_documentacion", "prioridad": "baja"},
    ),
    (
        "¿Qué documentos piden en la municipalidad para obtener una patente comercial?",
        {"categoria": "consulta_documentacion", "prioridad": "baja"},
    ),
    (
        "Me cobraron dos veces la membresía de este mes de la API y necesito el reembolso de uno de los cargos.",
        {"categoria": "facturacion", "prioridad": "alta"},
    ),
    (
        "Quisiera actualizar mis datos de facturación para la renovación automática de mi membresía de la aplicación.",
        {"categoria": "facturacion", "prioridad": "media"},
    ),
    (
        "Me gustaría que se incluyeran nuevos servicios públicos dentro de la aplicación.",
        {"categoria": "servicio_sin_informacion", "prioridad": "baja"},
    ),
    (
        "Al consultar los puntos de atención de ChileAtiende en Santiago, la respuesta viene vacía y no muestra información de servicio.",
        {"categoria": "servicio_sin_informacion", "prioridad": "alta"},
    ),
    (
        "No puedo iniciar sesión en el portal de la API porque dice que mi contraseña es incorrecta aunque ya la restablecí.",
        {"categoria": "falla_credencial", "prioridad": "alta"},
    ),
    (
        "No me llega el correo de recuperación para cambiar la contraseña de acceso a mi cuenta de la aplicación y no recuerdo cuál registré.",
        {"categoria": "falla_credencial", "prioridad": "media"},
    ),
]


def chequear_balance(ejemplos_raw: list[tuple[str, dict]], clave: str) -> Counter:
    categorias = Counter(salida[clave] for _, salida in ejemplos_raw)
    return categorias


def validar_dataset(
    examples: list[types.TuningExample], claves_esperadas: tuple[str, ...]
) -> list[str]:
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
    return problemas


if __name__ == "__main__":

    balance = chequear_balance(ejemplos_raw, "categoria")
    for categoria, cuenta in balance.most_common():
        print(f"{categoria}: {cuenta}")

    examples = [
        types.TuningExample(
            text_input=texto, output=json.dumps(salida, ensure_ascii=False)
        )
        for texto, salida in ejemplos_raw
    ]

    print(len(examples), "ejemplos construidos")
    print(examples[0])

    problemas = validar_dataset(examples, claves_esperadas=("categoria", "prioridad"))
    print(f"{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)
