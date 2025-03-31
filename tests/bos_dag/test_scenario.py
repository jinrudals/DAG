"""Unit tests for DAG Builder stage variable expansion."""

import unittest

from src.dag.builder import Builder  # Ensure PYTHONPATH includes the project root


class Scenario(unittest.TestCase):
    """Test scenarios for DAG builder."""

    def test_variable_extend(self):
        """Test variable resolution with cross-stage references."""
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
