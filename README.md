# Amherst settlement
## What is this?
This is a simple script to compute the settlement of the Amherst group, considering the limits of the graph.

## Workflow
1. Read the tri count settlemnt

2. Re compute the money flow according to the limits (graph connection, send limit, simplify, etc)

3. Notify the users

## Mathematical Formulation of the Debt Minimization Problem
### 1. Problem Setting
We have a group of participants who owe money to each other after shared expenses.  
Each participant $i$ has a **net balance** $b_i$:

- $b_i > 0$: participant $i$ must pay this amount.  
- $b_i < 0$: participant $i$ must receive this amount.  

The balances must satisfy the feasibility condition:
$$
\sum_i b_i = 0.
$$

Participants are connected through **payment channels** (e.g. Zelle, Venmo).  
Not every pair of participants is connected, and some channels impose **capacity limits**.

---

### 2. Decision Variables
- $x_{ij}^{c} \geq 0$: amount sent from participant $i$ to $j$ through channel $c$.  
- $y_{ij}^{c} \in \{0,1\}$: binary variable, equals 1 if edge $(i,j)$ via channel $c$ is used.  

To incorporate granularity (rounding), we enforce:
$$
x_{ij}^{c} = k \cdot z_{ij}^{c}, \quad z_{ij}^{c} \in \mathbb{Z}_{\geq 0},
$$
where $k$ is the minimal transferable unit (e.g. 1 dollar, 0.1 dollar).

---

### 3. Constraints

#### 3.1 Flow Conservation
For each participant $i$:
$$
\sum_{j,c} x_{ij}^{c} - \sum_{j,c} x_{ji}^{c} = b_i.
$$

#### 3.2 Channel Connectivity
If no edge $(i,j)$ exists in channel $c$, then:
$$
x_{ij}^{c} = 0.
$$

#### 3.3 Channel Capacity
For users with daily sending limits (e.g. Zelle):
$$
\sum_{j} x_{ij}^{\text{Zelle}} \leq L_i,
$$
where $L_i$ is the limit for sender $i$.

#### 3.4 Linking Constraints
To connect continuous and binary variables:
$$
x_{ij}^{c} \leq M \cdot y_{ij}^{c},
$$
with $M$ a sufficiently large constant.

---

### 4. Objectives (Lexicographic Optimization)

1. **Stage 1: Minimize Total Transfer Amount**
$$
\min \; T = \sum_{i,j,c} x_{ij}^{c}.
$$

2. **Stage 2: Minimize Number of Transactions**  
Subject to the optimal value $T^\star$ from Stage 1:
$$
\min \; \sum_{i,j,c} y_{ij}^{c},
$$
with the additional constraint:
$$
\sum_{i,j,c} x_{ij}^{c} = T^\star.
$$

---

### 5. Interpretation
- **Stage 1** ensures money flow is globally efficient (no extra cash circulation).  
- **Stage 2** reduces practical complexity by minimizing the number of payments.  
- **Granularity $k$** controls the rounding:  
  - $k = 1$ → exact dollars only.  
  - $k = 0.1$ → amounts rounded to 10 cents.  

---

### 6. Key Properties
- This is a **Mixed-Integer Linear Program (MILP)**.  
- If the graph of allowed transfers is disconnected, each connected component must satisfy $\sum_{i \in C} b_i = 0$.  
- The model guarantees:
  - Feasibility (flow conservation).  
  - Practical constraints (channel limits, connectivity).  
  - Optimality in both **amount** and **transaction count**.


## Command log
### Git
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/hibiki-kato/Amherst-settlement.git
git branch -M main
git push -u origin main
```
### uv
```bash
uv init .
uv add requests pulp pytest
```


