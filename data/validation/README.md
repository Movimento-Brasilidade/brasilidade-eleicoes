# Validação de fontes

Consulta realizada em 19/10/2026.

## TRE-RJ: fonte territorial complementar

Contrato: https://apps.tre-rj.jus.br/api-dados-abertos/v2/api-docs

Endpoints públicos consultados, sem envio da chave do Eleições.dev:

- GET https://apps.tre-rj.jus.br/api-dados-abertos/locaisvotacao — 4.989 registros, 92 nomes distintos de municípios.
- GET https://apps.tre-rj.jus.br/api-dados-abertos/zonas — 165 registros.

Respostas salvas em `tre-rj-locaisvotacao.json` e `tre-rj-zonas.json`; contrato em `tre-rj-openapi.json`. Atualização: executar `scripts/fetch-tre-rj.ps1` na raiz do projeto.

O contrato também oferece filtros de locais por município, bairro e zona. Não documenta resultados, votos, candidatos, ano ou turno. Portanto, esta fonte não substitui os resultados do Eleições.dev ou os arquivos oficiais do TSE.

Limitações observadas:

- Todos os 4.989 locais retornaram `numZona: 0`; não usar esse campo para relacionar locais e zonas sem validação adicional.
- Os locais contêm nomes de municípios, endereços e seções, mas não códigos municipais IBGE/TSE nem latitude/longitude.
- Não há indicação de ciclo eleitoral na resposta. Não classificar automaticamente estes locais como a base histórica de 2026.
- 92 nomes distintos não comprovam, sozinhos, a correspondência com as 92 geometrias do IBGE.

## Eleições.dev

`elections.json` registra o catálogo. Primeiro turno de 2026: códigos TSE 6257 (federal) e 6259 (estadual), data 04/10/2026.

As consultas de resultados municipais do RJ com `round=1` retornaram HTTP 500 para presidente, governador, senador, deputado federal e deputado estadual. O total estadual para governador também falhou. O contrato `openapi.json` não oferece filtro por ano/eleição em `/results`; a identidade do ciclo exige validação antes do uso.

## Arquivos TSE fornecidos pelo usuário

Os cinco ZIPs adicionados contêm dados de 2026. A leitura integral dos CSVs por município/zona selecionou os arquivos `_RJ.csv` e `_BR.csv`, filtrando `SG_UF=RJ`; não somou o consolidado `_BRASIL.csv`, evitando duplicação. Presidente está no arquivo `_BR.csv`.

O inventário `tse-rj-inventory.json`, reproduzível com `python scripts/inspect-tse.py`, confirmou primeiro turno, códigos eleitorais 6257/6259 e 92 municípios/165 zonas para cada um dos cinco cargos. Os totais estaduais de votos nominais válidos coincidem entre as bases de candidatos, partidos e detalhamento:

| Cargo | Votos nominais válidos |
| --- | ---: |
| Presidente | 9.369.700 |
| Governador | 8.394.627 |
| Senador | 15.923.657 |
| Deputado federal | 8.467.054 |
| Deputado estadual | 7.943.403 |

Para deputados, os votos válidos totais incluem também legenda: 276.699 para federal e 536.018 para estadual. Não confundir votos nominais brutos com nominais válidos.

As bases município/zona têm geração em 18/10 (detalhe) e 19/10 (candidatos/partidos). Os cabeçalhos/amostras das bases por seção têm geração em 05/10 e 06/10; sua conferência integral ainda não foi feita. O CSV de votação por seção do RJ tem cerca de 2,08 GB descompactado e permanece dentro do ZIP.

Temos agora fonte local de votos para o experimento, independente da disponibilidade do Eleições.dev. A concordância estadual não comprova concordância de todas as linhas nem validação externa dos downloads.

## Conferência municipal e correspondência IBGE

Executado `python scripts/validate-municipalities.py` sobre os arquivos fornecidos:

- 460 combinações município/cargo (92 municípios × 5 cargos), todas aprovadas.
- Em cada combinação, votos nominais válidos coincidem entre candidatos, partidos e detalhe.
- Votos válidos de legenda coincidem entre partidos e detalhe.
- Nominais válidos de candidatos + legenda válida de partidos coincidem com o total válido do detalhe.
- 92 correspondências TSE/IBGE únicas, sem municípios ausentes ou códigos IBGE duplicados.

Artefatos:

- `municipality-crosswalk.csv`: códigos TSE e IBGE preservados como texto, nomes de ambas as fontes e método de correspondência.
- `municipality-vote-checks.csv`: valores comparados e resultado para cada município/cargo.
- `municipality-validation.json`: resumo, divergências e identificação dos membros dos ZIPs por nome, tamanho e CRC32.

A correspondência foi inferida por nomes normalizados (acentos, pontuação e caixa) dentro do RJ e verificada como um-para-um; não é uma tabela oficial de correspondência TSE/IBGE. A malha é de 2025 e a evolução histórica dos limites não foi auditada. Esta etapa valida totais municipais, não cada candidato ou seção individualmente. A definição dos denominadores dos percentuais para o mapa continua pendente.
