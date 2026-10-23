# Independent Pyomo formulation of the synthetic optimisation study

The controlled 100 TWh electricity and CO2 demonstration is independently written in Pyomo and solved through the HiGHS backend. Its objective and emissions constraints are cross-checked with the separately encoded SciPy linprog implementation across all six scenarios, including a genuine infeasible case. The design is not a causal investigation of IAM trajectories. Both formulations use the same HiGHS family, so this is independent algebraic formulation validation, **not an independent solver technology, empirical calibration, MESSAGEix, or GAMS experience**.

Run with Python extras including pyomo and highspy: python -m pip install -e '.[dev,pyomo]' ; python -m pytest tests/test_pyomo_validation.py -q ; python -m residual_pathways validate-pyomo --output results/pyomo_validation.json.

This fulfills the separate Pyomo/HiGHS fallback software experiment in v3 if MESSAGEix/GAMS execution is blocked. The official Westeros/MESSAGEix demonstration requires an actual verified solve and separate proof. No credentials or claimed GAMS install are emitted here.
