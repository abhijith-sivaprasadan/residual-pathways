# Controlled optimisation: actual solved HiGHS experiment, not MESSAGEix

This package implements a single-period, single-region electricity/CO2 linear programme solved with SciPy/HiGHS. The 100 TWh demand, technology costs, emissions intensity, resource limits, 8 Mt exogenous process emissions and 25 Mt net cap are all authored hypothetical parameters.

Variables: renewable TWh, fossil TWh, fossil point-source CCS Mt, DAC atmospheric removal Mt. Annual atmospheric positive CO2 after CCS = 0.75 * fossil TWh - fossil CCS Mt + process emissions Mt. Annual net CO2 = positive atmospheric CO2 - DAC Mt. Fossil CCS must not be re-counted as an atmospheric removal. CCS capture <= 85% of generated fossil CO2 and storage capacity. Both DAC and renewables have distinct annual upper bounds. Supply >= demand.

Costs in million USD: 1 TWh at 1 USD/MWh = 1 million USD; 1 Mt at 1 USD/t = 1 million USD. Optimise supply, abatement and removals subject to constraints. All one-factor interventions retain other assumptions; combined-severe case deliberately tests infeasibility. None of these assumptions is a calibrated estimate of real costs or technology performance.

Reproduce: python -m pip install -e ".[dev]" ; python -m residual_pathways model-sensitivity --output results/model_sensitivity

The code checks mass balance, solver feasibility and known solutions. No causal or quantitative inference about the AR6 ensemble, global mitigation innovation, climate policy or industry is justified by these synthetic outputs.

Official MESSAGEix Westeros baseline documentation: https://docs.messageix.org/en/stable/tutorials.html. Actual MESSAGEix/GAMS framework claims require licensed GAMS, executed Westeros notebook, baseline and intervention solver logs and source provenance. This has not occurred here.
