"""Lightweight reliability checks (no API calls)."""

import os
import tempfile
import unittest
from pathlib import Path

from core.fault_tolerant_orchestrator import FaultTolerantOrchestrator
from utils.gemini_client import GeminiClient
from utils.output_paths import pptx_output_valid


class TestGeminiClientNoKey(unittest.TestCase):
    def test_no_key_has_logger_and_safe_generate(self):
        client = GeminiClient(api_key="")
        self.assertIsNotNone(client.logger)
        self.assertIsNone(client.model)
        out = client.generate_response("hello")
        self.assertIn("not configured", out.lower())

    def test_structured_response_empty_without_model(self):
        client = GeminiClient(api_key="")
        self.assertEqual(client.generate_structured_response("{}"), {})


class TestOutputPaths(unittest.TestCase):
    def test_pptx_output_valid(self):
        self.assertFalse(pptx_output_valid(None))
        self.assertFalse(pptx_output_valid(""))
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"x")
            path = f.name
        try:
            self.assertTrue(pptx_output_valid(path))
            os.truncate(path, 0)
            self.assertFalse(pptx_output_valid(path))
        finally:
            os.unlink(path)


class TestMainLogging(unittest.TestCase):
    def test_setup_logging_creates_parent_dir(self):
        import main as main_mod

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "deep" / "nested" / "run.log"
            self.assertFalse(log_path.parent.exists())
            main_mod.setup_logging(verbose=False, log_file=str(log_path))
            self.assertTrue(log_path.parent.is_dir())
            self.assertTrue(log_path.exists())


class TestFaultTolerantSchema(unittest.TestCase):
    def test_document_body_nested_schema(self):
        parser_like = {
            "parsed_data": {"sections": [{"title": "A"}], "elements": [{"type": "p"}], "title": "T"},
            "numeric_data": [],
        }
        body = FaultTolerantOrchestrator._document_body(parser_like)
        self.assertEqual(body.get("title"), "T")
        self.assertEqual(len(body.get("sections", [])), 1)


class TestRobustPipelineWritesPptx(unittest.TestCase):
    def test_robust_workflow_writes_nonzero_pptx(self):
        from agents import ParserAgent, PPTXGeneratorAgent
        from agents.insight_agent import InsightAgent
        from agents.storyline_agent import StorylineAgent
        from agents.slide_planning_agent import SlidePlanningAgent

        gc = GeminiClient(api_key="")
        agents = {
            "parser_agent": ParserAgent(),
            "insight_agent": InsightAgent(gc),
            "storyline_agent": StorylineAgent(gc),
            "slide_planning_agent": SlidePlanningAgent(gc),
            "pptx_generator_agent": PPTXGeneratorAgent(),
        }
        orch = FaultTolerantOrchestrator(agents)
        md = "# Hello\n\nSome **body** text.\n"
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            out = tmp.name
        try:
            orch.execute_workflow_robust({
                "markdown_content": md,
                "output_path": out,
                "slide_count": 5,
            })
            self.assertTrue(pptx_output_valid(out), "robust pipeline must write a non-empty PPTX")
        finally:
            if os.path.isfile(out):
                os.unlink(out)


if __name__ == "__main__":
    unittest.main()
