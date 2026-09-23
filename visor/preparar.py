"""Pasa cada STL listado en modelos.json a base64 (.txt) para publicarlo en el visor.

El servidor de artifacts no sirve .stl, así que el visor descarga el .txt y lo
decodifica. Uso: python visor/preparar.py
"""
import base64, json, pathlib

aqui = pathlib.Path(__file__).parent
for m in json.loads((aqui / "modelos.json").read_text()):
    origen = aqui.parent / m["origen"]
    destino = aqui / m["archivo"]
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(base64.b64encode(origen.read_bytes()).decode())
    print(m["id"], "->", destino.relative_to(aqui.parent))
