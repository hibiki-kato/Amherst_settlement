from typing import Dict, List, Tuple, Optional
import heapq

Person = str
Channel = str
Arc = Tuple[Person, Person]
PlanKey = Tuple[Channel, Person, Person]


def optimal_settle(
    balances: Dict[Person, float],
    zelle_pairs: List[Arc],
    venmo_pairs: List[Arc],
) -> Dict[PlanKey, float]:
    # 合計は0
    if abs(sum(balances.values())) > 1e-6:
        raise ValueError("Balances must sum to 0")

    nodes = sorted(balances.keys())

    # 無向→両向き
    def mk_arcs(pairs: List[Arc], channel: Channel) -> List[PlanKey]:
        out: List[PlanKey] = []
        seen = set()
        for a, b in pairs:
            if a == b:
                continue
            for u, v in ((a, b), (b, a)):
                k = (channel, u, v)
                if k not in seen:
                    out.append(k)
                    seen.add(k)
        return out

    arcs: List[PlanKey] = mk_arcs(zelle_pairs, "zelle") + mk_arcs(venmo_pairs, "venmo")

    class Edge:
        __slots__ = ("to", "rev", "cap", "cost", "key")

        def __init__(
            self, to: int, rev: int, cap: float, cost: float, key: Optional[PlanKey]
        ):
            self.to = to
            self.rev = rev
            self.cap = cap
            self.cost = cost
            self.key = key

    class MCMF:
        def __init__(self, N: int):
            self.g: List[List[Edge]] = [[] for _ in range(N)]

        def add_edge(
            self,
            fr: int,
            to: int,
            cap: float,
            cost: float,
            key: Optional[PlanKey] = None,
        ):
            fwd = Edge(to, len(self.g[to]), cap, cost, key)
            rev = Edge(fr, len(self.g[fr]), 0.0, -cost, None)
            self.g[fr].append(fwd)
            self.g[to].append(rev)

        def min_cost_flow(self, s: int, t: int, max_f: float):
            N = len(self.g)
            INF = 1e30
            h = [0.0] * N
            flow = 0.0
            key_flow: Dict[PlanKey, float] = {}

            while flow + 1e-12 < max_f:
                dist = [INF] * N
                prev_v = [-1] * N
                prev_e = [-1] * N
                dist[s] = 0.0
                pq = [(0.0, s)]
                while pq:
                    d, v = heapq.heappop(pq)
                    if d > dist[v] + 1e-15:
                        continue
                    for i, e in enumerate(self.g[v]):
                        if e.cap <= 1e-12:
                            continue
                        nd = d + e.cost + h[v] - h[e.to]
                        if nd + 1e-15 < dist[e.to]:
                            dist[e.to] = nd
                            prev_v[e.to] = v
                            prev_e[e.to] = i
                            heapq.heappush(pq, (nd, e.to))

                if dist[t] >= INF / 2:
                    raise RuntimeError("No feasible path")

                for v in range(N):
                    if dist[v] < INF / 2:
                        h[v] += dist[v]

                add_f = max_f - flow
                v = t
                while v != s:
                    pv = prev_v[v]
                    pe = prev_e[v]
                    e = self.g[pv][pe]
                    add_f = min(add_f, e.cap)
                    v = pv

                v = t
                while v != s:
                    pv = prev_v[v]
                    pe = prev_e[v]
                    e = self.g[pv][pe]
                    re = self.g[v][e.rev]
                    e.cap -= add_f
                    re.cap += add_f
                    if e.key is not None:
                        key_flow[e.key] = key_flow.get(e.key, 0.0) + add_f
                    v = pv

                flow += add_f

            return key_flow, flow

    idx = {name: i for i, name in enumerate(nodes)}
    S = len(nodes)
    T = S + 1
    mcmf = MCMF(T + 1)

    # 1ホップ=コスト1
    for ch, u, v in arcs:
        if u in idx and v in idx:
            mcmf.add_edge(idx[u], idx[v], cap=1e18, cost=1.0, key=(ch, u, v))

    total_demand = 0.0
    for n in nodes:
        b = balances[n]
        if b < -1e-9:  # debtor: S->n
            mcmf.add_edge(S, idx[n], cap=(-b), cost=0.0)
            total_demand += -b
        elif b > 1e-9:  # creditor: n->T
            mcmf.add_edge(idx[n], T, cap=b, cost=0.0)

    flow_map, sent = mcmf.min_cost_flow(S, T, max_f=total_demand)
    if abs(sent - total_demand) > 1e-6:
        raise RuntimeError("Could not send all flow")

    return {k: v for k, v in flow_map.items() if abs(v) > 1e-8}
