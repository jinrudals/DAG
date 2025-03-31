import unittest

from src.bos_dag.builder import Builder


class Scenario(unittest.TestCase):
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
    pass