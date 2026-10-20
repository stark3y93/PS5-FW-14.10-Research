from __future__ import annotations

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .db import build_database, search, stats
from .ecosystem import update_files


def dashboard_data(path: str | Path) -> dict:
    with closing(sqlite3.connect(path)) as con:
        con.row_factory = sqlite3.Row
        findings = []
        for f in con.execute("SELECT * FROM finding ORDER BY id"):
            row = dict(f)
            row["evidence"] = [dict(x) for x in con.execute("SELECT source_id,kind,locator,supports,source_url FROM evidence WHERE finding_id=? ORDER BY id", (row["id"],))]
            row["firmware"] = [dict(x) for x in con.execute("SELECT firmware_id,relationship,status FROM finding_firmware WHERE finding_id=?", (row["id"],))]
            findings.append(row)
        fw = [dict(x) for x in con.execute("SELECT v.*, (SELECT count(*) FROM finding_firmware ff WHERE ff.firmware_id=v.id) AS linked_findings FROM firmware v ORDER BY version")]
        contradictions = []
        for x in con.execute("SELECT * FROM contradiction ORDER BY severity DESC,id"):
            row = dict(x)
            row["sources"] = [dict(s) for s in con.execute("SELECT cs.source_id, COALESCE(d.url,r.url) AS url, COALESCE(d.title,r.name) AS title FROM contradiction_source cs LEFT JOIN source d ON d.id=cs.source_id LEFT JOIN repository r ON r.id=cs.source_id WHERE cs.contradiction_id=?", (row["id"],))]
            contradictions.append(row)
        questions = []
        for x in con.execute("SELECT * FROM question ORDER BY rank"):
            row = dict(x)
            row["evidence"] = [dict(e) for e in con.execute("SELECT source_id,supports,source_url FROM question_evidence WHERE question_id=? ORDER BY source_id", (row["id"],))]
            questions.append(row)
        sources = [dict(x) for x in con.execute("SELECT id,title,url,kind,version_scope,provenance FROM source UNION ALL SELECT id,name,url||'/tree/'||commit_id,'repository',firmware_claim,license FROM repository ORDER BY title")]
        vulnerabilities = []
        for x in con.execute("SELECT * FROM vulnerability ORDER BY identifier"):
            row = dict(x)
            row["sources"] = [dict(s) for s in con.execute("SELECT vs.source_id, COALESCE(d.url,r.url) AS url FROM vulnerability_source vs LEFT JOIN source d ON d.id=vs.source_id LEFT JOIN repository r ON r.id=vs.source_id WHERE vs.vulnerability_id=?", (row["id"],))]
            vulnerabilities.append(row)
        experiments = [dict(x) for x in con.execute("SELECT * FROM experiment ORDER BY id")]
        projects = []
        for row in con.execute("SELECT r.id,r.name,r.url,r.commit_id,r.license,ep.categories,ep.maturity,ep.reuse_gate,ep.checked_at,ep.source_credibility FROM ecosystem_project ep JOIN repository r ON r.id=ep.repository_id ORDER BY r.name"):
            item = dict(row); item["categories"] = json.loads(item["categories"]); projects.append(item)
        claims = [dict(row) for row in con.execute("SELECT c.*,r.name AS project_name FROM compatibility_claim c JOIN repository r ON r.id=c.repository_id ORDER BY r.name,c.firmware_scope")]
        capabilities = []
        for row in con.execute("SELECT * FROM platform_capability ORDER BY name"):
            item = dict(row)
            item["projects"] = [dict(x) for x in con.execute("SELECT r.id,r.name,r.url FROM capability_project cp JOIN repository r ON r.id=cp.repository_id WHERE cp.capability_id=? ORDER BY r.name", (item["id"],))]
            item["dependencies"] = [dict(x) for x in con.execute("SELECT name,license,source_url FROM capability_dependency WHERE capability_id=? ORDER BY name", (item["id"],))]
            capabilities.append(item)
        observations = [dict(x) for x in con.execute("SELECT repository_name,event_type,title,source_url,upstream_updated_at,upstream_state,classification FROM source_observation ORDER BY observed_at DESC LIMIT 100")]
        candidates = [dict(x) for x in con.execute("SELECT repository_name,url,description,stars,pushed_at,first_seen,status FROM discovered_candidate ORDER BY pushed_at DESC")]
    return {"stats": stats(path), "findings": findings, "firmware": fw, "contradictions": contradictions, "questions": questions, "sources": sources, "vulnerabilities": vulnerabilities, "experiments": experiments, "ecosystem_projects": projects, "compatibility_claims": claims, "capabilities": capabilities, "source_observations": observations, "discovery_candidates": candidates}


def render_dashboard(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>PS5 Research Knowledge Base</title>
<style>body{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#17202a}h1,h2{color:#17365d}.cards{display:flex;flex-wrap:wrap;gap:.7rem}.card{border:1px solid #ccd5df;border-radius:8px;padding:.8rem;min-width:130px}input{padding:.7rem;width:min(100%,500px)}article{border-bottom:1px solid #ddd;padding:1rem 0}.tag{font-size:.8em;background:#e8eef5;padding:.2em .5em;border-radius:4px}small{color:#586575}li{margin:.5em 0}a{overflow-wrap:anywhere}</style>
<h1>PS5 firmware research knowledge base</h1><p>Static, source-linked snapshot generated from the local SQLite catalog. Classification and reproduction status are displayed as recorded.</p><section id="metrics" class="cards"></section><h2>Search findings and open questions</h2><input id="q" type="search" placeholder="Filter findings and open questions"><div id="findings"></div><ul id="questionMatches"></ul><h2>PC-only experiments and archive checks</h2><ul id="experiments"></ul><h2>Firmware version records</h2><p>No historical package cleared the Sony provenance gate; this catalog view is not a cross-package binary comparison.</p><table id="firmware"></table><h2>Tracked ecosystem projects</h2><table id="projects"></table><h2>Cross-project compatibility claims</h2><p>Project documentation, source observations and independently reproduced tests are separate evidence classes. Unknown ranges are not compatibility assertions.</p><table id="compatibility"></table><h2>Freedom OS capability and dependency matrix</h2><div id="capabilities"></div><h2>Unreviewed discovery candidates</h2><p>New repository matches remain candidates until a researcher verifies identity, license and evidence.</p><ul id="candidates"></ul><h2>Recent source activity</h2><ul id="activity"></ul><h2>Vulnerability identifiers and upstream scope</h2><ul id="vulnerabilities"></ul><h2>Contradictions to review</h2><ul id="contradictions"></ul><h2>Highest-ranked open questions</h2><ol id="questions"></ol><h2>Indexed sources</h2><ul id="sources"></ul>
<script>const D=__DATA__;const el=id=>document.getElementById(id);for(const [k,v] of Object.entries(D.stats)){let d=document.createElement('div');d.className='card';d.innerHTML='<b>'+String(v)+'</b><br>'+k.replaceAll('_',' ');el('metrics').append(d)}
function show(){let q=el('q').value.toLowerCase();el('findings').replaceChildren();el('questionMatches').replaceChildren();el('experiments').replaceChildren();for(const f of D.findings.filter(x=>(x.title+' '+x.summary+' '+x.scope+' '+x.firmware_relevance).toLowerCase().includes(q))){let a=document.createElement('article');let evidence=f.evidence.map(e=>'<li><a href="'+safe(e.source_url)+'">'+esc(e.source_id)+' — '+esc(e.locator)+'</a> <span class="tag">'+esc(e.kind)+'</span><br><small>'+esc(e.supports)+'</small></li>').join('');a.innerHTML='<h3>'+esc(f.title)+' <span class="tag">'+esc(f.classification)+'</span></h3><p>'+esc(f.summary)+'</p><small>'+esc(f.confidence)+' · '+esc(f.firmware_relevance)+' · '+esc(f.reproduction_status)+'</small><ul>'+evidence+'</ul>';el('findings').append(a)}for(const x of D.questions.filter(x=>(x.question+' '+x.rationale+' '+x.method).toLowerCase().includes(q))){let li=document.createElement('li');li.textContent='Q'+x.rank+': '+x.question+' ';for(const e of x.evidence){let a=document.createElement('a');a.href=safe(e.source_url);a.textContent=e.source_id+' ';li.append(a)}el('questionMatches').append(li)}for(const x of D.experiments.filter(x=>(x.title+' '+x.result+' '+x.firmware_relevance).toLowerCase().includes(q))){let li=document.createElement('li');li.innerHTML='<b>'+esc(x.title)+'</b> <span class="tag">'+esc(x.status)+'</span> — '+esc(x.result)+' <small>'+esc(x.confidence)+'; '+esc(x.firmware_relevance)+'; log: '+esc(x.log_path)+'</small> <a href="'+safe(x.source_url)+'">source</a>';el('experiments').append(li)}}function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function safe(s){s=String(s);return s.startsWith('https://')||s.startsWith('../../notes/')?esc(s):'#'}el('q').addEventListener('input',show);show();
const pt=el('projects');pt.innerHTML='<tr><th>Project</th><th>Categories</th><th>Pinned commit</th><th>License</th><th>Last checked</th><th>Source credibility and limits</th></tr>';for(const p of D.ecosystem_projects){let tr=document.createElement('tr'),a=document.createElement('a');a.href=safe(p.url);a.textContent=p.name;let first=document.createElement('td');first.append(a);tr.append(first);for(const v of [p.categories.join(', '),p.commit_id,p.license,p.checked_at,p.source_credibility+'; '+p.maturity+'; '+p.reuse_gate]){let td=document.createElement('td');td.textContent=v;tr.append(td)}pt.append(tr)}const ct=el('compatibility');ct.innerHTML='<tr><th>Project</th><th>Area</th><th>Firmware scope</th><th>Hardware</th><th>Evidence</th><th>Status</th><th>Notes</th></tr>';for(const c of D.compatibility_claims){let tr=document.createElement('tr');for(const v of [c.project_name,c.claim_type,c.firmware_scope,c.hardware_scope,c.evidence_class,c.status,c.notes]){let td=document.createElement('td');td.textContent=v||'unspecified';tr.append(td)}let a=document.createElement('a');a.href=safe(c.source_url);a.textContent='pinned source';tr.cells[4].append(document.createElement('br'),a);ct.append(tr)}for(const c of D.capabilities){let a=document.createElement('article'),deps=c.dependencies.map(x=>'<li>'+esc(x.name)+' — '+esc(x.license)+' (<a href="'+safe(x.source_url)+'">source</a>)</li>').join(''),projects=c.projects.map(x=>'<a href="'+safe(x.url)+'">'+esc(x.name)+'</a>').join(', ');a.innerHTML='<h3>'+esc(c.name)+'</h3><p>'+esc(c.status)+' · '+esc(c.platform)+' · '+esc(c.firmware_scope)+'</p><p>Projects: '+projects+'</p><p>'+esc(c.notes)+'</p><details><summary>Dependencies and licenses</summary><ul>'+deps+'</ul></details>';el('capabilities').append(a)}for(const c of D.discovery_candidates){let li=document.createElement('li'),a=document.createElement('a');a.href=safe(c.url);a.textContent=c.repository_name+' — '+c.status+'; '+c.stars+' stars; '+c.description;li.append(a);el('candidates').append(li)}for(const o of D.source_observations){let li=document.createElement('li'),a=document.createElement('a');a.href=safe(o.source_url);a.textContent=o.repository_name+' · '+o.event_type+' · '+o.title;li.append(a,document.createTextNode(' — '+o.classification+'; '+(o.upstream_state||'state unknown')+'; '+(o.upstream_updated_at||'date unknown')));el('activity').append(li)}
const t=el('firmware');t.innerHTML='<tr><th>Version</th><th>Build</th><th>Release date</th><th>Catalog status</th><th>Linked findings</th></tr>';for(const f of D.firmware){let tr=document.createElement('tr');for(const v of [f.version,f.build||'',f.release_date||'',f.status,f.linked_findings]){let td=document.createElement('td');td.textContent=v;tr.append(td)}t.append(tr)}for(const v of D.vulnerabilities){let li=document.createElement('li');li.textContent=v.identifier+' — '+v.title+' — '+v.upstream_status+': '+v.upstream_summary+' ';for(const s of v.sources){let a=document.createElement('a');a.href=safe(s.url);a.textContent=s.source_id+' ';li.append(a)}el('vulnerabilities').append(li)}for(const c of D.contradictions){let li=document.createElement('li');li.textContent=c.title+' ['+c.status+']: '+c.summary+' ';for(const s of c.sources){let a=document.createElement('a');a.href=safe(s.url);a.textContent=s.source_id+' ';li.append(a)}el('contradictions').append(li)}for(const q of D.questions){let li=document.createElement('li');li.textContent=q.question+' — priority '+q.priority_score+'/5 (relevance '+q.firmware_relevance+'/5); '+q.rationale+' ';for(const e of q.evidence){let a=document.createElement('a');a.href=safe(e.source_url);a.textContent=e.source_id+' ';li.append(a)}el('questions').append(li)}for(const s of D.sources){let li=document.createElement('li'),a=document.createElement('a');a.href=safe(s.url);a.textContent=s.title+' ['+s.id+']';li.append(a);li.append(document.createTextNode(' — '+s.kind+'; '+s.version_scope+'; '+s.provenance));el('sources').append(li)}</script></html>""".replace("__DATA__", payload)


def main() -> int:
    p = argparse.ArgumentParser(prog="ps5knowledge")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-db"); b.add_argument("--catalog", type=Path, default=Path("research/knowledge-base/catalog.json")); b.add_argument("--database", type=Path, default=Path("research/knowledge-base/ps5-research.sqlite3"))
    s = sub.add_parser("stats"); s.add_argument("--database", type=Path, default=Path("research/knowledge-base/ps5-research.sqlite3"))
    q = sub.add_parser("search"); q.add_argument("query"); q.add_argument("--limit", type=int, default=20); q.add_argument("--database", type=Path, default=Path("research/knowledge-base/ps5-research.sqlite3"))
    d = sub.add_parser("dashboard"); d.add_argument("--database", type=Path, default=Path("research/knowledge-base/ps5-research.sqlite3")); d.add_argument("--output", type=Path, default=Path("research/knowledge-base/dashboard.html"))
    u = sub.add_parser("update-sources"); u.add_argument("--ecosystem", type=Path, default=Path("research/knowledge-base/ecosystem.json")); u.add_argument("--state", type=Path, default=Path("research/knowledge-base/updates.json")); u.add_argument("--report", type=Path, default=Path("research/knowledge-base/update-report.md")); u.add_argument("--enable", action="store_true", help="explicitly override the default-disabled tracker setting")
    args = p.parse_args()
    if args.cmd == "build-db": result = build_database(args.catalog, args.database)
    elif args.cmd == "stats": result = stats(args.database)
    elif args.cmd == "search": result = search(args.database, args.query, args.limit)
    elif args.cmd == "update-sources": result = update_files(args.ecosystem, args.state, args.report, enable=args.enable)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(render_dashboard(dashboard_data(args.database)), encoding="utf-8"); result = {"dashboard": str(args.output)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
