# Deduplicación de los CSV del SRI

!!! info "Registro histórico"
    Documenta una limpieza puntual del **7 de junio de 2026**. Se conserva
    porque explica por qué `data/clean/` existe y por qué los CSV van por Git
    LFS, pero describe acciones ya ejecutadas: no es un procedimiento a repetir.
    El estado actual de los datos está en [datos](datos.md).

## 1. Detección y eliminación de duplicados

`scripts/reporting/audits/quality.py` identificó duplicados de fila exacta en
todos los CSV anuales. Se eliminaron **≈ 1,26 millones** de filas con
`pandas.DataFrame.drop_duplicates()`. Cada archivo original se respaldó como
`<nombre>.bak` antes de sobrescribirse.

## 2. Reorganización del directorio de datos

Los CSV deduplicados se movieron a `data/clean/`. Los originales y sus `.bak`
quedaron fuera del repositorio.

Hoy `data/raw/` **ya no existe** en el clon: lo único que se esperaría ahí es el
diccionario Excel `SRI_Vehiculos_DD.xlsx`, que está en `.gitignore` y hay que
conseguir aparte (ver [reportes](reportes.md)).

## 3. Configuración

`config/config.yaml` pasó a apuntar al patrón limpio, que es lo que leen todas
las etapas de perfilado y reportes:

```yaml
data:
  files_pattern: "data/clean/SRI_Vehiculos_Nuevos_*.csv"
```

## 4. Git LFS

Los CSV superan el límite de 100 MB por archivo de GitHub, así que se rastrean
como punteros LFS. `.gitattributes` **actual**:

```text
data/clean/*.csv filter=lfs diff=lfs merge=lfs -text
```

La entrada `data/raw/*.csv` que existió en su momento se eliminó: ese directorio
ya no está. El detalle de por qué existe el hook que impide commitear los CSV
como blobs está en [Git LFS](git_lfs.md).

## 5. Regeneración de figuras

Tras el cambio de rutas se re-ejecutaron todas las etapas de visualización, de
modo que las figuras de `reports/figures/` reflejan matriculaciones únicas y no
las filas duplicadas.
