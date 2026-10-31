# Resultados da Fase 2 — 31/10/2026

## Implementado

- `factory.py`: comandos `research`, `topics`, `plan`, `produce`, `queue`, `review` e `daily`.
- Pesquisa limitada a páginas primárias, descoberta de links de notícias, snapshots, URLs, datas de publicação quando disponíveis, datas de consulta e hashes. Falhas de acesso são registradas, não convertidas em notícias.
- Cinco regras auditáveis de fatos, roteiros PT-BR com citações por cena, separação de análise, deduplicação persistente por pauta/formato e validade de evidência de 48 horas. Roteiros usam templates editoriais originais, sem LLM pago. Teorias/rumores novos ainda exigem curadoria humana.
- Voz neural local Piper opcional com cache por texto/modelo/configuração/versão; configuração de voz exige licença e hashes. Utilitário para obter modelos e conferir checksums do publicador.
- Novo renderer reaproveita as funções dos renderizadores existentes, acrescenta cortes, movimento suave, fades, legendas por segmento medido, MP4, SRT, thumbnail, capítulos, metadados e checklist.
- Fila SQLite, decisão manual, histórico de revisões e hashes dos arquivos revisados. Não há integração de upload ou agendamento instalado.
- `.gitignore` para segredos, dados, modelos e outputs. `make_short.py`, `make_long.py`, demos e `requirements.txt` ficaram sem alterações.

## Verificações executadas

| Verificação | Resultado |
| --- | --- |
| `python -m unittest discover -s tests -v` | **30 testes passaram**, incluindo exportações e decodificação reais com FFmpeg |
| Pesquisa/extrator/roteiros | Testados offline com fixtures isoladas; incluem expiração, retratação, rumores, links maliciosos, deduplicação e referências |
| Nova exportação vertical | 1080×1920/30 fps H.264/AAC com áudio sintético de teste, legendas e assets; arquivos temporários removidos ao terminar |
| Nova exportação horizontal | Prévia 640×360/24 fps com áudio sintético de teste, legendas e assets |
| Orquestração Piper/cache/alinhamento | Engine simulado, WAVs reais para medir segmentos; **não comprova qualidade acústica de uma voz real** |
| Manifestos/revisão | Aprovação exige checklist; artefatos alterados são recusados; rejeição registrada; prévia não pode ser aprovada como episódio completo |
| Dependências | `pip check` passou. Dependências originais reaproveitadas; apenas o extra Piper e suas dependências foram instalados |
| Integridade do patch | `git diff --check` passou; renderizadores existentes inalterados |

O teste completo do renderizador original foi executado após dry-run e prévia de duas cenas. Arquivo:

`output/aguardando_revisao/fase2_longo_completo_1080p.mp4`

- Duração medida: **511,566667 segundos** (8min31,57s).
- Resolução: **1920×1080**, **30 fps**, vídeo **H.264**, áudio **AAC**.
- MP4, SRT, thumbnail 1280×720, capítulos TXT, metadados JSON e checklist MD produzidos.
- **Decodificação integral do áudio e vídeo passou sem erros**; frame de inspeção conferido visualmente.
- Voz e roteiro: **demo bundled existente**. O episódio testa exportação Full HD; não é uma nova produção noticiosa baseada na coleta desta etapa. A voz é robótica, o SRT é aproximado e o material continua aguardando revisão.
- Evidência local: `output/aguardando_revisao/fase2_fullhd_validacao.json`.

## Bloqueios externos

O coletor foi executado nas três páginas configuradas. O proxy devolveu **CONNECT 403** antes do acesso à Rockstar/Take-Two. Nenhuma página oficial foi coletada e nenhum fato real foi inserido no banco de produção. `factory.py research` saiu com código 2 e `plan --format short` recusou produzir sem evidências.

O acesso ao modelo Piper em `huggingface.co` também recebeu CONNECT 403. Não foi possível baixar o modelo nem examinar sua MODEL_CARD. Portanto, **a voz neural real e sua licença ainda não foram validadas**, e **o Short novo de GTA 6 com fatos verificados e voz natural ainda não foi produzido**. Os testes técnicos com fontes fictícias e áudio sintético não substituem essa entrega.

O novo rascunho recebeu **somente** permissões de rede adicionais para:

- `www.rockstargames.com`
- `rockstargames.com`
- `www.take2games.com`
- `ir.take2games.com`
- `huggingface.co`

Scripts anteriores de instalação e startup não foram reaplicados nem substituídos. O salvamento confirmou persistência do rascunho, não aplicação das permissões na máquina. A ferramenta sinalizou `requires_publish`: revise e salve as alterações nas configurações e publique a nova versão **do ambiente** para persistir essa configuração. Nenhuma publicação foi feita pelo agente.

## Próximo passo após aplicar a rede

1. Reexecutar a pesquisa e confirmar conteúdo oficial legível. Caso o site exija JavaScript/CAPTCHA, diagnosticar o conector; não presumir que permitir o domínio resolve tudo.
2. Baixar a voz, ler e registrar licença/atribuição, ouvir uma amostra e verificar se é adequada. Eventuais domínios CDN devem ser identificados pelo erro real antes de acrescentar permissões.
3. Gerar o roteiro curto a partir de evidências reais, sintetizar e exportar em 1080×1920. Conferir fatos, voz, legendas e visuais; deixar a decisão para o usuário.
4. O teste de exportação Full HD já concluído não precisa ser repetido sem uma nova mudança relevante.

Nenhuma API paga foi chamada. O fluxo local não exige chave de API. Nenhum vídeo foi publicado, e nenhuma rotina diária foi ativada.
