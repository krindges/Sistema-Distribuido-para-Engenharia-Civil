#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa os resultados da Copa do Mundo FIFA 2026 (Canadá / México / EUA) e gera
arquivos prontos para consumo: JSON, CSV, Markdown e as tabelas de classificação.

Fonte dos dados: projeto open source openfootball/worldcup (domínio público),
arquivo `2026--usa/cup.txt`, hospedado no GitHub (raw.githubusercontent.com).
Esse arquivo é atualizado continuamente ao longo do torneio.

Uso:
    python3 baixar_resultados_copa.py

Não requer chave de API. Só precisa de acesso de saída ao raw.githubusercontent.com.
"""

import csv
import json
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

FONTE_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup/master/"
    "2026--usa/cup.txt"
)

DIR_SAIDA = Path(__file__).resolve().parent

MESES = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}

# --- expressões regulares de parsing do formato openfootball ---------------
RE_GRUPO = re.compile(r"^▪\s+Group\s+([A-L])\s*$")
RE_DATA = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+([A-Z][a-z]+)\s+(\d{1,2})\s*$"
)
# Jogo já disputado:  HH:MM TZ  Casa  X-Y (a-b) Fora  @ Sede
RE_JOGADO = re.compile(
    r"^\s*(\d{1,2}:\d{2})\s+\S+\s+(.+?)\s+(\d+)-(\d+)\s+\((\d+)-(\d+)\)\s+"
    r"(.+?)\s+@\s+(.+?)\s*$"
)
# Jogo agendado (sem placar):  HH:MM TZ  Casa  v  Fora  @ Sede
RE_AGENDADO = re.compile(
    r"^\s*(\d{1,2}:\d{2})\s+\S+\s+(.+?)\s+v\s+(.+?)\s+@\s+(.+?)\s*$"
)


def baixar_texto(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "copa2026/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def parse(texto: str):
    """Retorna a lista de jogos (disputados e agendados) na ordem do arquivo."""
    jogos = []
    grupo = None
    data_iso = None
    ano = 2026
    ultimo_jogo = None

    for linha in texto.splitlines():
        m = RE_GRUPO.match(linha)
        if m:
            grupo = m.group(1)
            ultimo_jogo = None
            continue

        m = RE_DATA.match(linha)
        if m and m.group(1) in MESES:
            data_iso = f"{ano:04d}-{MESES[m.group(1)]:02d}-{int(m.group(2)):02d}"
            ultimo_jogo = None
            continue

        m = RE_JOGADO.match(linha)
        if m and grupo:
            hora, casa, gc, gf, gc1, gf1, fora, sede = m.groups()
            ultimo_jogo = {
                "grupo": grupo,
                "data": data_iso,
                "hora": hora,
                "mandante": casa.strip(),
                "visitante": fora.strip(),
                "gols_mandante": int(gc),
                "gols_visitante": int(gf),
                "placar": f"{gc}-{gf}",
                "intervalo": f"{gc1}-{gf1}",
                "sede": sede.strip(),
                "disputado": True,
                "marcadores": "",
            }
            jogos.append(ultimo_jogo)
            continue

        m = RE_AGENDADO.match(linha)
        if m and grupo:
            hora, casa, fora, sede = m.groups()
            ultimo_jogo = {
                "grupo": grupo,
                "data": data_iso,
                "hora": hora,
                "mandante": casa.strip(),
                "visitante": fora.strip(),
                "gols_mandante": None,
                "gols_visitante": None,
                "placar": None,
                "intervalo": None,
                "sede": sede.strip(),
                "disputado": False,
                "marcadores": "",
            }
            jogos.append(ultimo_jogo)
            continue

        # linha de continuação = marcadores (gols) entre parênteses
        if ultimo_jogo is not None and linha.strip():
            txt = linha.strip().strip("()").strip()
            if txt:
                sep = " " if not ultimo_jogo["marcadores"] else " "
                ultimo_jogo["marcadores"] = (
                    ultimo_jogo["marcadores"] + sep + txt
                ).strip()

    return jogos


def calcular_classificacao(jogos):
    """Calcula a tabela de cada grupo a partir dos jogos já disputados."""
    tabela = defaultdict(lambda: defaultdict(
        lambda: {"P": 0, "J": 0, "V": 0, "E": 0, "D": 0, "GP": 0, "GC": 0}
    ))
    for j in jogos:
        if not j["disputado"]:
            continue
        g = j["grupo"]
        casa, fora = j["mandante"], j["visitante"]
        gc, gf = j["gols_mandante"], j["gols_visitante"]
        for time, marcados, sofridos in ((casa, gc, gf), (fora, gf, gc)):
            t = tabela[g][time]
            t["J"] += 1
            t["GP"] += marcados
            t["GC"] += sofridos
        if gc > gf:
            tabela[g][casa]["V"] += 1
            tabela[g][casa]["P"] += 3
            tabela[g][fora]["D"] += 1
        elif gc < gf:
            tabela[g][fora]["V"] += 1
            tabela[g][fora]["P"] += 3
            tabela[g][casa]["D"] += 1
        else:
            tabela[g][casa]["E"] += 1
            tabela[g][fora]["E"] += 1
            tabela[g][casa]["P"] += 1
            tabela[g][fora]["P"] += 1

    classificacao = {}
    for g, times in tabela.items():
        linhas = []
        for nome, s in times.items():
            s = dict(s)
            s["time"] = nome
            s["SG"] = s["GP"] - s["GC"]
            linhas.append(s)
        # ordena: pontos, saldo, gols pró, nome
        linhas.sort(key=lambda x: (-x["P"], -x["SG"], -x["GP"], x["time"]))
        classificacao[g] = linhas
    return dict(sorted(classificacao.items()))


def gravar_json(jogos, classificacao, gerado_em):
    dados = {
        "torneio": "Copa do Mundo FIFA 2026 (Canadá / México / EUA)",
        "fonte": FONTE_URL,
        "gerado_em": gerado_em,
        "total_jogos": len(jogos),
        "jogos_disputados": sum(1 for j in jogos if j["disputado"]),
        "jogos_agendados": sum(1 for j in jogos if not j["disputado"]),
        "jogos": jogos,
        "classificacao": classificacao,
    }
    (DIR_SAIDA / "resultados.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def gravar_csv(jogos):
    campos = [
        "grupo", "data", "hora", "mandante", "gols_mandante",
        "gols_visitante", "visitante", "placar", "intervalo", "sede",
        "disputado", "marcadores",
    ]
    with (DIR_SAIDA / "resultados.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for j in jogos:
            w.writerow({c: j.get(c) for c in campos})


def gravar_markdown(jogos, classificacao, gerado_em):
    out = []
    out.append("# Resultados — Copa do Mundo FIFA 2026")
    out.append("")
    out.append("Sede: Canadá, México e Estados Unidos · 48 seleções · 12 grupos")
    out.append("")
    out.append(f"- Gerado em: {gerado_em}")
    out.append(f"- Fonte: [openfootball/worldcup]({FONTE_URL})")
    disp = sum(1 for j in jogos if j["disputado"])
    out.append(f"- Jogos disputados: **{disp}** / {len(jogos)}")
    out.append("")

    grupos = sorted({j["grupo"] for j in jogos})
    for g in grupos:
        out.append(f"## Grupo {g}")
        out.append("")
        # tabela de classificação
        out.append("| # | Seleção | P | J | V | E | D | GP | GC | SG |")
        out.append("|---|---------|---|---|---|---|---|----|----|----|")
        for i, s in enumerate(classificacao.get(g, []), 1):
            out.append(
                f"| {i} | {s['time']} | {s['P']} | {s['J']} | {s['V']} | "
                f"{s['E']} | {s['D']} | {s['GP']} | {s['GC']} | {s['SG']:+d} |"
            )
        out.append("")
        out.append("**Jogos:**")
        out.append("")
        for j in jogos:
            if j["grupo"] != g:
                continue
            data = j["data"] or "?"
            if j["disputado"]:
                out.append(
                    f"- {data} — {j['mandante']} **{j['placar']}** "
                    f"{j['visitante']}  ({j['sede']})"
                )
            else:
                out.append(
                    f"- {data} — {j['mandante']} vs {j['visitante']} "
                    f"— _a disputar_  ({j['sede']})"
                )
        out.append("")
    (DIR_SAIDA / "resultados.md").write_text("\n".join(out), encoding="utf-8")


def main():
    print(f"Baixando resultados de:\n  {FONTE_URL}")
    try:
        texto = baixar_texto(FONTE_URL)
    except Exception as e:
        print(f"ERRO ao baixar: {e}", file=sys.stderr)
        return 1

    # guarda a fonte bruta exatamente como baixada
    (DIR_SAIDA / "cup_2026.txt").write_text(texto, encoding="utf-8")

    jogos = parse(texto)
    classificacao = calcular_classificacao(jogos)
    gerado_em = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    gravar_json(jogos, classificacao, gerado_em)
    gravar_csv(jogos)
    gravar_markdown(jogos, classificacao, gerado_em)

    disp = sum(1 for j in jogos if j["disputado"])
    print(f"OK — {len(jogos)} jogos ({disp} disputados) em {len(classificacao)} grupos.")
    print("Arquivos gerados:")
    for nome in ("cup_2026.txt", "resultados.json", "resultados.csv", "resultados.md"):
        print(f"  - {DIR_SAIDA / nome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
