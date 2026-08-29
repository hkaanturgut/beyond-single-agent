# Captured terminal output

Real runs against a live Foundry project. Tab-separated:
`<seconds-since-start>\t<line>`. The endpoint is scrubbed.

| File | Shows | Real duration |
|---|---|---|
| `01-deploy.tsv` | three agents created in Foundry | 2.1s |
| `02-valletta.tsv` | fan-out, fan-in, within budget | 39.7s |
| `03-tokyo-overbudget.tsv` | the conditional edge firing | 58.6s |
| `brief-valletta.md` | actual output | — |
| `brief-tokyo.md` | actual output, post-revision | — |

Replay these as an animated terminal rather than shipping video. Compress the
gaps — 22 seconds of two agents thinking is correct behaviour and terrible
theatre — but show the real elapsed time on screen so nothing is misrepresented.

Re-capture with:

```bash
python3 -u deploy_agents.py 2>&1 | python3 -u stamp.py > 01-deploy.tsv
```

`python3 -u` matters. Without it the pipe buffers and every line lands on the
same timestamp, which looks like it worked.
