# Resultados da Copa do Mundo FIFA 2026

Download e processamento dos resultados da Copa do Mundo de 2026
(Canadá / México / EUA — 48 seleções, 12 grupos).

> Observação: esta pasta é independente do sistema distribuído de cálculo de
> matrizes do restante do repositório. Foi adicionada apenas para atender ao
> pedido de baixar os resultados dos jogos da Copa.

## Arquivos

| Arquivo | Descrição |
|---------|-----------|
| `baixar_resultados_copa.py` | Script que baixa e gera todos os arquivos abaixo |
| `cup_2026.txt` | Dado bruto baixado da fonte (formato openfootball) |
| `resultados.json` | Todos os jogos + tabelas de classificação (estruturado) |
| `resultados.csv` | Todos os jogos em planilha (um jogo por linha) |
| `resultados.md` | Resumo legível: classificação e jogos por grupo |

## Fonte

Os dados vêm do projeto open source **[openfootball/worldcup](https://github.com/openfootball/worldcup)**
(domínio público), arquivo `2026--usa/cup.txt`, que é atualizado ao longo do
torneio. Não é necessária chave de API.

## Como atualizar

```bash
python3 baixar_resultados_copa.py
```

O script baixa a versão mais recente da fonte, recalcula as tabelas de
classificação a partir dos jogos disputados e regrava os quatro arquivos de
saída. Requer apenas acesso de saída a `raw.githubusercontent.com`.

## Situação no momento da geração (24/06/2026)

- **48** de 72 jogos da fase de grupos já disputados (2 rodadas completas);
  a 3ª e última rodada da fase de grupos ocorre entre 24 e 27 de junho.
- Classificação de cada grupo calculada automaticamente
  (vitória = 3 pts, empate = 1, derrota = 0; critérios de desempate: pontos,
  saldo de gols, gols pró).
