from datetime import datetime, timezone
from pathlib import Path
import yaml
from scripts.build_dashboard import summarize, render


def test_failed_requests_stay_in_error_and_retrieval_denominators():
    records = [
        {'event':'request_received','ts':'2026-09-29T07:41:00Z'},
        {'event':'request_received','ts':'2026-09-29T07:41:01Z'},
        {'event':'response_sent','ts':'2026-09-29T07:41:02Z','latency_ms':100,'ttft_ms':20,'tokens_in':10,'tokens_out':30,'cost_usd':0.01,'quality_score':0.9,'tool_name':'retrieval','tool_success':True},
        {'event':'request_failed','ts':'2026-09-29T07:41:03Z','error_type':'RuntimeError','tool_name':'retrieval','tool_success':False},
    ]
    summary = summarize(records)
    assert summary['requests'] == 2
    assert summary['errors'] == {'Error %':50.0,'Retrieval success %':50.0}
    assert summary['latency']['P95'] == 100
    assert summary['tokens'] == {'Input':10,'Output':30}
    config = yaml.safe_load(Path('config/dashboard.yaml').read_text())['dashboard']
    slo = yaml.safe_load(Path('config/slo.yaml').read_text())
    html, data = render(records,config,slo,datetime(2026,9,29,7,41,tzinfo=timezone.utc),datetime(2026,9,29,7,42,tzinfo=timezone.utc),'test',live=True)
    assert html.count('<section>') == 6
    assert 'percent · ≤ 2' in html and 'percent · ≥ 90' in html
    assert 'http-equiv="refresh" content="30"' in html
    assert data['requests'] == 2


def test_empty_dashboard_does_not_report_zero_errors_as_success():
    summary = summarize([])
    assert summary['errors']['Error %'] is None
    assert summary['errors']['Retrieval success %'] is None
    assert summary['latency']['P95'] is None
    assert summary['quality']['Mean'] is None
