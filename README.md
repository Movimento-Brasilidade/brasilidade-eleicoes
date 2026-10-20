# brasilidade-eleicoes

## Mapa e GitHub Pages

A publicação usa os arquivos da raiz: `index.html`, os dois CSVs de votos e `capital-neighborhood-crosswalk.csv` / `.json`. Os links são relativos e não dependem de API. O gerador `scripts/build-map.py` mantém a raiz e `map/` sincronizados.

## De-para da capital

167 bairros, 49 zonas e 470 relações com área positiva; 14 relações integrais (cobertura >=99,9%) e 41 residuais (<0,1%). Residuais ficam identificadas para revisão. Cruzamento nos polígonos originais em EPSG:31983; simplificação somente para exibição. Contato apenas na borda não conta.

Todos os bairros têm alguma cobertura, mas há lacunas entre as malhas. A malha eleitoral tem datas internas de 2018 e vigência em 2026 não confirmada. Percentuais são de área, nunca de votos ou de residência dos eleitores.

## Atualização local

Com as bases e dependências pyshp, shapely e pyproj disponíveis:

```powershell
python scripts/fetch-neighborhoods.py
python scripts/prepare-neighborhoods.py
python scripts/build-map.py
python scripts/check-neighborhoods.py
```

O download só é necessário para atualizar a fonte. Relatório: `data/validation/neighborhood-validation.json`. ZIPs e bases brutas não são necessários na hospedagem.

## Comparação de candidatos

Em **Análise → Comparar candidatos**, compare Léo Lupi (2026) e Pedro Porto (2024) nas 49 zonas da capital. A medida padrão compara a participação de cada zona no total do próprio candidato na capital. A alternativa mostra diferença absoluta de votos. Azul indica Léo; laranja indica Pedro. O cruzamento entre anos é exploratório, sem confirmação de continuidade dos limites territoriais.

Preparação: `python scripts/prepare-comparison.py`, seguida de `python scripts/build-map.py`. Verificação: `python scripts/check-comparison.py`. Os ZIPs oficiais de 2024 devem estar em `data/raw/tse-2024/`. A navegação usa apenas dados incorporados ao HTML; os arquivos `capital-comparison.csv` e `.json` acompanham a publicação. Fontes e limitações: `data/validation/capital-comparison.md`.

## Seleção individual

O seletor **Candidato** permite abrir Léo Lupi ou Pedro Porto sem comparação. Pedro fica nas 49 zonas da capital, com percentual dos votos válidos para vereador (incluindo legenda) ou votos absolutos. A comparação permanece opcional e restaura a visualização individual ao sair.

Preparação adicional: `python scripts/prepare-pedro.py`; validação: `python scripts/check-individual.py`. Requer `detalhe_votacao_munzona_2024.zip` e `votacao_partido_munzona_2024.zip` em `data/raw/tse-2024/`. Conferência: 3.016.873 votos válidos do cargo na capital, com nominais e legenda reconciliados por zona entre as duas fontes oficiais; Pedro totaliza 4.220 votos. O CSV individual acompanha os arquivos estáticos. Sem novo push nesta etapa.
