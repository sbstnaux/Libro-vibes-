"""Punto de entrada para Vercel: expone la variable `app` que detecta el runtime de Python.

No se llama app.py para no chocar con el paquete app/. En local se sigue usando run.py.
"""
from app import create_app

app = create_app()
