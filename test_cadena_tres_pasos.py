from unittest.mock import MagicMock
from langchain_core.messages import AIMessage
from cadena_tres_pasos import construir_cadena

def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    modelo_falso.side_effect = [
    AIMessage(content="punto 1\npunto 2\npunto 3"),
    AIMessage(content="texto simplificado"),
    AIMessage(content="- viñeta 1\n- viñeta 2"),
    ]
    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"texto": "texto de prueba"})
    assert modelo_falso.call_count == 3
    assert "viñeta" in resultado