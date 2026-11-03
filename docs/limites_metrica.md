# Límites de la métrica de evaluación


## Qué mide

Coincidencia entre frases revisando palabras y la cantidad de ocurrencias.

Calcula métricas de precisión, cobertura y F1, donde F1 se define como:

$$f1 = 2 * precisión * cobertura / (precisión + cobertura)$$


## Modos de falla conocidos

- Sinónimos y paráfrasis correctas puntúan F1 bajo.
```
F1("el auto es veloz","el vehiculo es rapido") = 0.5
```
- Datos incorrectos (fechas, cifras) pueden puntuar F1 alto si el
  resto de la oración tiene alta coincidencia de palabras.
 ```
 F1("Python fue inventado en 1991","Python fue inventado en 1992") = 0.8
 ``` 
- Negaciones ausentes casi no bajan el valor de F1, aunque
  inviertan el significado de la respuesta esperada.
``` 
F1("Python NO fue inventado en 1992","Python fue inventado en 1992") = 0.8 
```




## Muestra revisada

10 casos: los 5 con menor F1 y los 5 con mayor F1, sobre 20
respuestas generadas el 02-11-2026 con modelo Gemini-3.5-flash-lite.
Se utilizó como parámetro **system instruction** el siguiente: _"Entrega la respuesta más concisa cuando sea posible y, en caso contrario, que la respuesta se entregue en menos de 210 caracteres"_, con objeto de obtener mejores resultados de la medición de las respuestas del modelo respecto a las referencias entregadas.


## Recomendación de uso

Usar F1 para realizar comparación en volumen entre versiones del cliente.

Revisar siempre de formal manual cualquier respuesta que contenga fechas, cifras o nombres propios.