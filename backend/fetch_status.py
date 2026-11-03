import json
import urllib.request
import ssl
from datetime import datetime
import pytz

def get_subte_c():
    url = "https://www.metrovias.com.ar/servicios/subte.json"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as res:
            data = json.loads(res.read().decode('utf-8'))
            for linea in data:
                if linea.get("linea") == "C" or "C" in str(linea.get("nombre", "")):
                    return {
                        "estado": linea.get("estado", "Normal"),
                        "mensaje": str(linea.get("mensaje", "")).strip() or "Servicio normal"
                    }
    except Exception:
        pass
    return {"estado": "Normal", "mensaje": "Sin novedades"}

def get_tren_roca_korn():
    url = "https://trenesargentinos.gob.ar/api/estado-lineas"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as res:
            data = json.loads(res.read().decode('utf-8'))
            for linea in data.get("lineas", []):
                if "roca" in str(linea.get("nombre", "")).lower():
                    for ramal in linea.get("ramales", []):
                        if "korn" in str(ramal.get("nombre", "")).lower():
                            return {
                                "estado": ramal.get("estado", "Normal"),
                                "mensaje": str(ramal.get("mensaje", "")).strip() or "A horario"
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
    
