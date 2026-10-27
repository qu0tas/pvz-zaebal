"""Experimental GW2 legacy EBX diagnostic reader. Not a writer or full Frosty SDK."""
import struct,uuid,json
from pathlib import Path

def read(path):
 b=Path(path).read_bytes()
 def u(fmt,p):return struct.unpack_from('<'+fmt,b,p)
 def hs(s):
  h=5381
  for c in s:h=((h*33)^ord(c))&0xffffffff
  return h
 magic,so,sd,ng=u('4I',0);ni,ne,nu,nc,nf,tn=u('6H',16);sl,na,dl=u('3I',28)
 assert magic==0x0fb2d1ce
 imports=[(str(uuid.UUID(bytes_le=b[64+i*32:80+i*32])),str(uuid.UUID(bytes_le=b[80+i*32:96+i*32]))) for i in range(ng)]
 p=64+ng*32; names={hs(x.decode()):x.decode() for x in b[p:p+tn].split(b'\0') if x};p+=tn
 fs=[]
 for i in range(nf):
  h,t,cl,off,o2=u('IHHII',p);p+=16;fs.append((names[h],(t>>4)&31,cl,off))
 cs=[]
 for i in range(nc):
  h,fi,fn,al,t,sz,sz2=u('IiBBHHH',p);p+=16;cs.append((names[h],fi,fn,al,sz))
 inst=[]
 for i in range(ni):
  cl,n=u('HH',p);p+=4;inst.append((cl,n,i<ne))
 p=(p+15)//16*16;ars=[]
 for i in range(na):ars.append(u('IIi',p));p+=12
 obs=[];p=so+sl
 for cl,n,exp in inst:
  c=cs[cl]
  for _ in range(n):
   p=(p+c[3]-1)//c[3]*c[3];g=str(uuid.UUID(bytes_le=b[p:p+16])) if exp else None
   pos=p+(16 if exp else 0);pos+=8 if c[3]!=4 else 0;base=pos-8
   obs.append((cl,g,base));p=base+c[4]
 def fields(cl,base):
  out={};c=cs[cl]
  for name,t,fc,off in fs[c[1]:c[1]+c[2]]:
   if t==0:out.update(fields(fc,base))
   else:out[name]=value(t,fc,base+off)
  return out
 def value(t,cl,pos):
  if t==4:
   ix=u('I',pos)[0];off,n,_=ars[ix];ac=cs[cl];_,et,ec,_=fs[ac[1]]
   stride=cs[ec][4] if et==2 else {3:4,7:4,8:4,15:4,16:4,19:4,10:1}[et]
   return [value(et,ec,so+sl+dl+off+i*stride) for i in range(n)]
  if t==2:return fields(cl,pos)
  if t==3:
   v=u('I',pos)[0]
   return {'external':imports[v&0x7fffffff]} if v&0x80000000 else ({'internal':obs[v-1][1], 'index':v-1} if v else None)
  if t==7:
   o=u('I',pos)[0]
   if o==0xffffffff:return ''
   return b[so+o:b.index(0,so+o)].decode()
  if t==10:return bool(b[pos])
  if t in [8,15,16,19]:return u({8:'i',15:'i',16:'I',19:'f'}[t],pos)[0]
  if t==14:return u('H',pos)[0]
  if t==21:return str(uuid.UUID(bytes_le=b[pos:pos+16]))
  return {'unparsed_type':t,'position':pos}
 result=[dict(type=cs[cl][0],guid=g,fields=fields(cl,base)) for cl,g,base in obs]
 return {'file_guid':str(uuid.UUID(bytes_le=b[40:56])),'imports':imports,'objects':result}

if __name__ == '__main__':
 import argparse
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('input',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
 args.output.write_text(json.dumps(read(args.input),ensure_ascii=False,indent=2),encoding='utf-8')
 print('Wrote',args.output)
