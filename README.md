# Consumir Gemini API con Python 🚀

Este proyecto es una aplicación en Python diseñada para interactuar con los modelos de Inteligencia Artificial de Google Gemini. La lógica de comunicación con la API está centralizada en `consumir_gemini.py`, la cual es ejecutada y orquestada desde el punto de entrada principal del programa: `main.py`.

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
* **Python 3.10** o superior.
* Una cuenta de Google AI Studio para obtener tu clave de API (API Key).

## 🚀 Instalación y Configuración

Sigue estos pasos para clonar y preparar el entorno de desarrollo:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/ncordovav/IA_Accenture_2026 prueba-gate1

   cd prueba-gate1
   ```

2. **Crear y activar un entorno virtual (Recomendado):**
   ```bash
   # En Windows:
     python -m venv venv
     .\venv\Scripts\Activate.ps1

   # En macOS/Linux:
     python3 -m venv venv
     source venv/bin/activate
   ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Nota: Asegúrate de que tu `requirements.txt` incluya `requests`,`google-genai` y `python-dotenv`).*


4. **Crear el archivo .env a partir del .env.example:**
   crea un archivo llamado `.env` en la raíz del proyecto a partir del archivo `.env.example`.
   ```bash
   # En Windows:
     Copy-Item .env.example .env

   # En macOS/Linux:
     cp .env.example .env
   ```

5. **Configurar las Variables de Entorno:**
   añade tu API Key de Gemini al archivo `.env`: 
   ```env
   GEMINI_API_KEY= tu_llave_aqui
   ```

## 💻 Arquitectura del Proyecto

* **`main.py`**: punto de entrada oficial de la aplicación. Maneja la interfaz de usuario (consola o argumentos), inicializa los flujos y llama a las funciones del módulo de Gemini.
* **`consumir_gemini.py`**: módulo que contiene la lógica de integración, configuración del cliente de Google, manejo de prompts y retorno de respuestas de la API.
* **`.env`**: archivo local oculto para guardar credenciales de forma segura (no se sube al repositorio).

## 🛠️ Uso

Para ejecutar la aplicación, ejecuta el script principal desde la terminal:

```bash
# En Windows:
  python main.py

# En macOS/Linux:
  python3 main.py
```


## Estructura de carpetas

- `src/` : contiene el código fuente del proyecto.
- `docs/` : documentación técnica del proyecto (diagramas, decisiones de arquitectura, notas).
- `tests/` : pruebas de código.
- `prompts/` : banco de prompts y pruebas de consistencia.
- `requirements.txt` : dependencias de Python de tu proyecto, para que cualquier otra persona pueda reconstruir tu entorno con un solo comando.
- `.env.example` : plantilla de las variables de entorno, sin valores reales. 
- `.gitignore` : archivos y carpetas que son ignorados por Git.

## Registro del ensayo de instalación limpia
- **Fecha:** 2026-10-22
- **Encontrado:** faltaba actualizar archivo **README** y mejorar algunos manejos de errores (try/except).
- **Corregido:** se actualizan archivos **README**, **main.py** y **consumir_gemini.py**, tras lo cual se actualiza repositorio.
- **Resultado tras la corrección:** el proyecto corre sin intervención manual.
