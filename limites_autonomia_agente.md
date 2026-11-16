# Limitación autonomía agente: Asistente de Servicios Públicos (`mi_agente.py`)

Este documento describe la arquitectura, componentes, herramientas, controles de seguridad y funciones de un agente conversacional construido con **LangChain** y el modelo **`gemini-3.1-flash-lite`**. Su propósito es asistir a ciudadanos en consultas de trámites públicos, cálculos de pagos y gestión de reembolsos bajo supervisión humana.

## 1. Arquitectura y Dependencias

* **Modelo Base:** `ChatGoogleGenerativeAI` configurado con `gemini-3.1-flash-lite`.

* **Framework de Agentes:** LangChain (`create_tool_calling_agent`, `AgentExecutor`, `RunnableWithMessageHistory`).

* **Validación de Esquemas:** `Pydantic` (`BaseModel`, `Field`) para estructurar y documentar los argumentos de entrada de las herramientas.

* **Persistencia y Concurrencia:** `json` para registros de auditoría (`.jsonl`) y `threading` para gestionar tiempos de espera en aprobaciones humanas.

## 2. Bases de Datos Simuladas (En Memoria)

El script utiliza dos diccionarios globales para simular fuentes de datos externas:

1. **`ESTADOS`**: Almacena el estado actual y el historial cronológico de tramitación de cédulas de identidad y pasaportes indexados por RUN (ej. `"9.874.229-8"`, `"98.765.432-1"`).

2. **`OFICINAS_CHILEATIENDE_RM`**: Contiene información de sucursales (nombre, dirección, horario y servicios disponibles) organizadas por comuna de la Región Metropolitana (`santiago`, `ñuñoa`, `providencia`, `maipú`, `puente alto`).

## 3. Herramientas del Agente (`@tool`)

| Herramienta | Esquema / Parámetros | Nivel de Riesgo | Descripción | 
| ----- | ----- | ----- | ----- | 
| `consultar_estado_cedula_pasaporte` | `run` (str), `incluir_historial` (bool) | **Bajo** (Solo lectura) | Consulta el estado de retiro de documentos y opcionalmente su historial. | 
| `buscar_documentacion` | `comuna` (str) | **Bajo** (Solo lectura) | Entrega ubicación, horario y servicios de oficinas ChileAtiende en la RM. | 
| `calcular_permiso_circulacion` | `patente` (str), `avaluo_fiscal` (float) | **Bajo** (Cálculo) | Estima el costo del permiso multiplicando el avalúo fiscal por $0.045$. | 
| `calcular_reembolso_membresia` | `tipo_membresia` (str), `cantidad_meses` (int) | **Medio** (Cálculo) | Calcula devoluciones según plan (*premium*: \$15.000 CLP; estándar: $10.500 CLP). | 
| `generar_reembolso_membresia` | `numero_cliente` (str), `monto` (float) | **Alto** (Irreversible) | Ejecuta la devolución monetaria tras obtener aprobación humana explícita. | 

## 4. Catálogo y Propósito de Funciones

### A. Herramientas de Negocio

* **`consultar_estado_cedula_pasaporte(run, incluir_historial)`**: Busca un RUN en `ESTADOS`. Si existe, retorna el estado actual y, cuando `incluir_historial=True`, anexa la lista de etapas previas del trámite.

* **`buscar_documentacion(comuna)`**: Limpia y convierte a minúsculas el nombre de la comuna para buscar en `OFICINAS_CHILEATIENDE_RM`. Formatea los datos de la sucursal o lista las comunas disponibles si no encuentra coincidencias.

* **`calcular_permiso_circulacion(patente, avaluo_fiscal)`**: Valida que el avalúo fiscal sea un número positivo y calcula el monto estimado del permiso aplicando una tasa del $4.5\%$.

* **`calcular_reembolso_membresia(tipo_membresia, cantidad_meses)`**: Determina el cobro mensual según el tipo de membresía y lo multiplica por los meses cobrados por error, recordando que la facturación ocurre el día 1° de cada mes.

* **`generar_reembolso_membresia(numero_cliente, monto)`**: Solicita autorización a un operador humano antes de confirmar un reembolso económico y registra el resultado de dicha validación.

### B. Supervisión Humana (*Human-in-the-Loop*)

**`generar_reembolso_membresia(numero_cliente, monto)`**: para evitar ejecuciones irreversibles sin supervisión, el flujo de esta herramienta combina **`esperar_aprobacion()`** y **`registrar_aprobacion()`**. Si el tiempo de espera expira o la respuesta del operador es distinta a `"s"`, la operación se deniega automáticamente por seguridad.

### C. Orquestación, Memoria y Trazabilidad

* **`normalizar_salida_agente(resultado)`**: Estandariza la respuesta del modelo extrayendo únicamente el contenido de texto plano cuando el LLM devuelve estructuras en formato lista o diccionario.

* **`obtener_historial(session_id)`**: Gestiona el diccionario `historiales`, devolviendo la instancia de `InMemoryChatMessageHistory` asociada a una sesión o creando una nueva si no existe.

* **`registrar_traza(session_id, entrada, resultado)`**: Guarda cada interacción completa en el archivo `trazas_agente.jsonl` (formato JSON Lines), incluyendo timestamp UTC, ID de sesión, consulta, herramientas ejecutadas con sus observaciones y respuesta final.

* **`reiniciar_sesion(session_id)`**: Limpia y elimina de forma segura el historial en memoria mediante **`historiales.pop(session_id, None)`**, y **registra automáticamente el evento `"reiniciar_sesion"`** (con timestamp UTC, `session_id` y descripción) en el archivo `trazas_agente.jsonl` para mantener una auditoría completa de las intervenciones.

* **`crear_agente_con_memoria()`**: Configura el *system prompt* (incluyendo la regla obligatoria de mencionar siempre el RUN al informar sobre trámites), vincula las 5 herramientas, crea el `AgentExecutor` y lo envuelve con `RunnableWithMessageHistory`.

* **`imprimir_pasos_intermedios(resultado)`**: Recorre `intermediate_steps` para mostrar en consola qué herramientas invocó el agente, con qué argumentos y qué salida obtuvo.

* **`ejecutar_consulta(agente, pregunta, session_id)`**: Centraliza la invocación del agente para una sesión específica, imprime tanto la consulta como la respuesta, muestra los pasos intermedios y dispara `registrar_traza()`.

## 5. Revisión de trazas

* **Frecuencia:** diaria para validación de correcta ejecución de las interacciones con el agente, en especial de las herramientas de riesgo alto.

* **Qué se busca:** 

1. **Alucinaciones o Desvíos del Prompt del Sistema (System Prompt).**
Si el agente ignora instrucciones críticas de comportamiento (por ejemplo, si olvidó mencionar obligatoriamente el RUN del usuario al entregar el estado de un trámite).

2. **Uso Inadecuado o Redundante de Herramientas (Tool Calls):**
Si el agente está invocando herramientas con argumentos erróneos, vacíos o en un orden incorrecto (por ejemplo, intentando generar un reembolso sin haber ejecutado primero la herramienta de cálculo).

3. **Trazabilidad de Acciones Críticas e Irreversible (Human-in-the-Loop)**
La correcta ejecución y registro de los mecanismos de aprobación humana antes de realizar acciones de alto riesgo (como **`generar_reembolso_membresia(numero_cliente, monto)`**).

4. **Inconsistencia y No Aislamiento del Historial de Sesión:**
Fugas de contexto o mezcla de información entre distintos usuarios o sesiones (session_id).

## 6. Qué hacer ante un comportamiento inesperado

Si el agente presenta desviaciones (como omitir el RUN obligatorio, alucinar datos, entrar en bucles de herramientas o intentar ejecutar reembolsos erróneos), se deben seguir estos pasos en orden:

1. **Contener acciones críticas (Rechazo inmediato):** Si el agente solicita aprobación en consola para **`generar_reembolso_membresia`** con montos o clientes incorrectos, ingresar `n` (o dejar expirar los 300 segundos de **`esperar_aprobacion()`**) para bloquear la ejecución.

2. **Aislar, reiniciar y auditar la sesión afectada:** Invocar la función **`reiniciar_sesion(session_id)`**, la cual purga el contexto contaminado mediante **`historiales.pop(session_id, None)`** y deja constancia automática del evento en `trazas_agente.jsonl`:

```python
# Reinicia la memoria de una sesión específica y registra el evento en trazas_agente.jsonl
reiniciar_sesion("session_001")
```

3. **Auditar las trazas registradas:** Revisar el archivo `trazas_agente.jsonl` filtrando por `session_id` y `timestamp` (tanto las interacciones como los eventos `"reiniciar_sesion"`), además de inspeccionar `registro_aprobaciones`, para verificar qué herramientas (`acciones`), argumentos y observaciones desencadenaron el fallo.

4. **Diagnosticar la causa raíz:**

   * *Error de validación/formato:* Ajustar las descripciones o tipos en los esquemas `Pydantic` (`ArgumentosConsultaCedulaPasaporte`, `ArgumentosBuscarDocumentacion`).

   * *Incumplimiento de reglas (ej. no mencionar el RUN o usar Markdown):* Reforzar las instrucciones del *system prompt* en **`crear_agente_con_memoria()`**.

   * *Fallo en lógica de negocio:* Revisar el manejo de excepciones dentro de la función `@tool` correspondiente.

5. **Validar antes de reanudar:** Ejecutar una consulta controlada tras el reinicio y verificar en `trazas_agente.jsonl` que el comportamiento se haya corregido.

## 7. Flujo de Ejecución (`__main__`)

Al ejecutarse como script principal:

1. Inicializa el agente mediante **`crear_agente_con_memoria()`**.

2. Ejecuta **6 consultas de prueba** distribuidas en distintas sesiones (`session_001` a `session_05`) para validar:
   * Consultas de estado de cédula y pasaporte (`session_001` y `session_002`).
   * Cálculo del permiso de circulación (`session_003`).
   * Flujo multiturno en una misma sesión (`session_004`) para calcular una devolución de membresía y luego solicitar su ejecución con aprobación humana.
   * Búsqueda de sucursales de ChileAtiende (`session_05`).

3. Ejecuta **`reiniciar_sesion("session_001")`** para demostrar la limpieza de memoria y su registro automático en `trazas_agente.jsonl`.