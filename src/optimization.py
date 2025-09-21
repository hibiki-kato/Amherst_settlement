from dataclasses import dataclass
from typing import Dict, List, Tuple
import pulp

Person = str
Channel = str
Arc = Tuple[Person, Person]


@dataclass
class InputData:
    balances: Dict[
        Person, float
    ]  # Should pay=positive, should receive=negative. sum=0 is feasibility condition
    zelle_limits: Dict[Person, float] = (
        None  # Zelle daily limits per sender (None = no limits)
    )
    include_future_venmo: bool = (
        False  # Future: add hibiki<->matt, hibiki<->Guillermo to Venmo
    )
    k: float = 1.0  # Granularity (1.0=dollars, 0.1=10 cents)
    M: float = 1e9  # Big-M (sufficiently large)
    enforce_zelle_limits: bool = False  # Whether to enforce Zelle limits
    zelle_pairs: List[Tuple[str, str]] = None  # Zelle pairs for edge building
    venmo_pairs: List[Tuple[str, str]] = None  # Venmo pairs for edge building


def build_edges(
    include_future_venmo: bool,
    zelle_pairs: List[Tuple[str, str]] = None,
    venmo_pairs: List[Tuple[str, str]] = None,
):
    """Build channel-specific edge sets. All bidirectional."""
    zelle_pairs = zelle_pairs or []
    venmo_pairs = venmo_pairs or []

    Ez: List[Arc] = []
    for u, v in zelle_pairs:
        Ez += [(u, v), (v, u)]  # 双方向エッジを追加

    Ev: List[Arc] = []
    for u, v in venmo_pairs:
        Ev += [(u, v), (v, u)]  # 双方向エッジを追加

    if include_future_venmo:
        Ev += [
            ("hibiki", "matt"),
            ("matt", "hibiki"),
            ("hibiki", "Guillermo"),
            ("Guillermo", "hibiki"),
        ]

    return {"zelle": Ez, "venmo": Ev}


def solve_stage1_min_amount(data: InputData):
    """Stage 1: Minimize total transfer amount (strictly reflecting granularity k)"""
    E = build_edges(data.include_future_venmo, data.zelle_pairs, data.venmo_pairs)
    V = sorted(set(list(data.balances.keys())))
    if abs(sum(data.balances.values())) > 1e-6:
        raise ValueError("Infeasible: sum(balances) must be 0")

    prob = pulp.LpProblem("min_total_amount_with_granularity", pulp.LpMinimize)

    # Integer variables: z >= 0, x = k*z
    z = {
        (ch, u, v): pulp.LpVariable(
            f"z__{ch}__{u}__{v}", lowBound=0, cat=pulp.LpInteger
        )
        for ch, arcs in E.items()
        for (u, v) in arcs
    }

    def X(ch, u, v):  # Actual amount
        return data.k * z[ch, u, v]

    # Objective: minimize total amount
    prob += pulp.lpSum(X(ch, u, v) for ch, arcs in E.items() for (u, v) in arcs)

    # Flow conservation: outflow - inflow = b_i (b_i>0 = should pay)
    for i in V:
        outflow = pulp.lpSum(
            X(ch, i, v) for ch, arcs in E.items() for (u, v) in arcs if u == i
        )
        inflow = pulp.lpSum(
            X(ch, u, i) for ch, arcs in E.items() for (u, v) in arcs if v == i
        )
        prob += (outflow - inflow == data.balances.get(i, 0.0)), f"flow_{i}"

    # Zelle limits: total Zelle outflow per sender <= limit (if enforced)
    if data.enforce_zelle_limits and data.zelle_limits:
        for i, L in data.zelle_limits.items():
            outflow_z = pulp.lpSum(X("zelle", i, v) for (u, v) in E["zelle"] if u == i)
            prob += (outflow_z <= L), f"zelle_cap_{i}"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Stage1 not optimal: {pulp.LpStatus[status]}")

    print("Problem Status:", pulp.LpStatus[status])
    print("Objective Value:", pulp.value(prob.objective))
    for v in prob.variables():
        print(v.name, "=", v.varValue)
    print("Constraints:")
    for name, constraint in prob.constraints.items():
        print(name, ":", constraint, "->", constraint.value())

    T_star = pulp.value(prob.objective)
    # Return only actual amounts that flow through edges
    x_val = {
        (ch, u, v): pulp.value(X(ch, u, v))
        for ch, arcs in E.items()
        for (u, v) in arcs
        if pulp.value(X(ch, u, v)) > 1e-9
    }
    return T_star, x_val, E, V


def solve_stage2_min_edges(data: InputData, T_star: float, E, V, tol=1e-6):
    """Stage 2: Minimize number of edges while maintaining total amount T* (y: 0/1 usage flag)"""
    prob = pulp.LpProblem("min_num_edges_at_optimal_amount", pulp.LpMinimize)

    # Variables: z>=0 (integer), y∈{0,1}, x = k*z
    z = {
        (ch, u, v): pulp.LpVariable(
            f"z__{ch}__{u}__{v}", lowBound=0, cat=pulp.LpInteger
        )
        for ch, arcs in E.items()
        for (u, v) in arcs
    }
    y = {
        (ch, u, v): pulp.LpVariable(
            f"y__{ch}__{u}__{v}", lowBound=0, upBound=1, cat=pulp.LpBinary
        )
        for ch, arcs in E.items()
        for (u, v) in arcs
    }

    def X(ch, u, v):
        return data.k * z[ch, u, v]

    # Objective: minimize number of used edges
    prob += pulp.lpSum(y[ch, u, v] for ch, arcs in E.items() for (u, v) in arcs)

    # Flow conservation
    for i in V:
        outflow = pulp.lpSum(
            X(ch, i, v) for ch, arcs in E.items() for (u, v) in arcs if u == i
        )
        inflow = pulp.lpSum(
            X(ch, u, i) for ch, arcs in E.items() for (u, v) in arcs if v == i
        )
        prob += (outflow - inflow == data.balances.get(i, 0.0)), f"flow_{i}"

    # Linking constraint: x <= M*y
    for ch, arcs in E.items():
        for u, v in arcs:
            prob += X(ch, u, v) <= data.M * y[ch, u, v]

    # Fixed total amount (±tol)
    total = pulp.lpSum(X(ch, u, v) for ch, arcs in E.items() for (u, v) in arcs)
    prob += total >= T_star - tol
    prob += total <= T_star + tol

    # Zelle limits (if enforced)
    if data.enforce_zelle_limits and data.zelle_limits:
        for i, L in data.zelle_limits.items():
            outflow_z = pulp.lpSum(X("zelle", i, v) for (u, v) in E["zelle"] if u == i)
            prob += (outflow_z <= L), f"zelle_cap_{i}"

    status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Stage2 not optimal: {pulp.LpStatus[status]}")

    x_val = {
        (ch, u, v): pulp.value(X(ch, u, v))
        for ch, arcs in E.items()
        for (u, v) in arcs
        if pulp.value(X(ch, u, v)) > 1e-9
    }
    y_val = {
        (ch, u, v): int(round(pulp.value(y[ch, u, v])))
        for ch, arcs in E.items()
        for (u, v) in arcs
        if pulp.value(y[ch, u, v]) > 1e-9
    }
    used_edges = sum(y_val.values())
    T2 = sum(x_val.values())
    return T2, used_edges, x_val, y_val
