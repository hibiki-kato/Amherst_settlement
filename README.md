# Amherst settlement
## What is this?
This is a simple script to compute the settlement of the Amherst group, considering the limits of the graph.

## Workflow
1. Read the tri count settlemnt

2. Re compute the money flow according to the limits (graph connections)

## How to use
0. Install git and uv (Python task runner).

    Google it.
1. clone this repo
    ```
    git clone https://github.com/hibiki-kato/Amherst_settlement.git
    ```
2. Create a environment using uv (uv file is included)
    ```
    cd Amherst_settlement
    uv sync --locked
    ```
3. Create a .env file in a root directory of this repo.
    In the .env file, write the following line:
    ```
    TRICOUNT_KEY=your_tricount_key
    ```
    `your_tricount_key` can be found in the URL of your tricount page, like `https://www.tricount.com/your_tricount_key`.

4. Run the main.py using uv
    ```
    uv run python -O src/main.py
    ```

5. Got the settlement plan printed in the terminal.
    ```
    === Simple Network-Based Settlement ===
    Balances:
    Guillermo: 262.91
    Matt: -95.18
    Hibiki: 741.74
    Gowtham: -909.47
    Balance sum: 0.0

    Settlement Plan:
    Gowtham → Hibiki: $741.74 via zelle
    Gowtham → Matt: $167.73 via zelle
    Matt → Guillermo: $262.91 via venmo

    Total transaction amount: $1172.38

    Verification:
    Guillermo: expected 262.91, actual 262.91, diff 0.000000
    Matt: expected -95.18, actual -95.18, diff 0.000000
    Hibiki: expected 741.74, actual 741.74, diff 0.000000
    Gowtham: expected -909.47, actual -909.47, diff 0.000000
    ```