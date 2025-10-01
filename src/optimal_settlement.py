from typing import Dict, List, Tuple
from collections import defaultdict, deque

Person = str
Channel = str


def _components(graph: Dict[str, set]) -> List[set]:
    seen = set()
    comps = []
    for n in graph:
        if n in seen:
            continue
        q = deque([n])
        comp = set()
        while q:
            u = q.popleft()
            if u in comp:
                continue
            comp.add(u)
            seen.add(u)
            for v in graph.get(u, []):
                if v not in comp:
                    q.append(v)
        comps.append(comp)
    return comps


def find_shortest_path(graph: Dict[str, set], start: str, end: str) -> List[str]:
    """Find shortest path between two nodes using BFS."""
    if start == end:
        return [start]
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        node, path = queue.popleft()
        for neighbor in graph.get(node, ()):  # safe get
            if neighbor == end:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None


def optimal_settle(
    balances: Dict[Person, float],
    zelle_pairs: List[Tuple[str, str]],
    venmo_pairs: List[Tuple[str, str]],
) -> Dict[Tuple[str, str, str], float]:
    """
    Greedy pairing by component: repeatedly match largest debtor with largest creditor,
    route payment along shortest path and aggregate flows. This tends to minimize number
    of transactions versus per-payee collection.
    """
    graph = defaultdict(set)
    edge_channels = {}
    nodes = set(balances.keys())

    for u, v in zelle_pairs:
        graph[u].add(v)
        graph[v].add(u)
        edge_channels[(u, v)] = "zelle"
        edge_channels[(v, u)] = "zelle"
        nodes.update([u, v])

    for u, v in venmo_pairs:
        graph[u].add(v)
        graph[v].add(u)
        edge_channels[(u, v)] = "venmo"
        edge_channels[(v, u)] = "venmo"
        nodes.update([u, v])

    for n in list(nodes):
        graph.setdefault(n, set())

    settlement_plan: Dict[Tuple[str, str, str], float] = {}

    for comp in _components(graph):
        balances_sub = {p: balances.get(p, 0.0) for p in comp if p in balances}
        if not balances_sub:
            continue

        total_sum = sum(balances_sub.values())
        if abs(total_sum) < 0.1:
            err = total_sum / len(balances_sub)
            balances_sub = {person: bal - err for person, bal in balances_sub.items()}

        payers = {person: -bal for person, bal in balances_sub.items() if bal < -1e-6}
        payees = {person: bal for person, bal in balances_sub.items() if bal > 1e-6}
        if not payers or not payees:
            continue

        graph_sub = {n: {m for m in graph.get(n, ()) if m in comp} for n in comp}

        # greedy: match largest debtor with largest creditor
        import heapq

        payer_heap = [(-amt, person) for person, amt in payers.items()]
        payee_heap = [(-amt, person) for person, amt in payees.items()]
        heapq.heapify(payer_heap)
        heapq.heapify(payee_heap)

        while payer_heap and payee_heap:
            payer_amt, payer = heapq.heappop(payer_heap)
            payee_amt, payee = heapq.heappop(payee_heap)
            payer_amt = -payer_amt
            payee_amt = -payee_amt
            transfer = min(payer_amt, payee_amt)

            path = find_shortest_path(graph_sub, payer, payee)
            if not path:
                continue

            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                channel = edge_channels.get(
                    (a, b), edge_channels.get((b, a), "unknown")
                )
                key = (channel, a, b)
                settlement_plan[key] = settlement_plan.get(key, 0.0) + transfer

            rem_payer = payer_amt - transfer
            rem_payee = payee_amt - transfer
            if rem_payer > 1e-6:
                heapq.heappush(payer_heap, (-rem_payer, payer))
            if rem_payee > 1e-6:
                heapq.heappush(payee_heap, (-rem_payee, payee))

    return settlement_plan
