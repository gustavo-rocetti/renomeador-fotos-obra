# Renomeador de fotos de obra

Organiza e renomeia as fotos de obra conforme as linhas do escopo, sem ninguém abrir pasta por pasta.

Esta é uma versão genérica, sem dados de cliente, de uma automação que criei como Analista de Processos. Lá ela reduziu de **20 h para 2 h por semana** o tempo de organizar os registros fotográficos.

## O problema

A equipe de campo manda dezenas de fotos por dia com nomes como `IMG_4821.jpg`. Para o relatório e a medição, alguém precisa descobrir a qual tarefa do escopo cada foto pertence, renomear e guardar na pasta certa. É lento, repetitivo e fácil de errar.

## Como funciona

1. A foto é ligada a uma linha do escopo pelo **código da tarefa**, que pode vir da subpasta (`3.2.1/IMG_001.jpg`) ou do começo do nome do arquivo (`3.2.1 parede.jpg`).
2. A data vem do **EXIF** da foto (quando foi tirada). Se não houver, usa a data do arquivo.
3. A foto é **copiada** para `saida/<codigo> - <descricao>/` com um nome padrão:
   `3.2.1_alvenaria-bloco-ceramico_2026-03-10_01.jpg`
4. Fotos sem código vão para `saida/_sem_escopo` e são listadas no `relatorio.csv`.

Os originais nunca são alterados.

## Uso

```bash
pip install -r requirements.txt
python renomear.py escopo_exemplo.csv pasta_das_fotos saida --dry-run   # simula
python renomear.py escopo_exemplo.csv pasta_das_fotos saida             # executa
```

O escopo é um CSV com as colunas `codigo` e `descricao` (separador `;` ou `,`). Veja `escopo_exemplo.csv`.

## Testes

```bash
pip install pytest
pytest -q
```

## Stack

Python 3.10+ · Pillow (leitura de EXIF) · pytest
