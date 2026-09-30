from pathlib import Path
import concurrent.futures,json,subprocess
from acquire import fetch,ROOT
PAPERS={
 'GDN':'https://arxiv.org/pdf/2106.06947',
 'CSDI':'https://proceedings.neurips.cc/paper_files/paper/2021/file/cfe8504bda37b575c70ee1a8276f3486-Paper.pdf',
 'TSAD-C':'https://arxiv.org/pdf/2308.12563v5',
 'CAGAD':'https://arxiv.org/pdf/2407.02143v1',
 'Hara':'https://proceedings.mlr.press/v38/hara15.pdf',
 'Shi':'https://ceur-ws.org/Vol-4073/BEHAIV2025_CRV_4.pdf',
 'Conformal':'https://arxiv.org/pdf/2202.13415',
 'Xu':'https://raw.githubusercontent.com/mlresearch/v329/main/assets/xu26a/xu26a.pdf',
 'TSB-AD':'https://proceedings.neurips.cc/paper_files/paper/2024/file/c3f3c690b7a99fba16d0efd35cb83b2c-Paper-Datasets_and_Benchmarks_Track.pdf',
}
def retrieve(item):
    name,url=item; path=ROOT/'literature/downloads'/(name+'.pdf')
    try:
        record=fetch(url,path)
        result=subprocess.run(['pdftotext','-layout',str(path),str(path.with_suffix('.txt'))],capture_output=True,text=True)
        record['text_extract_success']=result.returncode==0
        return name,record
    except Exception as e: return name,dict(url=url,error=str(e))
results={}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for name,record in pool.map(retrieve,PAPERS.items()):
        results[name]=record; print(name,'error' if 'error' in record else 'downloaded',flush=True)
(ROOT/'literature/sources.json').write_text(json.dumps(results,indent=2)+'\n')
