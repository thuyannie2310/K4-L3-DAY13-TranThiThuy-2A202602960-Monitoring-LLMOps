"""Exercise the real ASGI app locally without pretending to create cloud traces."""
import asyncio
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from app.main import app


async def main():
    output={}
    payloads=[json.loads(line) for line in Path('data/sample_queries.jsonl').read_text().splitlines() if line.strip()]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local') as client:
        output['health']=(await client.get('/health')).json()
        for scenario in ('baseline','rag_slow','tool_fail','recovery'):
            if scenario in ('rag_slow','tool_fail'):
                await client.post(f'/incidents/{scenario}/enable')
            results=await asyncio.gather(*(client.post('/chat',json=p) for p in payloads))
            output[scenario]=[{'status':r.status_code,'correlation_id':r.headers['x-request-id'],**r.json()} for r in results]
            if scenario in ('rag_slow','tool_fail'):
                await client.post(f'/incidents/{scenario}/disable')
        output['metrics']=(await client.get('/metrics')).json()
    Path('submission/evidence/local-runtime.json').write_text(json.dumps(output,indent=2))


if __name__=='__main__':
    asyncio.run(main())
