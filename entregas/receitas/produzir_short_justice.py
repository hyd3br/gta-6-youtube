"""Verified editorial Short; local formant voice fallback, no network/publishing."""
from __future__ import annotations

import ctypes as C
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys
import wave

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gta6.research import Store,parse_page,now,digest
from gta6.editorial import write_json,digest_bytes,update_episode
from gta6.production import render,validate_cues

BASE=ROOT/'data/phase3'
WORK=ROOT/'work/phase3_justice'
OUT=ROOT/'output/aguardando_revisao/short_justice_20261031'
ID='short-justice-20261029'


class EventId(C.Union):
    _fields_=[('number',C.c_int),('name',C.c_char_p),('string',C.c_char*8)]


class Event(C.Structure):
    _fields_=[('type',C.c_int),('unique_identifier',C.c_uint),('text_position',C.c_int),
              ('length',C.c_int),('audio_position',C.c_int),('sample',C.c_int),
              ('user_data',C.c_void_p),('id',EventId)]


class LocalVoice:
    def __init__(self):
        package=Path(importlib.util.find_spec('piper').origin).parent
        self.lib=C.CDLL(str(package/'espeakbridge.so'))
        self.lib.espeak_Initialize.argtypes=[C.c_int,C.c_int,C.c_char_p,C.c_int]
        self.lib.espeak_Initialize.restype=C.c_int
        self.rate=self.lib.espeak_Initialize(2,0,str(package/'espeak-ng-data').encode(),0)
        if self.rate<=0: raise ValueError('Falha ao iniciar voz local.')
        self.lib.espeak_SetVoiceByName.argtypes=[C.c_char_p]
        if self.lib.espeak_SetVoiceByName(b'pt-br')!=0: raise ValueError('Voz pt-BR ausente.')
        self.lib.espeak_SetParameter.argtypes=[C.c_int,C.c_int,C.c_int]
        self.lib.espeak_Synth.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_int,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
        self.Callback=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_short),C.c_int,C.POINTER(Event))

    def speak(self,text,path,wpm):
        parts=[];events=[]
        @self.Callback
        def receive(samples,n,items):
            if samples and n>0: parts.append(C.string_at(samples,n*2))
            index=0
            while items and items[index].type!=0 and index<1000:
                e=items[index]
                if e.type==1:
                    events.append({'position':e.text_position-1,'length':e.length,'start':e.audio_position/1000})
                index+=1
            return 0
        self.lib.espeak_SetSynthCallback.argtypes=[self.Callback]
        self.lib.espeak_SetSynthCallback(receive)
        self.lib.espeak_SetParameter(1,wpm,0)
        self.lib.espeak_SetParameter(2,100,0)
        self.lib.espeak_SetParameter(3,50,0)
        self.lib.espeak_SetParameter(4,50,0)
        buffer=C.create_string_buffer(text.encode('utf-8'))
        if self.lib.espeak_Synth(buffer,len(buffer),0,1,0,1,None,None)!=0:
            raise ValueError('Falha na síntese local.')
        self.lib.espeak_Synchronize()
        pcm=b''.join(parts)
        if not pcm: raise ValueError('Narração vazia.')
        with wave.open(str(path),'wb') as wav:
            wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(self.rate);wav.writeframes(pcm)
        seconds=len(pcm)/(2*self.rate)
        # Actual word-start events from the synthesizer, grouped into readable cues.
        unique=[]
        for e in events:
            if e['position']<0 or e['position']>=len(text): continue
            if not unique or (e['position']>unique[-1]['position'] and e['start']>unique[-1]['start']):
                unique.append(e)
        cues=[]
        for i in range(0,len(unique),5):
            end=min(i+5,len(unique))
            text_end=unique[end]['position'] if end<len(unique) else len(text)
            cues.append({'text':text[unique[i]['position']:text_end].strip(),
                         'start':unique[i]['start'],
                         'end':unique[end]['start'] if end<len(unique) else seconds})
        validate_cues(cues,seconds)
        write_json(path.with_suffix('.timing.json'),{'text':text,'word_events':unique,'cues':cues,'seconds':seconds,'rate_wpm':wpm})
        return seconds,cues


def build():
    if (OUT/'video.mp4').exists(): raise ValueError('Saída já existe; preservar revisão anterior.')
    checks=json.loads((BASE/'access_checks.json').read_text())
    index_raw=(BASE/'rockstar_vi.body').read_text()
    article_raw=(BASE/'rockstar_score.html').read_text()
    index=parse_page(index_raw,'https://www.rockstargames.com/VI')
    article=parse_page(article_raw,'https://www.rockstargames.com/newswire/article/39ak8a12395591')
    # Restore actual fetch times, not script execution time.
    index['fetched_at']=next(r['checked_at'] for r in checks if r['name']=='rockstar_vi')
    article['fetched_at']=json.loads((BASE/'rockstar_score.json').read_text())['fetched_at']
    credit='The Grand Theft Auto VI: Original Score is composed by Grammy Award winners Justice, the renowned French duo of Gaspard Augé and Xavier de Rosnay.'
    date_quote='Grand Theft Auto VI: Original Score by Justice October 29, 2026'
    separation='In-Game Radio, Soundtrack, and Score'
    for quote,page in ((credit,article),(date_quote,index),(separation,index)):
        if quote not in page['text']: raise ValueError('Evidência ausente; não produzir.')
    claims=[]
    for key,statement,quote,page,published in (
        ('score_author','A Rockstar credita ao duo francês Justice a composição do score original de GTA VI.',credit,article,None),
        ('score_date','O destaque da página oficial data o anúncio da trilha em 29 de outubro de 2026.',date_quote,index,'2026-10-29'),
        ('music_categories','O site oficial menciona rádio, soundtrack e score na seção de música.',separation,index,None),
    ):
        claims.append({'id':digest('phase3:'+key)[:20],'key':key,'statement':statement,'classification':'confirmed',
                       'evidence':quote,'source_url':page['url'],'source_title':page['title'],
                       'source_sha256':page['sha256'],'checked_at':page['fetched_at'],'published_at':published})
    scene_text=[
        ('GTA 6 TEM UMA NOVIDADE MUSICAL','Uma novidade de GTA seis que não é sobre mapa nem gráficos: a trilha original.',[], 'intro'),
        ('JUSTICE ASSINA O SCORE','Em vinte e nove de outubro, a Rockstar destacou o anúncio: o duo francês Justice compõe a trilha original do jogo.',[0,1], 'confirmed'),
        ('SCORE NÃO É TODA A RÁDIO','Mas atenção: isso não significa que todas as músicas das rádios sejam deles. O próprio site menciona rádio, trilha sonora e score separadamente.',[2], 'fact_and_analysis'),
        ('FATO CONFIRMADO × INTERPRETAÇÃO','O fato confirmado é o crédito da composição. Minha leitura: vale observar como essa música vai ajudar a construir a identidade de Vice City.',[0], 'fact_and_analysis'),
        ('FONTE OFICIAL • ARTE ORIGINAL','As fontes e a data da consulta estão na descrição. Aqui usamos arte própria e nenhuma gravação oficial. Você curtiu essa escolha para a trilha? ',[], 'disclosure'),
    ]
    scenes=[]
    for i,(headline,speech,refs,kind) in enumerate(scene_text):
        scenes.append({'headline':headline,'speech':speech.strip(),'classification':kind,
                       'claim_ids':[claims[x]['id'] for x in refs],
                       'chapter':headline,'license_notes':'Arte procedural original do projeto; sem gameplay, screenshots, gravações de Justice ou música de terceiros.'})
    script={'title':'GTA 6: Justice assina a trilha original — confirmado pela Rockstar #Shorts',
            'thumbnail_title':'GTA 6: JUSTICE NA TRILHA',
            'format':'short','created_at':now(),'script_method':'curated_primary_evidence_phase3',
            'description':'A Rockstar credita a composição do score original de GTA VI ao duo francês Justice. O destaque de 29/10/2026 aparece no site oficial. Explicamos o alcance do anúncio sem extrapolar para todas as músicas das rádios.\n\nFontes consultadas em 31/10/2026:\n'+article['url']+'\n'+index['url']+'\n\nVoz sintética pt-BR local de contingência (eSpeak NG): robótica, não neural. Arte procedural própria. Não contém gravações de Justice, música oficial, gameplay ou screenshots. Opiniões identificadas como análise.\n\n#GTA6 #GTAVI #Justice #RockstarGames #Shorts',
            'hashtags':['#GTA6','#GTAVI','#Justice','#RockstarGames','#Shorts'],
            'tags':['gta 6','gta vi','Justice','trilha original gta 6','score gta vi'],
            'sources':[{'url':p['url'],'title':p['title'],'checked':p['fetched_at'],'sha256':p['sha256'],
                        'published_at':p['published_at']} for p in (article,index)],
            'claims':claims,'scenes':scenes,'automatic_upload':False,'status':'ROTEIRO_AGUARDANDO_REVISAO',
            'warnings':['Voz de contingência eSpeak NG pt-BR, mais robótica que a neural pretendida. Modelo Piper bloqueado pela política de rede em us.aws.cdn.hf.co.',
                        'Não há trilha musical; o anúncio é relatado sem reproduzir gravações de Justice.',
                        'Datas obtidas do destaque da página oficial; não confundir com o momento de coleta.']}
    script['word_count']=sum(len(s['speech'].split()) for s in scenes)
    WORK.mkdir(parents=True,exist_ok=True)
    voice=LocalVoice()
    wpm=145
    for attempt in range(3):
        total=0
        for i,scene in enumerate(scenes):
            path=WORK/f'voice_{i+1:02d}.wav'
            seconds,cues=voice.speak(scene['speech'],path,wpm)
            scene.update(audio_path=str(path),audio_sha256=digest_bytes(path),captions=cues)
            total+=math.ceil((seconds+0.25)*30)/30
        print(f'Narração: {total:.2f}s, {script["word_count"]} palavras, configuração {wpm} ppm',flush=True)
        if 45<=total<=60: break
        wpm=max(100,min(190,round(wpm*total/53)))
    else: raise ValueError('Narração fora da meta de 45–60s.')
    script['voice']={'provider':'espeak_ng_local_fallback','language':'pt-br','rate_wpm':wpm,
                     'quality':'robotic_formant_not_neural','caption_alignment':'measured_word_start_events_grouped_5',
                     'license_notes':'Motor eSpeak NG incluído no Piper já instalado (GPL); fala sintética original, sem gravação de voz de terceiros.',
                     'paid_api_calls':0}
    OUT.mkdir(parents=True,exist_ok=True)
    write_json(OUT/'roteiro.json',script)
    (OUT/'descricao.txt').write_text(script['title']+'\n\n'+script['description'],encoding='utf-8')
    report='# Fontes e verificação editorial — Justice no score de GTA VI\n\nConsulta: 31/10/2026. Pauta real, sem fontes fictícias.\n\n'
    for claim in claims:
        report+=f'## {claim["key"]}\n\n**Afirmação:** {claim["statement"]}\n\n**Fonte:** {claim["source_url"]}\n\n**Evidência literal:** {claim["evidence"]}\n\n**Coleta UTC:** {claim["checked_at"]}\n\n**SHA-256 HTML:** `{claim["source_sha256"]}`\n\n'
    report+='## Limites e direitos\n\nO artigo devolve título e descrição editorial no HTML; seu corpo completo depende de JavaScript. A evidência utilizada é a descrição oficial. A data 29/10/2026 está no card correspondente da página oficial de GTA VI, não em metadados de publicação do artigo. Não afirmamos que Justice compôs todas as músicas das rádios. A frase iniciada por “Minha leitura” é interpretação editorial.\n\nA Take-Two respondeu na página atual de press-releases; a rota antiga /ir/news retornou 404. A Take-Two não foi usada para confirmar o crédito musical.\n\nSomente arte procedural própria, fontes DejaVu e voz sintética local. Nenhuma música de Justice, trailer, screenshot ou gameplay foi incorporado. A licença CC0 declarada no MODEL_CARD do Piper foi consultada, mas esse modelo NÃO foi usado porque seu download redirecionou para uma CDN bloqueada.\n\n'
    report+='## Narração\n\nVoz eSpeak NG pt-BR de contingência, já disponível localmente. Não é uma voz neural natural. Legendas agrupadas a partir dos eventos de início de palavras fornecidos pelo sintetizador, não por simples divisão proporcional do texto. A audição e a revisão humana continuam obrigatórias.\n'
    (OUT/'fontes.md').write_text(report,encoding='utf-8')
    sources=OUT/'fontes_html';sources.mkdir(exist_ok=True)
    (sources/'rockstar_score.html').write_text(article_raw)
    (sources/'rockstar_vi.html').write_text(index_raw)
    write_json(OUT/'access_checks.json',checks)
    write_json(OUT/'pending_network_change.json',{'persistence':'not_saved_draft_not_editable',
               'config':{'network':{'allowed_domains':['huggingface.co','ir.take2games.com','rockstargames.com','www.rockstargames.com','www.take2games.com','us.aws.cdn.hf.co']}}})
    manifest=render(script,OUT)
    store=Store(BASE/'editorial')
    episode={'id':ID,'format':'short','topic_key':'justice-score-20261029','claim_ids':[c['id'] for c in claims],
             'script':str(OUT/'roteiro.json'),'status':'AGUARDANDO_REVISAO_HUMANA',
             'created_at':script['created_at'],'render':str(manifest),'automatic_upload':False,'preview':False}
    with store.db:
        old=store.db.execute('SELECT status FROM episodes WHERE id=?',(ID,)).fetchone()
        if old:
            if old['status']!='AGUARDANDO_REVISAO_HUMANA': raise ValueError('Preservar episódio já revisado.')
            update_episode(store,episode)
        else:
            store.db.execute('INSERT INTO episodes VALUES (?,?,?,?,?)',(ID,episode['topic_key'],'short',episode['status'],json.dumps(episode,ensure_ascii=False)))
    store.db.close()
    print('EXPORTED',OUT/'video.mp4',flush=True)
    print('REVIEW: python factory.py --data-dir data/phase3/editorial review '+ID+' approve --checks facts,licenses,audio,subtitles,visuals --note "Sua revisão"',flush=True)


if __name__=='__main__': build()
