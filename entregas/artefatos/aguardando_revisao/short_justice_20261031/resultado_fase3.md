# Fase 3 — primeiro Short real para revisão

Produzido em 31/10/2026, sem API paga e sem publicação.

## Ambiente e preservação

- O teste inicial de execução completou antes de qualquer alteração.
- Commit `7f70d1587eee2a11e136ce03d55b84fb71e63ac8` e os 16 arquivos da Fase 2 confirmados.
- Python 3.12.14, FFmpeg/FFprobe 7.1.5, Pillow 13.0.0, python-dotenv 1.2.4, openai 3.42.0, Piper 1.8.0 e ONNX Runtime 1.31.1 disponíveis. `pip check` passou; nada foi reinstalado.
- Os renderizadores originais `make_short.py`/`make_long.py`, demos, vídeos longos e Shorts anteriores foram preservados.

## Fontes testadas

| Destino | Resultado |
| --- | --- |
| https://www.rockstargames.com/VI/ | HTTP 200, conteúdo editorial e destaques legíveis |
| https://www.rockstargames.com/newswire | HTTP 200; listagem depende de JavaScript, sem artigos no HTML inicial |
| https://www.take2games.com/ir/news | HTTP 404: rota antiga, não bloqueio de rede |
| https://ir.take2games.com/news-releases | HTTP 200 após redirecionar para `/ir/press-releases` |
| Hugging Face, metadados e MODEL_CARD da voz pt_BR-faber-medium | HTTP 200 |
| Arquivo de pesos da voz | Redireciona para `us.aws.cdn.hf.co`; CONNECT 403 pelo proxy |

A semente da Take-Two foi corrigida para a rota atual. A extração de fatos passou a ignorar páginas de índice: um título de GTA próximo de uma plataforma de outro jogo não deve gerar uma confirmação falsa. Foi acrescentado um teste de regressão. As legendas verticais foram elevadas para não sobrepor o rodapé.

## Pauta verificada

**Justice assina o score original de GTA VI.**

- Anúncio: https://www.rockstargames.com/newswire/article/39ak8a12395591
- Contexto e data do destaque: https://www.rockstargames.com/VI
- Data exibida pela Rockstar no card correspondente: **29/10/2026**.
- Consulta nesta execução: **31/10/2026** (timestamps UTC e hashes no relatório do vídeo).

O artigo fornece o crédito musical em sua descrição editorial no HTML. Seu corpo completo depende de JavaScript. A data veio do card oficial correspondente, não de um campo de publicação inventado. O Short separa o crédito confirmado da interpretação sobre identidade musical; não afirma que Justice criou todas as faixas de rádio. A Take-Two foi testada, mas não foi usada para atribuir a autoria da música.

## Arquivo produzido

`output/aguardando_revisao/short_justice_20261031/video.mp4`

- **49 segundos**, **1080×1920**, **30 fps**, H.264/AAC, áudio estéreo a 48 kHz.
- Roteiro original de **108 palavras**, cinco cenas com movimento suave, cortes e fades.
- **23 legendas**, agrupadas pelos eventos reais de início de palavras do sintetizador.
- Narração sintética pt-BR local **eSpeak NG, robótica e não neural**.
- Arte procedural original, sem screenshots, gameplay, músicas de Justice ou outras gravações de terceiros.
- Título, descrição, hashtags, SRT, thumbnail, capítulos, relatório de fontes, manifesto e checklist na mesma pasta.
- Narrações originais e dados de tempo também incluídos no pacote de revisão.

**Estado: AGUARDANDO_REVISAO_HUMANA.** Não foi aprovado automaticamente. A auditoria de fontes e a audição da voz continuam necessárias.

## Qualidade e testes

- **31 testes passaram**, incluindo exportações reais com FFmpeg e a regressão do índice corporativo.
- Arquivo final decodificado integralmente, com vídeo e áudio sem erros.
- Resolução, codecs, FPS e duração conferidos com FFprobe.
- Texto das legendas confrontado com o roteiro; eventos do sintetizador não cortam palavras e os WAVs contêm sinal audível sem saturação de amostras.
- Frames de inspeção visual conferidos; sobreposição inicial de legenda com rodapé corrigida e exportação refeita.
- O frameamento não substitui assistir e ouvir o vídeo inteiro; naturalidade e pronúncia de “Justice” precisam da revisão do criador.

## Pendência para a voz neural

A licença da voz Faber declara dataset **CC0**, mas os pesos não puderam ser baixados. O modelo neural não foi usado. Para não depender de uma API paga, o vídeo foi concluído com uma voz local de contingência já instalada.

O hostname exato necessário é **`us.aws.cdn.hf.co`**. A tentativa de acrescentá-lo à lista permitida retornou `draft_not_editable`; uma nova leitura manteve o rascunho antigo. **O salvamento dessa mudança não foi confirmado**. Nenhuma restrição foi contornada e TLS/checksums foram preservados.

A proposta aditiva, preservando os cinco domínios existentes, está em `pending_network_change.json` na pasta do Short. Aplique o domínio nas configurações de rede do ambiente para substituir posteriormente a voz robótica por Piper gratuito. Se o produto não permitir editar esse rascunho, use um novo chat de configuração a partir das configurações do ambiente e leve a proposta salva. Não é necessário autorizar uma API paga para esse caminho.

## Aprovar ou rejeitar localmente

O Short está em uma fila separada, preservando a base anterior:

```bash
python factory.py --data-dir data/phase3/editorial queue
python factory.py --data-dir data/phase3/editorial review short-justice-20261029 approve --checks facts,licenses,audio,subtitles,visuals --note "Sua revisão após assistir"
python factory.py --data-dir data/phase3/editorial review short-justice-20261029 reject --note "Motivo da rejeição"
```

Esses comandos apenas registram a decisão; não fazem upload. A receita e as cópias completas das fontes permanecem em `work/phase3_justice` e `data/phase3` para auditoria local. Os snapshots oficiais completos não são redistribuídos no pacote de revisão.
