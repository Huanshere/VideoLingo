"""Read literal task data, including the numeric repr used by NumPy 2."""
import ast
import math


class _NumpyNumbers(ast.NodeTransformer):
    def visit_Call(self, node):
        # Permit only np.float32/64(<numeric literal>), never arbitrary calls.
        func = node.func
        if not (isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                and func.value.id == 'np' and func.attr in ('float32', 'float64')
                and len(node.args) == 1 and not node.keywords):
            raise ValueError('Unsupported expression in task data')
        number = ast.literal_eval(node.args[0])
        if type(number) not in (int, float) or not math.isfinite(number):
            raise ValueError('Expected a finite numeric literal in NumPy task data')
        return ast.copy_location(ast.Constant(value=float(number)), node)


def parse_task_literal(value):
    if not isinstance(value, str):
        return value
    return ast.literal_eval(_NumpyNumbers().visit(ast.parse(value, mode='eval')))
