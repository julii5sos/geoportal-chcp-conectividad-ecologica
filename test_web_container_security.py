import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class WebContainerSecurityTests(unittest.TestCase):
    def test_container_runs_as_non_root_and_uses_bounded_gunicorn(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("--max-requests 50", dockerfile)
        self.assertIn("--timeout ${WEB_WORKER_TIMEOUT:-540}", dockerfile)
        self.assertNotIn("GEE_SERVICE_ACCOUNT_JSON=", dockerfile)
        self.assertNotIn("GOOGLE_APPLICATION_CREDENTIALS=", dockerfile)

    def test_build_context_excludes_common_credentials_and_local_state(self):
        dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8")
        for pattern in (
            ".streamlit/secrets.toml",
            ".env.*",
            "**/credentials*.json",
            "**/service-account*.json",
            "**/*.pem",
            "**/*.p12",
            "**/.config/gcloud",
        ):
            self.assertIn(pattern, dockerignore)

    def test_cloud_run_template_is_private_ready_and_conservative(self):
        template = (ROOT / "deploy" / "cloud-run-service.template.yaml").read_text(encoding="utf-8")
        self.assertIn('autoscaling.knative.dev/maxScale: "2"', template)
        self.assertIn("containerConcurrency: 4", template)
        self.assertIn("timeoutSeconds: 600", template)
        self.assertIn("WEB_MAX_CONCURRENT_ANALYSES", template)
        self.assertNotIn("private_key", template)


if __name__ == "__main__":
    unittest.main()
