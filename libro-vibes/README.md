# 📚 Libro Vibes

Recomendador de libros basado en contenido. Escribes un libro que te gustó y el sistema
encuentra otros parecidos comparando título, autor, géneros y descripción con **TF-IDF**
y **similitud coseno**, sobre un dataset de Goodreads.

## Estructura

```
libro-vibes/
├── backend/                 # API REST (Flask) + modelo de ML
│   ├── app/
│   │   ├── __init__.py      # Application factory (create_app)
│   │   ├── config.py        # Configuración desde variables de entorno
│   │   ├── preprocessing.py # Limpieza del dataset
│   │   ├── recommender.py   # Modelo: entrenar, guardar, cargar, recomendar
│   │   └── routes.py        # Endpoints /api/*
│   ├── scripts/
│   │   └── build_model.py   # Entrena y guarda el modelo
│   ├── model/               # Modelo entrenado para Vercel (se sube a git)
│   ├── tests/               # Tests con pytest
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── index.py             # Punto de entrada para Vercel
│   └── run.py               # Arranque en desarrollo
├── frontend/                # HTML + CSS + JS sin frameworks
│   ├── index.html
│   ├── css/styles.css
│   └── js/ (config.js, api.js, app.js)
├── data/
│   ├── raw/                 # Dataset original (goodreads_data.xlsx)
│   └── processed/           # Modelo entrenado (ignorado por git)
├── notebooks/               # Exploración
├── .github/workflows/       # CI (tests) y despliegue del frontend
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── .env.example
```

## Puesta en marcha local

Requisitos: Python 3.10 o superior.

```bash
# 1. Entorno virtual (desde la raíz del proyecto)
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

# 2. Dependencias
pip install -r backend/requirements-dev.txt

# 3. Variables de entorno
cp .env.example .env          # en Windows: copy .env.example .env

# 4. Dataset: copia tu archivo a data/raw/goodreads_data.xlsx

# 5. Entrenar el modelo (opcional: si no existe, se entrena al arrancar)
cd backend
python -m scripts.build_model

# 6. Arrancar
python run.py
```

Abre <http://localhost:5000>. Flask sirve la API y también el frontend.

En VS Code también puedes usar **Run and Debug → "Backend: Flask"**.

### Tests

```bash
cd backend
pytest -q
ruff check .
```

## API

| Método | Ruta                     | Descripción                                 |
|--------|--------------------------|---------------------------------------------|
| GET    | `/api/health`            | Estado del servicio y número de libros      |
| GET    | `/api/books/search?q=..` | Autocompletado de títulos                   |
| POST   | `/api/recommend`         | Recomendaciones para un libro               |

Ejemplo:

```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"libro": "The Hobbit", "n": 5}'
```

Si el libro no existe responde `404` con sugerencias de títulos parecidos
(útil cuando hay errores de escritura).

## Despliegue

**Opción A: todo junto en Render (la más simple).** Sube el repo a GitHub, entra a
[Render](https://render.com) → *New → Blueprint* y elige el repo. `render.yaml` ya define
cómo instalar, entrenar el modelo y arrancar con gunicorn. La app queda en una sola URL.

**Opción B: frontend en GitHub Pages + backend en Render.**
1. Despliega el backend como en la opción A.
2. En `frontend/js/config.js` pon `API_BASE_URL` con la URL de Render.
3. En Render, cambia `CORS_ORIGINS` a `https://TU_USUARIO.github.io`.
4. En GitHub: *Settings → Pages → Source: GitHub Actions*. El workflow `pages.yml`
   publica la carpeta `frontend/` en cada push.

**Opción C: Docker.**

```bash
docker compose up --build
```

### Despliegue en Vercel

Se usan **dos proyectos de Vercel** sobre el mismo repo: uno para el backend y otro para
el frontend. Vercel solo sube la carpeta del *Root Directory*, así que el backend no ve
`data/`, y además su sistema de archivos es de solo lectura: el modelo debe ir ya
entrenado dentro de `backend/model/`.

1. **Entrenar el modelo** dentro del backend:

   ```bash
   cd backend
   python -m scripts.build_model --output model/recommender.joblib
   ```

2. **Subir el modelo a GitHub** (`backend/model/recommender.joblib` no está en `.gitignore`):

   ```bash
   git add backend/model/recommender.joblib
   git commit -m "Agrega modelo entrenado para Vercel"
   git push
   ```

3. **Proyecto backend** en Vercel (*Add New → Project*, elige el repo):
   - *Root Directory*: `libro-vibes/backend`
   - *Framework Preset*: **Flask** (detecta `app` en `index.py`)
   - Variables de entorno:
     - `SERVE_FRONTEND=false`
     - `CORS_ORIGINS=<url del frontend>`, p. ej. `https://libro-vibes.vercel.app`

4. **Verificar** que responde abriendo `https://<url-del-backend>/api/health`.

5. **Proyecto frontend** en Vercel (otro proyecto sobre el mismo repo):
   - *Root Directory*: `libro-vibes/frontend`
   - *Framework Preset*: **Other**, sin *Build Command* ni *Output Directory*.
   - Antes de desplegar, cambia `API_BASE_URL` en `frontend/js/config.js` por la URL
     del backend.

Si el frontend se despliega después de configurar `CORS_ORIGINS` con una URL provisional,
actualiza esa variable en el proyecto backend y vuelve a desplegarlo.

## Cómo funciona el modelo

1. **Limpieza**: se descartan filas sin título, se quitan duplicados (mismo título y
   autor) y se normalizan los géneros, que pueden venir como `"['Fantasy', 'Classics']"`
   o `"Fantasy, Classics"`.
2. **Texto por libro**: título + autor + géneros (con doble peso) + descripción.
3. **TF-IDF** con unigramas y bigramas, `sublinear_tf` y sin *stop words* en inglés.
4. **Similitud**: al pedir una recomendación se calcula la similitud del libro contra
   todos los demás (una sola fila), en lugar de guardar la matriz completa N×N en memoria.
5. **Búsqueda tolerante**: ignora mayúsculas, tildes y signos; acepta títulos parciales
   y, si no encuentra nada, sugiere títulos parecidos.

## Seguridad

- Nunca subas `.env` ni claves al repositorio (ya está en `.gitignore`).
- Si alguna vez publicaste un token (por ejemplo de ngrok), revócalo desde el panel
  del servicio y genera uno nuevo.
