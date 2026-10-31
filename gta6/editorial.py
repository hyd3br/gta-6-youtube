"""Evidence-bound PT-BR scripts, persistent duplicate prevention and manual review."""
from __future__ import annotations

import json
from pathlib import Path

from .research import digest, now

REVIEW_CHECKS = ['facts', 'licenses', 'audio', 'subtitles', 'visuals']


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2), encoding='utf-8')
    temp.replace(path)


CONTEXT = {
    'setting': ('CENÁRIO NÃO É TAMANHO',
        'Imagine comparar dois mundos abertos só pelo nome da região. Essa comparação deixaria de fora a distância entre os pontos de interesse, as possibilidades de deslocamento e a variedade de situações. Para o jogador, atravessar uma área sem decisões interessantes pode ser menos marcante do que explorar um espaço compacto. Essa é uma lente de análise, não uma descrição de sistemas confirmados para GTA seis. Ao acompanhar um anúncio sobre a ambientação, a pergunta útil é: o que exatamente foi apresentado? Um nome, uma imagem e uma sequência jogável respondem a perguntas diferentes. Guardar essa diferença ajuda a avaliar o próximo anúncio sem criar expectativas a partir de números inventados.'),
    'vice_city': ('RECONHECER NÃO É CONHECER',
        'Uma referência visual pode despertar memória e curiosidade. Mas memória de outro jogo não funciona como documentação deste projeto. Se alguém reconhece um bairro ou uma inspiração arquitetônica, isso pode render uma boa comparação editorial, desde que a comparação não vire promessa de acesso ou interatividade. Para nossa análise, vale perguntar como a comunicação oficial descreve aquele espaço e o que pode ser observado diretamente. Não vamos contar estabelecimentos visitáveis com base em fachadas. Também não vamos calcular uma rota completa a partir de cortes de edição. O interesse está em discutir o significado da ambientação sem confundir reconhecimento visual com uma lista de funcionalidades.'),
    'protagonists': ('NARRATIVA NÃO É MECÂNICA',
        'Uma dupla de personagens abre espaço para discutir relações, conflitos e pontos de vista. Essa discussão é interessante justamente porque várias estruturas narrativas são possíveis. O cuidado começa quando uma possibilidade é apresentada como regra do jogo. Alternância de controle, progressão individual e decisões permanentes são questões específicas. A presença de duas pessoas numa apresentação não responde automaticamente a nenhuma delas. Nosso método é descrever o que o material afirma e reservar outra parte do vídeo para perguntas. Assim, o público pode participar da análise sabendo onde começa a interpretação. Não precisamos inventar missões, diálogos ou finais para explicar por que uma relação entre personagens pode despertar curiosidade.'),
    'ps5': ('COMO AVALIAR DESEMPENHO',
        'Quando uma plataforma é mencionada, é natural querer saber como será a experiência naquele aparelho. A resposta exige cuidado com o tipo de evidência. Uma apresentação de divulgação pode ter edição, compressão e condições de captura que não conhecemos. Por isso, resolução do arquivo publicado não é sinônimo de resolução interna do jogo. Também não basta contar quadros num vídeo para prometer estabilidade numa sessão inteira. Uma avaliação útil precisaria explicar o método de medição, a versão utilizada e as condições do teste. Aqui, não temos esse teste. Temos uma referência de plataforma, que deve ser lida dentro do seu alcance, sem extrapolar números de desempenho.'),
    'xbox': ('COMPARAÇÕES COM CRITÉRIO',
        'Comparar aparelhos exige mais do que observar seus nomes numa página. O que interessa ao jogador pode envolver estabilidade, qualidade de imagem, opções de acessibilidade e tempos de carregamento. Cada uma dessas questões pede uma medição própria. Antes de uma avaliação verificável, previsões precisam ser chamadas de previsões. Uma lista de plataformas também pode mudar ao longo do tempo, por isso guardamos a data da consulta. Se houver nova comunicação oficial, o conteúdo precisa ser reavaliado. Esse procedimento evita usar um anúncio antigo como se ele fosse uma garantia eterna ou como prova de que uma versão não mencionada jamais poderá existir.')
}


def generate_script(facts, kind='short'):
    if kind not in ('short','long'): raise ValueError('Formato deve ser short ou long.')
    needed = 2 if kind=='short' else 4
    if len(facts)<needed:
        raise ValueError(f'Faltam fatos recentes: {kind} exige pelo menos {needed}. Rode research; não invente conteúdo para preencher.')
    facts = facts[:3] if kind=='short' else facts[:5]
    sources = []
    for f in facts:
        if f['classification']!='confirmed' or not f.get('evidence'):
            raise ValueError('Roteiro automático aceita somente fatos com evidência primária.')
        if f['source_url'] not in [s['url'] for s in sources]:
            sources.append({'title':f.get('source_title','Fonte primária — GTA VI'),'url':f['source_url'],
                            'checked':f['checked_at'],'published_at':f['published_at'],
                            'sha256':f['source_sha256']})
    scenes=[]
    def scene(headline,speech,refs=(),chapter=None,classification='analysis'):
        item={'headline':headline,'speech':speech,'claim_ids':list(refs),
              'classification':classification,'license_notes':'Arte procedural original criada pelo projeto; não é captura oficial do jogo.'}
        if chapter: item['chapter']=chapter
        scenes.append(item)
    if kind=='short':
        scene('GTA 6: FATO OU EXPECTATIVA?',
              'O que dá para afirmar sobre GTA seis sem cair em boatos? Vamos separar a fonte da nossa expectativa.',chapter='Abertura')
        for f in facts:
            scene(f['headline'],f['statement'],[f['id']],classification='confirmed')
        scene('ANÁLISE, NÃO PROMESSA',facts[0]['analysis'])
        scene('CONFIRA A FONTE',
              'Os links e a data da consulta estão na descrição. As imagens são ilustrativas. Qual detalhe você quer investigar com evidências?')
    else:
        scene('GTA 6: O ALCANCE DA EVIDÊNCIA',
              'Uma informação oficial pode ser verdadeira e ainda assim não responder à pergunta que mais interessa ao jogador. Neste vídeo, vamos partir de evidências registradas sobre GTA seis para explicar o que cada uma permite concluir e onde começam as interpretações. A proposta não é resumir uma lista de rumores. É construir um método de leitura que você possa usar no próximo anúncio. Todos os links e as datas de consulta acompanham o vídeo. Nossos visuais são arte ilustrativa original; eles não são capturas de jogabilidade.',chapter='Como ler os anúncios')
        for f in facts:
            scene(f['headline'],f['statement']+' '+f['analysis'],[f['id']],chapter=f['headline'],classification='fact_and_analysis')
            heading,context=CONTEXT[f['key']]
            scene(heading,context,[f['id']])
        scene('O QUE UMA FONTE COMPROVA',
              'Vale voltar ao procedimento de pesquisa. Nós registramos a página consultada, preservamos um trecho de evidência e guardamos o momento da coleta. A data de consulta não é a data de publicação. Quando a fonte não informa quando o texto foi publicado, esse campo permanece desconhecido. Esse cuidado parece pequeno, mas evita transformar uma página antiga numa notícia de hoje. Também permite revisar o roteiro quando uma informação desaparece ou muda. Se a coleta falha, o sistema registra a falha em vez de preencher a lacuna com uma frase convincente. Transparência sobre o que não foi possível verificar faz parte da qualidade editorial.',chapter='Fontes e atualizações')
        scene('TEORIA COM RÓTULO CLARO',
              'Curiosidades e teorias têm espaço numa conversa sobre jogos. O problema não é imaginar possibilidades, mas esconder que são possibilidades. Uma teoria útil explica qual observação a motivou, quais explicações alternativas existem e qual evidência futura poderia confirmá-la ou derrubá-la. Neste fluxo automático, rumores não entram como afirmações confirmadas. A pauta pode registrar uma pergunta para investigação humana, mas não deve apresentar uma resposta inventada. Se surgir uma informação nova, voltamos à fonte original, conferimos o contexto e reavaliamos o que já foi produzido. Velocidade não compensa uma conclusão que a evidência não sustenta.',chapter='Teorias e rumores')
        scene('PRÓXIMA INVESTIGAÇÃO',
              'A principal conclusão desta análise é que acompanhar GTA seis pode ser mais interessante quando sabemos exatamente o que estamos observando. Ambientação, narrativa e experiência técnica não são a mesma coisa. Uma peça de divulgação pode esclarecer uma delas e deixar as outras em aberto. Antes de compartilhar uma afirmação, confira o link, a data e a frase que realmente foi publicada. Antes de discordar de uma teoria, pergunte se ela foi apresentada como interpretação ou como fato. Agora escolha: qual ponto merece uma investigação mais aprofundada? A próxima pauta deve nascer de uma boa pergunta, sustentada por uma fonte verificável.',chapter='Conclusão')
    words=sum(len(s['speech'].split()) for s in scenes)
    if kind=='long' and not 850<=words<=1740:
        raise ValueError(f'Roteiro longo tem {words} palavras; revisar profundidade e duração antes de produzir.')
    return {'title':'GTA 6: o que as fontes oficiais realmente confirmam'+(' #Shorts' if kind=='short' else ''),
            'thumbnail_title':'GTA 6: FATO OU EXPECTATIVA?',
            'description':'Análise original baseada nas fontes primárias listadas. Visuais ilustrativos próprios; voz sintética. Informações válidas na data da consulta, sem promessa sobre novidades não verificadas.',
            'tags':['gta 6','gta vi','análise gta 6','fontes oficiais'],
            'hashtags':['#GTA6','#GTAVI','#RockstarGames']+(['#Shorts'] if kind=='short' else []),
            'sources':sources,'claims':facts,'scenes':scenes,'format':kind,
            'created_at':now(),'script_method':'deterministic_editorial_templates_v1',
            'estimated_minutes':round(words/145,2),'word_count':words,
            'automatic_upload':False,'status':'ROTEIRO_AGUARDANDO_REVISAO'}


def plan(store, kind):
    facts=store.facts()
    script=generate_script(facts,kind)
    ids=sorted(f['id'] for f in script['claims'])
    topic_key=digest('|'.join(ids))[:20]
    for row in store.db.execute('SELECT body FROM episodes WHERE format=?',(kind,)):
        previous=json.loads(row['body'])
        old=set(previous.get('claim_ids',[]))
        if old and len(old.intersection(ids))/max(len(old),len(ids))>=0.8:
            raise ValueError('Pauta já produzida ou na fila para este formato; escolha uma investigação editorial diferente.')
    episode_id=kind+'-'+topic_key
    folder=store.folder/'episodes'/episode_id
    folder.mkdir(parents=True,exist_ok=True)
    script_path=folder/'script.json'
    write_json(script_path,script)
    episode={'id':episode_id,'format':kind,'topic_key':topic_key,'claim_ids':ids,
             'script':str(script_path.resolve()),'status':'ROTEIRO_AGUARDANDO_REVISAO',
             'created_at':now(),'render':None,'automatic_upload':False}
    store.db.execute('INSERT INTO episodes VALUES (?,?,?,?,?)',
                     (episode_id,topic_key,kind,episode['status'],json.dumps(episode,ensure_ascii=False)))
    store.db.commit()
    return episode


def get_episode(store,episode_id):
    row=store.db.execute('SELECT body FROM episodes WHERE id=?',(episode_id,)).fetchone()
    if not row: raise ValueError('Episódio não encontrado.')
    return json.loads(row['body'])


def update_episode(store,episode):
    store.db.execute('UPDATE episodes SET status=?,body=? WHERE id=?',
                     (episode['status'],json.dumps(episode,ensure_ascii=False),episode['id']))
    store.db.commit()


def review(store,episode_id,decision,note,checks=()):
    if decision not in ('approve','reject'): raise ValueError('Decisão inválida.')
    if not note.strip(): raise ValueError('Informe uma nota de revisão.')
    e=get_episode(store,episode_id)
    if e['status'] not in ('AGUARDANDO_REVISAO_HUMANA','APROVADO','REJEITADO'):
        raise ValueError('Só é possível revisar uma exportação concluída.')
    if decision=='approve':
        if e.get('preview'): raise ValueError('Prévia parcial não pode ser aprovada como episódio completo.')
        if set(checks)!=set(REVIEW_CHECKS): raise ValueError('Aprovação exige facts,licenses,audio,subtitles,visuals.')
        manifest=Path(e['render'])
        if not manifest.is_file(): raise ValueError('Manifesto de exportação ausente.')
        rendered=json.loads(manifest.read_text())
        for name,expected in rendered['artifact_sha256'].items():
            if Path(name).name!=name: raise ValueError('Nome de artefato inválido no manifesto.')
            file=manifest.parent/name
            if not file.is_file() or digest_bytes(file)!=expected:
                raise ValueError('Artefato alterado ou ausente; renderize/revise novamente.')
    e['status']='APROVADO' if decision=='approve' else 'REJEITADO'
    e['review']={'decision':decision,'note':note,'checks':list(checks),'at':now(),
                 'automatic_upload':False}
    store.db.execute('INSERT INTO reviews(episode_id,decision,note,created_at) VALUES (?,?,?,?)',
                     (episode_id,decision,note,now()))
    update_episode(store,e)
    if e.get('render'):
        write_json(Path(e['render']).parent/'review_decision.json',e['review'])
    return e


def digest_bytes(path):
    import hashlib
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
