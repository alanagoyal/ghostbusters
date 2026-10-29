import unittest
from unittest.mock import Mock, patch

from backend.src.clients.baseten_client import BasetenClient
from backend.src.clients.vision import create_vision_client, vision_settings


class BasetenTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(
            "os.environ",
            {
                "BASETEN_API_KEY": "test-key",
                "BASETEN_MODEL_URL": "https://example.test/predict",
                "BASETEN_MODEL": "test-model",
            },
        ):
            self.client = BasetenClient()
        self.client.session = Mock()

    def test_classification_parses_fenced_json_and_bounds_request_time(self):
        response = self.client.session.post.return_value
        response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"classification":"Witch",'
                        '"confidence":0.9,'
                        '"description":"Pointed hat"}\n```'
                    }
                }
            ]
        }
        self.assertEqual(
            self.client.classify_costume(b"test-image"),
            ("Witch", 0.9, "Pointed hat"),
        )
        self.assertEqual(self.client.session.post.call_args.kwargs["timeout"], (10, 60))

    def test_connectivity_request_has_timeout(self):
        self.client.session.post.return_value.json.return_value = {"choices": []}
        self.assertTrue(self.client.test_connection())
        self.assertEqual(self.client.session.post.call_args.kwargs["timeout"], (10, 60))


class BasetenConfigurationTests(unittest.TestCase):
    def test_hosted_model_uses_configured_model_and_bearer_auth(self):
        with patch.dict(
            "os.environ",
            {
                "BASETEN_API_KEY": "test-key",
                "BASETEN_MODEL_URL": "https://inference.baseten.co/v1/chat/completions",
                "BASETEN_MODEL": "vision-model",
                "BASETEN_AUTH_SCHEME": "Bearer",
            },
        ):
            client = BasetenClient()
        self.assertEqual(client.model, "vision-model")
        self.assertEqual(client.session.headers["Authorization"], "Bearer test-key")

    def test_missing_or_blank_model_fails_without_inference(self):
        for model in (None, "", "   "):
            env = {
                "BASETEN_API_KEY": "test-key",
                "BASETEN_MODEL_URL": "https://example.test/predict",
            }
            if model is not None:
                env["BASETEN_MODEL"] = model
            with self.subTest(model=model), patch.dict("os.environ", env, clear=True):
                self.assertEqual(vision_settings()[2], model)
                with patch("requests.Session.post") as post:
                    for factory in (BasetenClient, create_vision_client):
                        with self.assertRaisesRegex(ValueError, "explicitly"):
                            factory()
                    post.assert_not_called()

    def test_legacy_model_can_still_be_selected_explicitly(self):
        with patch.dict("os.environ", {}, clear=True):
            client = BasetenClient(
                api_key="test-key",
                model_url="https://example.test/predict",
                model="gemma",
                auth_scheme="Api-Key",
            )
        self.assertEqual(client.model, "gemma")
