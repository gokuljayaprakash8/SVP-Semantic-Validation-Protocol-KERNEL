import unittest
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

import app as app_module


class _FakeEmbeddingModel:
    def embed(self, texts):
        return [np.ones(4, dtype=float) for _ in texts]


class ApplicationReadinessTests(unittest.TestCase):
    def setUp(self):
        self.original_model = app_module._model
        self.original_policy_vectors = app_module._policy_vectors
        self.original_pattern_meta = app_module._pattern_meta
        self.original_model_error = app_module._model_initialization_error
        self.original_policy_error = app_module._policy_initialization_error
        app_module._model = None
        app_module._policy_vectors = None
        app_module._pattern_meta = None
        app_module._model_initialization_error = None
        app_module._policy_initialization_error = None
        self.client = TestClient(app_module.app)

    def tearDown(self):
        app_module._model = self.original_model
        app_module._policy_vectors = self.original_policy_vectors
        app_module._pattern_meta = self.original_pattern_meta
        app_module._model_initialization_error = self.original_model_error
        app_module._policy_initialization_error = self.original_policy_error

    def test_health_is_lightweight_and_does_not_initialize_model(self):
        with patch.object(app_module, "_ensure_model_loaded") as ensure_model:
            response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        ensure_model.assert_not_called()

    def test_ready_reports_success_after_model_probe(self):
        with patch.object(
            app_module,
            "_build_embedding_model",
            return_value=_FakeEmbeddingModel(),
        ):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["checks"]["model"], "ok")
        self.assertEqual(payload["checks"]["governance"], "ok")
        self.assertEqual(
            payload["model"]["revision"],
            app_module.MODEL_REVISION,
        )

    def test_ready_reports_model_initialization_failure(self):
        with patch.object(
            app_module,
            "_build_embedding_model",
            side_effect=RuntimeError("model unavailable"),
        ):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "not_ready")
        self.assertEqual(
            response.json()["detail"]["error"],
            "MODEL_INITIALIZATION_FAILED",
        )

    def test_ready_reports_policy_initialization_failure(self):
        app_module._policy_initialization_error = ValueError("invalid policy")

        response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"]["error"],
            "POLICY_INITIALIZATION_FAILED",
        )
        self.assertEqual(
            response.json()["detail"]["checks"]["policy"],
            "error",
        )

    def test_audit_returns_structured_model_failure(self):
        with patch.object(
            app_module,
            "_build_embedding_model",
            side_effect=RuntimeError("model unavailable"),
        ):
            response = self.client.post(
                "/v1/audit",
                json={"steps": ["read a synthetic record"]},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["status"], "unavailable")
        self.assertEqual(
            response.json()["detail"]["error"],
            "MODEL_INITIALIZATION_FAILED",
        )


if __name__ == "__main__":
    unittest.main()