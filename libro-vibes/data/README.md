# Datos

- `raw/`: coloca aquí el dataset original con el nombre `goodreads_data.xlsx`
  (también acepta `.csv`). Columnas necesarias: `Book`, `Author`, `Description`,
  `Genres`, `Avg_Rating`. Opcionales: `Num_Ratings`, `URL`.
- `processed/`: aquí se guarda el modelo entrenado (`recommender.joblib`).
  Se genera automáticamente y **no** se sube a GitHub.

Si el dataset pesa más de 100 MB, GitHub no lo acepta: usa Git LFS o descárgalo en el build.
