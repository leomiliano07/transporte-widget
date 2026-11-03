import json
import urllib.request
from datetime import datetime
import pytz

def get_subte_c():
    url = "https://www.metrovias.com.ar/servicios/subte.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            for linea in data:
                if linea.get("linea") == "C" or "Línea C" in linea.get("nombre", ""):
                    return {
                        "estado": linea.get("estado", "Normal"),
                        "mensaje": linea.get("mensaje", "").strip() or "Servicio normal"
                    }
    except Exception:
        pass
    return {"estado": "Normal", "mensaje": "Sin novedades"}

def get_tren_roca_korn():
    url = "https://trenesargentinos.gob.ar/api/estado-lineas"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode())
            for linea in data.get("lineas", []):
                if "roca" in linea.get("nombre", "").lower():
                    for ramal in linea.get("ramales", []):
                        if "korn" in ramal.get("nombre", "").lower():
                            return {
                                "estado": ramal.get("estado", "Normal"),
                                "mensaje": ramal.get("mensaje", "").strip() or "A horario"
                            }
    except Exception:
        pass
    return {"estado": "Normal", "mensaje": "A horario"}

def main():
    tz = pytz.timezone('America/Argentina/Buenos_Aires')
    now = datetime.now(tz).strftime("%H:%M")

    payload = {
        "actualizado": now,
        "subte_c": get_subte_c(),
        "tren_roca": get_tren_roca_korn()
    }

    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
