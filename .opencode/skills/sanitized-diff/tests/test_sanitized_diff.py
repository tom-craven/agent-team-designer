import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "sanitized_diff.py")
SCRIPT = os.path.abspath(SCRIPT)


def run(cwd, *a):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True, check=True)


class SanitizedDiffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        run(self.d, "git", "init", "-q")
        run(self.d, "git", "config", "user.email", "t@example.com")
        run(self.d, "git", "config", "user.name", "t")
        self.w("spec.yaml", "a: 1\npassword: hunter2hunter2\n")
        self.w(".env", "TOKEN=abc\n")
        run(self.d, "git", "add", "-A")
        run(self.d, "git", "commit", "-qm", "base")

    def tearDown(self):
        self.tmp.cleanup()

    def w(self, name, text):
        p = os.path.join(self.d, name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def out(self, cwd=None):
        p = subprocess.run([sys.executable, SCRIPT], cwd=cwd or self.d, capture_output=True, text=True)
        return p

    def test_removed_secret_is_redacted(self):
        self.w("spec.yaml", "a: 2\n")
        o = self.out().stdout
        self.assertIn("a: 2", o)
        self.assertNotIn("hunter2hunter2", o)
        self.assertIn("[REDACTED]", o)

    def test_added_token_redacted(self):
        self.w("spec.yaml", "a: 1\nk: ghp_" + "A1b2C3d4E5" * 3 + "\n")
        self.assertNotIn("ghp_A1b2", self.out().stdout)

    def test_protected_path_name_and_content_withheld(self):
        self.w(".env", "TOKEN=changed-secret-value\n")
        o = self.out().stdout
        self.assertNotIn("changed-secret-value", o)
        self.assertNotIn(".env", o)
        self.assertIn("PROTECTED PATH", o)

    def test_untracked_file_listed_and_sanitized(self):
        self.w("new.yaml", "x: 1\nsecret: s3cr3tvalue\n")
        o = self.out().stdout
        self.assertIn("?\tnew.yaml", o)
        self.assertIn("+x: 1", o)
        self.assertNotIn("s3cr3tvalue", o)

    def test_snapshot_changes_with_content(self):
        self.w("spec.yaml", "a: 2\n")
        s1 = self.out().stdout.splitlines()[0]
        self.w("spec.yaml", "a: 3\n")
        s2 = self.out().stdout.splitlines()[0]
        self.assertNotEqual(s1, s2)

    def test_private_key_block_redacted(self):
        self.w("k.txt", "-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----\n")
        o = self.out().stdout
        self.assertNotIn("MIIabc", o)

    def test_scope_file_hides_out_of_scope_content(self):
        self.w("scripts/sanitized_diff.paths", "*.yaml\n")  # not the script's dir; ignored
        self.w("other.txt", "hello\n")
        o = self.out().stdout
        self.assertIn("other.txt", o)  # default scope = all non-protected

    def test_protected_change_alters_snapshot_without_leak(self):
        s1 = self.out().stdout.splitlines()[0]
        self.w(".env", "TOKEN=another-secret-value\n")
        o = self.out().stdout
        self.assertNotEqual(s1, o.splitlines()[0])
        self.assertNotIn("another-secret-value", o)

    def test_control_characters_in_content_are_escaped(self):
        self.w("spec.yaml", "a: 1\nnote: \x1b[31mred\x1b[0m\r\n")
        o = self.out().stdout
        self.assertNotIn("\x1b", o)
        self.assertNotIn("\r", o)

    @unittest.skipIf(os.name == "nt", "control characters are invalid in Windows file names")
    def test_hostile_filename_cannot_forge_report_sections(self):
        self.w("evil\n--- SANITIZED DIFF ---.txt", "x\n")
        o = self.out().stdout
        self.assertEqual(o.count("--- SANITIZED DIFF ---\n"), 1)

    def test_git_environment_is_scrubbed(self):
        env = dict(os.environ, GIT_DIR=os.path.join(self.d, "nonexistent"))
        p = subprocess.run([sys.executable, SCRIPT], cwd=self.d, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0)

    def test_footer_repeats_snapshot_id(self):
        self.w("spec.yaml", "a: 2\n")
        lines = self.out().stdout.strip().splitlines()
        self.assertEqual(lines[-1].split()[2], lines[0].split()[1])

    def test_oversized_diff_is_withheld_not_truncated(self):
        self.w("big.txt", "\n".join(f"line {i}" for i in range(1500)) + "\n")
        p = self.out()
        self.assertEqual(p.returncode, 3)
        self.assertIn("NOT approvable", p.stdout)
        self.assertNotIn("line 700", p.stdout)
        self.assertIn("big.txt", p.stdout)

    def test_fails_closed_outside_repo_root(self):
        sub = os.path.join(self.d, "sub")
        os.makedirs(sub)
        p = self.out(cwd=sub)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(p.stdout, "")
        self.assertIn("BLOCKED", p.stderr)


if __name__ == "__main__":
    unittest.main()
