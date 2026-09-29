import asyncio
import json
import re

import httpx
import pytest
from app import logging_config
from app.main import app
from app.pii import scrub_text
from app.logging_config import scrub_event


@pytest.mark.parametrize('value,kind', [('012345678901','CCCD'),('4111 1111 1111 1111','CREDIT_CARD'),('4111-1111-1111-1111','CREDIT_CARD')])
def test_sensitive_identifiers(value,kind):
    assert scrub_text(value) == f'[REDACTED_{kind}]'


def test_nested_pii():
    result=scrub_event(None,'error',{'detail':'a@example.com','payload':{'items':[{'text':'+84 90 123 4567'}]},'exception':'a@example.com'})
    raw=json.dumps(result)
    assert 'a@example.com' not in raw
    assert '+84 90' not in raw


def test_concurrent_context_and_headers(monkeypatch,tmp_path):
    path=tmp_path/'logs.jsonl'
    monkeypatch.setattr(logging_config,'LOG_PATH',path)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
            async def send(i):
                return await client.post('/chat',headers={'x-request-id':f'req-{i:08x}'},json={'user_id':f'user-{i}','session_id':f'session-{i}','feature':'qa','message':'monitoring'})
            responses=await asyncio.gather(*(send(i) for i in range(4)))
            for i,response in enumerate(responses):
                assert response.status_code==200
                assert response.headers['x-request-id']==f'req-{i:08x}'
                assert float(response.headers['x-response-time-ms'])>=0
            response=await client.get('/health',headers={'x-request-id':'unsafe@example.com'})
            assert re.fullmatch(r'req-[0-9a-f]{8}',response.headers['x-request-id'])
    asyncio.run(run())
    events=[json.loads(line) for line in path.read_text().splitlines()]
    assert len(events)==8
    for event in events:
        i=int(event['correlation_id'][4:],16)
        assert event['session_id']==f'session-{i}'
        assert event['model'] and event['env']
