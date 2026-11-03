import json

revision_manual = [
    {
        "consulta": "¿Por qué se considera que el ornitorrinco es un animal tan extraño?",
        "f1": 0.10526315789473685,
        "correccion factual": "no",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "la respuesta es más detallada que la referencia, ya que nombra las características y las asocia con el tipo de vertebrado. Sin embargo, hay conceptos que no nombra"
        ),
    },
    {
        "consulta": "¿Cuál fue la causa de la guerra de los 80 años entre España y Países Bajos?",
        "f1": 0.33333333333333337,
        "correccion factual": "parcialmente",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "la respuesta contiene sinónimos de la referencia o parafrásis del contexto que no puntúan bien. "
        ),
    },
    {
        "consulta": "¿Cuál es la función de la retina en el ojo humano?",
        "f1": 0.358974358974359,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta contiene sinónimos de la referencia que no puntúan bien. "
        ),
    },
    {
        "consulta": "¿Qué representa un byte?",
        "f1": 0.3888888888888889,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta contiene sinónimos de la referencia que no puntúan bien. "
        ),
    },
    {
        "consulta": "¿Cuál es el país más pequeño del mundo?",
        "f1": 0.4,
        "correccion factual": "parcialmente",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": ("la respuesta no contiene el nombre completo del país."),
    },
    {
        "consulta": "¿Qué es el sistema binario?",
        "f1": 0.6511627906976745,
        "correccion factual": "no",
        "completitud": "parcialmente",
        "contradiccion": "no",
        "nota": (
            "la respuesta es más detallada que la referencia, pero la definición básica es la misma."
        ),
    },
    {
        "consulta": "¿Cómo se llama el triángulo con 2 ángulos iguales?",
        "f1": 0.6666666666666666,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta es un poco más larga que la referencia, pero básicamente idéntica debido a que se indica sólo el nombre de la figura geométrica."
        ),
    },
    {
        "consulta": "¿Para qué se utiliza el test de Turing?",
        "f1": 0.7317073170731708,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta es casi idéntica a la referencia salvo que no comienza con el enunciado de la pregunta. "
        ),
    },
    {
        "consulta": "¿Cuál es el nombre del primer cosmonauta ruso y en qué año realizó su vuelo espacial?",
        "f1": 0.8,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta es corta y básicamente idéntica a la referencia, debido a que contiene un nombre, un apellido y una fecha (año)."
        ),
    },
    {
        "consulta": "Nombra los 5 libros de la Biblia que se encuentran en la Torá",
        "f1": 1.0,
        "correccion factual": "no",
        "completitud": "sí",
        "contradiccion": "no",
        "nota": (
            "la respuesta es idéntica a la referencia porque hay solo una respuesta correcta posible."
        ),
    },
]


with open("revision_manual.json", "w", encoding="utf-8") as archivo:

    json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)
