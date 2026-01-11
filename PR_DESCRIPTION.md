# Add "Group by Scenario" Toggle for Batch Experiment Analysis

## Summary
This PR adds a new "Group by Scenario" toggle to the scenario comparison GUI that allows users to group scenarios by their base index across all weight combinations. This enables comparing the same base scenario across different routing weight configurations (alpha, beta, gamma).

## Changes Made

### 1. New "Group by Scenario" Toggle Widget
- Added `scenario_grouping_toggle` checkbox widget next to the existing "Group by Directory" toggle
- Default value: `False` (disabled by default)
- Positioned in the scenario selection controls area

### 2. Enhanced `rebuild_selection_options()` Function
The function now supports three grouping modes:

#### Mode 1: Group by Scenario (NEW)
- When `scenario_grouping_toggle` is ON:
  - Groups scenarios by their base index (e.g., base0, base1, base2) across all directories
  - Extracts base index from file names (format: `{alpha}_{beta}_{gamma}_{base_index}`)
  - Creates selection options like "Base Scenario 0", "Base Scenario 1", etc.
  - Each group contains all scenarios with the same base index from different weight combinations

#### Mode 2: Group by Directory (EXISTING)
- When `directory_grouping_toggle` is ON:
  - Groups scenarios by weight combination directory (e.g., "0.0_0.0_0.0", "5.0_5.0_5.0")
  - Shows one option per directory containing all base scenarios for that weight combination

#### Mode 3: No Grouping (EXISTING)
- When both toggles are OFF:
  - Shows all individual scenarios separately
  - Useful for detailed per-scenario analysis

### 3. Mutual Exclusivity Between Toggles
- Implemented logic to ensure only one grouping mode is active at a time
- When "Group by Scenario" is turned ON, "Group by Directory" is automatically turned OFF
- When "Group by Directory" is turned ON, "Group by Scenario" is automatically turned OFF
- Uses unobserve/observe pattern to prevent callback loops
- Includes update lock mechanism to prevent recursive updates

### 4. Improved Display Names for Individual Scenarios
- Fixed display name generation when viewing individual scenarios from grouped base scenarios
- **Before**: `Base Scenario 0 (scenario 0)` - confusing, doesn't show which weights
- **After**: `Base Scenario 0 (0.0_5.0_5.0)` - clearly shows the weight combination
- Extracts weights (alpha_beta_gamma) from file names and displays them in parentheses
- File name format: `{alpha}_{beta}_{gamma}_{base_index}` → Display: `Base Scenario {base_index} ({alpha}_{beta}_{gamma})`

### 5. Updated Callback Functions
- Created `on_grouping_toggle_change()` to handle both toggles
- Maintains `on_directory_grouping_toggle_change()` for backward compatibility
- Both callbacks:
  - Rebuild selection options based on toggle states
  - Update scenario dropdown options
  - Clear caches and selections
  - Update `all_scenario_names` for "Select All" functionality

### 6. UI Layout Updates
- Added `scenario_grouping_toggle` to the scenario selection box
- Positioned alongside "Group by Directory" toggle in a horizontal layout
- Maintains consistent styling with existing widgets

## Use Cases

### Use Case 1: Compare Same Base Scenario Across Weight Combinations
1. Enable "Group by Scenario" toggle
2. Select "Base Scenario 0" (or any base scenario)
3. Enable "Batch View" to see averaged results across all weight combinations for that base scenario
4. Disable "Batch View" to see individual results for each weight combination

### Use Case 2: Compare Different Base Scenarios
1. Enable "Group by Scenario" toggle
2. Select multiple base scenarios (e.g., "Base Scenario 0", "Base Scenario 1")
3. Compare how different base scenarios perform across weight combinations

### Use Case 3: Traditional Weight-Based Comparison
1. Enable "Group by Directory" toggle (or disable both)
2. Select weight combinations (e.g., "0.0_0.0_0.0", "5.0_5.0_5.0")
3. Compare performance across different weight configurations

## Technical Details

### File Name Parsing
- File names follow format: `scenario_{alpha}_{beta}_{gamma}_{base_index}.pkl`
- After removing "scenario_" prefix: `{alpha}_{beta}_{gamma}_{base_index}`
- Base index extraction: Last part after splitting by `_`
- Weights extraction: All parts except the last one

### Grouping Logic
```python
# Scenario grouping extracts base index from file names
file_name = "0.0_5.0_5.0_8"  # file_info['name']
parts = file_name.split('_')
base_index = parts[-1]  # "8"
weights = '_'.join(parts[:-1])  # "0.0_5.0_5.0"
```

### Display Name Generation
- When viewing individual scenarios from grouped base scenarios:
  - Format: `Base Scenario {base_index} ({alpha}_{beta}_{gamma})`
  - Example: `Base Scenario 0 (0.0_5.0_5.0)`

## Testing
- Verified syntax of all code cells
- Tested base index extraction logic
- Confirmed mutual exclusivity between toggles
- Validated display name generation with various file name formats

## Files Modified
- `compare_scenarios2.ipynb`: Added scenario grouping functionality and improved display names

## Backward Compatibility
- All existing functionality remains unchanged
- "Group by Directory" toggle behavior is preserved
- Default state (both toggles OFF) shows individual scenarios as before
- No breaking changes to existing API or data structures

