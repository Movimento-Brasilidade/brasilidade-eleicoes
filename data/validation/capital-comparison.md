# Comparação territorial: Léo Lupi × Pedro Porto

- Recorte: município do Rio de Janeiro, 1º turno, agregado por zona.
- Léo: eleição 6259 / candidatura 190002541800 / deputado estadual 2026. Capital: 13.195; estado: 23.105 votos válidos.
- Pedro: eleição 619 / candidatura 190002169885 / vereador 2024 / PDT / 12345. Total: 4.220 votos válidos.
- Fonte Pedro: https://dadosabertos.tse.jus.br/dataset/resultados-2024, obtida em 20/10/2026. CSV gerado em 20/10/2026.
- Conferência independente: arquivo oficial `619_RJ_RIO-DE-JANEIRO_2024_T1.pdf`, páginas 99 e 133, total de 4.220 votos para PEDRO ARTHUR MARTINS LANDIM PORTO.
- 49 zonas em cada base; nenhum número ausente ou extra. Identidade administrativa confere por RJ + município 60011 + zona.
- Continuidade territorial NÃO confirmada: o histórico institucional do TRE-RJ e a página de mapas não forneceram evidência suficiente para certificar limites idênticos em 2024/2026. Todas as relações são explicitamente exploratórias; nenhuma equivalência de eleitorado é afirmada. A malha exibida mantém datas internas de 2018.
- Histórico consultado: https://www.tre-rj.jus.br/institucional/memoria/evolucao-das-zonas-eleitorais-resumo
- Distribuição: votos da zona / votos do próprio candidato na capital × 100. Diferença em pontos percentuais: Léo − Pedro. Não usa o total do cargo.
- Absoluto: votos de Léo − votos de Pedro. Cada escala é simétrica, com limite no maior módulo observado. Azul Léo; laranja Pedro; zero neutro; ausência cinza.
- Exemplo zona 4: 294 e 166 votos; diferença +128. Distribuições 2,2281% e 3,9336%; diferença −1,7056 p.p.
- Não há atribuição de votos a bairros, identificação de pessoas ou inferência de transferência de votos.
- CSV/JSON preservam identidades completas, recorte e situação exploratória. Não é preciso consultar API na navegação.

Validação: `python scripts/check-comparison.py`. Navegador: duas medidas, retorno ao modo individual, manutenção de zoom e 3 zonas relacionadas a Copacabana; viewport 390 px sem rolagem horizontal.

Publicação: ajustes anteriores enviados em 43f8b8d. Nova comparação preparada localmente, sem push.

Seleção individual adicionada: Pedro 2024 com 3.016.873 votos válidos para vereador como denominador municipal. Conferência por zona de nominais e legenda entre detalhamento e partidos; 49 zonas, 4.220 votos do candidato. Percentuais por zona usam denominadores locais. Arquivos oficiais obtidos em 20/10/2026. Testes de denominador zero/ausente, CSV, troca de candidato, preservação de bairro/zoom, restauração ao sair da comparação e tela de 390px concluídos. Atualização somente local.
