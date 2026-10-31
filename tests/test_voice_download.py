import hashlib
from pathlib import Path
import tempfile
import unittest
from tools.prepare_voice import download


class DownloadTests(unittest.TestCase):
    def test_existing_weights_still_checked_against_upstream_lfs(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'voice.onnx'; p.write_bytes(b'synthetic model fixture')
            download('https://unused.invalid',p,{'lfs':{'oid':hashlib.sha256(p.read_bytes()).hexdigest()}})
            with self.assertRaises(ValueError): download('https://unused.invalid',p,{'lfs':{'oid':'0'*64}})
    def test_metadata_git_blob_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'MODEL_CARD'; p.write_bytes(b'License fixture')
            raw=p.read_bytes(); oid=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            download('https://unused.invalid',p,{'oid':oid})
            with self.assertRaises(ValueError): download('https://unused.invalid',p,{'oid':'0'*40})
    def test_missing_integrity_metadata_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config';p.write_bytes(b'{}')
            with self.assertRaises(ValueError): download('https://unused.invalid',p,{})
