"""Locally hosted Java 17 coding practice app. Run: python server.py"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, subprocess, tempfile, os, sys, base64, time
try:
    import resource
except ImportError:
    resource = None

ROOT=Path(__file__).resolve().parent

# Each challenge uses an independent Java method and a fixed set of sample/private tests.
PROBLEMS={
 1: dict(method='sumOfDistinct',signature='public int sumOfDistinct(int[] input1)',cases=[('[1,2,2,3,4,4]', '10'),('[5,5,5]', '5'),('[-2,-2,3,1,1]', '2'),('[]','0')]),
 2: dict(method='rearrangeString',signature='public String rearrangeString(String input1)',cases=[('"beauty"','"betayu"'),('"applee"','"papele"'),('"aabb"','"baba"'),('"code"','"code"')]),
 3: dict(method='calculateNetCurrent',signature='public int[] calculateNetCurrent(int input1, int[] input2)',cases=[('[2,0,-3,0,5]','[2,-3,-3,5,5]'),('[0,4,0,0,-6]','[4,4,-6,-6,-6]'),('[0,0,7,0,0]','[7,7,7,7,7]'),('[-5,0,2,0,-8]','[-5,-5,2,-8,-8]')]),
 4: dict(method='longestUniqueSubstring',signature='public int longestUniqueSubstring(String input1)',cases=[('"abcabcbb"','3'),('"bbbbb"','1'),('"pwwkew"','3'),('""','0')]),
 5: dict(method='countPairs',signature='public int countPairs(int[] input1, int input2)',cases=[('[1,5,7,-1,5]|6','3'),('[1,1,1,1]|2','6'),('[2,4,3]|100','0'),('[-1,0,1,2,-2]|0','2')])
}

def jstr(s): return '"'+s.replace('\\','\\\\').replace('"','\\"')+'"'
def arr_literal(xs): return 'new int[]{'+','.join(map(str,xs))+'}'
def arguments(n, encoded):
 if n in (1,3,5):
  if n==5:
   arr,k=encoded.split('|'); return arr_literal(json.loads(arr))+','+str(int(k))
  xs=json.loads(encoded)
  if n==3: return str(len(xs))+','+arr_literal(xs)
  return arr_literal(xs)
 return jstr(json.loads(encoded))
def expected_literal(n, encoded):
 if n==2: return jstr(json.loads(encoded))
 if n==3: return arr_literal(json.loads(encoded))
 return str(int(encoded))
def runner_source(n):
 p=PROBLEMS[n]
 items=[]
 for index,(inp,exp) in enumerate(p['cases']):
  arg=arguments(n,inp); expected=expected_literal(n,exp)
  comparison='java.util.Arrays.equals(got,expected)' if n==3 else ('java.util.Objects.equals(got,expected)' if n==2 else 'got==expected')
  fmt='java.util.Arrays.toString(got)' if n==3 else 'String.valueOf(got)'
  efmt='java.util.Arrays.toString(expected)' if n==3 else 'String.valueOf(expected)'
  typ='int[]' if n==3 else ('String' if n==2 else 'int')
  items.append(f'''try {{ {typ} expected = {expected}; {typ} got = impl.{p["method"]}({arg});
    boolean ok = {comparison};
    emit({index}, ok, {efmt}, {fmt});
  }} catch(Throwable ex) {{ emit({index}, false, "{exp.replace('"','')}", "Error: " + ex.getClass().getSimpleName()); }}''')
 return '''import java.util.*;
public class Runner {
 static void emit(int i, boolean pass, String expected, String actual) {
   System.out.println(i + "|" + (pass ? "1" : "0") + "|" + Base64.getEncoder().encodeToString(expected.getBytes(java.nio.charset.StandardCharsets.UTF_8)) + "|" + Base64.getEncoder().encodeToString(actual.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
 }
 public static void main(String[] args) {
  UserMainCode impl = new UserMainCode();
  '''+'\n'.join(items)+'''\n }
}'''

def limits():
 if resource is None: return
 try:
  resource.setrlimit(resource.RLIMIT_CPU,(5,6))
  resource.setrlimit(resource.RLIMIT_FSIZE,(5_000_000,5_000_000))
  resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
 except Exception: pass

def evaluate(data):
 n=int(data.get('question',0)); code=data.get('code','')
 if n not in PROBLEMS: return {'error':'Unknown question'}
 if not isinstance(code,str) or len(code)>50000: return {'error':'Code must be under 50,000 characters'}
 if 'class UserMainCode' not in code: return {'error':'Keep the class name UserMainCode in your code.'}
 p=PROBLEMS[n]
 with tempfile.TemporaryDirectory(prefix='java_practice_') as td:
  Path(td,'UserMainCode.java').write_text(code,encoding='utf-8')
  Path(td,'Runner.java').write_text(runner_source(n),encoding='utf-8')
  started=time.monotonic()
  try:
   compile_result=subprocess.run(['javac','--release','17','-encoding','UTF-8','UserMainCode.java','Runner.java'],cwd=td,capture_output=True,text=True,timeout=12,preexec_fn=limits if os.name=='posix' else None)
   if compile_result.returncode: return {'compiled':False,'error':compile_result.stderr[-4500:]}
   run=subprocess.run(['java','-Xmx96m','-cp',td,'Runner'],cwd=td,capture_output=True,text=True,timeout=7,preexec_fn=limits if os.name=='posix' else None)
  except subprocess.TimeoutExpired: return {'compiled':True,'error':'Time limit exceeded.'}
  results=[]
  for line in run.stdout.splitlines():
   parts=line.split('|')
   if len(parts)==4 and parts[0].isdigit():
    try:
     idx=int(parts[0]); inp=p['cases'][idx][0]
     results.append(dict(index=idx+1,passed=parts[1]=='1',input=inp,expected=base64.b64decode(parts[2]).decode(),actual=base64.b64decode(parts[3]).decode()))
    except (ValueError,IndexError): pass
  return {'compiled':True,'results':results,'total':len(p['cases']),'elapsedMs':round((time.monotonic()-started)*1000),'error':run.stderr[-1600:] if run.returncode else ''}

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_POST(self):
  if self.path!='/api/run': self.send_error(404);return
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size>100000: self.send_error(413);return
   data=json.loads(self.rfile.read(size)); response=evaluate(data)
   output=json.dumps(response).encode()
   self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(output)));self.end_headers();self.wfile.write(output)
  except Exception as ex:
   result=json.dumps({'error':str(ex)}).encode();self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(result)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', '10000'))
    print(f'Assessment server listening on port {port}')
    ThreadingHTTPServer(('0.0.0.0', port), Handler).serve_forever()
