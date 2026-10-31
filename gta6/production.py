"""Free neural narration and animated exports using the existing audiovisual primitives."""
from __future__ import annotations

import importlib.metadata
import json
import math
from pathlib import Path
import re
import subprocess
import wave

import make_long as long_renderer
import make_short as short_renderer

from .editorial import digest_bytes, write_json
from .research import digest, now

ROOT=Path(__file__).resolve().parent.parent


def run(args):
    subprocess.run([str(a) for a in args],check=True,cwd=ROOT)


def media_info(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],text=True))


def check_media(path,width,height):
    probe=media_info(path)
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    if (video['codec_name'],video['width'],video['height'])!=('h264',width,height) or audio['codec_name']!='aac':
        raise ValueError('Formato final inesperado: exige H.264/AAC e resolução solicitada.')
    if float(probe['format']['duration'])<=0: raise ValueError('Vídeo sem duração.')
    run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',path,'-f','null','-'])
    return probe


def voice_segments(text,max_words=14):
    """Bounded caption/voice chunks; boundaries measured from each synthesized WAV."""
    result=[]
    for sentence in re.split(r'(?<=[.!?;:])\s+',text.strip()):
        words=sentence.split()
        for i in range(0,len(words),max_words):
            result.append(' '.join(words[i:i+max_words]))
    if not result: raise ValueError('Texto de narração vazio.')
    return result


def load_voice_spec(path):
    spec_path=Path(path).resolve()
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    for field in ('model','model_sha256','config_sha256','license_url','license_notes'):
        if not spec.get(field): raise ValueError(f'Configuração de voz exige {field}.')
    model=(spec_path.parent/spec['model']).resolve()
    config=Path(str(model)+'.json')
    if not model.is_file() or not config.is_file(): raise ValueError('Modelo Piper ou configuração ausente.')
    if digest_bytes(model)!=spec['model_sha256'] or digest_bytes(config)!=spec['config_sha256']:
        raise ValueError('Checksum do modelo/configuração não corresponde ao registro de licença.')
    conf=json.loads(config.read_text())
    if conf.get('language',{}).get('code') not in ('pt_BR','pt-BR'):
        raise ValueError('A voz deve ser pt-BR.')
    return spec,model


def synthesize(script,voice_spec,folder):
    """No API calls, no implicit model downloads, no charges."""
    spec,model=load_voice_spec(voice_spec)
    from piper import PiperVoice, SynthesisConfig
    voice=PiperVoice.load(model,use_cuda=False)
    # Bound local CPU usage while encoding may be running elsewhere.
    cache=ROOT/'work'/'tts_cache'
    cache.mkdir(parents=True,exist_ok=True)
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    result=json.loads(json.dumps(script))
    for i,scene in enumerate(result['scenes']):
        chunks=[]
        pcm=[]
        rate=None
        start=0.0
        for text in voice_segments(scene['speech']):
            key=digest(json.dumps({'text':text,'model':spec['model_sha256'],
                                   'config':spec['config_sha256'],'piper':importlib.metadata.version('piper-tts'),
                                   'length_scale':1.0},sort_keys=True))
            wav=cache/(key+'.wav')
            if not wav.exists():
                temp=wav.with_suffix('.tmp.wav')
                with wave.open(str(temp),'wb') as out:
                    voice.synthesize_wav(text,out,SynthesisConfig(length_scale=1.0))
                temp.replace(wav)
            with wave.open(str(wav),'rb') as part:
                if part.getnchannels()!=1 or part.getsampwidth()!=2:
                    raise ValueError('Formato de voz Piper inesperado.')
                rate=rate or part.getframerate()
                if rate!=part.getframerate(): raise ValueError('Taxa de áudio inconsistente.')
                frames=part.readframes(part.getnframes())
                length=part.getnframes()/rate
            pcm.append(frames)
            chunks.append({'text':text,'start':round(start,6),'end':round(start+length,6)})
            start+=length
        audio=folder/f'voice_{i+1:02d}.wav'
        with wave.open(str(audio),'wb') as out:
            out.setnchannels(1); out.setsampwidth(2); out.setframerate(rate)
            for frames in pcm: out.writeframes(frames)
        scene['audio_path']=str(audio.resolve())
        scene['captions']=chunks
        scene['audio_sha256']=digest_bytes(audio)
    result['voice']={'provider':'piper_local','model_sha256':spec['model_sha256'],
                     'license_url':spec['license_url'],'license_notes':spec['license_notes'],
                     'caption_alignment':'measured_synthesized_segments_not_word_level'}
    write_json(folder/'script_voiced.json',result)
    return result


def srt_text(cues):
    return '\n'.join(f'{i+1}\n{long_renderer.tcode(c["start"],srt=True)} --> {long_renderer.tcode(c["end"],srt=True)}\n{c["text"]}\n'
                     for i,c in enumerate(cues))


def validate_cues(cues,duration):
    previous=0.0
    if not cues: raise ValueError('Legendas medidas ausentes.')
    for c in cues:
        if not c.get('text') or not previous<=c['start']<c['end']<=duration+0.02:
            raise ValueError('Legendas fora dos limites ou sobrepostas.')
        previous=c['end']


def render(script,folder,*,preview=False,preset='veryfast'):
    """One H.264 encode per scene; concatenate/mux without a second video encode."""
    folder=Path(folder).resolve()
    if ROOT not in folder.parents: raise ValueError('Exportação deve ficar dentro do projeto.')
    if (folder/'manifest.json').exists() or (folder/'video.mp4').exists():
        raise ValueError('Saída já existe. Use outra pasta; não sobrescrevemos revisões.')
    folder.mkdir(parents=True,exist_ok=True)
    if script.get('format') not in ('short','long'): raise ValueError('Formato inválido.')
    if not script.get('scenes') or len(script['scenes'])>36:
        raise ValueError('Roteiro precisa ter entre 1 e 36 cenas.')
    is_short=script['format']=='short'
    w,h=(1080,1920) if is_short else ((640,360) if preview else (1920,1080))
    fps=24 if preview else 30
    work=ROOT/'work'/('phase2_'+digest(str(folder))[:16])
    work.mkdir(parents=True,exist_ok=True)
    scenes=script['scenes'][:2] if preview else script['scenes']
    audios=[]; lengths=[]; all_cues=[]; clips=[]
    elapsed=0.0
    for i,scene in enumerate(scenes):
        # Phase 2 deliberately uses original procedural visuals; never downloads trailers.
        if scene.get('image_path') or scene.get('video_path'):
            raise ValueError('Este perfil usa arte original. Mídias externas devem passar pela revisão de licença do renderer existente.')
        if not scene.get('license_notes'): raise ValueError('Cena sem registro de licença visual.')
        audio=Path(scene['audio_path'])
        if digest_bytes(audio)!=scene['audio_sha256']: raise ValueError('Áudio mudou após alinhamento.')
        seconds=long_renderer.duration(audio)
        cues=scene['captions']
        validate_cues(cues,seconds)
        duration=math.ceil((seconds+0.25)*fps)/fps
        lengths.append(duration); audios.append(audio)
        for c in cues: all_cues.append({**c,'start':c['start']+elapsed,'end':c['end']+elapsed})
        elapsed+=duration
        still=work/f'scene_{i:02d}.png'
        if is_short:
            short_renderer.scene_image({**scene,'speech':'FONTES E DATA NA DESCRIÇÃO'},i,len(scenes),w,h,still)
        else:
            long_renderer.make_slide(scene,i,len(scenes),ROOT/'script.json',w,h,still,work/f'overlay_{i:02d}.png')
        captions=work/f'captions_{i:02d}.srt'
        captions.write_text(srt_text(cues),encoding='utf-8')
        # A gentle moving crop plus short fades, hard cuts between editorial scenes.
        style=("Fontname=DejaVu Sans,Fontsize=9,Outline=1,Shadow=0,Alignment=2,MarginV=42,MarginL=18,MarginR=18"
               if is_short else "Fontname=DejaVu Sans,Fontsize=19,Outline=2,Shadow=0,Alignment=2,MarginV=36")
        relative=captions.relative_to(ROOT).as_posix()
        vf=(f'scale={w+40}:{h+40},crop={w}:{h}:x=20+18*sin(t*0.30):y=20+18*cos(t*0.23),'
            f"subtitles=filename='{relative}':force_style='{style}',"
            f'fade=t=in:d=0.12,fade=t=out:st={max(0,duration-0.12):.3f}:d=0.12,format=yuv420p')
        clip=work/f'segment_{i:02d}.mp4'
        print(f'Render {i+1}/{len(scenes)}: {duration:.1f}s {w}x{h}',flush=True)
        run(['ffmpeg','-y','-hide_banner','-loglevel','error','-loop','1','-framerate',fps,
             '-i',still,'-t',f'{duration:.6f}','-vf',vf,'-an','-c:v','libx264',
             '-threads','2','-preset',preset,'-crf','24','-r',fps,clip])
        clips.append(clip)
    narration=work/'narration.wav'
    long_renderer.merge_audio(audios,lengths,narration)
    sequence=work/'sequence.txt'
    sequence.write_text(''.join("file '"+str(p).replace("'","'\\''")+"'\n" for p in clips))
    output=folder/'video.mp4'
    run(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',sequence,
         '-i',narration,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k',
         '-movflags','+faststart','-shortest',output])
    probe=check_media(output,w,h)
    actual_seconds=float(probe['format']['duration'])
    (folder/'video.srt').write_text(srt_text(all_cues),encoding='utf-8-sig')
    long_renderer.create_thumbnail(script,folder/'thumbnail.jpg')
    chapters=long_renderer.chapter_file(scenes,lengths,folder/'capitulos.txt')
    warnings=['Imagens ilustrativas originais; não são capturas oficiais.',
              'Legendas medidas por segmento sintetizado, não palavra por palavra.',
              'Ouvir e revisar a naturalidade, os fatos e as licenças antes de aprovar.']
    if not is_short and not preview and not 360<=actual_seconds<=720:
        warnings.append('Duração real fora da meta de 6–12 minutos; revisar roteiro/ritmo sem preencher artificialmente.')
    metadata={**script,'scenes':scenes,'duration_seconds':actual_seconds,
              'resolution':f'{w}x{h}','frames_per_second':fps,'chapters':chapters,
              'preview':preview,'status':'AGUARDANDO_REVISAO_HUMANA','automatic_upload':False,
              'warnings':warnings}
    write_json(folder/'metadata.json',metadata)
    (folder/'revisao.md').write_text('# Revisão humana obrigatória\n\n'+
        '\n'.join('- [ ] '+t for t in ('Fatos e datas confrontados com fontes','Licenças de voz e arte',
                                      'Narração natural e inteligível','Sincronismo de legendas','Legibilidade e edição'))+
        '\n\nNão há publicação automática. Use factory.py review após assistir ao vídeo.\n',encoding='utf-8')
    manifest={'created_at':now(),'automatic_upload':False,'status':'AGUARDANDO_REVISAO_HUMANA',
              'artifact_sha256':{p.name:digest_bytes(p) for p in folder.iterdir() if p.is_file()}}
    write_json(folder/'manifest.json',manifest)
    return folder/'manifest.json'
