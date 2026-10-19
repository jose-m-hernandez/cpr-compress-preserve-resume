"""Tests for the evals clean-room lint. Run with: python3 -m unittest discover tests"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

import cleanroom  # noqa: E402

CANARY = "zqcanary7731"
RUN = ROOT / "evals" / "run.py"


def lint_env(terms_file=None):
    env = {k: v for k, v in os.environ.items() if k != cleanroom.ENV_VAR}
    if terms_file is not None:
        env[cleanroom.ENV_VAR] = str(terms_file)
    return env


def run_cli(*args, env):
    return subprocess.run(
        [sys.executable, str(RUN), "lint", *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )


class CleanroomTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.terms = self.tmp / "terms.txt"
        self.terms.write_text(f"# comment\n\n{CANARY}\n", encoding="utf-8")
        self.rules = cleanroom.load_public(ROOT / "evals" / "cleanroom-public.txt")

    def scan_text(self, text, name="sample.txt"):
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return cleanroom.scan_file(path, name, self.rules, cleanroom.load_terms([self.terms]))

    def test_private_term_found_case_insensitively(self):
        hits = self.scan_text(f"clean line\nsee {CANARY.upper()} here\n")
        self.assertEqual(hits, [(2, "private-1:3")])

    def test_home_path_found_and_placeholder_not(self):
        path = "/" + "Users" + "/" + "someone" + "/work"
        self.assertEqual([h[1] for h in self.scan_text(path + "\n")], ["home-path-macos"])
        self.assertEqual(self.scan_text("/" + "Users" + "/<name>/work\n"), [])

    def test_dot_directory_forms_found(self):
        for prefix in ("~", "$" + "HOME", "${" + "HOME}"):
            with self.subTest(prefix=prefix):
                hits = self.scan_text(prefix + "/." + "config" + "/x\n")
                self.assertEqual(len(hits), 1, hits)
        self.assertEqual(self.scan_text("~/." + "<name>\n"), [])

    def test_email_and_key_shapes(self):
        self.assertEqual(self.scan_text("a@example.com b@example.org.\n"), [])
        self.assertEqual(len(self.scan_text("a@" + "other.io\n")), 1)
        self.assertEqual(len(self.scan_text("sk" + "-" + "A" * 24 + "\n")), 1)
        self.assertEqual(self.scan_text("ask-for-something-really-long-today\n"), [])

    def test_file_name_with_canary_found(self):
        hits = self.scan_text("harmless\n", name=f"{CANARY}.txt")
        self.assertEqual(hits, [(0, "private-1:3")])

    def test_path_option_finds_canary_in_single_file(self):
        extra = self.tmp / "extra.txt"
        extra.write_text(f"x\n{CANARY}\n", encoding="utf-8")
        proc = run_cli("--path", str(extra), env=lint_env(self.terms))
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{extra.as_posix()}:2: private-1:3", proc.stdout)

    def test_output_never_contains_term_text(self):
        extra = self.tmp / "extra.txt"
        extra.write_text(f"x\n{CANARY}\n", encoding="utf-8")
        proc = run_cli("--path", str(extra), env=lint_env(self.terms))
        self.assertNotIn(CANARY, proc.stdout)
        self.assertNotIn(CANARY, proc.stderr)

    def test_output_masks_canary_in_file_name(self):
        extra = self.tmp / f"{CANARY}.txt"
        extra.write_text("harmless\n", encoding="utf-8")
        proc = run_cli("--path", str(extra), env=lint_env(self.terms))
        self.assertEqual(proc.returncode, 1)
        self.assertIn(":0: private-1:3", proc.stdout)
        self.assertNotIn(CANARY, proc.stdout)
        self.assertNotIn(CANARY, proc.stderr)

    def test_path_parents_are_not_name_matched(self):
        deep = self.tmp / "private" / "tmp" / "var" / "folders" / "x"
        deep.mkdir(parents=True)
        msg = deep / "msg"
        msg.write_text("a harmless message\n", encoding="utf-8")
        for arg in (msg, deep):
            with self.subTest(arg=arg.name):
                proc = run_cli("--path", str(arg), env=lint_env(self.terms))
                # The repo scan also runs and sees the canary in this file, so judge
                # only findings reported for the --path target.
                self.assertNotIn(str(deep), proc.stdout)

    def test_canary_in_subdirectory_name_found_under_path_dir(self):
        sub = self.tmp / "d" / f"{CANARY}-sub"
        sub.mkdir(parents=True)
        (sub / "f.txt").write_text("harmless\n", encoding="utf-8")
        proc = run_cli("--path", str(self.tmp / "d"), env=lint_env(self.terms))
        self.assertEqual(proc.returncode, 1)
        self.assertIn(":0: private-1:3", proc.stdout)
        self.assertNotIn(CANARY, proc.stdout)

    def test_unset_terms_exit_3(self):
        proc = run_cli(env=lint_env())
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(proc.stdout.strip(), "cleanroom: private terms not configured")

    def test_missing_or_empty_terms_file_exit_3(self):
        empty = self.tmp / "empty.txt"
        empty.write_text("# only a comment\n", encoding="utf-8")
        for target in (empty, self.tmp / "absent.txt"):
            with self.subTest(target=target.name):
                out = io.StringIO()
                code = cleanroom.run_lint(ROOT, [], lint_env(target), out=out)
                self.assertEqual(code, 3)

    def test_repo_scan_is_clean(self):
        if not os.environ.get(cleanroom.ENV_VAR):
            self.skipTest("CPR_EVAL_PRIVATE_TERMS not set")
        proc = run_cli(env=dict(os.environ))
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertRegex(proc.stdout.strip().splitlines()[-1], r"^cleanroom: 0 findings ")


class HardeningTests(unittest.TestCase):
    """H3: fail closed, bounded regexes, normalization, scope."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.terms_file = self.tmp / "terms.txt"
        self.terms_file.write_text(CANARY + "\n", encoding="utf-8")
        self.rules = cleanroom.load_public(ROOT / "evals" / "cleanroom-public.txt")
        self.terms = cleanroom.load_terms([self.terms_file])

    def scan_bytes(self, data, name="s.txt"):
        path = self.tmp / name
        path.write_bytes(data)
        return cleanroom.scan_file(path, name, self.rules, self.terms)

    def labels(self, data):
        return sorted({label for _, label in self.scan_bytes(data)})

    # Fail closed.
    def run_lint(self, *extra):
        out = io.StringIO()
        code = cleanroom.run_lint(ROOT, list(extra), lint_env(self.terms_file), out=out)
        return code, out.getvalue()

    def test_missing_path_is_exit_3(self):
        code, out = self.run_lint(str(self.tmp / "absent"))
        self.assertEqual(code, 3)
        self.assertIn("scan incomplete", out)

    def test_dangling_symlink_is_exit_3(self):
        link = self.tmp / "dangling"
        link.symlink_to(self.tmp / "nowhere")
        self.assertEqual(self.run_lint(str(link))[0], 3)

    def test_a_symlinked_directory_is_exit_3_not_skipped(self):
        real = self.tmp / "real"
        real.mkdir()
        (real / "a.txt").write_text("x\n", encoding="utf-8")
        tree = self.tmp / "tree"
        tree.mkdir()
        (tree / "b.txt").write_text("x\n", encoding="utf-8")
        (tree / "link").symlink_to(real, target_is_directory=True)
        code, out = self.run_lint(str(tree))
        self.assertEqual(code, 3, out)
        self.assertIn("symlinked directory", out)
        with self.assertRaises(cleanroom.ScanError):
            cleanroom._walk(tree)

    def test_a_non_text_file_is_exit_3_but_utf16_with_a_bom_and_plain_text_are_scanned(self):
        for name, data in (("nul.bin", b"abc\x00def\n"), ("junk.bin", bytes(range(128, 256)) * 4)):
            tree = self.tmp / name.split(".")[0]
            tree.mkdir()
            (tree / name).write_bytes(data)
            code, out = self.run_lint(str(tree))
            self.assertEqual(code, 3, name)
            self.assertIn("non-text file", out)
            with self.assertRaises(cleanroom.ScanError):
                cleanroom._walk(tree)
        ok = self.tmp / "ok"
        ok.mkdir()
        (ok / "wide.txt").write_bytes("clean line\n".encode("utf-16"))  # BOM, and NUL bytes inside
        (ok / "plain.txt").write_text("clean line, caf\u00e9\n", encoding="utf-8")
        self.assertEqual([p.name for p in cleanroom._walk(ok)], ["plain.txt", "wide.txt"])
        empty_root = self.tmp / "emptyroot"
        empty_root.mkdir()
        findings, scanned = cleanroom.scan(empty_root, [ok], self.rules, self.terms)
        self.assertEqual((findings, scanned), ([], 2))

    @unittest.skipIf(os.geteuid() == 0, "root reads everything")
    def test_unreadable_file_and_unreadable_directory_are_exit_3(self):
        f = self.tmp / "locked.txt"
        f.write_text("x\n", encoding="utf-8")
        f.chmod(0)
        d = self.tmp / "lockeddir"
        d.mkdir()
        (d / "a.txt").write_text("x\n", encoding="utf-8")
        d.chmod(0)
        self.addCleanup(f.chmod, 0o644)
        self.addCleanup(d.chmod, 0o755)
        self.assertEqual(self.run_lint(str(f))[0], 3)
        self.assertEqual(self.run_lint(str(d))[0], 3)

    # ReDoS.
    def test_long_lines_finish_quickly(self):
        cases = ["a" * 200000, "a" * 200000 + "@", "a@" * 100000, "a@" + "b." * 100000, "a@b." + "c" * 200000,
                 "." * 200000, "a" * 200000 + "@" + "b" * 200000]
        for line in cases:
            with self.subTest(prefix=line[:6], size=len(line)):
                started = time.time()
                self.scan_bytes((line + "\n").encode("utf-8"))
                self.assertLess(time.time() - started, 2.0)

    def test_email_rule_is_bounded_but_still_matches_normal_addresses(self):
        self.assertEqual(self.labels(b"mail a@other.io now\n"), ["email-not-example"])
        self.assertEqual(self.labels(b"mail a@example.com now\n"), [])

    def test_ls_long_owner_flags_any_owner_but_user(self):
        row = "-rw-r--r--@ 1 {} staff 1234 " + "O" + "ct 16 10:02 notes.txt"
        self.assertEqual(self.labels(row.format("zed").encode()), ["ls-long-owner"])
        self.assertEqual(self.labels(row.format("user").encode()), [])
        self.assertEqual(self.labels(b'{"text": "drwxr-xr-x 3 zed staff 96 Oct 16 10:02 d\\n"}'), ["ls-long-owner"])
        self.assertEqual(self.labels(b"drwxr-xr-x 3 username staff 96 Oct 16 10:02 d"), ["ls-long-owner"])

    # Normalization.
    def test_zero_width_nbsp_nul_and_fullwidth_are_normalized(self):
        zw = "\u200b"
        self.assertTrue(self.labels(("zq" + zw + "canary" + "\u2060" + "7731\n").encode("utf-8")))
        self.assertTrue(self.labels(("zq\x00canary7731\n").encode("utf-8")))
        fullwidth = "".join(chr(ord(c) + 0xFEE0) for c in CANARY)
        self.assertTrue(self.labels((fullwidth + "\n").encode("utf-8")))
        home = "/" + "Users" + "\u00a0"  # NBSP must not hide a path boundary
        self.assertEqual(self.labels(("/" + "Users" + "/x\n").encode("utf-8")), ["home-path-macos"])
        self.assertEqual(self.labels((home + "\n").encode("utf-8")), [])

    def test_utf16_with_bom_is_decoded(self):
        self.assertTrue(self.labels(("see " + CANARY + "\n").encode("utf-16")))
        self.assertTrue(self.labels(("see " + CANARY + "\n").encode("utf-16-be").join([b"\xfe\xff", b""])))

    def test_term_split_across_two_lines_is_found(self):
        self.assertTrue(self.labels(b"zqcana\nry7731\n"))
        self.assertTrue(self.labels(b"zqcanary\n7731\n"))
        self.assertEqual(self.labels(b"zqcana\n\nry7731\n"), [])

    def test_escaped_home_paths(self):
        parts = "\\/" + "Users" + "\\/someone"
        self.assertEqual(self.labels((parts + "\n").encode("utf-8")), ["home-path-json-macos"])
        self.assertEqual(self.labels(("\\/" + "home" + "\\/someone\n").encode("utf-8")), ["home-path-json-linux"])
        self.assertEqual(self.labels(("%2F" + "Users" + "%2Fsomeone\n").encode("utf-8")), ["home-path-urlenc-macos"])
        self.assertEqual(self.labels(("%2f" + "home" + "%2fsomeone\n").encode("utf-8")), ["home-path-urlenc-linux"])
        self.assertEqual(self.labels(("\\/" + "Users" + "\\/<name>\n").encode("utf-8")), [])

    # Scope.
    def test_scope_covers_any_tests_path_containing_evals_and_exempts_only_one_file(self):
        root = self.tmp / "repo"
        (root / "evals").mkdir(parents=True)
        (root / "tests" / "deep" / "evals_sub").mkdir(parents=True)
        (root / "tests" / "other").mkdir(parents=True)
        (root / "evals" / "cleanroom-public.txt").write_text("x\ty\n", encoding="utf-8")
        home = "/" + "Users" + "/someone"
        (root / "tests" / "deep" / "evals_sub" / "a.txt").write_text(home + "\n", encoding="utf-8")
        (root / "tests" / "other" / "x.py").write_text(home + "\n", encoding="utf-8")
        (root / "tests" / "test_evals_cleanroom.py").write_text(home + "\n", encoding="utf-8")
        (root / "tests" / "deep" / "test_evals_cleanroom.py").write_text(home + "\n", encoding="utf-8")
        found, _ = cleanroom.scan(root, [], self.rules, self.terms)
        paths = sorted({rel for rel, _, _ in found})
        self.assertEqual(paths, ["tests/deep/evals_sub/a.txt", "tests/deep/test_evals_cleanroom.py"])

    def test_raw_directories_are_skipped_anywhere_under_evals_but_other_files_are_not(self):
        root = self.tmp / "repo"
        home = "/" + "Users" + "/someone"
        for sub in ("evals/results/x/_raw", "evals/_raw", "evals/results/x"):
            (root / sub).mkdir(parents=True, exist_ok=True)
            (root / sub / "log.txt").write_text(home + "\n", encoding="utf-8")
        found, _ = cleanroom.scan(root, [], self.rules, self.terms)
        self.assertEqual(sorted({rel for rel, _, _ in found}), ["evals/results/x/log.txt"])
        explicit, _ = cleanroom.scan(root, [root / "evals" / "results" / "x"], self.rules, self.terms)
        self.assertIn("evals/results/x/_raw/log.txt", {rel for rel, _, _ in explicit})  # --path still scans everything


if __name__ == "__main__":
    unittest.main()
