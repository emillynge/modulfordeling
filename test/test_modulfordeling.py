from modulfordeling import modulfordeling

MODULER_PATH = "test/moduler.yaml"
PRIO_PATH = "test/priorities.csv"


def test_read_moduler() -> None:
    moduler = modulfordeling.read_moduler(MODULER_PATH)
    assert moduler["pioner"].key == "pioner"
    assert moduler["pioner"].n_periods == 1


def test_read_prio() -> None:
    prio = modulfordeling.read_priorities(PRIO_PATH)
    assert len(prio) == 4


def test_problem() -> None:
    modulfordeling.init_problem(
        modulfordeling.read_priorities(PRIO_PATH),
        modulfordeling.read_moduler(MODULER_PATH),
    )
