# Decisión de arquitectura: elección de modelo
  
 ## Modelo elegido
  Gemini 3.1 Flash-Lite para la funcionalidad principal de la miniaplicación.
  
 ## Diagrama de arquitectura
 ![Diagrama de arquitectura de la miniaplicación](.\diagrama_arquitectura.png)

 El flujo completo va desde el ingreso por terminal de la pregunta del usuario hasta la respuesta final, pasando por **'construir_peticion'** (que valida la pregunta bajo ciertos criterios indicados en el diagrama), **'enviar_peticion'** (con la credencial **'GEMINI_API_KEY'** leída desde **'.env'** y el manejo de errores en **'try/except'**) y **'extraer_texto'** (que además calcula el costo total a partir de **'usageMetadata'**). El diagrama completo está en ***'docs/diagrama-arquitectura.png'***.
  
 ## Comparación de candidatos
 | Criterio | Gemini 3.1 Flash-Lite| Gemini 3.5 Flash-Lite|
 |---|---|---|
 |Costo por 1000 tokens de entrada|USD 0,00025|USD 0,0003|
 |Costo por 1000 tokens de salida |USD 0,0015 |USD 0,0025|
 |Latencia promedio (seg)|9,588 |2,115 |
 |Calidad de respuesta|Buena, cumple con lo solicitado.|Muy buena, proporciona mayor nivel de detalle.|
 |Fecha de medición| 2026-10-20| 2026-10-20

 ## Justificación

 **- Alcance y Requerimientos:** La miniaplicación maneja respuestas acotadas y estandarizadas (datos de contacto, horario de atención y listado de trámites), por lo que no requiere capacidades complejas de razonamiento profundo.

 **- Evaluación de Rendimiento (Trade-off):** Si bien Gemini 3.1 Flash-Lite ofrece menor profundidad contextual y una latencia ligeramente superior frente a la versión 3.5, este comportamiento se encuentra dentro de los márgenes tolerados por la aplicación y no afecta la experiencia de usuario.

**- Criterio de Decisión (Factor Económico):** El menor costo por token de salida de Gemini 3.5 Flash-Lite es el argumento principal de la decisión, maximizando la eficiencia de costos operativos sin comprometer el éxito de los entregables iniciales.
  
 ## Alternativa descartada y por qué
 Inicialmente se opta por un modelo más ligero para la fase de prototipado con el fin de optimizar los costos de la API. Aunque el modelo descartado (Gemini 3.5 Flash-Lite) ofrece mayor detalle y menor latencia, su consumo por token no se alinea con las restricciones presupuestarias actuales de la miniaplicación. Queda abierta la posibilidad de migrar a él en etapas posteriores del desarrollo.