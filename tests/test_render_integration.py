"""Real FFmpeg export/decoding with synthetic audio, not a publishable GTA news video."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
import wave

from gta6.production import ROOT,render
from gta6.editorial import digest_bytes
from gta6.research import digest


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg is required')
class RenderIntegration(unittest.TestCase):
    def test_real_export_caption_assets_and_integrity(self):
        self.check_export('long',True)

    def test_full_resolution_vertical_export(self):
        self.check_export('short',False)

    def check_export(self,kind,preview):
        (ROOT/'output').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='test_phase2_',dir=ROOT/'output') as temp:
            base=Path(temp)
            wav=base/'synthetic.wav'
            with wave.open(str(wav),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000)
                out.writeframes(struct.pack('<h',100)*16000)
            scene={'headline':'TESTE TÉCNICO — NÃO É NOTÍCIA','speech':'Exemplo técnico.',
                   'audio_path':str(wav),'audio_sha256':digest_bytes(wav),
                   'captions':[{'start':0,'end':1,'text':'Teste técnico, não é notícia.'}],
                   'chapter':'Teste','license_notes':'Tom sintético e arte procedural próprios.'}
            script={'format':kind,'title':'TEST FIXTURE','thumbnail_title':'TESTE TÉCNICO',
                    'sources':[],'scenes':[scene,scene],'automatic_upload':False}
            folder=base/'export'
            work=ROOT/'work'/('phase2_'+digest(str(folder.resolve()))[:16])
            try:
                manifest=render(script,folder,preview=preview,preset='ultrafast')
                m=json.loads(manifest.read_text())
                self.assertFalse(m['automatic_upload'])
                for name,value in m['artifact_sha256'].items():
                    self.assertEqual(digest_bytes(folder/name),value)
                meta=json.loads((folder/'metadata.json').read_text())
                self.assertEqual(meta['resolution'],'640x360' if preview else '1080x1920')
                self.assertEqual(meta['preview'],preview)
                self.assertGreater(meta['duration_seconds'],2)
                self.assertIn('00:00:01,250' if preview else '00:00:01,267',(folder/'video.srt').read_text(encoding='utf-8-sig'))
                with self.assertRaises(ValueError): render(script,folder,preview=True)
            finally:
                if work.exists(): shutil.rmtree(work)


if __name__=='__main__': unittest.main()
