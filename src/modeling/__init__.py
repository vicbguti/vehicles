"""Modelado supervisado del asignador vehículo-camión.

Núcleo compartido por los cuatro modelos (MLP, XGBoost, LightGBM y transformer).
Ninguno de ellos reimplementa la canonicalización, los tensores, el
decodificador, las métricas ni la partición: todo eso vive aquí, que es lo que
hace que sus cifras sean comparables entre sí.

No calcula la etiqueta. Esa es responsabilidad del maestro exacto
(`src/loading/labeler.py`); aquí solo se consumen los dos parquet que
`scripts/build_scenarios.py` produce.

Módulos
-------
canonicalization  Reordena la flota por capacidad y remapea las etiquetas de camión.
dataset           Join episodios ⋈ vehículos y comprobación de fugas entre particiones.
features          Tensores por par (vehículo, camión) + contexto del manifiesto.
protocol          El único sitio donde se construye una partición (holdout temporal).
mlp_classifier    El MLP compartido en Keras 3.
capacity_decoder  Decodificación factible (nunca excede capacidad).
metrics           Métricas de dominio contra el maestro exacto.
"""
