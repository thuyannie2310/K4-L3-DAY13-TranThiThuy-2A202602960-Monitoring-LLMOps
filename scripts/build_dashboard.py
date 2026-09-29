"""Render six dashboard panels from real JSONL events; no external assets."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import statistics

import yaml


def percentile(values, pct):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * pct / 100
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def summarize(records):
    received = [r for r in records if r['event'] == 'request_received']
    success = [r for r in records if r['event'] == 'response_sent']
    failures = [r for r in records if r['event'] == 'request_failed']
    tools = [r for r in success + failures if r.get('tool_name') == 'retrieval' and r.get('tool_success') is not None]
    traffic, cost = Counter(), defaultdict(float)
    for r in received:
        traffic[r['ts'][:16]] += 1
    for r in success:
        cost[r['ts'][:16]] += r['cost_usd']
    return {
        'latency': {**{f'P{p}': percentile([r['latency_ms'] for r in success], p) for p in (50,95,99)}, 'TTFT P95': percentile([r['ttft_ms'] for r in success],95)},
        'traffic': dict(sorted(traffic.items())),
        'errors': {'Error %': 100*len(failures)/len(received) if received else None, 'Retrieval success %': 100*sum(r['tool_success'] is True for r in tools)/len(tools) if tools else None},
        'cost': {**dict(sorted(cost.items())), 'Total': sum(cost.values())},
        'tokens': {'Input': sum(r['tokens_in'] for r in success), 'Output': sum(r['tokens_out'] for r in success)},
        'quality': {'Mean': statistics.mean(r['quality_score'] for r in success) if success else None},
        'error_types': dict(Counter(r['error_type'] for r in failures)),
        'requests': len(received),
    }


def render(records, config, slo, start, end, source, live=False):
    records = [r for r in records if start <= datetime.fromisoformat(r['ts'].replace('Z', '+00:00')) <= end]
    summary = summarize(records)
    sections = []
    for panel in config['panels']:
        values = summary[panel['id']]
        threshold = panel['threshold']['value']
        maximum = max([v for v in values.values() if v is not None] + [threshold, 1]) * 1.1
        if panel['id'] == 'errors':
            maximum = 100
        rows = []
        for label, value in values.items():
            applies = (panel['id'] not in ('latency', 'cost') or
                       (panel['id'] == 'latency' and label == 'P95') or
                       (panel['id'] == 'cost' and label == 'Total'))
            row_threshold = threshold
            operator = panel['threshold']['operator']
            if label == 'Retrieval success %':
                row_threshold = slo['guardrails']['retrieval_success_rate_pct_min']
                operator = 'gte'
            formatted = 'N/A' if value is None else f'{value:.6g}'
            width = 0 if value is None else value / maximum * 100
            marker = f'<em style="left:{row_threshold / maximum * 100}%"></em>' if applies else ''
            note = f' · {"≤" if operator == "lte" else "≥"} {row_threshold}' if applies else ''
            rows.append(f'<div class="row"><label>{escape(label)}<b>{formatted}</b></label><small>{escape(panel["unit"])}{note}</small><div class="bar"><i style="width:{width}%"></i>{marker}</div></div>')
        extra = f'<p>Error types: {escape(json.dumps(summary["error_types"]))}</p>' if panel['id'] == 'errors' else ''
        sections.append(f'<section><h2>{escape(panel["title"])}</h2>'+''.join(rows)+extra+'</section>')
    refresh = f'<meta http-equiv="refresh" content="{config["refresh_seconds"]}">' if live else ''
    mode = f'Live · refresh {config["refresh_seconds"]}s' if live else 'Frozen practice evidence · not official challenge'
    html = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Day13 — Monitoring & LLMOps</title>' + refresh + '<style>body{background:#101827;color:#e4edf9;font:14px system-ui;margin:24px}main{display:grid;grid-template-columns:1fr 1fr;gap:14px}section{background:#1c2940;padding:18px;border-radius:12px}h1{font-size:24px}h2{font-size:18px;margin:0 0 12px}p,small{color:#b4c6dd}label{display:flex;justify-content:space-between;gap:10px}.row{margin:10px 0}.bar{height:8px;background:#293d57;position:relative;margin-top:5px}i{display:block;background:#46cbb6;height:8px}em{position:absolute;background:#ffba69;width:2px;height:12px;top:-2px}footer{margin-top:16px;font-size:12px}b{color:#fff}</style><h1>K4-L3A · Day13 Monitoring &amp; LLMOps</h1>' + f'<p>Tran Thi Thuy · 2A202602960 · {mode}</p><p>UTC {start.isoformat()} → {end.isoformat()}<br>{summary["requests"]} requests · source: {escape(source)}</p><main>' + ''.join(sections) + '</main><footer>Orange lines apply only to the labeled metric. SLO: 99.5% successful requests within 3000 ms / 28 days.<br>Latency/TTFT, tokens, cost and quality use successful responses. Cost/tokens are simulated; quality is a heuristic.</footer></html>'
    return html, {'start':start.isoformat(), 'end':end.isoformat(), **summary}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--logs', default='data/logs.jsonl')
    parser.add_argument('--output', default='submission/evidence/11-dashboard.html')
    parser.add_argument('--end', help='ISO timestamp to reproduce a frozen 60-minute evidence window')
    parser.add_argument('--serve', action='store_true', help='Serve only the dashboard on localhost with live refresh')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    config = yaml.safe_load(Path('config/dashboard.yaml').read_text())['dashboard']
    slo = yaml.safe_load(Path('config/slo.yaml').read_text())
    def build():
        end = datetime.fromisoformat(args.end.replace('Z','+00:00')) if args.end else datetime.now(timezone.utc)
        if end.tzinfo is None:
            raise ValueError('--end must include a timezone')
        start = end - timedelta(minutes=config['time_range_minutes'])
        records = [json.loads(line) for line in Path(args.logs).read_text().splitlines() if line.strip()]
        return render(records, config, slo, start, end, args.logs, live=args.serve and not args.end)
    if args.serve:
        from http.server import BaseHTTPRequestHandler, HTTPServer
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path not in ('/', '/dashboard.json'):
                    self.send_error(404)
                    return
                html, data = build()
                payload = (json.dumps(data) if self.path.endswith('.json') else html).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json' if self.path.endswith('.json') else 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(payload)
        print(f'Dashboard: http://127.0.0.1:{args.port}', flush=True)
        HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
    else:
        html, data = build()
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(html, encoding='utf-8')
        output.with_suffix('.json').write_text(json.dumps(data, indent=2))
        print(f'Dashboard: {output}')


if __name__ == '__main__':
    main()
