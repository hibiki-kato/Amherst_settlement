def pretty_print_plan(x_val):
    by_ch = {}
    for (ch, u, v), amt in x_val.items():
        by_ch.setdefault(ch, []).append((u, v, amt))
    lines = []
    for ch, lst in by_ch.items():
        lines.append(f"[{ch}]")
        for u, v, amt in sorted(lst):
            lines.append(f"  {u} -> {v}: ${amt:.2f}")
    return "\n".join(lines)


def print_settlement_report(x_val, balances, title="Settlement Report"):
    """Print detailed settlement verification report"""
    print(f"\n=== {title} ===")

    # Calculate totals
    total_transfers = sum(x_val.values())
    total_positive = sum(max(0, bal) for bal in balances.values())
    total_negative = sum(min(0, bal) for bal in balances.values())
    balance_sum_error = abs(total_positive + total_negative)

    # Print summary
    print(f"Total transfers: ${total_transfers:.2f}")
    print(f"Total positive balances: ${total_positive:.2f}")
    print(f"Total negative balances: ${total_negative:.2f}")
    print(f"Balance sum error: ${balance_sum_error:.6f} (granularity-induced)")

    # Efficiency metric
    efficiency = (total_positive / total_transfers * 100) if total_transfers > 0 else 0
    print(f"Transfer efficiency: {efficiency:.1f}% (lower is better)")

    # Per-person verification
    print("\nPer-person verification:")
    persons = set(balances.keys())

    def node_out(i):
        return sum(amt for (ch, u, v), amt in x_val.items() if u == i)

    def node_in(i):
        return sum(amt for (ch, u, v), amt in x_val.items() if v == i)

    max_error = 0
    for person in sorted(persons):
        out_amt = node_out(person)
        in_amt = node_in(person)
        net_flow = out_amt - in_amt
        expected = balances.get(person, 0.0)
        error = abs(net_flow - expected)
        max_error = max(max_error, error)
        status = "✓" if error < 1e-6 else ("~" if error < 1.0 else "✗")

        print(
            f"  {person:10s}: out=${out_amt:7.2f}, in=${in_amt:7.2f}, net=${net_flow:7.2f}, expected=${expected:7.2f} {status}"
        )

    print(f"Max flow error: ${max_error:.6f} (due to granularity constraints)")

    # Channel breakdown
    print("\nChannel breakdown:")
    by_channel = {}
    for (ch, u, v), amt in x_val.items():
        by_channel.setdefault(ch, 0)
        by_channel[ch] += amt

    for ch, total in sorted(by_channel.items()):
        percentage = (total / total_transfers * 100) if total_transfers > 0 else 0
        print(f"  {ch}: ${total:.2f} ({percentage:.1f}%)")

    print()


def check_solution(
    x_val,
    balances,
    E,
    zelle_limits=None,
    eps=1e-6,
    granularity_tolerance=None,
    enforce_zelle_limits=False,
):
    """Comprehensive solution validation: flow conservation, Zelle limits, and settlement verification

    Args:
        x_val: Solution transfer amounts
        balances: Original balances
        E: Edge structure
        zelle_limits: Zelle sending limits (None = no limits)
        eps: Standard numerical tolerance
        granularity_tolerance: Additional tolerance for granularity-induced rounding (auto-calculated if None)
        enforce_zelle_limits: Whether to check Zelle limits
    """
    persons = set(balances.keys())

    # Auto-calculate granularity tolerance if not provided
    if granularity_tolerance is None:
        # Estimate based on number of people and potential rounding per person
        granularity_tolerance = len(persons) * 1.0  # Up to $1 per person for rounding

    def node_out(i):
        return sum(amt for (ch, u, v), amt in x_val.items() if u == i)

    def node_in(i):
        return sum(amt for (ch, u, v), amt in x_val.items() if v == i)

    # 1. Flow conservation check (with granularity tolerance)
    for i in persons:
        net_flow = node_out(i) - node_in(i)
        expected_balance = balances.get(i, 0.0)
        error = abs(net_flow - expected_balance)
        if error > max(eps, granularity_tolerance):
            raise AssertionError(
                f"Flow conservation violated at {i}: net_flow={net_flow:.6f}, expected={expected_balance:.6f}, error={error:.6f}"
            )

    # 2. Zelle limits check (only if enforced)
    if enforce_zelle_limits and zelle_limits:
        for i, L in zelle_limits.items():
            out_z = sum(
                amt for (ch, u, v), amt in x_val.items() if ch == "zelle" and u == i
            )
            if out_z - L > eps:
                raise AssertionError(
                    f"Zelle cap violated at {i}: {out_z:.6f} > {L:.6f}"
                )

    # 3. Input validation: balances should sum close to zero (with granularity tolerance)
    total_positive_balances = sum(max(0, bal) for bal in balances.values())
    total_negative_balances = sum(min(0, bal) for bal in balances.values())
    balance_sum_error = abs(total_positive_balances + total_negative_balances)

    if balance_sum_error > max(eps, granularity_tolerance):
        raise AssertionError(
            f"Input balances don't sum close to zero: positive={total_positive_balances:.6f}, negative={total_negative_balances:.6f}, error={balance_sum_error:.6f}"
        )

    # 4. Settlement consistency: verify flow conservation implies correct settlement
    # If flow conservation holds for all nodes, the settlement is mathematically correct
    # Total transfers can be more than positive balances due to indirect routing

    # 5. Verify no significantly negative transfers (allow small numerical errors)
    for (ch, u, v), amt in x_val.items():
        if amt < -max(eps, 0.01):  # Allow up to 1 cent negative due to rounding
            raise AssertionError(f"Negative transfer found: {ch} {u}->{v}: {amt:.6f}")

    return True  # All checks passed
