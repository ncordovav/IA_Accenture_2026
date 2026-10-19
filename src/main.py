from consumir_gemini import obtener_dato_de_prueba

try:
     resultado = obtener_dato_de_prueba(pregunta)
     print(resultado)
 except (ValueError, RuntimeError) as error:
     print("No se pudo completar la operación:", error)

