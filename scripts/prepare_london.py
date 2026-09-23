"""One official archive -> typed split/bucket Parquet, without held-out analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import time
import urllib.request
import zipfile

URL = 'https://data.london.gov.uk/download/vqm0d/3527bf39-d93e-4071-8451-df2ade1ea4f2/LCL-FullData.zip'
ROOT = Path('data/regional')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--download-only', action='store_true')
    args = p.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    out = Path('results/regional')
    out.mkdir(parents=True, exist_ok=True)
    archive = ROOT/'LCL-FullData.zip'
    if shutil.disk_usage(ROOT).free < 15_000_000_000:
        raise RuntimeError('Need 15 GB free before starting')
    start = time.perf_counter()
    downloaded=False
    download_seconds=0.0
    if not archive.exists():
        transfer_start=time.perf_counter()
        partial = archive.with_suffix('.partial')
        subprocess.run(['curl', '--fail', '--location', '--max-time', '1800',
                        '--max-filesize', '1000000000', '--output', str(partial), URL], check=True)
        partial.rename(archive)
        downloaded=True
        download_seconds=time.perf_counter()-transfer_start
    sha = hashlib.sha256()
    with archive.open('rb') as f:
        for chunk in iter(lambda: f.read(8*1024**2), b''):
            sha.update(chunk)
    z = zipfile.ZipFile(archive)
    manifest = dict(url=URL, license='CC BY 4.0',
        license_url='https://creativecommons.org/licenses/by/4.0/',
        attribution='UK Power Networks, Low Carbon London, London Datastore',
        bytes=archive.stat().st_size, sha256=sha.hexdigest(),
        files=[dict(name=x.filename, bytes=x.file_size) for x in z.infolist()],
        download_and_hash_seconds=time.perf_counter()-start,
        downloaded_this_invocation=downloaded,download_seconds=download_seconds,
        units='kWh per half-hour', timestamp='Source clock labels; UTC/DST convention not documented by catalog',
        heldout_policy='Only structural typing/partitioning/deduplication; no held-out demand summaries')
    Path('manifests/regional_source.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest), flush=True)
    if args.download_only:
        return
    import duckdb
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.csv as csv
    import pyarrow.parquet as pq
    stage = ROOT/'staging'
    final = ROOT/'parquet'
    if final.exists() and any(final.rglob('*.parquet')):
        raise RuntimeError('Final dataset exists; preserve it instead of overwriting')
    stage.mkdir(exist_ok=True)
    start = time.perf_counter()
    total = 0
    stages = []
    for info in z.infolist():
        if not info.filename.lower().endswith('.csv') or '__MACOSX' in info.filename:
            continue
        decoder = subprocess.Popen(['7z','x','-so',str(archive),info.filename],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        with decoder.stdout as stream:
            reader = csv.open_csv(stream, read_options=csv.ReadOptions(block_size=16*1024**2),
                                  convert_options=csv.ConvertOptions(column_types={
                                      'LCLid': pa.string(), 'stdorToU': pa.string(),
                                      'DateTime': pa.string(), 'KWH/hh (per half hour) ': pa.string(),
                                      'KWH/hh (per half hour)': pa.string()}))
            for idx, batch in enumerate(reader):
                before = time.perf_counter()
                names = batch.schema.names
                if len(names) != 4:
                    raise ValueError('Unexpected source schema: '+str(names))
                # Cast readings permissively in DuckDB so Null/invalid tokens remain NULL.
                raw = pa.Table.from_batches([batch]).rename_columns(['meter','tariff','clock','reading'])
                conn = duckdb.connect()
                conn.execute("SET threads=2")
                conn.register('raw', raw)
                tab = conn.execute("""SELECT meter, tariff,
                    try_cast(clock AS TIMESTAMP) AS timestamp,
                    CASE WHEN try_cast(reading AS DOUBLE)>=0 AND isfinite(try_cast(reading AS DOUBLE))
                         THEN try_cast(reading AS DOUBLE) ELSE NULL END AS kwh,
                    row_number() OVER () + ? AS source_row,
                    CASE WHEN clock >= '2012-01-01' AND clock < '2013-01-01' THEN 'train'
                         WHEN clock >= '2013-01-01' AND clock < '2013-04-01' THEN 'development'
                         ELSE 'sealed' END AS split,
                    try_cast(substr(meter, 4) AS INTEGER)%16 AS bucket
                    FROM raw""", [total]).fetch_arrow_table()
                conn.close()
                for split in ['train','development','sealed']:
                    selected = tab.filter(pc.equal(tab['split'], split))
                    if not len(selected):
                        continue
                    for bucket in range(16):
                        subset = selected.filter(pc.equal(selected['bucket'], bucket))
                        if len(subset):
                            folder = stage/split/str(bucket)
                            folder.mkdir(parents=True, exist_ok=True)
                            pq.write_table(subset.drop(['split','bucket']), folder/('%012d.parquet'%total),
                                           compression='zstd')
                total += len(tab)
                stages.append(dict(stage='stream_parse', rows=len(tab), seconds=time.perf_counter()-before,
                                   cumulative_rows=total, elapsed_seconds=time.perf_counter()-start,
                                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
                if idx % 30 == 0:
                    print('parsed',total,'rows',round(time.perf_counter()-start,1),'seconds',flush=True)
                if sum(x.stat().st_size for x in ROOT.rglob('*') if x.is_file()) > 29_000_000_000:
                    raise RuntimeError('Cache cap approaching')
        if decoder.wait() != 0:
            raise RuntimeError('7z archive decoder/CRC check failed')
    # Only keys/counts summarized for sealed partitions. Deterministic first source row
    # retained for duplicate keys; all duplicate keys excluded later from fit/replay.
    counts = []
    con = duckdb.connect()
    con.execute("SET memory_limit='2GB'; SET threads=4")
    con.execute("SET temp_directory='data/regional/duckdb_tmp'")
    for split in ['train','development','sealed']:
        for bucket in range(16):
            folder = stage/split/str(bucket)
            if not folder.exists():
                continue
            before = time.perf_counter()
            dest = final/split/('bucket=%02d'%bucket)
            dest.mkdir(parents=True, exist_ok=True)
            query = """SELECT meter, tariff, timestamp, kwh, source_row, duplicate_count
                FROM (SELECT *, count(*) OVER(PARTITION BY meter,timestamp) AS duplicate_count,
                    row_number() OVER(PARTITION BY meter,timestamp ORDER BY source_row) AS rn
                    FROM read_parquet(?)) WHERE rn=1 ORDER BY meter,timestamp"""
            relation=con.sql(query,params=[str(folder/'*.parquet')])
            relation.write_parquet(str(dest/'records.parquet'),compression='zstd')
            vals = con.execute("SELECT count(*),count(DISTINCT meter),sum(duplicate_count-1),"
                               "sum(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) FROM read_parquet(?)",
                               [str(dest/'records.parquet')]).fetchone()
            counts.append(dict(split=split,bucket=bucket,distinct_keys=vals[0],meters=vals[1],
                               duplicate_excess=vals[2],invalid_timestamps=vals[3]))
            stages.append(dict(stage='deduplicate_partition',rows=vals[0],seconds=time.perf_counter()-before,
                               peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024))
            shutil.rmtree(folder)
    con.close()
    result = dict(source_rows=total, partition_counts=counts, seconds=time.perf_counter()-start,
                  archive_bytes=archive.stat().st_size,
                  parquet_bytes=sum(x.stat().st_size for x in final.rglob('*.parquet')),
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                  stages=stages, schema=str(tab.schema),
                  duplicate_policy='First source row retained; every duplicate key excluded from model/replay',
                  invalid_policy='Negative/nonfinite/non-numeric readings become NULL; missing is not zero')
    (out/'ingestion.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Complete',total,'rows',result['seconds'],'seconds',flush=True)


if __name__ == '__main__':
    main()
