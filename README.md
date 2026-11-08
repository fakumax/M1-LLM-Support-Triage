# M1 · LLM Support Triage

Servicio de triage de tickets de soporte con LLMs: recibe una consulta en texto libre y devuelve una respuesta estructurada con el contrato `{answer, confidence, category, actions}`.

> Proyecto integrador del Módulo 1 de AI Engineering (Henry). Caso: **Nubbix**, un SaaS ficticio de gestión para pymes de LATAM cuya mesa de soporte recibe unos 400 tickets por día.

> 🚧 En desarrollo.

## Requisitos

- Python 3.12
- API key de [OpenRouter](https://openrouter.ai) y de Gemini ([Google AI Studio](https://aistudio.google.com)). Las dos tienen un nivel gratuito.

## Instalación

```bash
git clone https://github.com/fakumax/M1-LLM-Support-Triage.git
cd M1-LLM-Support-Triage
python -m venv .venv
```

Activar el entorno virtual:

- Windows: `.venv\Scripts\activate`
- macOS / Linux: `source .venv/bin/activate`

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

Copiar `.env.example` a `.env` y completar las claves:

| Variable | Descripción |
|---|---|
| `OPENROUTER_API_KEY` | API key de OpenRouter |
| `GEMINI_API_KEY` | API key de Gemini (Google AI Studio) |

`.env` está en `.gitignore`: las credenciales nunca se suben al repositorio.
