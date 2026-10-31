# Fase 2 — pesquisa, roteiro e fila local

Esta etapa acrescenta `factory.py` sem substituir `make_short.py`, `make_long.py` ou os demos. Não existe integração de upload. Aprovar um vídeo só registra a decisão localmente.

## Fluxo editorial

1. Coletar páginas primárias de Rockstar/Take-Two. Registrar URL canônica, título, data de publicação quando informada, momento da consulta UTC, trecho de evidência, hash e cópia local do HTML.
2. Extrair apenas fatos reconhecidos por regras auditáveis. A versão inicial reconhece ambientação em Leonida/Vice City, Jason/Lucia e plataformas. **Não resume qualquer notícia arbitrária**, nem infere lançamento, preço, FPS ou mecânicas a partir de trailers. Novos tipos de informação exigem regras e testes editoriais próprios.
3. Criar pautas analíticas e roteiros em português com referências por cena. O gerador usa templates editoriais escritos para o projeto, não um LLM pago. Fatos e análise têm rótulos diferentes. Rumores não viram confirmações; teorias novas exigem curadoria. Falta de evidência interrompe a geração.
4. Sintetizar com Piper local, criar arte procedural própria, cortes, movimento suave, fades, SRT, legendas incorporadas, thumbnail, capítulos, metadados e checklist.
5. Exportar em `output/aguardando_revisao/<episodio>-<tentativa>/`. Assistir, verificar fontes/licenças e aprovar ou rejeitar. Nada é publicado automaticamente.

O banco SQLite e os snapshots ficam em `data/`, fora do Git. As evidências expiram após 48 horas. Páginas alteradas invalidam fatos removidos. Pautas com os mesmos fatos (ou sobreposição >=80%) são recusadas para o mesmo formato, inclusive após reiniciar. Shorts e longos podem analisar os mesmos fatos em formatos diferentes. Não há promessa de originalidade universal: os roteiros ainda precisam de edição humana; não repetir templates indefinidamente numa rotina de publicação.

## Usar o ambiente existente

```bash
cd /workspace/gta-6-youtube
source /workspace/.venvs/gta-6-youtube/bin/activate
export XDG_CACHE_HOME=/workspace/.cache/gta-6-youtube
mkdir -p "$XDG_CACHE_HOME/fontconfig"
python -m pip check
```

As dependências originais foram reaproveitadas. A única instalação adicional desta etapa foi `piper-tts==1.8.0` e suas dependências, para voz neural gratuita. Numa máquina sem esse extra:

```bash
python -m pip install -r requirements-local-tts.txt
```

## Rede e voz neural

A configuração original permite registros de pacotes, mas não os sites de pesquisa nem os modelos. Foram acrescentados ao **rascunho** estes domínios: `www.rockstargames.com`, `rockstargames.com`, `www.take2games.com`, `ir.take2games.com`, `huggingface.co`. O rascunho não aplica a mudança na máquina. Aplique as permissões nas configurações do ambiente. Não desative proxy, TLS ou verificações de checksum para contornar falhas.

Depois da liberação:

```bash
python tools/prepare_voice.py --voice pt_BR-faber-medium
```

O utilitário baixa modelo/configuração/MODEL_CARD do repositório Piper Voices e confere SHA-256 LFS ou hash do blob Git contra os metadados do publicador. Downloads já existentes também são conferidos. Leia `models/pt_BR-faber-medium/MODEL_CARD`: a licença do programa Piper não substitui a licença da voz/dataset. Confirme permissão comercial e atribuição. Repita com `--license-notes "LICENÇA E ATRIBUIÇÃO VERIFICADAS NA MODEL_CARD"`, preenchendo uma nota verdadeira. Sem essa nota não é criado `voice.json`.

Um redirecionamento da Hugging Face pode exigir um domínio adicional de armazenamento; só acrescente o hostname exato diagnosticado. Não autorize `*`. Nenhum modelo foi baixado enquanto a política bloqueou o primeiro destino; a licença específica ainda precisa ser examinada. Uma voz pode ter limitações de naturalidade e pronúncia: ouça o resultado. O download usa até 100 MB por artefato.

Não é necessária chave de API para pesquisa ou Piper. Para usar áudio já produzido, os renderizadores originais continuam oferecendo `--tts files`. O modo Windows continua exclusivo do Windows. O modo OpenAI legado é pago, requer uma decisão explícita e a chave `OPENAI_API_KEY` apenas em `.env` local ou configuração segura da máquina; não foi chamado nem migrado nesta etapa. O novo `factory.py` **não tem provedor pago**, logo não inicia cobranças silenciosamente. Nunca coloque chaves em JSONs, commits, exemplos preenchidos ou conversa. `.gitignore` protege `.env`, dados, modelos, caches e saídas.

## Pesquisa e roteiros

```bash
python factory.py research
python factory.py topics
python factory.py plan --format short
python factory.py plan --format long
python factory.py queue
```

`config/sources.json` define páginas iniciais e limite de coleta (máximo 30). Links de notícias dentro dos domínios primários também são descobertos. A coleta não usa pesquisa paga nem tenta contornar CAPTCHA ou páginas que exigem JavaScript. Se um site não fornecer HTML legível, informe uma página oficial acessível ou implemente um conector para um feed oficial documentado. O relatório `data/last_research.json` registra falhas; `research` retorna código 2 quando a coleta está incompleta ou sem fatos. `daily` não continua nessas condições. Não confundir os testes offline com notícias verificadas.

Um roteiro curto exige pelo menos dois fatos frescos e o longo pelo menos quatro. O longo tem meta de 850–1740 palavras; a duração real depende da voz. As datas dos anúncios não são inventadas: quando ausentes, ficam `null`. A data de consulta não é apresentada como novidade. O roteiro final inclui `claims`, referências de cada cena, fontes, tags e sugestões de hashtags.

## Produzir e revisar

Use o ID mostrado por `plan`:

```bash
python factory.py produce short-ID --voice-spec models/pt_BR-faber-medium/voice.json
python factory.py produce long-ID --voice-spec models/pt_BR-faber-medium/voice.json --preview
```

Uma prévia parcial **não pode ser aprovada como episódio completo**. Para testar apenas a prévia e depois produzir o longo, use uma base separada para os testes (`--data-dir data/preview`) e a base padrão para a produção. Um longo completo cria automaticamente uma prévia de duas cenas em 640×360 antes da exportação 1920×1080:

```bash
python factory.py produce long-ID --voice-spec models/pt_BR-faber-medium/voice.json
```

O Short sai em 1080×1920/30 fps e o longo completo em 1920×1080/30 fps. O novo perfil só usa visuais procedurais originais, identificados como ilustração. Não baixa mídia da Rockstar nem música. O cache da voz inclui texto, modelo, configuração e versão do sintetizador. Cada legenda acompanha um segmento de voz com duração medida no WAV; **não é alinhamento palavra por palavra**. A segmentação curta pode afetar a prosódia e precisa de escuta humana. Os demos originais mantêm o sincronismo aproximado que já possuíam.

O pipeline verifica codecs, resolução e decodifica o arquivo inteiro. Manifestos com hashes vinculam a aprovação aos arquivos efetivamente revisados. Resultados existentes não são sobrescritos. Falhas ficam como `FALHOU` e podem ser tentadas de novo com `produce`; processos interrompidos à força em `RENDERIZANDO` exigem recuperação manual do estado antes de outra tentativa (não há supervisor nesta versão).

```bash
python factory.py review short-ID approve --checks facts,licenses,audio,subtitles,visuals --note "Assisti e conferi fontes, voz, arte e legendas."
python factory.py review short-ID reject --note "Corrigir pronúncia e sincronismo antes de nova revisão."
```

Rejeitar preserva o histórico e os arquivos; não publica nem apaga. Não agende aprovação automática.

## Rotina futura e testes

`daily` executa uma rodada completa de coleta → pauta → roteiro → voz → exportação. Não agenda tarefas, não publica, e não produz a mesma pauta duas vezes:

```bash
python factory.py daily --format short --voice-spec models/pt_BR-faber-medium/voice.json
python -m unittest discover -s tests -v
```

Só programe uma rotina externa depois de validar fontes reais, voz licenciada e fila de revisão. A rotina deve registrar códigos de saída, ter limite de concorrência e manter backup de `data/`. Testes usam fontes fictícias isoladas, identificadas como fixtures, e um teste de integração faz exportação e decodificação real com áudio sintético; nenhum desses testes cria notícias para produção.

Veja [resultados desta execução](FASE2_RESULTADOS.md).
