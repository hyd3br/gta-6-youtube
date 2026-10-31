# Regras para Codex — GTA6 Factory

1. O projeto produz Shorts **e** vídeos longos sobre GTA 6 em português brasileiro.
2. Preservar `make_short.py` e o Short demo. Longos ficam em `make_long.py` com render 16:9 1920×1080, meta de 6–12 min.
3. NUNCA fazer upload ou publicação automática. Todo arquivo gerado precisa de revisão humana.
4. Checar fatos em fontes primárias e guardar URL + data. Separar confirmações, interpretações e especulações; não inventar notícias.
5. Não baixar imagens/clipes protegidos sem autorização. Usar conteúdo próprio ou licenciado e exigir `license_notes`.
6. `.env` e chaves privadas não devem ser adicionadas a ZIP público nem a repositórios. Verificar `.gitignore`.
7. Padrão de arquivo: MP4 H.264/AAC, SRT, thumbnail JPG, capítulos TXT, metadados JSON, checklist MD.
8. Antes de criar um episódio completo, validar roteiro com `--dry-run` e gerar prévia 640×360 com `--preview-scenes 2`.
9. O modo `bundled` é para demo com falas imutáveis. O modo `windows` usa System.Speech e o `openai` faz chamadas pagas sob decisão do usuário.
10. `gpt-4o-mini-tts` / Speech API foi depreciado e encerra em 2027-01-06. Migrar para fluxo Realtime suportado antes dessa data, verificando documentação oficial.
11. Não prometer legendas palavra por palavra: este MVP distribui tempos por comprimento de texto de cada cena.
12. Para produção recorrente: primeiro propor um plano de pesquisa verificável e fila editorial com aprovações, depois implementar com testes e sem upload.
