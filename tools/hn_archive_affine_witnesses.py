#!/usr/bin/env python3
"""Independently validate four explicit witnesses and archive their exact bytes.

No solver, geometry kernel, or graph construction is imported. An optional
GitHub API call stores a blob only, never updates a branch or creates a commit.
"""
import argparse,base64,gzip,hashlib,json,os,urllib.request
from pathlib import Path

EXPECTED_RAW_SHA256='72240175a62057f5be4c5fe455df28569b49ad4057c6f94a7562c697f0b5fb7c'
S1='528997412960b6b34530eeca3e6557d8a6be606f'
S2='dfdecef3d644a3fcb554a0ee283e3d9b72799d27'
GRAPHS={'u':(15908,103045,'7a04684f1a91ec20697387f0af155e0d8d38447f1fb19cf38afe7ff6c67fd6dc'),
'fork':(23090,154809,'bf17bfe425178823c16d2b3c586ebc8e4706eb2bd6866f6571e4a6223b272af1')}

def digest(b):return hashlib.sha256(b).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--store-git-blob',action='store_true');a=ap.parse_args()
    entries=[('u','t1',10431436190,35057449450,S1),('u','t4',10431436190,35057449450,S1),
             ('f1','',10431546654,35058000720,S2),('f4','',10431347184,35058000720,S2)]
    witnesses=[]
    for folder,sub,aid,run,commit in entries:
        root=a.input/folder;p=root/sub
        if (root/'SOURCE_COMMIT.txt').read_text().strip()!=commit:raise ValueError('wrong source commit')
        g=json.loads((root/'GRAPH.json').read_text());r=json.loads((p/'RESULT.json').read_text())
        case='u' if folder=='u' else 'fork';n=len(g['pts']);edges=g['edges']
        semantic=digest(json.dumps({k:g[k] for k in ('pts','edges')},sort_keys=True,separators=(',',':')).encode())
        if (n,len(edges),semantic)!=GRAPHS[case]:raise ValueError('wrong exact graph')
        if r['status']!='SAT' or r['semantic_sha256']!=semantic:raise ValueError('not a bound SAT result')
        raw=(p/'COLORING.txt').read_bytes();text=raw.decode().strip()
        if len(text)!=n or any(c not in '01234' for c in text):raise ValueError('bad five-color vector')
        if digest(raw)!=r['coloring_sha256']:raise ValueError('wrong witness hash')
        if any(text[u]==text[v] for u,v in edges):raise ValueError('monochromatic original edge')
        w=dict(r,artifact_id=aid,run_id=run,colors=text)
        if folder!='u':w['source_commit']=commit
        witnesses.append(w)
    bundle={'format':'full-five-color-witnesses-v1','source_commits':[S1,S2],'witnesses':witnesses}
    raw=json.dumps(bundle,sort_keys=True,separators=(',',':')).encode()+b'\n'
    if digest(raw)!=EXPECTED_RAW_SHA256:raise ValueError('archive differs from locally audited planned content')
    data=gzip.compress(raw,mtime=0);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'AFFINE_FIVE_COLORINGS.json.gz').write_bytes(data)
    git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    meta={'witnesses':4,'raw_sha256':digest(raw),'gzip_sha256':digest(data),'git_blob_sha':git_sha,
          'gzip_bytes':len(data),'all_original_edges_checked':True,'branch_ref_updated':False}
    if a.store_git_blob:
        payload=json.dumps({'content':base64.b64encode(data).decode(),'encoding':'base64'}).encode()
        req=urllib.request.Request('https://api.github.com/repos/HeliCorgi/hadwiger-nelson-lab/git/blobs',
            data=payload,method='POST',headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],
            'Accept':'application/vnd.github+json','Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as response:remote=json.load(response)
        if remote['sha']!=git_sha:raise ValueError('remote blob differs')
        meta['git_blob_created']=True
    (a.out/'BLOB_META.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
if __name__=='__main__':main()
