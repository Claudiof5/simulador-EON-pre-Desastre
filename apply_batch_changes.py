#!/usr/bin/env python3
"""
Script to apply batch comparison changes to compare_scenarios2.ipynb

This script modifies the notebook JSON to add batch directory support.
"""

import json
from pathlib import Path

def apply_batch_changes():
    """Apply batch directory detection and averaging to compare_scenarios2.ipynb"""
    
    notebook_path = Path("compare_scenarios2.ipynb")
    
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Find the cell with create_comparison_gui function
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Check if this is the create_comparison_gui cell
            if 'def create_comparison_gui():' in source:
                print(f"Found create_comparison_gui at cell {cell_idx}")
                
                # Update 1: Add batch directory detection after scenario discovery
                old_pattern = '    scenario_names = sorted(scenario_paths.keys())\n    \n    # Create display names'
                new_pattern = '''    # Detect batch directories (directories with multiple scenarios)
    batch_directories = detect_batch_directories(output_path)
    
    # Create selection options: show directories for batch, individual scenarios for single
    selection_options = {}  # Maps selection_key -> {'type': 'batch'|'single', 'files': [...], 'display_name': ...}
    updated_display_names = {}
    
    # Add batch directories as options
    for dir_path, files in batch_directories.items():
        display_name = dir_path.split('/')[-1] if '/' in dir_path else dir_path
        selection_options[dir_path] = {
            'type': 'batch',
            'files': files,
            'display_name': display_name
        }
        updated_display_names[dir_path] = display_name
    
    # Add single scenarios (not in batch directories) as individual options
    batch_scenario_paths = set()
    for dir_path, files in batch_directories.items():
        for f in files:
            batch_scenario_paths.add(f"{dir_path}/{f['name']}")
    
    for name in scenario_paths.keys():
        if name not in batch_scenario_paths:
            selection_options[name] = {
                'type': 'single',
                'files': [scenario_paths[name]],
                'display_name': name.split('/')[-1] if '/' in name else name
            }
            updated_display_names[name] = name.split('/')[-1] if '/' in name else name
    
    # Update scenario_names and scenario_display_names
    scenario_names = sorted(selection_options.keys())
    scenario_display_names = updated_display_names
    
    # Create display names (just the filename, not the full path)'''
                
                if old_pattern in source:
                    cell['source'] = source.replace(old_pattern, new_pattern).split('\n')
                    cell['source'] = [line + '\n' if not line.endswith('\n') and idx < len(cell['source'])-1 else line 
                                     for idx, line in enumerate(cell['source'])]
                    print("✓ Updated batch directory detection")
                
                # Update 2: Update load_scenarios to handle batch directories
                old_load_pattern = '''            for name in selected_names:
                # Use scenario_paths to get correct file locations
                paths = scenario_paths[name]
                with open(paths['pkl'], "rb") as f:
                    scenarios[name] = pickle.load(f)
                dataframes[name] = pd.read_csv(paths['csv'], low_memory=False)
            
            # Get shared disaster info from first scenario
            first_scenario = scenarios[selected_names[0]]'''
                
                new_load_pattern = '''            for name in selected_names:
                # Check if this is a batch directory
                if name in batch_directories:
                    # Load and average all scenarios in this directory
                    dir_scenarios = []
                    dir_dataframes = []
                    
                    for file_info in batch_directories[name]:
                        with open(file_info['pkl'], "rb") as f:
                            dir_scenarios.append(pickle.load(f))
                        dir_dataframes.append(pd.read_csv(file_info['csv'], low_memory=False))
                    
                    if dir_scenarios:
                        # Use first scenario as representative (they should have same config)
                        scenarios[name] = dir_scenarios[0]
                        # Average dataframes
                        dataframes[name] = average_dataframes_simple(dir_dataframes)
                        status_label.value += f"<br>✓ Averaged {len(dir_dataframes)} scenarios from directory '{name}'"
                elif name in scenario_paths:
                    # Single scenario - load normally
                    paths = scenario_paths[name]
                    with open(paths['pkl'], "rb") as f:
                        scenarios[name] = pickle.load(f)
                    dataframes[name] = pd.read_csv(paths['csv'], low_memory=False)
                else:
                    print(f"⚠️ Warning: '{name}' not found in scenario_paths or batch_directories")
            
            # Get shared disaster info from first scenario
            first_scenario = list(scenarios.values())[0]'''
                
                if old_load_pattern in source:
                    cell['source'] = source.replace(old_load_pattern, new_load_pattern).split('\n')
                    cell['source'] = [line + '\n' if not line.endswith('\n') and idx < len(cell['source'])-1 else line 
                                     for idx, line in enumerate(cell['source'])]
                    print("✓ Updated load_scenarios function")
                
                # Update 3: Update scenario_select description
                if "description='Select Scenarios:'" in source:
                    cell['source'] = source.replace(
                        "description='Select Scenarios:'",
                        "description='Select Scenarios/Directories:'"
                    ).split('\n')
                    cell['source'] = [line + '\n' if not line.endswith('\n') and idx < len(cell['source'])-1 else line 
                                     for idx, line in enumerate(cell['source'])]
                    print("✓ Updated scenario select description")
                
                break
    
    # Write updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"\n✓ Updated {notebook_path}")

if __name__ == "__main__":
    apply_batch_changes()


