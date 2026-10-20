"""Synthetic source and ownership fixtures; no engine or console execution."""
import hashlib
import io
import contextlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
import urllib.request

from ps5fwlab.webkit_patch import (
    CSS_PATH, FONT_PATH, classify_snapshot, compare_snapshots, fetch_snapshot,
    inspect_functions, model_client_iteration, model_load_lifetime, render_report,
)


def sources(guard=False, pin=False):
    call = "if (clients.contains(client)) callback(client);" if guard else "callback(client);"
    loop = "{ " + call + " }" if guard else call
    css = ("namespace WebCore {\nstatic void iterateClients(WeakHashSet<CSSFontFaceClient>& clients, "
           "const Function<void(CSSFontFaceClient&)>& callback) {\n"
           "for (auto& client : copyToVectorOf<Ref<CSSFontFaceClient>>(clients)) " + loop + "\n}\n}\n")
    backing = "protect(m_backing)" if pin else "m_backing"
    font = ("namespace WebCore {\nauto FontFace::loadForBindings() -> LoadedPromise& {\n"
            "m_mayLoadedPromiseBeScriptObservable = true;\n" + backing + "->load();\n"
            "return m_loadedPromise.get();\n}\n}\n")
    return {CSS_PATH: css.encode(), FONT_PATH: font.encode()}


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.refs = []
        for rev, guard, pin in (("1"*40, False, False), ("2"*40, True, True),
                                ("3"*40, False, True)):
            self.refs.append({"revision": rev, "label": "synthetic", "files": {
                path: hashlib.sha256(raw).hexdigest() for path, raw in sources(guard, pin).items()}})

    def snapshot(self, name="old", guard=False, pin=False, revision=None):
        root = self.root / name
        raw_files = sources(guard, pin)
        entries = []
        for path, raw in raw_files.items():
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
            entries.append({"path": path, "sha256": hashlib.sha256(raw).hexdigest(),
                            "origin_url": "https://example.invalid/synthetic"})
        manifest = {"schema_version": 1, "label": name,
                    "provenance": {"kind": "synthetic", "revision": revision}, "files": entries}
        p = root / "snapshot.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        return p

    def inspect(self, path):
        return classify_snapshot(path, references=self.refs)

    def test_known_unprotected_pair_is_source_verified_only(self):
        report = self.inspect(self.snapshot())
        self.assertEqual(report["classification"], "VULNERABLE IMPLEMENTATION — VERIFIED")
        self.assertEqual(report["ps5_1410_classification"], "INSUFFICIENT EVIDENCE")

    def test_known_pair_with_both_safeguards_is_patched(self):
        r = self.inspect(self.snapshot(guard=True, pin=True))
        self.assertEqual(r["classification"], "PATCHED — VERIFIED")
        self.assertEqual(r["functions"]["client_iteration"]["state"], "guarded")

    def test_lifetime_only_backport_is_not_called_unpatched_uaf(self):
        r = self.inspect(self.snapshot(pin=True))
        self.assertEqual(r["classification"], "MODIFIED / AMBIGUOUS")
        self.assertEqual(r["functions"]["backing_load"]["state"], "pinned")
        self.assertEqual(r["functions"]["client_iteration"]["state"], "unguarded")

    def test_changed_hash_rejects_tampered_source(self):
        p = self.snapshot()
        (p.parent / FONT_PATH).write_bytes(b"tampered")
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_modified_complete_file_with_matching_function_is_ambiguous(self):
        p = self.snapshot()
        f = p.parent / CSS_PATH
        f.write_bytes(f.read_bytes() + b"\nvoid unrelatedChange() {}\n")
        data = json.loads(p.read_text())
        data["files"][0]["sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
        p.write_text(json.dumps(data))
        self.assertEqual(self.inspect(p)["classification"], "MODIFIED / AMBIGUOUS")

    def test_revision_label_cannot_override_file_hashes(self):
        p = self.snapshot(revision="2"*40)
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_target_claim_does_not_authenticate_firmware(self):
        p = self.snapshot()
        d = json.loads(p.read_text())
        d["provenance"].update({"target": "PS5", "firmware": "14.10",
                                "target_mapping_verified": True, "user_agent": "AppleWebKit/605.1.15"})
        p.write_text(json.dumps(d))
        self.assertEqual(self.inspect(p)["ps5_1410_classification"], "INSUFFICIENT EVIDENCE")

    def test_missing_component_is_explicit(self):
        p = self.snapshot()
        for path in (CSS_PATH, FONT_PATH): (p.parent / path).unlink()
        self.assertEqual(self.inspect(p)["classification"], "COMPONENT NOT FOUND")

    def test_one_missing_file_is_insufficient(self):
        p = self.snapshot()
        (p.parent / FONT_PATH).unlink()
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_no_manifest_is_insufficient(self):
        self.assertEqual(self.inspect(self.root / "missing.json")["classification"], "INSUFFICIENT EVIDENCE")

    def test_path_traversal_is_rejected(self):
        p = self.snapshot()
        d = json.loads(p.read_text());d["files"][0]["path"] = "../outside.cpp"
        p.write_text(json.dumps(d))
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_compare_cites_changed_function_and_hashes(self):
        a,b=self.snapshot(),self.snapshot("fixed",True,True)
        r=compare_snapshots(a,b,references=self.refs)
        self.assertTrue(r["function_changes"])
        self.assertIn("PATCHED — VERIFIED", render_report(r))
        self.assertIn("sha256", json.dumps(r))

    def test_fetch_requires_audited_full_revision_before_network(self):
        with self.assertRaises(ValueError): fetch_snapshot("main", self.root / "download")
        self.assertFalse((self.root / "download").exists())

    def test_fetch_refuses_existing_directory(self):
        with self.assertRaises(FileExistsError): fetch_snapshot("1"*40,self.root,references=self.refs)

    def test_invalid_manifest_root_is_insufficient(self):
        p=self.root / "invalid.json";p.write_text("[]")
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_invalid_provenance_is_insufficient(self):
        p=self.snapshot();d=json.loads(p.read_text());d["provenance"]=[];p.write_text(json.dumps(d))
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_excessive_json_nesting_returns_insufficient(self):
        p=self.root / "nested.json"
        p.write_text('{"schema_version":1,"files":[],"extra":'+'['*20000+'0'+']'*20000+'}')
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_parsable_but_deep_metadata_is_rejected(self):
        p=self.root / "nested.json"
        p.write_text('{"schema_version":1,"files":[],"extra":'+'['*100+'0'+']'*100+'}')
        self.assertEqual(self.inspect(p)["classification"], "INSUFFICIENT EVIDENCE")

    def test_download_hash_mismatch_creates_no_snapshot(self):
        def opener(url, timeout):
            stream=io.BytesIO(b"wrong source");stream.geturl=lambda:url;return stream
        target=self.root / "download"
        with self.assertRaises(ValueError): fetch_snapshot("1"*40,target,references=self.refs,opener=opener)
        self.assertFalse(target.exists())

    def test_download_uses_pinned_bytes_and_official_full_commit_urls(self):
        pair=sources();calls=[]
        def opener(url, timeout):
            calls.append(url)
            body=pair[next(name for name in pair if url.endswith(name))]
            stream=io.BytesIO(body);stream.geturl=lambda:url;return stream
        p=fetch_snapshot("1"*40,self.root / "download",references=self.refs,opener=opener)
        self.assertEqual(self.inspect(p)["classification"], "VULNERABLE IMPLEMENTATION — VERIFIED")
        self.assertTrue(all(url.startswith("https://raw.githubusercontent.com/WebKit/WebKit/"+"1"*40) for url in calls))

    def test_redirect_is_rejected_without_snapshot(self):
        def opener(url, timeout):
            stream=io.BytesIO(b"source");stream.geturl=lambda:"https://example.invalid";return stream
        with self.assertRaises(ValueError): fetch_snapshot("1"*40,self.root / "download",references=self.refs,opener=opener)

    def test_redirect_is_blocked_before_contacting_another_host(self):
        from ps5fwlab.webkit_patch import NoSourceRedirect
        handler=NoSourceRedirect()
        request=urllib.request.Request('https://raw.githubusercontent.com/WebKit/WebKit/'+'1'*40+'/'+CSS_PATH)
        with self.assertRaises(ValueError):
            handler.redirect_request(request,None,302,'Found',{},'http://127.0.0.1/private')

    def test_unified_cli_emits_source_and_target_classifications(self):
        from tools.ps5_research import main
        p=self.snapshot();out=io.StringIO()
        with contextlib.redirect_stdout(out):
            main(["--webkit-snapshot",str(p),"--format","json"])
        report=json.loads(out.getvalue())
        # Synthetic files are not in the shipped production reference catalog.
        self.assertEqual(report["classification"], "MODIFIED / AMBIGUOUS")
        self.assertEqual(report["ps5_1410_classification"], "INSUFFICIENT EVIDENCE")


class SignatureTests(unittest.TestCase):
    def test_comments_and_strings_cannot_fake_a_function(self):
        css = '/* void iterateClients() { if (clients.contains(client)) callback(client); } */\n'
        font = 'const char* s = "FontFace::loadForBindings() { protect(m_backing)->load(); }";'
        r = inspect_functions(css,font)
        self.assertEqual(r["client_iteration"]["state"], "unrecognized")
        self.assertEqual(r["backing_load"]["state"], "unrecognized")

    def test_guard_mentioned_after_callback_is_not_a_patch(self):
        pair=sources();css=pair[CSS_PATH].decode().replace("callback(client);", "callback(client); clients.contains(client);")
        self.assertEqual(inspect_functions(css,pair[FONT_PATH].decode())["client_iteration"]["state"], "unrecognized")

    def test_truncated_body_is_detected(self):
        pair=sources()
        r=inspect_functions(pair[CSS_PATH].decode()[:-5],pair[FONT_PATH].decode())
        self.assertEqual(r["client_iteration"]["state"], "incomplete")

    def test_duplicate_function_definitions_are_ambiguous(self):
        pair=sources();css=pair[CSS_PATH].decode()
        self.assertEqual(inspect_functions(css+css,pair[FONT_PATH].decode())["client_iteration"]["state"], "unrecognized")


class LifetimeModelTests(unittest.TestCase):
    def test_removing_future_client_skips_it_only_with_guard(self):
        actions={"A": {"remove": ["B"]}}
        self.assertEqual(model_client_iteration(["A","B"],actions,False)["callbacks"],["A","B"])
        self.assertEqual(model_client_iteration(["A","B"],actions,True)["callbacks"],["A"])

    def test_added_client_is_not_in_current_snapshot(self):
        r=model_client_iteration(["A","B"],{"A":{"add":["C"]}},True)
        self.assertEqual(r["callbacks"],["A","B"])
        self.assertIn("C",r["live_clients"])

    def test_order_dependence_is_explicit(self):
        outcomes=[]
        for order in itertools.permutations(["A","B"]):
            outcomes.append(model_client_iteration(order,{"A":{"remove":["B"]}},True)["callbacks"])
        self.assertIn(["A"],outcomes);self.assertIn(["B","A"],outcomes)

    def test_removing_self_does_not_cancel_current_callback(self):
        r=model_client_iteration(["A","B"],{"A":{"remove":["A"]}},True)
        self.assertEqual(r["callbacks"],["A","B"])

    def test_lifetime_pin_keeps_backing_alive_during_reentry(self):
        self.assertFalse(model_load_lifetime(False)["alive_when_load_resumes"])
        fixed=model_load_lifetime(True)
        self.assertTrue(fixed["alive_when_load_resumes"])
        self.assertEqual(fixed["owners_after_return"],0)


if __name__ == "__main__": unittest.main()
