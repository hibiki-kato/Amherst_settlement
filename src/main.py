from typing import Tuple
from optimal_settlement import optimal_settle
from tricount_read import fetch_tricount_data, get_net_from_tricount

Person = str
Channel = str
Arc = Tuple[Person, Person]


def main():
    # Fetch data and compute net balances
    data = fetch_tricount_data()
    balances = get_net_from_tricount(data)

    # normalize names to canonical form to avoid case/whitespace mismatches
    def _canon(name: str) -> str:
        return name.strip().lower()

    canon_to_display = {}
    balances_canon = {}
    for name, amt in balances.items():
        c = _canon(name)
        canon_to_display[c] = name
        balances_canon[c] = float(amt)

    print("=== Simple Network-Based Settlement ===")
    print("## Balances:")
    for person, balance in balances.items():
        print(f"- *{person}*: ${balance:.2f}")
    # print(f"Balance sum: {sum(balances_canon.values())}")

    # Define Zelle and Venmo pairs (display names)
    zelle_pairs = [
        ("Matt", "Hibiki"),
        ("Matt", "Gowtham"),
        ("Hibiki", "Gowtham"),
    ]

    venmo_pairs = [
        ("Guillermo", "Matt"),
    ]

    # Canonicalize pairs
    zelle_pairs_canon = [(_canon(a), _canon(b)) for a, b in zelle_pairs]
    venmo_pairs_canon = [(_canon(a), _canon(b)) for a, b in venmo_pairs]

    # Use optimal settlement algorithm with canonicalized balances and pairs
    settlement_plan = optimal_settle(
        balances_canon, zelle_pairs_canon, venmo_pairs_canon
    )

    print("\n ## Settlement Plan:")
    total_amount = 0.0
    for (channel, sender, receiver), amount in settlement_plan.items():
        if amount > 0:
            s_disp = canon_to_display.get(sender, sender)
            r_disp = canon_to_display.get(receiver, receiver)
            print(f"- *{s_disp}* → *{r_disp}*: ${amount:.2f} ({channel})")
            total_amount += amount

    print(f"\nTotal transaction amount: ${total_amount:.2f}")

    # Verify the settlement
    net_flows = {person: 0.0 for person in balances_canon}
    for (channel, sender, receiver), amount in settlement_plan.items():
        if amount > 0:
            net_flows[sender] -= amount  # Sender pays money (negative flow)
            net_flows[receiver] += amount  # Receiver gets money (positive flow)

    # print("\nVerification:")
    for canon_name, display in canon_to_display.items():
        expected = balances_canon.get(canon_name, 0.0)
        actual = net_flows.get(canon_name, 0.0)
        # print(
        #     f"{display}: expected {expected:.2f}, actual {actual:.2f}, diff {abs(expected - actual):.6f}"
        # )


if __name__ == "__main__":
    main()
