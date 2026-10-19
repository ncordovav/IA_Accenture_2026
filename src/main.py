from consumir_gemini import obtener_dato_de_prueba

pregunta = input("Introduce tu pregunta: ")
try:
    resultado = obtener_dato_de_prueba(pregunta)
    print(resultado)
except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación:", error)

