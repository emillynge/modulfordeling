from collections import defaultdict
from typing import Dict, Iterable, List, Union

from pyscipopt.scip import ExprCons, Model, Variable

StrOrInt = Union[str, int]


class SparseMatrix(object):
    def __init__(
        self,
        model: Model,
        x_keys: Iterable[StrOrInt],
        y_keys: Iterable[StrOrInt],
        prefix: str,
    ):
        self.model = model
        self.prefix = prefix
        # self.variable_args = variable_args
        self.x_keys = set(iter(x_keys))
        self.y_keys = set(iter(y_keys))
        self.X_T: Dict[StrOrInt, Dict[StrOrInt, Variable]] = defaultdict(
            dict
        )  # ((y, dict()) for y in y_keys)
        self.X: Dict[StrOrInt, Dict[StrOrInt, Variable]] = defaultdict(
            dict
        )  # dict((x, dict()) for x in x_keys)

    def make_var(self, x: StrOrInt, y: StrOrInt):
        if x not in self.x_keys:
            raise KeyError(f"x={x} is not a valid key")
        if y not in self.y_keys:
            raise KeyError(f"y={y} is not a valid key")

        new_var: Variable = self.model.addVar(name=f"{self.prefix}_{x}_{y}", vtype="B")
        self.X[x][y] = new_var
        self.X_T[y][x] = new_var

    @property
    def x(self):
        for row_dict in self.X.values():
            yield row_dict.values()

    # def x_items(self):
    #     for row_dict in self.X.values():
    #         yield row_dict

    # def row_items(self, x_key):
    #     return self.X[x_key].items()

    # def col_items(self, y_key):
    #     return self.X_T[y_key].items()

    def row(self, x_key):
        return self.X[x_key].values()

    def col(self, y_key):
        return self.T[y_key].values()

    # @property
    # def y(self):
    #     for row_dict in self.X_T.values():
    #         yield row_dict.values()

    @property
    def T(self):
        return self.X_T

    def iter_flatten(self):
        for row_dict in self.X.values():
            for variable in row_dict.values():
                yield variable

    def flatten(self):
        return [var for var in self.iter_flatten()]

    def __str__(self):
        return "[" + ", ".join([str(x) for x in self.iter_flatten()]) + "]"

    def __getitem__(self, item):
        return self.X[item]


class Problem:
    z: SparseMatrix

    def __init__(self, name: str, x_keys: Iterable[str], y_keys: Iterable[str]):
        self.model = Model(name)
        self.X = SparseMatrix(self.model, x_keys, y_keys, "X")
        self.const: List[ExprCons] = list()
