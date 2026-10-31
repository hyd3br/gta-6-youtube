#!/usr/bin/env python3
"""GTA6 Shorts + Long Factory: renderer de vídeos horizontais para revisão humana.

- Vídeo 16:9, voz por cena, legendas SRT aproximadas, capítulos e thumbnail.
- Mídia: gráficos originais ou arquivos locais com licença/autorizações registradas.
- Não faz web scraping nem publica em nenhuma plataforma.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def cmdrun(args: list[str], *, cwd=ROOT, quiet=False):
    print('>', ' '.join(str(t) for t in args[:9]) + (' ...' if len(args) > 9 else ''))
    result = subprocess.run(args, cwd=cwd, capture_output=quiet, text=True if quiet else None)
    if result.returncode:
        if quiet:
            print(result.stderr[-4000:])
        raise RuntimeError('Falha no comando externo; confira a mensagem acima.')
    return result


def duration(path: Path) -> float:
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def tcode(sec: float, *, srt=False) -> str:
    ms = max(0, round(sec * 1000))
    hh, rem = divmod(ms, 3600000)
    mm, rem = divmod(rem, 60000)
    ss, msec = divmod(rem, 1000)
    return f'{hh:02d}:{mm:02d}:{ss:02d},{msec:03d}' if srt else (f'{hh:02d}:{mm:02d}:{ss:02d}' if hh else f'{mm:02d}:{ss:02d}')


def resolve_asset(script_file: Path, path_string: str) -> Path:
    p = (script_file.parent / path_string).resolve()
    if not p.is_file():
        raise ValueError(f'Arquivo de mídia/áudio ausente: {p}')
    return p


def choose_font(bold=False):
    choices = ([
        'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/segoeuib.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    ] if bold else [
        'C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/segoeui.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ])
    for item in choices:
        if Path(item).exists():
            return item
    raise RuntimeError('Arial, Segoe UI ou DejaVu Sans não encontrada.')


def fnt(px, bold=False):
    return ImageFont.truetype(choose_font(bold), max(12, int(px)))


def wrap(d: ImageDraw.ImageDraw, txt: str, ft, max_w: int) -> list[str]:
    output = []
    for para in txt.split('\n'):
        line = ''
        for word in para.split():
            attempt = (line + ' ' + word).strip()
            if d.textbbox((0, 0), attempt, font=ft)[2] <= max_w:
                line = attempt
            else:
                if line:
                    output.append(line)
                line = word
        if line:
            output.append(line)
    return output


def background(w: int, h: int, idx: int) -> Image.Image:
    """Paisagem procedural original, reutilizável sem fotos de terceiros."""
    out = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(out)
    for y in range(0, h, 3):
        t = y / h
        d.rectangle((0, y, w, min(y + 3, h)), fill=(int(11+29*t), int(13+9*t), int(35+38*t)))
    glow = Image.new('RGBA', (w, h))
    g = ImageDraw.Draw(glow)
    g.ellipse((int(w*.48), int(h*.1), int(w*.98), int(h*.94)), fill=(220, 48, 178, 77))
    g.ellipse((int(w*-.13), int(h*.27), int(w*.38), int(h*.95)), fill=(0, 228, 238, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(max(15, w//28)))
    out = Image.alpha_composite(out.convert('RGBA'), glow)
    d = ImageDraw.Draw(out, 'RGBA')
    sx, sy, rad = int(w*.73), int(h*.57), int(h*.28)
    d.ellipse((sx-rad, sy-rad, sx+rad, sy+rad), fill=(239, 75, 159, 76))
    rng = random.Random(202610 + idx)
    x = 0
    while x < w:
        bw = rng.randrange(max(23,w//45), max(40,w//21))
        top = int(h * rng.uniform(.58, .85))
        d.rectangle((x, top, x+bw, h), fill=(6,9,25,246))
        for wy in range(top + 12, h - 10, max(12,h//40)):
            for wx in range(x+7,x+bw-5,max(9,w//100)):
                if rng.random() > .68:
                    d.rectangle((wx,wy,wx+3,wy+5),fill=(236,81,178,125))
        x += bw + rng.randrange(0,max(2,w//140))
    return out.convert('RGB')


def cover_background(scene: dict, script_file: Path, w: int, h: int, i: int) -> Image.Image:
    src = scene.get('image_path')
    if not src:
        return background(w, h, i)
    image_path = resolve_asset(script_file, src)
    with Image.open(image_path) as image:
        img = ImageOps.fit(image.convert('RGB'), (w, h), method=Image.Resampling.LANCZOS)
    # escurecer imagem para proteger legibilidade
    shade = Image.new('RGBA', (w, h), (0,0,18,100))
    return Image.alpha_composite(img.convert('RGBA'), shade).convert('RGB')


def overlay(scene: dict, i: int, count: int, w: int, h: int) -> Image.Image:
    img = Image.new('RGBA', (w,h), (0,0,0,0))
    d = ImageDraw.Draw(img, 'RGBA')
    pad = int(w*.06)
    upper = int(h*.08)
    d.rounded_rectangle((pad,upper,pad+int(w*.012),int(h*.45)),radius=max(3,w//430),fill=(50,232,243,255))
    d.rounded_rectangle((pad+int(w*.035), upper-int(h*.005), pad+int(w*.21), upper+int(h*.042)), radius=int(h*.016),fill=(12,17,43,224))
    d.text((pad+int(w*.05),upper+int(h*.006)), 'GTA 6  /  ANÁLISE',font=fnt(h*.021,True),fill=(107,229,245,255))
    pct_rect = (pad, int(h*.962), w-pad, int(h*.971))
    d.rounded_rectangle(pct_rect,radius=5,fill=(237,231,255,55))
    d.rounded_rectangle((pct_rect[0],pct_rect[1],pct_rect[0]+(pct_rect[2]-pct_rect[0])*(i+1)/count,pct_rect[3]),radius=5,fill=(249,79,169,240))
    title = scene['headline'].upper()
    fs = int(h*.085)
    while fs > int(h*.050):
        ft = fnt(fs,True)
        lines = wrap(d,title,ft,int(w*.77))
        if len(lines)<=3:
            break
        fs -= 2
    yy = int(h*.265)
    for line in lines[:3]:
        d.text((pad+int(w*.04)+3,yy+4),line,font=ft,fill=(0,0,0,170))
        d.text((pad+int(w*.04),yy),line,font=ft,fill=(255,255,255,255))
        yy += fs*1.22
    take = scene.get('takeaway','').strip()
    if take:
        hbar = int(h*.10)
        yy = int(h*.59)
        d.rounded_rectangle((pad+int(w*.04),yy,w-pad-int(w*.07), yy+hbar),radius=max(10,int(h*.018)),fill=(9,12,32,219),outline=(137,87,196,188),width=max(1,int(h*.003)))
        ff = fnt(h*.035,True)
        while d.textbbox((0,0), take, font=ff)[2] > w*.71 and ff.size > int(h*.022):
            ff = fnt(ff.size-1,True)
        d.text((pad+int(w*.065),yy+int(h*.029)), take, font=ff,fill=(240,238,251,255))
    small = fnt(h*.016)
    d.text((int(w*.72),int(h*.088)), 'VISUAL ILUSTRATIVO',font=small,fill=(210,207,225,225))
    return img


def make_slide(scene, idx, count, script_file, w,h, imgpath, overlaypath):
    mask = overlay(scene,idx,count,w,h)
    mask.save(overlaypath, 'PNG')
    bg = cover_background(scene,script_file,w,h,idx)
    Image.alpha_composite(bg.convert('RGBA'), mask).convert('RGB').save(imgpath, 'PNG', optimize=True)


def split_subtitle(text: str, max_words=10) -> list[str]:
    words = text.split()
    return [' '.join(words[i:i+max_words]) for i in range(0,len(words),max_words)]


def subtitles(scenes, lengths, voice_lengths, dest: Path):
    start = 0.0
    n = 1
    records = []
    for scene, segment_length, voice_length in zip(scenes,lengths,voice_lengths):
        chunks = split_subtitle(scene['speech'])
        weights = [max(1,len(t.replace(' ',''))) for t in chunks]
        total = sum(weights)
        cursor = start
        for idx,(chunk,weight) in enumerate(zip(chunks,weights)):
            end = start + voice_length if idx==len(chunks)-1 else cursor + voice_length*weight/total
            records.append(f'{n}\n{tcode(cursor,srt=True)} --> {tcode(end,srt=True)}\n{chunk}\n')
            cursor = end
            n += 1
        start += segment_length
    dest.write_text('\n'.join(records),encoding='utf-8-sig')


def chapter_file(scenes, lengths, dest):
    elapsed = 0.0
    chapters = []
    for scene, section_duration in zip(scenes,lengths):
        if scene.get('chapter'):
            chapters.append({'time_seconds':round(elapsed,1),'label':scene['chapter']})
        elapsed += section_duration
    if not chapters or chapters[0]['time_seconds'] != 0:
        chapters.insert(0,{'time_seconds':0,'label':'Abertura'})
    dest.write_text('\n'.join(f'{tcode(c["time_seconds"])} {c["label"]}' for c in chapters)+'\n', encoding='utf-8')
    return chapters


def create_windows_voice(text: str, target: Path, work: Path):
    ps = ROOT / 'tools' / 'tts_windows.ps1'
    if not ps.is_file():
        raise RuntimeError('tools/tts_windows.ps1 ausente.')
    interpreter = shutil.which('powershell.exe') or shutil.which('powershell')
    if not interpreter:
        raise RuntimeError('TTS Windows precisa de Windows PowerShell 5.1; use --tts bundled ou --tts openai.')
    txt = work / (target.stem+'.txt')
    txt.write_text(text, encoding='utf-8-sig')
    cmdrun([interpreter, '-NoProfile','-ExecutionPolicy','Bypass','-File',str(ps),'-TextFile',str(txt),'-OutputFile',str(target)])


def create_api_voice(text: str, target: Path):
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('Sem OPENAI_API_KEY. Configure localmente no .env e não envie sua chave a ninguém.')
    if len(text)>4000:
        raise ValueError('Uma cena ultrapassa 4.000 caracteres: divida-a em duas cenas menores para a Speech API.')
    from openai import OpenAI
    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=os.getenv('OPENAI_TTS_MODEL','gpt-4o-mini-tts'),
        voice=os.getenv('OPENAI_TTS_VOICE','coral'),
        input=text,
        instructions='Narração em português brasileiro, ritmo de vídeo jornalístico de games, dicção clara, energia moderada.',
    ) as response:
        response.stream_to_file(target)


def get_voice(scene, idx, script_file: Path, work: Path, tts: str):
    if tts == 'bundled':
        if script_file.resolve() != (ROOT / 'roteiro_longo_exemplo.json').resolve():
            raise ValueError('Modo bundled só funciona com roteiro_longo_exemplo.json sem modificar o texto.')
        manifest = json.loads((ROOT/'demo_audio_long'/'manifest.json').read_text(encoding='utf-8'))
        expected = manifest['scenes'][idx]
        if hashlib.sha256(scene['speech'].encode('utf-8')).hexdigest() != expected:
            raise ValueError(f'Cena {idx+1} modificada: a voz demo não corresponde. Use --tts windows, openai ou files.')
        out = ROOT / 'demo_audio_long' / f'cena_{idx+1:02d}.mp3'
        if not out.exists():
            raise ValueError(f'Falta arquivo demo de áudio: {out}')
        return out
    if tts == 'files':
        if not scene.get('audio_path'):
            raise ValueError(f'Cena {idx+1} sem audio_path (necessário no modo files).')
        return resolve_asset(script_file,scene['audio_path'])
    sig = hashlib.sha256((scene['speech'] + '|' + tts + '|' + os.getenv('OPENAI_TTS_MODEL','') + '|' + os.getenv('OPENAI_TTS_VOICE','')).encode()).hexdigest()[:12]
    out = work / f'voz_{idx+1:02d}_{sig}.{ "mp3" if tts=="openai" else "wav"}'
    if not out.exists():
        if tts=='windows':
            create_windows_voice(scene['speech'],out,work)
        else:
            create_api_voice(scene['speech'],out)
    return out


def merge_audio(audios, section_durations, dest):
    inputs = []
    pieces = []
    for i,(audio,d) in enumerate(zip(audios,section_durations)):
        inputs += ['-i',str(audio)]
        pieces.append(f'[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,apad,atrim=duration={d:.6f},asetpts=PTS-STARTPTS[a{i}]')
    pieces.append(''.join(f'[a{i}]' for i in range(len(audios))) + f'concat=n={len(audios)}:v=0:a=1[out]')
    cmdrun(['ffmpeg','-y','-hide_banner','-loglevel','error',*inputs,'-filter_complex',';'.join(pieces),'-map','[out]','-ar','48000','-ac','2','-c:a','pcm_s16le',str(dest)])


def render_scene(scene, seconds, still_png, overlay_png, script_file, w,h,fps, dest, preset, crf):
    common=['-r',str(fps),'-an','-c:v','libx264','-preset',preset,'-crf',str(crf),'-pix_fmt','yuv420p','-movflags','+faststart',str(dest)]
    if scene.get('video_path'):
        media=resolve_asset(script_file,scene['video_path'])
        fil=(f'[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps}[bg];'
             f'[1:v]format=rgba[mask];[bg][mask]overlay=0:0:shortest=1[v]')
        cmdrun(['ffmpeg','-y','-hide_banner','-loglevel','error','-stream_loop','-1','-i',str(media),'-loop','1','-framerate',str(fps),'-i',str(overlay_png),'-t',f'{seconds:.3f}', '-filter_complex',fil,'-map','[v]',*common])
    else:
        cmdrun(['ffmpeg','-y','-hide_banner','-loglevel','error','-loop','1','-framerate',str(fps),'-i',str(still_png),'-t',f'{seconds:.3f}',*common])


def create_thumbnail(data, out, w=1280,h=720):
    img = background(w,h,221)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((65,65,390,130),radius=20,fill=(15,16,37))
    d.text((90,82),'GTA 6  /  ANÁLISE',font=fnt(36,True),fill=(67,231,241))
    title = data.get('thumbnail_title','GTA 6: ANÁLISE').upper()
    size=92
    while size>=48:
        ft=fnt(size,True)
        lines=wrap(d,title,ft,1080)
        if len(lines)<=3:
            break
        size-=3
    y=235
    for line in lines[:3]:
        d.text((83,y+6),line,font=ft,fill=(0,0,0))
        d.text((78,y),line,font=ft,fill='white')
        y+=size*1.22
    img.save(out, quality=88, subsampling=0)


def main():
    ap=argparse.ArgumentParser(description='GTA 6 Factory — vídeos longos 16:9 para revisão humana')
    ap.add_argument('--script',default='roteiro_longo_exemplo.json')
    ap.add_argument('--tts',choices=['bundled','windows','files','openai'],default='bundled')
    ap.add_argument('--output',default='output/aguardando_revisao/gta6_analise_longa.mp4')
    ap.add_argument('--width',type=int,default=1920)
    ap.add_argument('--height',type=int,default=1080)
    ap.add_argument('--fps',type=int,default=30)
    ap.add_argument('--pause',type=float,default=0.4)
    ap.add_argument('--preview-scenes',type=int,default=0,help='0 = todas as cenas; número = render parcial para teste')
    ap.add_argument('--music',help='Arquivo local de trilha com licença/autorização válida')
    ap.add_argument('--music-license-note',help='Texto da licença/permissão de uso da trilha')
    ap.add_argument('--music-volume',type=float,default=0.08)
    ap.add_argument('--no-burn-subtitles',action='store_true')
    ap.add_argument('--preset',default='veryfast',choices=['ultrafast','superfast','veryfast','faster','fast','medium'])
    ap.add_argument('--crf',type=int,default=24)
    ap.add_argument('--dry-run',action='store_true',help='Verifica roteiro sem renderizar nem cobrar API')
    args=ap.parse_args()
    load_dotenv(ROOT/'.env')
    if args.fps<12 or args.width<480 or args.height<270 or abs(args.width/args.height-16/9)>0.025:
        sys.exit('Erro: use resolução 16:9 com no mínimo 480x270 e FPS >= 12.')
    if not 0 <= args.music_volume <= 0.4:
        sys.exit('Erro: music-volume deve ficar entre 0 e 0.4 para preservar a voz.')
    if args.music and not args.music_license_note:
        sys.exit('Erro: registre --music-license-note para usar trilha de terceiros.')
    script_file=(ROOT/args.script).resolve()
    data=json.loads(script_file.read_text(encoding='utf-8'))
    all_scenes=data.get('scenes',[])
    if not 2<=len(all_scenes)<=36:
        sys.exit('Erro: o roteiro longo exige de 2 a 36 cenas.')
    scenes=all_scenes[:args.preview_scenes] if args.preview_scenes else all_scenes
    if len(scenes)<1:
        sys.exit('Erro: preview-scenes inválido.')
    for i,sc in enumerate(scenes):
        if not isinstance(sc,dict) or not sc.get('headline') or not sc.get('speech'):
            sys.exit(f'Erro: cena {i+1} sem headline ou speech.')
        if len(sc['speech'])>4000 and args.tts=='openai':
            sys.exit(f'Erro: cena {i+1} excede 4000 caracteres para a Speech API.')
        if sc.get('image_path') and sc.get('video_path'):
            sys.exit(f'Erro: cena {i+1}: use image_path OU video_path.')
        if (sc.get('image_path') or sc.get('video_path')) and not sc.get('license_notes'):
            sys.exit(f'Erro: cena {i+1} com mídia externa requer license_notes e autorização de uso.')
        for field in ('image_path','video_path'):
            if sc.get(field):
                resolve_asset(script_file,sc[field])
    words=sum(len(s['speech'].split()) for s in scenes)
    print(f'Roteiro validado: {len(scenes)} cenas, {words} palavras; estimativa {words/145:.1f} min de fala (145 ppm).')
    if args.dry_run:
        print('Validação concluída. Não gerou vídeo nem chamou APIs.')
        return
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        sys.exit('Instale FFmpeg e FFprobe e reabra o terminal.')
    out=(ROOT/args.output).resolve()
    if ROOT not in out.parents:
        sys.exit('A saída deve ficar dentro da pasta do projeto.')
    out.parent.mkdir(parents=True,exist_ok=True)
    work=ROOT/'work'/out.stem
    work.mkdir(parents=True,exist_ok=True)
    all_audios=[]; all_lengths=[]; voice_lengths=[]; stills=[]; masks=[]
    for i,sc in enumerate(scenes):
        voice=get_voice(sc,i,script_file,work,args.tts)
        seconds=duration(voice)
        voice_lengths.append(seconds)
        section_len=math.ceil((seconds+args.pause)*args.fps)/args.fps
        all_lengths.append(section_len)
        all_audios.append(voice)
        still=work/f'frame_{i+1:02d}.png'
        mask=work/f'overlay_{i+1:02d}.png'
        make_slide(sc,i,len(scenes),script_file,args.width,args.height,still,mask)
        stills.append(still); masks.append(mask)
        print(f'Cena {i+1}/{len(scenes)}: {section_len:.1f}s')
    narration=work/'voz_completa.wav'
    merge_audio(all_audios,all_lengths,narration)
    srt=out.with_suffix('.srt')
    subtitles(scenes,all_lengths,voice_lengths,srt)
    # ffmpeg libass lê o caminho relativo à raiz do projeto, independente da unidade do Windows.
    subtitles_rel=(work/'legendas.srt')
    shutil.copyfile(srt,subtitles_rel)
    chapters=chapter_file(scenes,all_lengths,out.with_name(out.stem+'_capitulos.txt'))
    thumb=out.with_name(out.stem+'_thumbnail.jpg')
    create_thumbnail(data,thumb)
    # Preparação de segmentos. Largos vídeos de terceiros são incluídos só quando autorizados.
    clips=[]
    for i,(sc,t,still,mask) in enumerate(zip(scenes,all_lengths,stills,masks)):
        clip=work/f'seg_{i+1:02d}.mp4'
        render_scene(sc,t,still,mask,script_file,args.width,args.height,args.fps,clip,args.preset,args.crf)
        clips.append(clip)
    concat=work/'sequencia.txt'
    # ffmpeg concat demuxer: nomes absolutos com barras, escapando apóstrofos
    concat.write_text(''.join("file '"+str(p.as_posix()).replace("'","'\\''")+"'\n" for p in clips),encoding='utf-8')
    raw=work/'video_sem_audio.mp4'
    cmdrun(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(raw)])
    final_inputs=['-i',str(raw),'-i',str(narration)]
    final_filter=[]
    aud_map='1:a:0'
    if args.music:
        music=resolve_asset(script_file,args.music)
        final_inputs+=['-stream_loop','-1','-i',str(music)]
        final_filter += [f'[1:a]volume=1.0[voc];[2:a]volume={args.music_volume:.3f}[mus];[voc][mus]amix=inputs=2:duration=first:dropout_transition=0[mix]']
        aud_map='[mix]'
    vf=[]
    if not args.no_burn_subtitles:
        # SRT com frases aproximadas; para sincronismo palavra-a-palavra é preciso alinhamento forçado.
        vf=[f"subtitles=filename='{subtitles_rel.relative_to(ROOT).as_posix()}':force_style='Fontname=Arial,Fontsize=19,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=67'"]
    final_cmd=['ffmpeg','-y','-hide_banner','-loglevel','error',*final_inputs]
    if final_filter:
        final_cmd+=['-filter_complex',';'.join(final_filter)]
    if vf:
        final_cmd+=['-vf',','.join(vf)]
    final_cmd+=['-map','0:v:0','-map',aud_map,
                '-c:v','libx264' if vf else 'copy']
    if vf:
        final_cmd+=['-preset',args.preset,'-crf',str(args.crf),'-pix_fmt','yuv420p']
    final_cmd+=['-c:a','aac','-b:a','160k','-ar','48000','-movflags','+faststart','-shortest',str(out)]
    cmdrun(final_cmd)
    total=duration(out)
    notices=[]
    if not 360<=total<=720:
        notices.append(f'Duração {total/60:.1f} minutos fora da meta editorial de 6–12 minutos; revisar conteúdo e ritmo.')
    if args.preview_scenes:
        notices.append('Prévia parcial: não é o vídeo completo para publicação.')
    if args.tts=='bundled':
        notices.append('Narração de demonstração com voz robótica. Trocar por TTS natural antes de publicar.')
    notices.append('Legendas distribuídas proporcionalmente à fala; revisar a sincronização e corrigir no editor se necessário.')
    notices.append('Conferir informações e direitos de todas as mídias antes de qualquer publicação.')
    info={
        'title':data.get('title','GTA 6 — Análise'),
        'description':data.get('description','')+'\n\nFontes consultadas:\n'+ '\n'.join(f'- {src.get("title","Fonte")}: {src.get("url","")}' for src in data.get('sources',[])) +
            ('\n\nTrilha: '+args.music_license_note if args.music else '')+'\n\nEste vídeo contém narração sintética gerada por IA.',
        'tags':data.get('tags',[]),
        'sources':data.get('sources',[]),
        'chapters':chapters,
        'duration_seconds':round(total,2),'resolution':f'{args.width}x{args.height}',
        'frames_per_second':args.fps,'speech_provider':args.tts,
        'video':str(out.relative_to(ROOT)),
        'thumbnail':str(thumb.relative_to(ROOT)),
        'subtitles':str(srt.relative_to(ROOT)),
        'status':'AGUARDANDO_REVISAO_HUMANA',
        'automatic_upload':False,
        'warnings':notices,
    }
    out.with_suffix('.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    report=out.with_name(out.stem+'_revisao.md')
    checkboxes=['Áudio inteligível e sem cortes','Legendas conferidas e sincronizadas','Fatos e datas confirmados nas fontes','Teorias identificadas como especulação','Mídias e música com direitos de uso verificados','Miniatura, título e capítulos corretos','Revisão final no YouTube Studio antes da publicação']
    report.write_text('# Revisão editorial — '+info['title']+'\n\n**Status:** AGUARDANDO_REVISAO_HUMANA\n\n'+
        f'**Duração:** {tcode(total)} | **Vídeo:** {info["resolution"]} | **TTS:** {args.tts}\n\n'+
        '## Itens a verificar\n\n'+'\n'.join('- [ ] '+x for x in checkboxes)+'\n\n## Alertas\n\n'+
        '\n'.join('- '+x for x in notices)+'\n\n## Capítulos\n\n'+out.with_name(out.stem+'_capitulos.txt').read_text(encoding='utf-8'),encoding='utf-8')
    print(f'\nOK: {out}\nDuração: {tcode(total)} | {args.width}x{args.height} | revisão manual obrigatória.')
    for notice in notices: print('AVISO:',notice)

if __name__=='__main__':
    try:
        main()
    except (ValueError,RuntimeError,subprocess.CalledProcessError) as exc:
        print('ERRO:',exc,file=sys.stderr)
        raise SystemExit(1)
