# GTA6 Factory — Shorts + vídeos longos (Windows 11)

## Projeto e entregas reunidos

O código, a documentação e os testes estão neste repositório. A pasta [entregas/](entregas/README.md) reúne os vídeos, roteiros, legendas, miniaturas, fontes e relatórios produzidos nas Fases 1–3, incluindo o Short real de 49 segundos e o vídeo longo completo em 1080p. Os materiais continuam aguardando revisão humana; não há publicação automática no YouTube.

## Fase 2: pesquisa e fila de produção no Linux

O novo `factory.py` conecta pesquisa em fontes primárias, roteiros com evidências, voz neural local gratuita e exportações para revisão humana. Os renderizadores e demos abaixo continuam disponíveis. Consulte [guia da Fase 2](docs/FASE2.md) e [resultados e pendências](docs/FASE2_RESULTADOS.md). Não há upload automático.

**Versão MVP funcional**, com dois renderizadores independentes:

- `make_short.py`: vídeo vertical **1080×1920 / 30 fps** (Short). O vídeo de demonstração original permanece disponível.
- `make_long.py`: vídeo horizontal **1920×1080 / 30 fps**, projetado para **6 a 12 minutos**, roteiro dividido em capítulos, narração por cena, legendas SRT, thumbnail 1280×720, descrição, marcação de capítulos e checklist de revisão.

**Este projeto NÃO publica vídeos nem pesquisa notícias sozinho.** A revisão humana é obrigatória. Mídias demo são gráficos procedurais originais. Para screenshots, trailers, jogos, músicas e vídeos de terceiros, confira direitos/licenças e permissões de uso antes de inserir arquivos. Não há garantia de monetização.

## 1. Instalar no Windows 11

Abra o PowerShell e instale Python, FFmpeg e, opcionalmente, Git. Instale Codex pelo aplicativo oficial do ChatGPT ou pelo caminho disponibilizado pela OpenAI. Os comandos winget podem ser executados separadamente:

```powershell
winget install --id Python.Python.3.14 -e
winget install --id Gyan.FFmpeg -e
winget install --id Git.Git -e
```

Feche e reabra o PowerShell. Confirme:

```powershell
python --version
ffmpeg -version
ffprobe -version
```

Extraia a pasta `GTA6-Canal-Completo` do ZIP para Documentos. Abra o terminal dentro dela:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Fazer o teste de Short

```powershell
.\.venv\Scripts\python.exe make_short.py --tts bundled
```

Saída: `output/primeiro_short.mp4`. O modo bundled é uma voz robótica de demonstração, não a voz final de publicação.

## 3. Fazer o teste do vídeo longo GRATUITAMENTE

O kit contém um **roteiro completo** sobre perguntas relevantes em GTA 6 e **10 vozes sintéticas de demonstração** em português brasileiro. A versão completa dura aproximadamente **8 minutos e meio**, depende apenas de Python e FFmpeg e não consome créditos de API.

Teste primeiro duas cenas em resolução leve:

```powershell
.\.venv\Scripts\python.exe make_long.py --tts bundled --preview-scenes 2 --width 640 --height 360 --fps 24 --output output/aguardando_revisao/preview_longo_640.mp4
```

Depois, gere o **episódio horizontal completo em Full HD**:

```powershell
.\.venv\Scripts\python.exe make_long.py --tts bundled
```

A renderização 1080p usa CPU e pode demorar conforme o seu computador. Para testar o episódio inteiro mais rápido, use:

```powershell
.\.venv\Scripts\python.exe make_long.py --tts bundled --width 640 --height 360 --fps 24 --output output/aguardando_revisao/episodio_teste_360p.mp4
```

Para um render mais rápido mantendo as legendas em `.srt` separado, acrescente `--no-burn-subtitles` (o MP4 ficará sem legendas embutidas).

Todos os resultados ficam em `output/aguardando_revisao/`:

- `.mp4`: vídeo H.264/AAC com narração e legendas incorporadas por padrão
- `.srt`: legenda separada, com **tempos estimados** a partir da duração de cada narração (não é alinhamento palavra por palavra)
- `.json`: título, descrição, fontes, tags, duração e avisos
- `_capitulos.txt`: capítulos e marcação de tempo prontos para YouTube
- `_thumbnail.jpg`: miniatura **1280×720** feita com gráficos originais
- `_revisao.md`: checklist obrigatório antes da publicação

O ZIP inclui um episódio demonstrativo completo em 360p, com aproximadamente 8min32s, narração robótica e SRT separado. É uma prova de funcionamento, não um vídeo final para publicar.

O programa **não** faz upload, nem envia vídeo ao YouTube.

## 4. Produzir NOVOS episódios (voz gratuita ou paga)

Copie `roteiro_longo_exemplo.json` para `meu_roteiro.json`. Edite `title`, `description`, `sources`, `tags` e `scenes`. Cada cena deve conter `headline` (texto na tela) e `speech` (narração); use `chapter` na primeira cena de cada capítulo e, opcionalmente, `takeaway`.

**Valide o roteiro antes de gastar com TTS:**

```powershell
.\.venv\Scripts\python.exe make_long.py --script meu_roteiro.json --tts windows --dry-run
```

A voz `bundled` só funciona com o roteiro de exemplo sem alterar as falas; para textos próprios, escolha:

### A. Windows gratuito (voz do sistema)

```powershell
.\.venv\Scripts\python.exe make_long.py --script meu_roteiro.json --tts windows --output output/aguardando_revisao/meu_episodio.mp4
```

Usa o `System.Speech` do **Windows PowerShell 5.1**. Escolhe uma voz SAPI `pt-BR` se disponível; se não houver, pode soar inadequada. É necessário instalar a voz brasileira compatível para melhorar esse modo. Não funciona pelo Linux sem Windows PowerShell.

### B. OpenAI API (voz mais natural, paga por uso)

A assinatura do ChatGPT não cobre a API. Crie sua chave em https://platform.openai.com/api-keys. Copie `.env.example` para `.env`, configure `OPENAI_API_KEY` localmente e execute:

```powershell
Copy-Item .env.example .env
notepad .env
.\.venv\Scripts\python.exe make_long.py --script meu_roteiro.json --tts openai --output output/aguardando_revisao/meu_episodio.mp4
```

**ATENÇÃO: o modelo `gpt-4o-mini-tts` da Speech API está depreciado e tem encerramento previsto para 6 de janeiro de 2027.** A substituição recomendada é `gpt-realtime-2.1-mini` via **Realtime API**, que requer uma integração de código diferente: não basta trocar o nome no `.env`. Antes dessa data, peça ao Codex que migre o provedor e execute testes. Informações: https://developers.openai.com/api/docs/deprecations

Os áudios gerados são armazenados em cache pelo texto + provedor + modelo + voz, evitando cobranças repetidas quando não há alterações.

### C. Arquivos de áudio prontos

Inclua `"audio_path": "assets/narracao_01.wav"` em cada cena. Use `--tts files`. Assim é possível importar narração produzida em um editor externo ou serviço de TTS.

## 5. Inserir imagens ou clipes próprios/licenciados

Em uma cena, use **somente um** dos dois campos abaixo (não os dois):

```json
{
  "headline": "O QUE FOI CONFIRMADO?",
  "speech": "Narração desta parte...",
  "image_path": "assets/minha_imagem.png",
  "license_notes": "Imagem própria, criada por mim em 2026."
}
```

Para vídeo, troque `image_path` por `video_path` com caminho local, por exemplo `assets/meu_clipe.mp4`, e informe `license_notes` com a autorização. O áudio do clipe não entra na edição; a narração é reproduzida sobre a sequência. O clipe será ajustado/cortado para 16:9 e repetido se for menor que a duração da cena. Use um arquivo de mídia com direitos adequados à distribuição e monetização.

Para trilha musical autorizada, use `--music assets/musica.mp3 --music-license-note "Licença ou permissão: ..."`; o volume padrão é baixo (`0.08`). O uso de música protegida sem autorização não é permitido.

## 6. Como produzir Shorts E longos no mesmo canal

Um fluxo editorial recomendado:

1. Pesquisar temas GTA 6 e salvar URLs/datas; separar **fato confirmado, análise e teoria**.
2. Criar um roteiro de 6–12 min, revisar e gerar vídeo longo.
3. Derivar 2–4 roteiros de Shorts **originais**, cada um com sua própria estrutura; não apenas recortar trechos idênticos em massa.
4. Exportar todos para a fila local e revisar os arquivos antes de publicar no YouTube Studio.
5. Manter registro de fontes, licenças e revisões. O sistema não automatiza o YouTube.

## 7. Limites importantes do MVP

- Não pesquisa ou verifica automaticamente notícias e não garante a precisão das informações do JSON.
- As imagens de demonstração são genéricas e ilustrativas, não screenshots/gameplay de GTA 6.
- A voz de demonstração é robótica e **não deve** ser considerada pronta para publicação profissional.
- O SRT usa tempos **aproximados** por bloco de palavras; para sincronização fina, use um alinhador de fala ou revise no Premiere/CapCut.
- Renderizar vídeos longos em Full HD consome CPU, tempo e disco; prévias em 640×360 ajudam a testar.
- Fontes, direitos de imagem, política do YouTube e uso comercial precisam ser verificados pelo criador.

## 8. Solicitação para Codex

Abra esta pasta no Codex, leia `AGENTS.md` e cole `PROMPT_PARA_CODEX.txt`. O agente poderá desenvolver pesquisa com fontes oficiais, histórico de pautas, aprovações e TTS de melhor qualidade a partir deste MVP.
