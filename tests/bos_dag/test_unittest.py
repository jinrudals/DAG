"""Unit tests for DAG Builder logic such as variable resolution and overrides."""

import unittest

from src.dag.builder import Builder  # Make sure PYTHONPATH includes project root


class TestDAG(unittest.TestCase):
    """Test DAG Builder functionality."""

    def test_variable_extend(self):
        """Test cross-stage variable resolution using @{Stage.Var} syntax."""
        dct = {
            "A": {
                "variables": {
                    "variable1": "value1"
                }
            },
            "B": {
                "variables": {
                    "variable1": "@{A.variable1}"
                }
            }
        }
        expected = "value1"
        builder = Builder(dct, [{"target": ""}])
        output = builder.build()
        self.assertEqual(expected, output[":B"]["variables"]["variable1"])

    def test_variable_override(self):
        """Test overriding stage variables via target-specific configuration."""
        dct = {
            "A": {
                "variables": {
                    "variable1": "value1"
                }
            },
            "B": {
                "variables": {
                    "variable1": "@{A.variable1}"
                }
            }
        }

        targets = [
            {
                "target": "",
                "overrides": {
                    "B": {
                        "variables": {
                            "variable1": "2",
                            "variable2": "3"
                        }
                    }
                }
            }
        ]
        expected = "2"
        builder = Builder(dct, targets)
        output = builder.build()
        self.assertEqual(expected, output[":B"]["variables"]["variable1"])
