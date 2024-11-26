# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
from __future__ import annotations

import unittest
from typing import Any, Optional, Sequence, TypeVar, Union

import parameterized

import onnxscript
import onnxscript.testing
from onnxscript import FLOAT, INT64, ir
from onnxscript.ir import _schemas

import unittest.mock
import onnx
_TestTypeVarConstraints = TypeVar("_TestTypeVarConstraints", INT64, FLOAT)
_TestTypeVarOneBound = TypeVar("_TestTypeVarOneBound", bound=INT64)
_TestTypeVarTwoBound = TypeVar("_TestTypeVarTwoBound", bound=Union[INT64, FLOAT])


class TypeConversionFunctionsTest(unittest.TestCase):
    @parameterized.parameterized.expand(
        [
            (
                "tensor_type_all",
                onnxscript.onnx_types.TensorType,
                {ir.TensorType(dtype) for dtype in ir.DataType},
            ),
            ("tensor_type", INT64, {ir.TensorType(ir.DataType.INT64)}),
            (
                "tensor_type_union",
                Union[INT64, FLOAT],
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "tensor_type_variadic_shape",
                INT64[...],
                {ir.TensorType(ir.DataType.INT64)},
            ),
            ("tensor_type_shape", INT64[10], {ir.TensorType(ir.DataType.INT64)}),
            (
                "type_var_constraints",
                _TestTypeVarConstraints,
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "type_bound_one",
                _TestTypeVarOneBound,
                {ir.TensorType(ir.DataType.INT64)},
            ),
            (
                "type_bound_two",
                _TestTypeVarTwoBound,
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "optional_tensor_type_all",
                Optional[onnxscript.onnx_types.TensorType],
                {ir.TensorType(dtype) for dtype in ir.DataType},
            ),
            (
                "optional_tensor_type",
                Optional[INT64],
                {ir.TensorType(ir.DataType.INT64)},
            ),
            (
                "optional_tensor_type_union",
                Optional[Union[INT64, FLOAT]],
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "optional_tensor_type_variadic_shape",
                Optional[INT64[...]],
                {ir.TensorType(ir.DataType.INT64)},
            ),
            (
                "optional_tensor_type_shape",
                Optional[INT64[10]],
                {ir.TensorType(ir.DataType.INT64)},
            ),
            (
                "optional_type_var_constraints",
                Optional[_TestTypeVarConstraints],
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "optional_type_bound_one",
                Optional[_TestTypeVarOneBound],
                {ir.TensorType(ir.DataType.INT64)},
            ),
            (
                "optional_type_bound_two",
                Optional[_TestTypeVarTwoBound],
                {ir.TensorType(ir.DataType.INT64), ir.TensorType(ir.DataType.FLOAT)},
            ),
            (
                "sequence_type_all",
                Sequence[onnxscript.onnx_types.TensorType],
                {ir.SequenceType(ir.TensorType(dtype)) for dtype in ir.DataType},
            ),
            (
                "sequence_type",
                Sequence[INT64],
                {ir.SequenceType(ir.TensorType(ir.DataType.INT64))},
            ),
            (
                "union_sequence_type",
                Union[Sequence[INT64], Sequence[FLOAT]],
                {
                    ir.SequenceType(ir.TensorType(ir.DataType.INT64)),
                    ir.SequenceType(ir.TensorType(ir.DataType.FLOAT)),
                },
            ),
            (
                "sequence_type_variadic_shape",
                Sequence[INT64[...]],
                {ir.SequenceType(ir.TensorType(ir.DataType.INT64))},
            ),
            (
                "sequence_type_shape",
                Sequence[INT64[10]],
                {ir.SequenceType(ir.TensorType(ir.DataType.INT64))},
            ),
            (
                "sequence_type_var_constraints",
                Sequence[_TestTypeVarConstraints],
                {
                    ir.SequenceType(ir.TensorType(ir.DataType.INT64)),
                    ir.SequenceType(ir.TensorType(ir.DataType.FLOAT)),
                },
            ),
            (
                "sequence_type_bound_one",
                Sequence[_TestTypeVarOneBound],
                {ir.SequenceType(ir.TensorType(ir.DataType.INT64))},
            ),
            (
                "sequence_type_bound_two",
                Sequence[_TestTypeVarTwoBound],
                {
                    ir.SequenceType(ir.TensorType(ir.DataType.INT64)),
                    ir.SequenceType(ir.TensorType(ir.DataType.FLOAT)),
                },
            ),
        ]
    )
    def test_pytype_to_ir_type(self, _, pytype: Any, expected: set[ir.TypeProtocol]):
        self.assertEqual(_schemas._get_allowed_types_from_type_annotation(pytype), expected)  # pylint: disable=protected-access

    @parameterized.parameterized.expand(
        [
            ("type_var", _TestTypeVarConstraints, "_TestTypeVarConstraints"),
            ("type_var_bound", _TestTypeVarOneBound, "_TestTypeVarOneBound"),
            (
                "optional_type_var",
                Optional[_TestTypeVarOneBound],
                "_TestTypeVarOneBound",
            ),
            (
                "sequence_type_var",
                Sequence[_TestTypeVarOneBound],
                "Sequence__TestTypeVarOneBound",
            ),
            ("normal_type", INT64, None),
            ("union_type", Union[INT64, FLOAT], None),
            ("optional_type", Optional[INT64], None),
            ("sequence_type", Sequence[INT64], None),
            ("optional_sequence_type", Optional[Sequence[INT64]], None),
            ("optional_union_type", Optional[Union[INT64, FLOAT]], None),
        ]
    )
    def test_get_type_constraint_name(self, _: str, pytype: Any, expected: str | None):
        self.assertEqual(_schemas._get_type_constraint_name(pytype), expected)  # pylint: disable=protected-access

    def test_convert_formal_parameter_plain_type(self):
        mock_param = unittest.mock.Mock()
        mock_param.type_str = "tensor(float)"
        mock_param.name = "param"
        mock_param.option = onnx.defs.OpSchema.FormalParameterOption.Single
        type_constraints = {}
        parameter = _schemas._convert_formal_parameter(mock_param, type_constraints)
        self.assertEqual(parameter.name, "param")
        self.assertTrue(ir.TensorType(ir.DataType.FLOAT) in parameter.type_constraint.allowed_types)


    def test_type_constraint_param_str_single_allowed_type(self):
        type_constraint = _schemas.TypeConstraintParam(
            name="TFloat",
            allowed_types={ir.TensorType(ir.DataType.FLOAT)}
        )
        expected_str = "TFloat=FLOAT"
        self.assertEqual(str(type_constraint), expected_str)


    def test_get_type_from_str_unknown_type_part(self):
        with self.assertRaises(ValueError) as context:
            _schemas._get_type_from_str("unknown(float)")
        self.assertIn("Unknown type part: 'unknown'", str(context.exception))


    def test_parameter_has_default(self):
        type_constraint = _schemas.TypeConstraintParam.any_tensor("T")
        param_with_default = _schemas.Parameter(
            name="param1", type_constraint=type_constraint, required=True, variadic=False, default=5
        )
        param_without_default = _schemas.Parameter(
            name="param2", type_constraint=type_constraint, required=True, variadic=False
        )
        self.assertTrue(param_with_default.has_default())
        self.assertFalse(param_without_default.has_default())


    def test_type_constraint_param_any_value(self):
        param = _schemas.TypeConstraintParam.any_value("TAny")
        expected_types = _schemas._ALL_VALUE_TYPES
        self.assertEqual(param.name, "TAny")
        self.assertEqual(param.allowed_types, expected_types)


    def test_type_constraint_param_any_tensor(self):
        param = _schemas.TypeConstraintParam.any_tensor("TFloat")
        expected_types = {ir.TensorType(dtype) for dtype in ir.DataType}
        self.assertEqual(param.name, "TFloat")
        self.assertEqual(param.allowed_types, expected_types)


    def test_empty_class_representation(self):
        empty_instance = _schemas._Empty()
        self.assertEqual(repr(empty_instance), "_EMPTY_DEFAULT")



if __name__ == "__main__":
    unittest.main()