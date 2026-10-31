import ctypes as C,importlib.util
from pathlib import Path
class Id(C.Union):
    _fields_=[('number',C.c_int),('name',C.c_char_p),('string',C.c_char*8)]
class Event(C.Structure):
    _fields_=[('type',C.c_int),('unique_identifier',C.c_uint),('text_position',C.c_int),('length',C.c_int),('audio_position',C.c_int),('sample',C.c_int),('user_data',C.c_void_p),('id',Id)]
p=Path(importlib.util.find_spec('piper').origin).parent
lib=C.CDLL(str(p/'espeakbridge.so'))
lib.espeak_Initialize.argtypes=[C.c_int,C.c_int,C.c_char_p,C.c_int];lib.espeak_Initialize.restype=C.c_int
rate=lib.espeak_Initialize(2,0,str(p/'espeak-ng-data').encode(),0)
lib.espeak_SetVoiceByName.argtypes=[C.c_char_p];lib.espeak_SetVoiceByName(b'pt-br')
lib.espeak_SetParameter(1,145,0)
CALLBACK=C.CFUNCTYPE(C.c_int,C.POINTER(C.c_short),C.c_int,C.POINTER(Event))
@CALLBACK
def callback(samples,n,events):
    i=0
    while events and events[i].type!=0 and i<100:
        e=events[i]
        if e.type==1: print(e.type,e.text_position,e.length,e.audio_position,flush=True)
        i+=1
    return 0
lib.espeak_SetSynthCallback.argtypes=[CALLBACK];lib.espeak_SetSynthCallback(callback)
lib.espeak_Synth.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_int,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
text='A trilha original de GTA seis tem uma novidade confirmada pela Rockstar.'
buf=C.create_string_buffer(text.encode());lib.espeak_Synth(buf,len(buf),0,1,0,1,None,None);lib.espeak_Synchronize()
print('Speech:',text)
