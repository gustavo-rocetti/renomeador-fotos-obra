import os
from datetime import datetime
from pathlib import Path

import pytest

from renomear import achar_codigo, ler_escopo, organizar, slug


def criar_foto(caminho: Path, quando: datetime) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(b"fake image")
    ts = quando.timestamp()
    os.utime(caminho, (ts, ts))
    return caminho


@pytest.fixture
def escopo():
    return {"3.2": "Alvenaria", "3.2.1": "Alvenaria bloco cerâmico", "4.1": "Instalações elétricas"}


def test_slug_remove_acentos_e_simbolos():
    assert slug("Instalações Elétricas / Quadro") == "instalacoes-eletricas-quadro"
    assert slug("") == "sem-descricao"


def test_ler_escopo_aceita_ponto_e_virgula(tmp_path):
    arq = tmp_path / "escopo.csv"
    arq.write_text("codigo;descricao\n1.1;Fundação\n1.2;Estrutura\n", encoding="utf-8")
    assert ler_escopo(arq) == {"1.1": "Fundação", "1.2": "Estrutura"}


def test_ler_escopo_vazio_da_erro(tmp_path):
    arq = tmp_path / "escopo.csv"
    arq.write_text("codigo,descricao\n", encoding="utf-8")
    with pytest.raises(ValueError):
        ler_escopo(arq)


def test_codigo_pela_pasta(tmp_path, escopo):
    foto = tmp_path / "4.1" / "IMG_001.jpg"
    assert achar_codigo(foto, tmp_path, escopo) == "4.1"


def test_codigo_pelo_nome_prefere_o_mais_longo(tmp_path, escopo):
    assert achar_codigo(tmp_path / "3.2.1 parede.jpg", tmp_path, escopo) == "3.2.1"
    assert achar_codigo(tmp_path / "3.2 parede.jpg", tmp_path, escopo) == "3.2"


def test_codigo_nao_casa_numero_parecido(tmp_path, escopo):
    assert achar_codigo(tmp_path / "3.25 parede.jpg", tmp_path, escopo) is None


def test_organizar_renomeia_numera_e_separa_sem_escopo(tmp_path, escopo):
    entrada, saida = tmp_path / "entrada", tmp_path / "saida"
    dia = datetime(2026, 3, 10, 9, 0)
    criar_foto(entrada / "4.1" / "a.jpg", dia)
    criar_foto(entrada / "4.1" / "b.JPG", dia.replace(hour=10))
    criar_foto(entrada / "sem_codigo.jpg", dia)

    resultados = organizar(escopo, entrada, saida)

    nomes = sorted(r.destino.name for r in resultados if r.status == "ok")
    assert nomes == [
        "4.1_instalacoes-eletricas_2026-03-10_01.jpg",
        "4.1_instalacoes-eletricas_2026-03-10_02.jpg",
    ]
    assert (saida / "4.1 - instalacoes-eletricas" / nomes[0]).exists()
    assert (saida / "_sem_escopo" / "sem_codigo.jpg").exists()
    assert (entrada / "4.1" / "a.jpg").exists(), "o original não pode ser apagado"


def test_dry_run_nao_grava_nada(tmp_path, escopo):
    entrada, saida = tmp_path / "entrada", tmp_path / "saida"
    criar_foto(entrada / "4.1" / "a.jpg", datetime(2026, 3, 10))
    organizar(escopo, entrada, saida, dry_run=True)
    assert not saida.exists()
