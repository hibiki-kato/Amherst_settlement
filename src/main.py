from typing import Tuple

from optimization import (
    InputData,
    build_edges,
    solve_stage1_min_amount,
    solve_stage2_min_edges,
)

from utils import pretty_print_plan, print_settlement_report, check_solution

Person = str
Channel = str
Arc = Tuple[Person, Person]

if __name__ == "__main__":
    # ======= Hardcoded example =======
    # Sign convention: should pay=positive, should receive=negative. Must sum to 0.
    # Example: matt +300, hibiki +50, gowtham 0, Guillermo -350
    balances = {
        "matt": -900.0,
        "hibiki": -900.0,
        "gowtham": 1000.0,
        "Guillermo": 800.0,
    }

    # Zelle limits (per sender) - now optional
    zelle_caps_day = {"gowtham": 500.0, "matt": 1000.0, "hibiki": 2000.0}
    zelle_caps_week = {"gowtham": 2200.0, "matt": 2500.0, "hibiki": 8000.0}

    # Granularity (change 1.0 → 0.1 for 10-cent precision with strict rounding)
    k = 1.0  # dollars
    # k = 0.1  # 10 cents
    # k = 0.01  # 1 cent

    # Define Zelle and Venmo pairs
    zelle_pairs = [
        ("matt", "hibiki"),
        ("matt", "gowtham"),
        ("hibiki", "gowtham"),
    ]

    venmo_pairs = [
        ("Guillermo", "matt"),
    ]

    print("=== SCENARIO: Zelle Daily and Weekly Limits ===")
    # --- Scenario considering Zelle daily and weekly limits ---
    data_with_limits = InputData(
        balances=balances,
        zelle_limits=zelle_caps_day,
        include_future_venmo=False,
        k=k,
        enforce_zelle_limits=True,
        zelle_pairs=zelle_pairs,
        venmo_pairs=venmo_pairs,
    )

    edges = build_edges(
        include_future_venmo=False,
        zelle_pairs=zelle_pairs,
        venmo_pairs=venmo_pairs,
    )

    T_star, x1, E_now, V_now = solve_stage1_min_amount(data_with_limits)
    T2, K, x2, y2 = solve_stage2_min_edges(data_with_limits, T_star, E_now, V_now)

    print("Settlement Plan:")
    print(pretty_print_plan(x2))
    check_solution(x2, balances, E_now, zelle_caps_day, enforce_zelle_limits=True)
    print_settlement_report(x2, balances, "Zelle Daily and Weekly Limits")

    print("\n=== SUMMARY ===")
    print(f"With Zelle limits:    ${T_star:.2f} (edges: {K})")

    print("Balances:", balances)
    print("Sum of balances:", sum(balances.values()))
    print("Zelle pairs:", zelle_pairs)
    print("Venmo pairs:", venmo_pairs)
    print("Zelle limits:", zelle_caps_day)
    print("Granularity (k):", k)
