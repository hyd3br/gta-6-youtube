#!/usr/bin/env python3
"""GTA6 Canal Completo: research -> script -> free local voice -> review queue."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import uuid4

from gta6.editorial import get_episode, plan, review, update_episode
from gta6.research import Store, collect, now

ROOT=Path(__file__).resolve().parent


def produce(store,episode_id,voice_spec,preview=False):
    from gta6.production import render, synthesize
    episode=get_episode(store,episode_id)
    # Atomic reservation prevents two daily workers from producing the same topic.
    with store.db:
        result=store.db.execute("UPDATE episodes SET status='RENDERIZANDO' WHERE id=? AND status IN ('ROTEIRO_AGUARDANDO_REVISAO','FALHOU')",(episode_id,))
        if result.rowcount!=1: raise ValueError('Episódio em produção ou já exportado/revisado.')
    try:
        script=json.loads(Path(episode['script']).read_text())
        fresh={f['id']:f for f in store.facts()}
        for fact in script['claims']:
            if fact['id'] not in fresh or fact['source_sha256']!=fresh[fact['id']]['source_sha256']:
                raise ValueError('Evidência vencida ou alterada. Atualize a pesquisa e revise o roteiro.')
        attempt=uuid4().hex[:10]
        folder=ROOT/'output'/'aguardando_revisao'/(episode_id+'-'+attempt)
        voiced=synthesize(script,voice_spec,store.folder/'episodes'/episode_id/('voice-'+attempt))
        if script['format']=='long' and not preview:
            # Always perform the repository-required low-res 2-scene preview first.
            render(voiced,folder.with_name(folder.name+'-preview'),preview=True)
        manifest=render(voiced,folder,preview=preview)
        episode['render']=str(manifest)
        episode['status']='AGUARDANDO_REVISAO_HUMANA'
        episode['preview']=preview
        update_episode(store,episode)
        return episode
    except Exception as e:
        episode['status']='FALHOU'
        episode['last_error']=type(e).__name__+': '+str(e)[:250]
        update_episode(store,episode)
        raise


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-dir',type=Path,default=ROOT/'data')
    sub=ap.add_subparsers(dest='command',required=True)
    research=sub.add_parser('research',help='Coleta somente fontes primárias; não usa API paga.')
    research.add_argument('--config',type=Path,default=ROOT/'config/sources.json')
    sub.add_parser('topics',help='Mostra fatos citáveis e perguntas editoriais para investigação.')
    p=sub.add_parser('plan',help='Cria roteiro original a partir de fatos recentes, sem LLM pago.')
    p.add_argument('--format',choices=['short','long'],required=True)
    sub.add_parser('queue')
    p=sub.add_parser('produce',help='Piper local e visuais próprios; nunca faz upload.')
    p.add_argument('episode_id')
    p.add_argument('--voice-spec',type=Path,required=True)
    p.add_argument('--preview',action='store_true')
    p=sub.add_parser('review')
    p.add_argument('episode_id')
    p.add_argument('decision',choices=['approve','reject'])
    p.add_argument('--note',required=True)
    p.add_argument('--checks',default='',help='Para aprovar: facts,licenses,audio,subtitles,visuals')
    p=sub.add_parser('daily',help='Uma rodada, sem agendar ou publicar. Falha fechada se a coleta falhar.')
    p.add_argument('--config',type=Path,default=ROOT/'config/sources.json')
    p.add_argument('--format',choices=['short','long'],default='short')
    p.add_argument('--voice-spec',type=Path,required=True)
    args=ap.parse_args(argv)
    store=Store(args.data_dir)
    try:
        if args.command in ('research','daily'):
            config=json.loads(args.config.read_text())
            report=collect(store,config['seeds'],config.get('max_pages',12))
            print(json.dumps(report,ensure_ascii=False,indent=2))
            if not report['pages'] or not report['fresh_facts'] or report['errors']:
                print('Pesquisa incompleta. Não serão inventados fatos nem iniciada produção diária.',file=sys.stderr)
                return 2
            if args.command=='research': return 0
        if args.command=='topics':
            facts=store.facts()
            result={'confirmed':facts,'analysis_questions':[
                {'question':f'Qual é o alcance da evidência: {f["headline"]}?','claim_ids':[f['id']],
                 'classification':'analysis','potential':'Explicar um fato e seus limites sem prometer mecânicas.'} for f in facts],
                'rumors':[],'note':'Rumores não são extraídos como confirmações. Pautas especulativas exigem curadoria humana.'}
        elif args.command in ('plan','daily'):
            result=plan(store,args.format)
            if args.command=='daily': result=produce(store,result['id'],args.voice_spec)
        elif args.command=='produce': result=produce(store,args.episode_id,args.voice_spec,args.preview)
        elif args.command=='review': result=review(store,args.episode_id,args.decision,args.note,args.checks.split(',') if args.checks else [])
        elif args.command=='queue':
            result=[{**json.loads(row['body']),'status':row['status']} for row in store.db.execute('SELECT status,body FROM episodes ORDER BY id')]
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    finally:
        store.db.close()


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError,sqlite3.Error,subprocess.CalledProcessError) as e:
        print('ERRO:',str(e),file=sys.stderr)
        raise SystemExit(1)
