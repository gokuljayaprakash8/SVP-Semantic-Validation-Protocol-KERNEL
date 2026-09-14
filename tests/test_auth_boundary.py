import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault(
    "SVP_AUTH_TOKENS",
    '{"test-client":{"token":"test-token-for-svp-auth-tests-123456","scopes":["audit:read","governance:evaluate","execution:execute"]}}',
)
os.environ.setdefault("SVP_CORS_ORIGINS", "http://localhost")

import app as app_module


class AuthenticationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_authenticator = app_module._authenticator
        cls.original_auth_configuration_error = app_module._auth_configuration_error

        app_module._authenticator = app_module.BearerTokenAuthenticator.from_json(
            '{"test-client":{"token":"test-token-for-svp-auth-tests-123456","scopes":["audit:read","governance:evaluate","execution:execute"]}}'
        )
        app_module._auth_configuration_error = None

        cls.client = TestClient(app_module.app)

    @classmethod
    def tearDownClass(cls):
        app_module._authenticator = cls.original_authenticator
        app_module._auth_configuration_error = cls.original_auth_configuration_error

    def _headers(self, token="test-token-for-svp-auth-tests-123456"):
        return {"Authorization": f"Bearer {token}"}

    def test_health_is_public(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_anonymous_govern_is_rejected(self):
        response = self.client.post(
            "/v1/govern",
            json={
                "principal": "agent",
                "agent": "test-agent",
                "delegation": {},
                "intent": "read data",
                "action": "read customer record",
                "resource": "crm://customer/1",
                "context": {},
                "state": {},
            },
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["error"], "AUTHENTICATION_REQUIRED")

    def test_anonymous_audit_is_rejected(self):
        response = self.client.post(
            "/v1/audit",
            json={"steps": ["read a synthetic record"]},
        )
        self.assertEqual(response.status_code, 401)

    def test_anonymous_audit_v06_is_rejected(self):
        response = self.client.post(
            "/v1/audit/v06",
            json={"steps": ["read a synthetic record"]},
        )
        self.assertEqual(response.status_code, 401)

    def test_anonymous_execution_is_rejected(self):
        response = self.client.post(
            "/v1/execute/v06-test",
            json={"action": "delete production data", "record": {}},
        )
        self.assertEqual(response.status_code, 401)

    def test_anonymous_audit_verify_is_rejected(self):
        response = self.client.get("/v1/audit/verify")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            "/v1/govern",
            json={
                "principal": "agent",
                "agent": "test-agent",
                "delegation": {},
                "intent": "read data",
                "action": "read customer record",
                "resource": "crm://customer/1",
                "context": {},
                "state": {},
            },
            headers=self._headers("definitely-not-a-valid-token"),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["error"], "INVALID_CREDENTIALS")

    def test_missing_scope_is_forbidden(self):
        original = app_module._authenticator
        try:
            app_module._authenticator = app_module.BearerTokenAuthenticator.from_json(
                '{"audit-only":{"token":"audit-only-test-token-123456","scopes":["audit:read"]}}'
            )

            response = self.client.post(
                "/v1/govern",
                json={
                    "principal": "agent",
                    "agent": "test-agent",
                    "delegation": {},
                    "intent": "read data",
                    "action": "read customer record",
                    "resource": "crm://customer/1",
                    "context": {},
                    "state": {},
                },
                headers={"Authorization": "Bearer audit-only-test-token-123456"},
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(
                response.json()["detail"]["error"],
                "INSUFFICIENT_SCOPE",
            )
        finally:
            app_module._authenticator = original

    def test_full_scope_token_can_reach_governance(self):
        response = self.client.post(
            "/v1/govern",
            json={
                "principal": "agent",
                "agent": "test-agent",
                "delegation": {},
                "intent": "read data",
                "action": "read customer record",
                "resource": "crm://customer/1",
                "context": {},
                "state": {},
            },
            headers=self._headers(),
        )
        self.assertEqual(response.status_code, 200)

    def test_execution_still_requires_governance_after_authentication(self):
        original = list(app_module.V06_EXECUTED_ACTIONS)
        try:
            response = self.client.post(
                "/v1/execute/v06-test",
                json={
                    "action": "delete production data",
                    "record": {},
                },
                headers=self._headers(),
            )

            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assertFalse(payload["executed"])
            self.assertEqual(
                payload["reason"],
                "REQUEST BINDING INVALID",
            )
            self.assertEqual(
                app_module.V06_EXECUTED_ACTIONS,
                original,
            )
        finally:
            app_module.V06_EXECUTED_ACTIONS[:] = original


if __name__ == "__main__":
    unittest.main()
