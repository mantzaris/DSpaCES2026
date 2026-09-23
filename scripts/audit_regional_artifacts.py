"""Audit keys and accessible partitions; never summarize sealed demand values."""
import hashlib
import json
from pathlib import Path
import time
import duckdb


def main():
    start=time.perf_counter()
    con=duckdb.connect(); con.execute("SET threads=4; SET memory_limit='2GB'")
    root=Path('data/regional')
    all_files=str(root/'parquet/*/*/*.parquet')
    # Across sealed partitions, project ONLY identity and duplicate count columns.
    total=con.execute('SELECT count(*),count(DISTINCT meter),sum(duplicate_count-1) FROM read_parquet(?)',[all_files]).fetchone()
    access={}
    for split in ['train','development']:
        file=str(root/'parquet'/split/'*/*.parquet')
        row=con.execute("""SELECT count(*),sum(CASE WHEN kwh IS NULL THEN 1 ELSE 0 END),
            sum(CASE WHEN duplicate_count>1 THEN 1 ELSE 0 END),
            sum(CASE WHEN minute(timestamp) NOT IN (0,30) OR second(timestamp)<>0 THEN 1 ELSE 0 END),
            min(timestamp),max(timestamp) FROM read_parquet(?)""",[file]).fetchone()
        access[split]=dict(zip(['distinct_keys','invalid_or_null_readings','duplicate_keys_excluded','off_grid_keys','first_label','last_label'],row))
        access[split]['first_label']=str(access[split]['first_label']); access[split]['last_label']=str(access[split]['last_label'])
    inventory=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and 'staging' not in p.parts:
            h=hashlib.sha256()
            with p.open('rb') as f:
                for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
            inventory.append(dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest()))
    result=dict(distinct_meter_time_keys=total[0],physical_households=total[1],duplicate_excess=total[2],
                accessible_quality=access,files=inventory,total_bytes=sum(x['bytes'] for x in inventory),
                heldout_access='identity/count columns and opaque file hashing only; no sealed kWh summaries',
                seconds=time.perf_counter()-start)
    Path('manifests/regional_durable_artifacts.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))


if __name__=='__main__':main()
