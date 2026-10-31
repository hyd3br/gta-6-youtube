#!/usr/bin/env python3
"""Download one pt-BR Piper voice with upstream checksums; no API key or charges."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from gta6.editorial import write_json,digest_bytes


def download(url,path,entry):
    if path.exists():
        raw=path.read_bytes()
    else:
        with urlopen(url,timeout=60) as response:
            # Hugging Face may redirect model weights to its storage CDN; the proxy
            # must explicitly permit it. TLS verification is never disabled.
            raw=response.read(100_000_001)
    if len(raw)>100_000_000: raise ValueError('Modelo excede o limite de 100 MB.')
    lfs=entry.get('lfs') or {}
    if lfs.get('oid'):
        if hashlib.sha256(raw).hexdigest()!=lfs['oid']: raise ValueError('Checksum LFS divergente.')
    elif entry.get('oid'):
        blob=b'blob '+str(len(raw)).encode()+b'\0'+raw
        if hashlib.sha1(blob).hexdigest()!=entry['oid']: raise ValueError('Checksum Git divergente.')
    else: raise ValueError('Metadados de checksum ausentes; download não será usado.')
    if not path.exists():
        tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_bytes(raw); tmp.replace(path)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--voice',default='pt_BR-faber-medium')
    ap.add_argument('--license-notes',help='Após ler MODEL_CARD: licença, atribuição e permissão de uso comercial.')
    args=ap.parse_args()
    match=re.fullmatch(r'pt_BR-([a-z0-9_]+)-(x_low|low|medium|high)',args.voice)
    if not match: raise ValueError('Nome de voz pt_BR inválido.')
    speaker,quality=match.groups()
    folder=ROOT/'models'/args.voice; folder.mkdir(parents=True,exist_ok=True)
    remote=f'pt/pt_BR/{speaker}/{quality}'
    api=f'https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/{remote}?expand=true'
    with urlopen(api,timeout=30) as response: entries=json.load(response)
    index={e['path'].split('/')[-1]:e for e in entries}
    files=['MODEL_CARD',args.voice+'.onnx.json',args.voice+'.onnx']
    for name in files:
        entry=index.get(name)
        if not entry: raise ValueError(f'Artefato oficial ausente: {name}')
        download(f'https://huggingface.co/rhasspy/piper-voices/resolve/main/{remote}/{name}',folder/name,entry)
    card_url=f'https://huggingface.co/rhasspy/piper-voices/blob/main/{remote}/MODEL_CARD'
    print('Modelo e configuração conferidos com os checksums do repositório oficial.')
    print('Leia a licença específica:',folder/'MODEL_CARD')
    if not args.license_notes:
        print('Sem registro de licença: voice.json NÃO foi criado. Leia o MODEL_CARD e repita com --license-notes.')
        return 2
    spec={'model':args.voice+'.onnx','model_sha256':digest_bytes(folder/(args.voice+'.onnx')),
          'config_sha256':digest_bytes(folder/(args.voice+'.onnx.json')),
          'license_url':card_url,'license_notes':args.license_notes}
    write_json(folder/'voice.json',spec)
    print('Configuração local:',folder/'voice.json')
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,OSError) as e:
        print('ERRO:',e,file=sys.stderr); raise SystemExit(1)
