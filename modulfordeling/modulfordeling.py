import csv
from itertools import chain
from typing import Dict, List, NamedTuple

import yaml
from pyscipopt import quicksum

from .scip_helpers import Problem, SparseMatrix


class Modul(NamedTuple):
    key: str
    seats: List[int]
    periods: List[int]
    n_periods: int
    name: str
    sub_names: List[str]
    type: str


Prio = Dict[str, Dict[str, int]]
Mod = Dict[str, Modul]


def read_moduler(path: str) -> Mod:
    with open(path, "r") as fp:
        moduler = yaml.load(fp, yaml.SafeLoader)

    defaults = moduler["defaults"]
    res = dict()
    for modul_key, modul in moduler["moduler"].items():
        for key, value in defaults.items():
            if key not in modul:
                modul[key] = value
        res[modul_key] = Modul(
            key=modul_key,
            sub_names=list(f"{modul_key}_{i}" for i in modul["periods"]),
            **modul,
        )

    return res


def read_priorities(path: str) -> Prio:
    def mod_row(row: Dict[str, str]):
        key = row.pop("ATTENDANT")
        return key, dict((k, int(v)) for k, v in row.items() if v)

    with open(path, "r") as fp:
        return dict(mod_row(row) for row in csv.DictReader(fp))


def print_solution(p: Problem):
    for X in [p.X, p.z]:
        for x in X.x:
            for var in x:
                if p.model.getVal(var) > 0.5:
                    print(var.name)

    for module, y in p.X.X_T.items():
        assigned = [
            attendee for attendee, var in y.items() if p.model.getVal(var) > 0.5
        ]
        if len(assigned) > 0:
            print(f"{module:20} {len(assigned)}")
            for att in assigned:
                print(f"    {att}")


def add_module_constraints(p: Problem, moduler: Mod):
    for mod in moduler.values():
        p.const.append(
            p.model.addCons(
                quicksum(p.z.row(mod.key)) <= mod.n_periods,
                f"run_module_{mod.key}_in_max_{mod.n_periods}_periods",
            )
        )

        if mod.seats[1] >= 0:
            for module_name in mod.sub_names:
                p.const.append(
                    p.model.addCons(
                        quicksum(p.X.col(module_name)) <= mod.seats[1],
                        f"at_most_{mod.seats[1]}_attendees_for_{module_name}",
                    )
                )

        if mod.seats[0] > 0:
            for period in mod.periods:
                module_name = f"{mod.key}_{period}"
                p.const.append(
                    p.model.addCons(
                        quicksum(p.X.col(module_name))
                        - p.z.X[mod.key][period] * mod.seats[0]
                        >= 0,
                        f"at_least_{mod.seats[0]}_attendees_for_{module_name}",
                    )
                )

        if len(mod.periods) > 1:
            for x in zip(*(p.X.col(module_name) for module_name in mod.sub_names)):
                attendee = x[0].name.split("_")[1]
                p.const.append(
                    p.model.addCons(
                        quicksum(x) <= 1, f"{attendee}_can_only_attend_{mod.key}_once"
                    )
                )


def add_simple_constraints(p: Problem, moduler: Mod):
    periods = set(chain(*(mod.periods for mod in moduler.values())))

    period2module_names = dict(
        (
            period,
            [
                f"{mod.key}_{period}"
                for mod in moduler.values()
                if period in mod.periods
            ],
        )
        for period in periods
    )

    for x_name, x in p.X.X.items():
        for period, module_names in period2module_names.items():
            vars = [x[mod] for mod in module_names if mod in x]
            c = p.model.addCons(
                quicksum(vars) <= 1, f"1_module_for_{x_name}_in_period_{period}"
            )
            p.const.append(c)


def init_problem(priorities: Prio, moduler: Mod):
    module_names_w_periods = list(chain(*(mod.sub_names for mod in moduler.values())))

    p = Problem("workshops", priorities.keys(), module_names_w_periods)
    obj = []
    const = []
    for attendee, prio in priorities.items():
        for prio_name, prio_val in prio.items():
            try:
                for period in moduler[prio_name].periods:
                    """ Decision variable: X_i_j: person i assigned to module j in period k """
                    p.X.make_var(attendee, f"{prio_name}_{period}")
                    obj.append(p.X.X[attendee][f"{prio_name}_{period}"] * prio_val)
            except KeyError as e:
                raise ValueError("priorities and modules are not consistent") from e

    theoretical_module_names = list(
        chain(*(mod.sub_names for mod in moduler.values() if mod.type == "theoretical"))
    )
    for x_name, x in p.X.X.items():
        vars = [x[mod] for mod in theoretical_module_names if mod in x]
        c = p.model.addCons(
            quicksum(vars) >= 1, f"at_least_1_theoretical_module_for_{x_name}"
        )
        const.append(c)

    obj.append(quicksum(-1000 * var for var in p.X.flatten()))

    periods = set(chain(*(mod.periods for mod in moduler.values())))
    z = SparseMatrix(p.model, moduler.keys(), periods, "z")
    p.z = z
    for mod in moduler.values():
        for period in mod.periods:
            z.make_var(mod.key, period)

    for x_name, x in z.X.items():
        for y_name, var in x.items():
            module_name = f"{x_name}_{y_name}"
            attendees_for_module = list(p.X.col(module_name))
            const.append(
                p.model.addConsOr(
                    attendees_for_module,
                    var,
                    f"module_{module_name}_must_run_to_have_attendees",
                )
            )
            obj.append(var * 100)

    add_simple_constraints(p, moduler)
    add_module_constraints(p, moduler)

    p.model.setObjective(quicksum(obj), "minimize")
    p.model.data = dict(enumerate(p.X.flatten()))
    p.model.optimize()

    print_solution(p)
