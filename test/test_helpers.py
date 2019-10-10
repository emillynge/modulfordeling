import pytest
from pyscipopt.scip import Model

from modulfordeling.scip_helpers import SparseMatrix


def test_matrix():
    m = SparseMatrix(Model("test"), ["hej", "med", "dig"], ["hello", "world"], "TEST")
    with pytest.raises(KeyError):
        m.make_var("hej", "dig")
    with pytest.raises(KeyError):
        m.make_var("hello", "world")

    m.make_var("med", "hello")
    m["med"]["hello"]
    str(m)
