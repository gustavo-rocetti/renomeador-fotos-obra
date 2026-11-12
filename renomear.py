"""Organiza e renomeia fotos de obra conforme as linhas do escopo.

Cada foto é ligada a uma linha do escopo pelo código da tarefa, que pode vir:
  - do nome da subpasta onde a foto está (ex.: entrada/3.2.1/IMG_001.jpg), ou
  - do começo do nome do arquivo (ex.: entrada/3.2.1 - parede.jpg).

As fotos são copiadas (os originais não são alterados) para:
  saida/<codigo> - <descricao>/<codigo>_<descricao>_<AAAA-MM-DD>_<NN>.jpg

Fotos sem código reconhecido vão para saida/_sem_escopo e aparecem no relatório.

Uso:
  python renomear.py escopo.csv pasta_entrada pasta_saida [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

EXTENSOES = {".jpg", ".jpeg", ".png", ".heic", ".webp"}
SEM_ESCOPO = "_sem_escopo"


@dataclass
class Resultado:
    origem: Path
    destino: Path
    codigo: str
    status: str  # "ok" ou "sem_escopo"


def slug(texto: str, limite: int = 40) -> str:
    """Texto em minúsculas, sem acentos, com hífens. Seguro para nome de arquivo."""
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].rstrip("-") or "sem-descricao"


def ler_escopo(caminho: Path) -> dict[str, str]:
    """Lê o CSV do escopo (colunas: codigo, descricao). Aceita ; ou , como separador."""
    texto = caminho.read_text(encoding="utf-8-sig")
    separador = ";" if texto.count(";") >= texto.count(",") else ","
    escopo: dict[str, str] = {}
    for linha in csv.DictReader(texto.splitlines(), delimiter=separador):
        codigo = (linha.get("codigo") or "").strip()
        if codigo:
            escopo[codigo] = (linha.get("descricao") or "").strip()
    if not escopo:
        raise ValueError(f"Nenhuma linha válida em {caminho} (colunas esperadas: codigo, descricao)")
    return escopo


def achar_codigo(foto: Path, entrada: Path, escopo: dict[str, str]) -> str | None:
    """Procura o código da tarefa nas pastas da foto e depois no nome do arquivo.

    Quando mais de um código combina (ex.: 3.2 e 3.2.1), vence o mais longo.
    """
    for pasta in reversed(foto.relative_to(entrada).parts[:-1]):
        if pasta.strip() in escopo:
            return pasta.strip()
    nome = foto.stem
    candidatos = [c for c in escopo if re.match(re.escape(c) + r"(?![\w.])", nome)]
    return max(candidatos, key=len) if candidatos else None


def data_da_foto(foto: Path) -> datetime:
    """Data em que a foto foi tirada (EXIF), ou a data de modificação do arquivo."""
    try:
        from PIL import Image

        with Image.open(foto) as img:
            valor = img.getexif().get_ifd(0x8769).get(36867) or img.getexif().get(306)
        if valor:
            return datetime.strptime(str(valor), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return datetime.fromtimestamp(foto.stat().st_mtime)


def organizar(escopo: dict[str, str], entrada: Path, saida: Path, dry_run: bool = False) -> list[Resultado]:
    fotos = sorted(
        (p for p in entrada.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSOES),
        key=lambda p: (data_da_foto(p), str(p)),
    )
    contadores: dict[tuple[str, str], int] = {}
    resultados: list[Resultado] = []

    for foto in fotos:
        codigo = achar_codigo(foto, entrada, escopo)
        if codigo is None:
            destino = saida / SEM_ESCOPO / foto.name
            resultados.append(Resultado(foto, destino, "", "sem_escopo"))
        else:
            descricao = slug(escopo[codigo])
            dia = data_da_foto(foto).strftime("%Y-%m-%d")
            chave = (codigo, dia)
            contadores[chave] = contadores.get(chave, 0) + 1
            nome = f"{codigo}_{descricao}_{dia}_{contadores[chave]:02d}{foto.suffix.lower()}"
            destino = saida / f"{codigo} - {descricao}" / nome
            resultados.append(Resultado(foto, destino, codigo, "ok"))

        if not dry_run:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(foto, destino)

    return resultados


def gravar_relatorio(resultados: list[Resultado], caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["status", "codigo", "origem", "destino"])
        for r in resultados:
            w.writerow([r.status, r.codigo, r.origem, r.destino])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Organiza e renomeia fotos de obra pelo escopo.")
    ap.add_argument("escopo", type=Path, help="CSV com as colunas codigo e descricao")
    ap.add_argument("entrada", type=Path, help="pasta com as fotos")
    ap.add_argument("saida", type=Path, help="pasta onde as fotos organizadas serão gravadas")
    ap.add_argument("--dry-run", action="store_true", help="só mostra o que seria feito")
    args = ap.parse_args(argv)

    escopo = ler_escopo(args.escopo)
    resultados = organizar(escopo, args.entrada, args.saida, args.dry_run)

    ok = sum(r.status == "ok" for r in resultados)
    sem = len(resultados) - ok
    if not args.dry_run:
        gravar_relatorio(resultados, args.saida / "relatorio.csv")
    for r in resultados:
        print(f"[{r.status}] {r.origem} -> {r.destino}")
    print(f"\n{ok} fotos organizadas, {sem} sem escopo" + (" (simulação)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
