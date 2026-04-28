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

_CARAC = {"quarto", "sala", "cozinha", "banheiro", "suite", "suíte",
          "varanda", "garagem", "area comum", "área comum", "area social"}

def _e_caracteristica(ln: str) -> bool:
    lower = ln.lower()
    return any(k in lower for k in _CARAC)

def ler_status(path: Path) -> dict:
    """
    Retorna dict com info completa de cada apto:
      {
        "103": {
          "status":    "livre",
          "valor":     "R$ 950,00",
          "condicoes": ["Agua e luz inclusos", "maximo 4 pessoas"]
        }
      }
    Formato do status.txt:
      103 - livre
            Valor R$ 950,00
            Agua e luz inclusos
      204 - ocupado
    """
    result  = {}
    current = None
    if not path.exists():
        return result
    for ln in path.read_text(encoding="utf-8").splitlines():
        stripped = ln.strip()
        if not stripped:
            continue
        m = re.match(r"(\d+)\s*[-:]\s*(\w+)", stripped)
        if m:
            current = m.group(1)
            result[current] = {"status": m.group(2).lower(), "valor": "",
                               "caracteristicas": [], "condicoes": []}
        elif current:
            vm = re.match(r"valor\s+(.*)", stripped, re.IGNORECASE)
            if vm:
                result[current]["valor"] = vm.group(1).strip()
            elif _e_caracteristica(stripped):
                result[current]["caracteristicas"].append(stripped)
            else:
                result[current]["condicoes"].append(stripped)
    return result

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

        # midia do proprio edificio (arquivos na raiz, nao em subpastas)
        edif_midia = []
        dest_edif = media_dir / slug_edif / "_capa"
        dest_edif.mkdir(parents=True, exist_ok=True)
        for arq in sorted(edif_dir.iterdir()):
            if not arq.is_file():
                continue
            ext = arq.suffix.lower()
            if ext not in (FOTOS | VIDEOS):
                continue
            nome_limpo = slugify(arq.stem) + ext
            shutil.copy2(arq, dest_edif / nome_limpo)
            tipo = "video" if ext in VIDEOS else "foto"
            edif_midia.append({"tipo": tipo, "src": f"{MEDIA}/{slug_edif}/_capa/{nome_limpo}"})

        apartamentos = []
        for apto_dir in sorted(edif_dir.iterdir()):
            if not apto_dir.is_dir():
                continue
            m = re.match(r"apto\s+(\d+)", apto_dir.name, re.IGNORECASE)
            if not m:
                continue
            numero    = m.group(1)
            info          = status_map.get(numero, {"status": "livre", "valor": "",
                                                     "caracteristicas": [], "condicoes": []})
            status        = info["status"]
            valor         = info["valor"]
            caracteristicas = info["caracteristicas"]
            condicoes     = info["condicoes"]

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
                "numero":         numero,
                "status":         status,
                "valor":          valor,
                "caracteristicas": caracteristicas,
                "condicoes":      condicoes,
                "midia":          midia,
            })

        edificios.append({
            "nome":         nome_edif,
            "slug":         slug_edif,
            "midia":        edif_midia,
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
