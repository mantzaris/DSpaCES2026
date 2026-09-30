"""Local evidence viewer with explicit operator review logging."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import argparse,json,sys,urllib.parse
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from iot_repair.persistence import log_decision
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if self.path=='/':self.path='/operator/index.html'
        if self.path=='/api/cases':
            paths=sorted((ROOT/'results/graph').glob('*.json'));self.send_json([str(p.relative_to(ROOT)) for p in paths if p.name!='persistence_audit.json']);return
        if self.path.startswith('/runtime/') or self.path.startswith('/data/raw/'):
            self.send_error(403);return
        return super().do_GET()
    def send_json(self,value,status=200):
        content=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
    def do_POST(self):
        if self.path!='/api/decision':self.send_error(404);return
        origin=self.headers.get('Origin')
        if origin and urllib.parse.urlparse(origin).netloc!=self.headers.get('Host'):
            self.send_error(403);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>8192:raise ValueError('Request too large')
            data=json.loads(self.rfile.read(length));record=log_decision(ROOT,data['hypothesis_id'],data['action'],data.get('note',''))
            self.send_json(record)
        except Exception as error:self.send_json({'error':str(error)},400)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8099);args=parser.parse_args()
    print(f'Operator evidence view at http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()
