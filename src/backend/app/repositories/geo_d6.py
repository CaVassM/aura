"""Lectura de D6 (GeoJSON) tal como viene, más la posición normalizada para el mapa."""

import json
from pathlib import Path


def cargar_geo_d6(ruta: Path) -> list[dict]:
    """Features de D6: `service_id`, `geometry` y `properties` originales, y `pos` {x, y}.

    `pos` normaliza las coordenadas al bounding box de los puntos: x crece hacia el este
    y y crece hacia el sur (0 = norte), como en pantalla.
    """
    features = json.loads(ruta.read_text(encoding="utf-8"))["features"]
    lons = [f["geometry"]["coordinates"][0] for f in features]
    lats = [f["geometry"]["coordinates"][1] for f in features]
    ancho = (max(lons) - min(lons)) or 1.0
    alto = (max(lats) - min(lats)) or 1.0
    return [
        {
            "service_id": f["properties"]["service_id"],
            "geometry": f["geometry"],
            "properties": f["properties"],
            "pos": {
                "x": round((lon - min(lons)) / ancho, 4),
                "y": round((max(lats) - lat) / alto, 4),
            },
        }
        for f, lon, lat in zip(features, lons, lats)
    ]
