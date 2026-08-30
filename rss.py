import json
import urllib.request
import xml.etree.ElementTree as ET

from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin

WEB_URL = "https://www.acciona-energia.com/es/actualidad/noticias"

API_URL = (
    "https://www.acciona-energia.com/content/energiacom/es/"
    "actualidad/noticias/jcr:content.filter.json"
    "?filter=news&page=1&pageSize=50"
)

OUTPUT_FILE = Path("acciona-energia.xml")


def descargar_noticias():
    request = urllib.request.Request(
        API_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            ),
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        datos = json.loads(response.read().decode("utf-8"))

    return datos.get("data", [])


def crear_rss(noticias):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Noticias de ACCIONA Energía"
    ET.SubElement(channel, "link").text = WEB_URL
    ET.SubElement(channel, "description").text = (
        "Últimas noticias publicadas por ACCIONA Energía"
    )
    ET.SubElement(channel, "language").text = "es"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    atom_link = ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
    )
    atom_link.set("href", WEB_URL)
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")

    for noticia in noticias:
        titulo = noticia.get("title", "").strip()
        enlace = urljoin(WEB_URL, noticia.get("url", ""))
        descripcion = noticia.get("description", "").strip()
        fecha = noticia.get("date", "").strip()

        if not titulo or not enlace:
            continue

        item = ET.SubElement(channel, "item")

        ET.SubElement(item, "title").text = titulo
        ET.SubElement(item, "link").text = enlace
        ET.SubElement(item, "description").text = descripcion

        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "true")
        guid.text = enlace

        if fecha:
            try:
                fecha_publicacion = datetime.strptime(
                    fecha, "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)

                ET.SubElement(item, "pubDate").text = format_datetime(
                    fecha_publicacion
                )
            except ValueError:
                pass

    ET.indent(rss, space="  ")

    arbol = ET.ElementTree(rss)
    arbol.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    noticias = descargar_noticias()

    if not noticias:
        raise RuntimeError("No se encontraron noticias de ACCIONA Energía")

    crear_rss(noticias)

    print(f"RSS creada correctamente con {len(noticias)} noticias")


if __name__ == "__main__":
    main()
