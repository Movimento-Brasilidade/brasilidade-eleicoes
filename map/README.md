# Mapa local de votos

Abrir `index.html` diretamente no navegador ou executar, na raiz:

```powershell
python -m http.server 4188 --bind 127.0.0.1 --directory map
```

O servidor expõe apenas a pasta `map`, sem as chaves locais. Não há chamadas externas na visualização.

## Reconstruir

Dependências de geometria: `python -m pip install --target .local-python pyshp==3.1.6 shapely==2.2.0`.

```powershell
python scripts/prepare-zones.py
python scripts/build-map.py
```

O mapa municipal e os arquivos processados do candidato precisam já existir. O template editável é `template.html`; `index.html` é gerado. Os ZIPs de zonas ficam em `data/raw/tre-rj`.

## Cobertura das zonas

- 165 zonas com votos e geometria; 49 na capital e 116 no interior.
- 165 conferências de votos nominais, legenda e total válido aprovadas.
- Soma do candidato: 23.105 votos no estado, sendo 13.195 nas zonas da capital.
- Nenhuma zona ausente, extra ou ambígua no cruzamento por UF/número.
- Interior: 143 registros geométricos reunidos por `rotulo`; capital: 49 registros identificados por `Name`.
- Zonas que abrangem mais de um município têm votos e denominadores somados antes do cálculo. Exemplo: zona 255, Carapebus e Quissamã, 44 votos / 23.318 válidos.

Fonte das malhas: https://www.tre-rj.jus.br/transparencia-e-prestacao-de-contas/tecnologia-da-informacao-e-comunicacao/mapas-de-delimitacao-das-zonas-eleitorais

Os ZIPs oficiais têm datas internas de maio de 2018. A correspondência dos números não confirma a vigência dos limites em 2026. Uso exploratório com ressalva na interface; não interpretar como geografia comprovadamente vigente em 2026 nem como residência dos eleitores.

Capital: SIRGAS 2000 geográfico; interior: WGS84 geográfico. Coordenadas angulares usadas na projeção esférica Mercator para visualização, sem transformação geodésica de precisão; não adequado a medição cadastral. Limites simplificados em 0,00015 grau preservando topologia de cada geometria. A simplificação independente não constitui auditoria topológica entre zonas adjacentes.

Relatório detalhado, hashes e comparação numérica: `data/validation/zone-validation.json`. Dados e CSV estaduais: `data/processed/leo-lupi-2026-rj-zones.*`.

## Verificação da interface

Testados no navegador: abertura nas 49 zonas da capital; estado com 165 zonas; zona 255 com dois municípios; retorno ao mapa municipal com 13.195 votos na cidade do Rio; zoom, arraste e reenquadramento. Tela estreita sem overflow horizontal. Uma página temporária simulou a zona 4 sem geometria: aviso exibido, cobertura reduzida para 48/49 e os 294 votos preservados na seleção. A página de teste foi removida.
