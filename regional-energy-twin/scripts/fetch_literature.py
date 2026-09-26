"""Bounded primary-source retrieval; retain hashes/access status, not copyrighted PDFs in git."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

SOURCES={
 'L1_ci_1997':'https://doi.org/10.1109/ACC.1997.609105',
 'L2_data_incest':'https://dihana.cps.unizar.es/proceedings/ICASSP/2003/pdfs/05-00269.pdf',
 'L3_partial_correlation':'https://dspace.zcu.cz/bitstreams/473253c1-ec1e-40b4-8a4d-5a7f38db7a4a/download',
 'L4_robust_fusion':'https://www.diva-portal.org/smash/get/diva2:1690215/FULLTEXT01.pdf',
 'L5_esci_2024':'https://arxiv.org/pdf/2403.03543',
 'L6_esci_2025':'https://arxiv.org/pdf/2501.07915',
 'L9_shrinkage':'https://www.ledoit.net/Well-conditioned2004.pdf',
 'L10_provenance':'https://web.cs.ucdavis.edu/~green/papers/pods07.pdf',
 'L11_jl':'https://cseweb.ucsd.edu/~dasgupta/papers/jl.pdf',
 'L12_cod':'https://proceedings.mlr.press/v54/mroueh17a/mroueh17a.pdf',
 'L13_conservative_compression':'https://arxiv.org/pdf/2403.05977',
 'L14_distributed_sketch':'https://jmlr.org/papers/volume22/20-705/20-705.pdf',
 'L15_dimension_reduced_fusion':'https://arxiv.org/pdf/2210.06947',
}


def fetch(entry):
    key,url=entry
    result=dict(id=key,url=url,retrieved_utc=datetime.now(timezone.utc).isoformat())
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'DSpaCES research source audit'})
        with urllib.request.urlopen(request,timeout=30) as response:
            body=response.read(20_000_001)
            if len(body)>20_000_000:raise RuntimeError('Source size cap exceeded')
            is_pdf=body.startswith(b'%PDF')
            suffix='.pdf' if is_pdf else '.html'
            Path('.cache/literature/'+key+suffix).write_bytes(body)
            result.update(status='pdf_retrieved' if is_pdf else 'html_only',bytes=len(body),
                sha256=hashlib.sha256(body).hexdigest(),final_url=response.url)
    except Exception as error:result.update(status='unavailable',error=str(error))
    return result


if __name__=='__main__':
    Path('.cache/literature').mkdir(parents=True,exist_ok=True)
    Path('manifests').mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,SOURCES.items()))
    Path('manifests/literature_access.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
