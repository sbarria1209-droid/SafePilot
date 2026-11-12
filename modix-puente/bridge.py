"""MODIX HTTPS relay. Solo memoria; una estación, sin comandos ni acceso a Duet."""
import os,json,time,secrets,threading,gzip,hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit

OWNER=os.environ.get('MODIX_OWNER_TOKEN','')
LOCK=threading.RLock();VIEWER='';SESSION='';UPDATED=0.;CAMERA_TIME=0.;STATE=None;MODEL=None;JPEG=None;REVISION=None
VIEWED=0.;OUTPUT_BYTES=0;OUTPUT_LIMIT=int(os.environ.get('MODIX_OUTPUT_LIMIT','1000000000'))
MONTH=time.strftime('%Y-%m');REQUESTS={}
def eq(a,b):return bool(a and b) and secrets.compare_digest(a.encode(),b.encode())

class Handler(BaseHTTPRequestHandler):
    server_version='MODIXRelay/8'
    protocol_version='HTTP/1.1'
    def setup(self):super().setup();self.connection.settimeout(15)
    def log_message(self,*args):pass
    def send(self,status,data=b'',kind='application/json',compress=False,etag=None):
        global OUTPUT_BYTES,MONTH
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
        compressed=compress and len(data)>1000 and 'gzip' in self.headers.get('Accept-Encoding','')
        if compressed:data=gzip.compress(data,compresslevel=2)
        with LOCK:
            month=time.strftime('%Y-%m')
            if month!=MONTH:MONTH=month;OUTPUT_BYTES=0
            if OUTPUT_BYTES+len(data)>OUTPUT_LIMIT:status=429;data=b'{"error":"Limite de transferencia alcanzado"}';compressed=False
            OUTPUT_BYTES+=len(data)
        if status>=400:self.close_connection=True
        self.send_response(status)
        if self.close_connection:self.send_header('Connection','close')
        self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','private, no-store');self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Content-Type-Options','nosniff')
        if compressed:self.send_header('Content-Encoding','gzip')
        if etag:self.send_header('ETag',etag)
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
    def token(self):
        value=self.headers.get('Authorization','');return value[7:] if value.startswith('Bearer ') else ''
    def body(self,limit):
        length=int(self.headers.get('Content-Length','0'))
        if not 0<length<=limit:raise ValueError('Tamaño inválido')
        data=self.rfile.read(length)
        if len(data)!=length:raise ValueError('Carga incompleta')
        if self.headers.get('Content-Encoding')=='gzip':
            import zlib
            obj=zlib.decompressobj(16+zlib.MAX_WBITS);data=obj.decompress(data,16*1024*1024+1)
            if len(data)>16*1024*1024 or obj.unconsumed_tail:raise ValueError('Carga descomprimida excesiva')
        return data
    def do_GET(self):
        global VIEWED
        path=urlsplit(self.path).path
        if path=='/health':self.send(200,{'service':'MODIX-HTTPS','protocol':7,'implementation':8,'ready':len(OWNER)>=32});return
        if path=='/':self.send(200,b'MODIX HTTPS - usa el cliente de escritorio.','text/plain; charset=utf-8');return
        token=self.token();now=time.time()
        # Sólo se toma una instantánea bajo el bloqueo. Ninguna respuesta de red,
        # compresión ni descarga del modelo mantiene bloqueado el vídeo.
        with LOCK:
            owner=eq(token,OWNER);viewer=eq(token,VIEWER)
            publisher_info={'viewing':now-VIEWED<7,'active':bool(VIEWER),'session':SESSION}
            fresh=now-UPDATED<=15;state=STATE;model=MODEL;jpeg=JPEG;camera_time=CAMERA_TIME
            if viewer and fresh:VIEWED=now
        if path=='/publish/status' and owner:self.send(200,publisher_info);return
        if not viewer:self.send(403,{'error':'Acceso cerrado o clave incorrecta'});return
        if not fresh:self.send(503,{'error':'La principal no publica datos recientes'});return
        if path=='/api/live':self.send(200,state or {},compress=True);return
        if path=='/api/layers':self.send(200,{'gcode':model},compress=True);return
        if path=='/camera.jpg':
            if jpeg is None or now-camera_time>7:self.send(404,{'error':'Cámara USB sin imagen reciente'});return
            etag='"'+hashlib.sha256(jpeg).hexdigest()[:24]+'"'
            if self.headers.get('If-None-Match')==etag:self.send(304,b'',etag=etag);return
            self.send(200,jpeg,'image/jpeg',etag=etag);return
        self.send(404,{'error':'Ruta no disponible'})
    def do_POST(self):
        global VIEWER,SESSION,UPDATED,STATE,MODEL,JPEG,CAMERA_TIME,REVISION
        if not eq(self.token(),OWNER):self.send(403,{'error':'Acceso denegado'});return
        path=urlsplit(self.path).path
        try:
            raw=self.body(8*1024*1024 if path=='/publish/model' else 2*1024*1024)
            data=None if path=='/publish/camera' else json.loads(raw)
            with LOCK:
                if path=='/publish/start':
                    key=data.get('viewer','');session=data.get('session','')
                    if not isinstance(key,str) or len(key)<32 or not isinstance(session,str) or len(session)<16:raise ValueError('Clave inválida')
                    VIEWER=key;SESSION=session;UPDATED=0;STATE=MODEL=JPEG=None;REVISION=None;CAMERA_TIME=0
                else:
                    if not VIEWER or self.headers.get('X-Modix-Session')!=SESSION:self.send(409,{'error':'La sesión fue sustituida o cerrada'});return
                    if path=='/publish/state':
                        if not isinstance(data,dict) or not isinstance(data.get('status'),dict):raise ValueError('Estado inválido')
                        STATE=data;UPDATED=time.time()
                    elif path=='/publish/model':
                        if data is not None and (not isinstance(data,dict) or len(data.get('segments',[]))>100000):raise ValueError('Modelo inválido')
                        MODEL=data;REVISION=(data or {}).get('sha256')
                    elif path=='/publish/camera':
                        if not raw.startswith(b'\xff\xd8') or len(raw)>1024*1024:raise ValueError('JPEG inválido')
                        JPEG=raw;CAMERA_TIME=time.time()
                    elif path=='/publish/stop':VIEWER='';SESSION='';STATE=MODEL=JPEG=None;UPDATED=CAMERA_TIME=0;REVISION=None
                    else:self.send(404,{'error':'Ruta no disponible'});return
            self.send(200,{'ok':True})
        except (ValueError,TypeError,OverflowError):self.send(400,{'error':'Carga inválida'})
    def do_PUT(self):self.send(405,{'error':'Método no permitido'})
    def do_DELETE(self):self.do_PUT()

def main():
    if len(OWNER)<32:raise SystemExit('Falta MODIX_OWNER_TOKEN (mínimo 32 caracteres)')
    http=ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','10000'))),Handler);http.daemon_threads=True;http.serve_forever()
if __name__=='__main__':main()

