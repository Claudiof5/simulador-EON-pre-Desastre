"""
Script to update Experiment_best_weight_for_scenario.ipynb and compare_scenarios2.ipynb
for batch processing with 10 base scenarios.

This script shows the required changes. Apply them manually to the notebooks.
"""

# Key changes needed:

# 1. Experiment_best_weight_for_scenario.ipynb - Cell 1 (load scenarios):
"""
# Load all 10 base scenarios (indexed 0-9)
print("📂 Loading 10 base scenarios from output/...")
cenarios_base = []
for i in range(10):
    scenario_path = Path(f"output/cenario_disaster_aware{i}.pkl")
    if scenario_path.exists():
        with open(scenario_path, "rb") as file:
            cenario_base = pickle.load(file)
            cenarios_base.append((i, cenario_base))
        print(f"  ✓ Loaded scenario {i}")
    else:
        print(f"  ⚠️ Warning: scenario {i} not found at {scenario_path}")

if not cenarios_base:
    raise FileNotFoundError("No base scenarios found!")

print(f"\n✓ Loaded {len(cenarios_base)} base scenarios")
"""

# 2. Experiment_best_weight_for_scenario.ipynb - Cell 4 (generate scenarios):
"""
# Generate scenarios with different weights for each base scenario
all_scenarios = []  # List of (base_index, weight_tuple, scenario)
total_scenarios = len(cenarios_base) * len(list_of_weights)

for base_index, cenario_base in cenarios_base:
    weight_scenarios = ScenarioGenerator.gerar_cenarios_com_diferentes_pesos(
        cenario_base, list_of_weights
    )
    for weight_tuple, scenario in zip(list_of_weights, weight_scenarios):
        all_scenarios.append((base_index, weight_tuple, scenario))
"""

# 3. Experiment_best_weight_for_scenario.ipynb - Cell 6 (parallel execution):
"""
# Prepare arguments - include base_index
scenario_args = [
    (scenario, base_index, idx, len(all_scenarios), str(BASE_OUTPUT_DIR))
    for idx, (base_index, weight_tuple, scenario) in enumerate(all_scenarios)
]

# Update print statements to use all_scenarios instead of scenarios
"""

# 4. experiment_worker.py - Already updated to handle base_index in filenames

# 5. compare_scenarios2.ipynb - Update scenario discovery to group by directory:
"""
# Group scenarios by directory
directory_groups = defaultdict(list)
for pkl_file in output_path.rglob("scenario_*.pkl"):
    dir_key = str(pkl_file.parent.relative_to(output_path)).replace("\\", "/")
    directory_groups[dir_key].append(pkl_file)

# Show directories with multiple scenarios as batch options
batch_directories = {
    dir_key: scenarios 
    for dir_key, scenarios in directory_groups.items() 
    if len(scenarios) > 1
}
"""

print("See comments in this file for required changes")


