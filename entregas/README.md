# GTA6 Canal Completo — entregas reunidas

Esta pasta reúne os materiais produzidos nas Fases 1, 2 e 3. O código atual do projeto permanece na raiz do repositório, junto de `gta6/`, `tools/`, `tests/`, `config/` e `docs/`.

## Abrir os vídeos

- **Primeiro Short real, 49 segundos:** [Justice na trilha de GTA VI](artefatos/aguardando_revisao/short_justice_20261031/video.mp4).
- **Relatório e fontes do Short:** [fontes.md](artefatos/aguardando_revisao/short_justice_20261031/fontes.md).
- **Roteiro, título, descrição e hashtags:** [pasta completa do Short](artefatos/aguardando_revisao/short_justice_20261031/).
- **Vídeo longo completo Full HD, aproximadamente 8min31s:** [MP4 1920×1080](artefatos/aguardando_revisao/fase2_longo_completo_1080p.mp4).
- **Short demo vertical:** [onboarding_short.mp4](artefatos/onboarding_short.mp4).
- **Prévias, legendas, miniaturas e validações:** [todos os artefatos](artefatos/aguardando_revisao/).

Os vídeos continuam **aguardando revisão humana**. O Short real usa narração local robótica de contingência; o longo usa o demo original. Não houve publicação no YouTube. Guardar os arquivos no GitHub não registra aprovação editorial.

## Conteúdo preservado

| Local | Conteúdo |
| --- | --- |
| `artefatos/` | Cópia dos resultados finais e das prévias mantidas em `output/`, incluindo MP4, SRT, JPG, roteiros, metadados, relatórios e narrações |
| `receitas/` | Receita histórica da produção do Short real e diagnóstico da voz local |
| `ambiente/install_cloud.sh` | Script reutilizável do ambiente de nuvem, sem credenciais |
| `fila_editorial.json` | Estado da fila do Short, com referências relativas para esta pasta |
| `inventario.json` | Tamanhos e SHA-256 dos materiais copiados, commits de origem e exclusões |

O commit `7f70d15` preserva a Fase 2, e `cc98569` preserva as correções e a documentação da Fase 3. O histórico Git acompanha o código na raiz.

As cópias mantêm os bytes dos arquivos originais para preservar seus manifestos. Alguns metadados e o backup SQLite registram caminhos absolutos da máquina em que os vídeos foram produzidos; são registros históricos. Use os arquivos desta pasta para assistir e revisar. Uma nova produção deve seguir os comandos de `factory.py` e a documentação atual, com fontes recentes.

As receitas históricas dependem das evidências locais da data da produção. Elas não devem ser executadas como se fossem pesquisa atual. Consulte [o relatório da Fase 3](../docs/FASE3_RESULTADOS.md) para detalhes de fontes, voz e revisão.

## Reutilizar o projeto

1. Clone ou baixe este repositório pelo botão **Code** do GitHub.
2. Consulte o [guia da Fase 2](../docs/FASE2.md) e o [README principal](../README.md).
3. No ambiente de nuvem existente, reutilize o ambiente virtual já instalado; não reinstale sem necessidade.
4. Em uma instalação nova, prepare Python, FFmpeg e as dependências indicadas nos arquivos `requirements*.txt`.
5. Não configure upload automático. A voz neural gratuita depende da permissão de rede descrita em `pending_network_change.json` na pasta do Short.

O script de nuvem assume o checkout em `/workspace/gta-6-youtube`, FFmpeg e fontes DejaVu previamente disponíveis. Revise os caminhos para outro computador.

## Arquivos que permanecem locais

Não foram incluídos credenciais, `.env` preenchido, ambientes virtuais, dependências instaladas, caches, intermediários de renderização, versões descartadas, modelos não obtidos ou cópias integrais de páginas oficiais coletadas para auditoria. As fontes públicas são registradas por links, datas, hashes e trechos curtos. Backups Git e ZIPs redundantes também foram omitidos: os arquivos úteis já estão organizados aqui.
