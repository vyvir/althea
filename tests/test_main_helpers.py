import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import main


class MainPathTests(unittest.TestCase):
    def test_resource_path_uses_repo_tree_when_not_installed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                path = main.resource_path("resources/version")
            finally:
                os.chdir(old_cwd)

        self.assertTrue(path.endswith("resources/version"))
        self.assertTrue(os.path.exists(path))

    def test_runtime_paths_resolve_from_data_directory(self):
        self.assertEqual(main.AltServer, os.path.join(main.altheapath, "AltServer"))
        self.assertEqual(
            main.AnisetteServer,
            os.path.join(main.altheapath, "anisette-server"),
        )
        self.assertEqual(main.AltStore, os.path.join(main.altheapath, "AltStore.ipa"))

    def test_install_log_helper_handles_missing_file_and_success(self):
        log_path = os.path.join(main.altheapath, "log.txt")
        if os.path.exists(log_path):
            os.remove(log_path)

        log_text = main.read_install_log(log_path)
        self.assertEqual(log_text, "")

        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write("Notify: Installation Succeeded\n")

        self.assertIn("Notify: Installation Succeeded", main.read_install_log(log_path))

    def test_parse_ios_version_handles_no_device_and_real_versions(self):
        original = main.ios_version
        try:
            main.ios_version = lambda: "result"  # ideviceinfo failed / no device
            self.assertIsNone(main.parse_ios_version())

            main.ios_version = lambda: "9.3"
            self.assertLess(main.parse_ios_version(), main.version.parse("15.0"))

            main.ios_version = lambda: "26.1"
            self.assertGreaterEqual(main.parse_ios_version(), main.version.parse("15.0"))
        finally:
            main.ios_version = original


if __name__ == "__main__":
    unittest.main()
