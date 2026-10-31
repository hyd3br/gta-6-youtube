#!/usr/bin/env python3
"""Gera um Short vertical original em PNG + FFmpeg, com narração por cena.

Modos de voz: bundled (somente para o roteiro de demonstração), files, openai.
O software NUNCA publica conteúdo no YouTube.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print('> ' + ' '.join(str(x) for x in cmd[:9]) + (' ...' if len(cmd) > 9 else ''))
    subprocess.run(cmd, check=True)


def probe_seconds(path: Path) -> float:
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def font_path(bold: bool = False) -> str:
    roots = [
        Path('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'),
        Path('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ]
    for path in roots:
        if path.exists():
            return str(path)
    raise RuntimeError('Fonte não encontrada: instale Arial ou Segoe UI no Windows.')


def font(sz: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path(bold), sz)


def lines_that_fit(draw: ImageDraw.ImageDraw, string: str, fnt, max_width: int) -> list[str]:
    words = string.split()
    out = []
    current = ''
    for word in words:
        trial = (current + ' ' + word).strip()
        if draw.textbbox((0, 0), trial, font=fnt)[2] <= max_width:
            current = trial
        else:
            if current:
                out.append(current)
            current = word
    if current:
        out.append(current)
    return out


def gradient_bg(w: int, h: int, scene_i: int) -> Image.Image:
    # Gráfico procedural original (sem imagens protegidas/prints de GTA).
    base = Image.new('RGB', (w, h))
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        v = (math.sin(t * 4.3 + scene_i * 0.37) + 1) * 0.5
        R = int(8 + 28 * t + 11 * v)
        G = int(10 + 9 * t + 5 * v)
        B = int(31 + 35 * t + 12 * v)
        for x in range(w):
            xx = x / max(1, w - 1)
            neon = max(0, 1 - math.hypot(xx - (0.70 if scene_i % 2 else 0.25), t - 0.48) / 0.58)
            px[x, y] = (min(255, int(R + 40 * neon)), min(255, int(G + 11 * neon)), min(255, int(B + 48 * neon)))
    return base


def scene_image(scene: dict, i: int, total: int, w: int, h: int, dest: Path):
    # Trabalhar inicialmente em dimensão final; não há dependência de imagens externas.
    img = gradient_bg(w, h, i)
    glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((int(w*.33), int(h*.18), int(w*1.25), int(h*.71)), fill=(224, 46, 149, 62))
    gd.ellipse((int(-w*.38), int(h*.37), int(w*.50), int(h*.82)), fill=(21, 203, 244, 38))
    glow = glow.filter(ImageFilter.GaussianBlur(max(12, w//18)))
    img = Image.alpha_composite(img.convert('RGBA'), glow)
    d = ImageDraw.Draw(img, 'RGBA')
    # Sol estilizado e horizonte (arte própria)
    sx, sy, sr = int(w*.69), int(h*.57), int(w*.22)
    d.ellipse((sx-sr, sy-sr, sx+sr, sy+sr), fill=(246, 85, 173, 115))
    # Silhueta urbana geométrica, sem copiar pontos identificáveis do jogo
    rng = random.Random(2917 + i)
    bx = 0
    skyline_y = int(h*.74)
    while bx < w:
        bw = rng.randint(max(20, w//22), max(36, w//10))
        bh = rng.randint(int(h*.07), int(h*.21))
        d.rectangle((bx, skyline_y-bh, bx+bw, h), fill=(8, 11, 26, 248))
        for wy in range(skyline_y-bh+15, skyline_y-10, max(12, w//38)):
            for wx in range(bx+9, bx+bw-5, max(12, w//35)):
                if rng.random() > .55:
                    d.rectangle((wx, wy, wx+3, wy+7), fill=(219, 80, 176, 155))
        bx += bw + rng.randint(0, max(3, w//64))
    d.rectangle((0, int(h*.915), w, h), fill=(8, 9, 22, 250))
    # Borda de destaque à esquerda
    d.rounded_rectangle((int(w*.062), int(h*.14), int(w*.072), int(h*.48)), radius=5, fill=(71, 226, 240, 255))
    # Cabeçalho
    small = font(max(18, int(w*.034)), True)
    d.text((w*.10, h*.065), 'GTA 6  /  RADAR', font=small, fill=(114, 238, 250, 255))
    progress = (w*.10, h*.104, w*.90, h*.110)
    d.rounded_rectangle(progress, radius=4, fill=(245,245,255,32))
    d.rounded_rectangle((progress[0], progress[1], progress[0] + (progress[2]-progress[0])*(i+1)/total, progress[3]), radius=4, fill=(244, 76, 169, 255))

    title = scene['headline'].strip().upper()
    fs = int(w*.096)
    max_w = int(w*.79)
    while fs >= int(w*.053):
        f = font(fs, True)
        title_lines = lines_that_fit(d, title, f, max_w)
        if len(title_lines) <= 4:
            break
        fs -= 3
    yy = int(h*.205)
    for line in title_lines:
        # halo da sombra
        d.text((int(w*.107)+3, yy+5), line, font=f, fill=(0,0,0,175))
        d.text((int(w*.107), yy), line, font=f, fill=(255,255,255,255))
        yy += int(fs*1.28)
    # Tarja inferior com narração, posicionada acima dos controles mais baixos do Shorts.
    start = int(h*.615)
    end = int(h*.72)
    d.rounded_rectangle((int(w*.09), start, int(w*.91), end), radius=int(w*.019), fill=(8,10,28,220), outline=(116,79,171,150), width=max(1,w//350))
    txt = scene['speech']
    caption_size = int(w*.038)
    while caption_size >= int(w*.029):
        tf = font(caption_size, True)
        cap_lines = lines_that_fit(d, txt, tf, int(w*.74))
        if len(cap_lines)*int(caption_size*1.42) < (end-start)*.81:
            break
        caption_size -= 1
    line_h = int(caption_size*1.34)
    cy = start + ((end-start) - line_h*len(cap_lines))//2
    for line in cap_lines:
        tw = d.textbbox((0,0), line, font=tf)[2]
        d.text(((w-tw)//2, cy), line, font=tf, fill=(242,243,252,255))
        cy += line_h
    footer = font(max(13, int(w*.023)), False)
    d.text((int(w*.10), int(h*.834)), 'VOZ SINTÉTICA  •  ROTEIRO ORIGINAL', font=footer, fill=(204, 198, 230, 220))
    img.convert('RGB').save(dest, 'PNG', optimize=True)


def create_openai_voice(text: str, outfile: Path, model: str, voice: str) -> None:
    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('OPENAI_API_KEY ausente. Coloque a chave no arquivo .env (não envie a chave ao Codex/chat).')
    from openai import OpenAI
    client = OpenAI()
    with client.audio.speech.with_streaming_response.create(
        model=model, voice=voice, input=text,
        instructions='Fale em português brasileiro, com naturalidade e energia de um narrador de curiosidades sobre games. Evite dramatização excessiva.',
    ) as resp:
        resp.stream_to_file(outfile)


def concat_audio(audios: list[Path], lengths: list[float], outfile: Path, pause: float) -> None:
    ins = []
    filters = []
    for i, path in enumerate(audios):
        ins += ['-i', str(path)]
        filters.append(f'[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=pad_dur={pause:.3f}[a{i}]')
    filters.append(''.join(f'[a{i}]' for i in range(len(audios))) + f'concat=n={len(audios)}:v=0:a=1[out]')
    run(['ffmpeg','-y','-hide_banner','-loglevel','error',*ins, '-filter_complex',';'.join(filters), '-map','[out]', '-ac','2', '-ar','44100', '-c:a','pcm_s16le',str(outfile)])


def main():
    ap = argparse.ArgumentParser(description='Shorts Factory: vídeos originais prontos para revisão.')
    ap.add_argument('--script', default='roteiro_exemplo.json', help='JSON de roteiro')
    ap.add_argument('--tts', choices=['bundled','openai','files'], default='bundled')
    ap.add_argument('--width', type=int, default=1080)
    ap.add_argument('--height', type=int, default=1920)
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--pause', type=float, default=0.35)
    ap.add_argument('--output', default='output/primeiro_short.mp4')
    args = ap.parse_args()
    load_dotenv(ROOT / '.env')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        sys.exit('ERRO: FFmpeg/FFprobe não encontrados no PATH. Instale FFmpeg e reabra o terminal.')
    if args.width < 300 or args.height < 500 or args.fps < 10:
        sys.exit('ERRO: dimensões ou FPS inválidos.')
    script_file = (ROOT / args.script).resolve()
    data = json.loads(script_file.read_text(encoding='utf-8'))
    scenes = data.get('scenes')
    if not isinstance(scenes, list) or not (1 <= len(scenes) <= 12):
        sys.exit('ERRO: o roteiro precisa de 1 a 12 cenas.')
    for i, scene in enumerate(scenes):
        if not isinstance(scene.get('speech'), str) or not isinstance(scene.get('headline'), str):
            sys.exit(f'ERRO: cena {i+1}: informe headline e speech.')
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    work = ROOT / 'work' / out.stem
    work.mkdir(parents=True, exist_ok=True)
    audios, images, lengths = [], [], []
    for i, scene in enumerate(scenes):
        print(f'Preparando cena {i+1}/{len(scenes)}...')
        if args.tts == 'bundled':
            # Áudios DEMO correspondem apenas ao roteiro original.
            if script_file.name != 'roteiro_exemplo.json':
                sys.exit('O modo bundled é exclusivo do roteiro_exemplo.json. Use --tts openai ou --tts files.')
            source = ROOT / 'demo_audio' / f'cena_{i+1:02d}.wav'
            if not source.exists():
                sys.exit(f'Falta o áudio de demonstração: {source}')
            audio = source
        elif args.tts == 'files':
            rel = scene.get('audio_path')
            if not rel:
                sys.exit(f'ERRO: cena {i+1}: informe audio_path no roteiro.')
            audio = (script_file.parent / rel).resolve()
            if not audio.is_file():
                sys.exit(f'Arquivo de áudio não encontrado: {audio}')
        else:
            audio = work / f'voice_{i+1:02d}.mp3'
            if not audio.exists():
                create_openai_voice(scene['speech'], audio, os.getenv('OPENAI_TTS_MODEL', 'gpt-4o-mini-tts'), os.getenv('OPENAI_TTS_VOICE','coral'))
        length = probe_seconds(audio)
        lengths.append(length + args.pause)
        audios.append(audio)
        path = work / f'scene_{i+1:02d}.png'
        scene_image(scene, i, len(scenes), args.width, args.height, path)
        images.append(path)
    audio_path = work / 'narracao_completa.wav'
    concat_audio(audios, lengths, audio_path, args.pause)
    list_file = work / 'slides.txt'
    with list_file.open('w', encoding='utf-8') as f:
        for png, seconds in zip(images, lengths):
            f.write("file '" + png.resolve().as_posix().replace("'", "'\\''") + "'\n")
            f.write(f'duration {seconds:.6f}\n')
        f.write("file '" + images[-1].resolve().as_posix().replace("'", "'\\''") + "'\n")
    total_duration = sum(lengths)
    run(['ffmpeg','-y','-hide_banner','-loglevel','error', '-f','concat','-safe','0','-i',str(list_file),'-i',str(audio_path),'-vf',f'fps={args.fps},format=yuv420p', '-c:v','libx264','-preset','veryfast','-crf','24', '-c:a','aac','-b:a','160k','-t',f'{total_duration:.3f}','-movflags','+faststart',str(out)])
    metadata = {
        'title': data.get('title','GTA 6: informação ou boato?'),
        'description': data.get('description','Exemplo com roteiro original. Voz gerada por IA.'),
        'sources': data.get('sources',[]),
        'file': str(out.relative_to(ROOT)), 'duration_seconds': round(probe_seconds(out),2),
        'resolution': f'{args.width}x{args.height}', 'tts': args.tts,
        'status': 'AGUARDANDO_REVISAO_HUMANA',
        'artificial_voice_disclosure': 'Voz sintética gerada por IA',
        'notice': 'Conteúdo ilustrativo original, sem imagens oficiais de GTA 6.',
    }
    out.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2), encoding='utf-8')
    print(f'\nSUCESSO: {out}\nDuração: {metadata["duration_seconds"]} s\nNão publicado: aguardando revisão humana.')

if __name__ == '__main__':
    main()
