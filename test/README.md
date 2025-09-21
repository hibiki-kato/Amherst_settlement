# Amherst Settlement Optimization Tests

This test suite comprehensively tests the settlement optimization system with the following components:

## Test Structure

### 1. TestBuildEdges
- Tests edge construction for different Venmo connectivity scenarios
- Verifies bidirectional edge creation for Zelle and Venmo networks

### 2. TestInputData  
- Tests the InputData dataclass creation and default values
- Validates parameter handling

### 3. TestStage1MinAmount
- Tests Stage 1 optimization (minimize total transfer amount)
- Covers various scenarios: 2-person, 3-person, constraint violations
- Tests granularity enforcement and Zelle limit constraints
- Validates infeasibility detection

### 4. TestStage2MinEdges
- Tests Stage 2 optimization (minimize number of transfers while maintaining total)
- Verifies edge count reduction while preserving optimal total amount

### 5. TestCheckSolution
- Tests solution validation functions
- Verifies flow conservation and constraint checking
- Tests violation detection

### 6. TestPrettyPrintPlan
- Tests output formatting functions
- Verifies proper display of transfer plans

### 7. TestIntegrationScenarios
- Tests complete end-to-end scenarios
- Includes the original hardcoded example
- Tests Venmo connectivity benefits
- Validates granularity precision handling

## Running Tests

To run all tests:
```bash
uv run pytest test_main.py -v
```

To run specific test classes:
```bash
uv run pytest test_main.py::TestStage1MinAmount -v
```

To run with coverage:
```bash
uv run pytest test_main.py --cov=main --cov-report=html
```

## Key Test Insights

1. **Connectivity Constraints**: Users must be in `zelle_limits` to send money via Zelle
2. **Granularity**: When k=1.0 (dollar precision), balances must be integers or rounded
3. **Optimization**: Stage 2 successfully reduces transfer count while maintaining optimal total
4. **Future Venmo**: Adding hibiki's Venmo connectivity can improve solution efficiency

## Test Coverage

The tests cover:
- ✅ Happy path scenarios
- ✅ Edge cases and constraint violations  
- ✅ Error handling and infeasibility detection
- ✅ Different granularity settings
- ✅ Network topology variations
- ✅ Solution validation and sanity checks