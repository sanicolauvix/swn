#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — Gera o site Imoveis SWN a partir da pasta de conteudo.

Estrutura esperada em ../swn/:
  <edificio>/
    status.txt          -> "103 - livre", "204 - ocupado", ...
    apto 103/           -> fotos e videos (jpg, png, mp4, etc.)
    apto 204/

Uso:
  python build.py

Saida em docs/ (GitHub Pages source).
"""

import os, re, json, shutil, unicodedata
from pathlib import Path

ORIGEM   = Path("../swn")
DESTINO  = Path("docs")
MEDIA    = "media"

FOTOS  = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEOS = {".mp4", ".webm", ".mov", ".avi"}

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s

def ler_status(path: Path) -> dict:
    status = {}
    if not path.exists():
        return status
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = re.match(r"(\d+)\s*[-:]\s*(\w+)", ln)
        if m:
            status[m.group(1)] = m.group(2).lower()
    return status

def build():
    media_dir = DESTINO / MEDIA
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)

    edificios = []

    for edif_dir in sorted(ORIGEM.iterdir()):
        if not edif_dir.is_dir():
            continue

        nome_edif = edif_dir.name.title()
        slug_edif = slugify(edif_dir.name)
        status_map = ler_status(edif_dir / "status.txt")

        apartamentos = []
        for apto_dir in sorted(edif_dir.iterdir()):
            if not apto_dir.is_dir():
                continue
            m = re.match(r"apto\s+(\d+)", apto_dir.name, re.IGNORECASE)
            if not m:
                continue
            numero = m.group(1)
            status = status_map.get(numero, "livre")

            midia = []
            if status != "ocupado":
                dest_apto = media_dir / slug_edif / f"apto_{numero}"
                dest_apto.mkdir(parents=True, exist_ok=True)

                for arq in sorted(apto_dir.iterdir()):
                    if not arq.is_file():
                        continue
                    ext = arq.suffix.lower()
                    if ext not in (FOTOS | VIDEOS):
                        continue
                    # sanitiza nome: remove acentos e espaços
                    nome_limpo = slugify(arq.stem) + ext
                    dest = dest_apto / nome_limpo
                    shutil.copy2(arq, dest)
                    tipo = "video" if ext in VIDEOS else "foto"
                    src_rel = f"{MEDIA}/{slug_edif}/apto_{numero}/{nome_limpo}"
                    midia.append({"tipo": tipo, "src": src_rel})

            apartamentos.append({
                "numero": numero,
                "status": status,
                "midia":  midia,
            })

        edificios.append({
            "nome":         nome_edif,
            "slug":         slug_edif,
            "apartamentos": apartamentos,
        })

    data = {"edificios": edificios}
    (DESTINO / "data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # resumo
    total = livre = ocup = 0
    for e in edificios:
        for a in e["apartamentos"]:
            total += 1
            if a["status"] == "livre": livre += 1
            else: ocup += 1

    print("OK data.json gerado")
    for e in edificios:
        print(f"  [{e['nome']}]  {len(e['apartamentos'])} apto(s)")
        for a in e["apartamentos"]:
            tag = "livre" if a["status"] == "livre" else "ocupado"
            mids = f"  ({len(a['midia'])} midia)" if a["midia"] else ""
            print(f"    {a['numero']} -- {tag}{mids}")
    print(f"\n  Total: {total}  |  Livres: {livre}  |  Ocupados: {ocup}")
    print(f"\n  Saida: {DESTINO.resolve()}")
    print("  Pronto! Commit e push para publicar.")

if __name__ == "__main__":
    build()
