import unittest

from src.bos_dag.builder import Builder


class TestDAG(unittest.TestCase):
    def test_variable_extend(self):
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
        a = Builder(dct, [{"target": ""}])
        output = a.build()
        output[":B"]
        self.assertEqual(
            expected,
            output[":B"]["variables"]["variable1"]
        )

    def test_variable_override(self):
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
        a = Builder(dct, targets)
        output = a.build()
        self.assertEqual(
            expected,
            output[":B"]["variables"]["variable1"]
        )
