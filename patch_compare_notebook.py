#!/usr/bin/env python3
"""
Patch compare_scenarios2.ipynb to add batch directory support.
"""

import json
from pathlib import Path

def patch_notebook():
    notebook_path = Path("compare_scenarios2.ipynb")
    
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Find create_comparison_gui cell
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source_lines = cell['source']
            source = ''.join(source_lines)
            
            if 'def create_comparison_gui():' in source:
                print(f"Found create_comparison_gui at cell {cell_idx}")
                
                # Update 1: Add batch directory detection
                new_lines = []
                skip_until_scenario_names = False
                skip_until_load = False
                
                for i, line in enumerate(source_lines):
                    # Add batch detection after scenario_paths is populated
                    if 'scenario_names = sorted(scenario_paths.keys())' in line:
                        new_lines.append('    # Detect batch directories (directories with multiple scenarios)\n')
                        new_lines.append('    batch_directories = detect_batch_directories(output_path)\n')
                        new_lines.append('    \n')
                        new_lines.append('    # Create selection options: show directories for batch, individual scenarios for single\n')
                        new_lines.append('    selection_options = {}\n')
                        new_lines.append('    updated_display_names = {}\n')
                        new_lines.append('    \n')
                        new_lines.append('    # Add batch directories as options\n')
                        new_lines.append('    for dir_path, files in batch_directories.items():\n')
                        new_lines.append('        display_name = dir_path.split(\'/\')[-1] if \'/\' in dir_path else dir_path\n')
                        new_lines.append('        selection_options[dir_path] = {\n')
                        new_lines.append('            \'type\': \'batch\',\n')
                        new_lines.append('            \'files\': files,\n')
                        new_lines.append('            \'display_name\': display_name\n')
                        new_lines.append('        }\n')
                        new_lines.append('        updated_display_names[dir_path] = display_name\n')
                        new_lines.append('    \n')
                        new_lines.append('    # Add single scenarios (not in batch directories) as individual options\n')
                        new_lines.append('    batch_scenario_paths = set()\n')
                        new_lines.append('    for dir_path, files in batch_directories.items():\n')
                        new_lines.append('        for f in files:\n')
                        new_lines.append('            batch_scenario_paths.add(f\"{dir_path}/{f[\'name\']}\")\n')
                        new_lines.append('    \n')
                        new_lines.append('    for name in scenario_paths.keys():\n')
                        new_lines.append('        if name not in batch_scenario_paths:\n')
                        new_lines.append('            selection_options[name] = {\n')
                        new_lines.append('                \'type\': \'single\',\n')
                        new_lines.append('                \'files\': [scenario_paths[name]],\n')
                        new_lines.append('                \'display_name\': name.split(\'/\')[-1] if \'/\' in name else name\n')
                        new_lines.append('            }\n')
                        new_lines.append('            updated_display_names[name] = name.split(\'/\')[-1] if \'/\' in name else name\n')
                        new_lines.append('    \n')
                        new_lines.append('    # Update scenario_names and scenario_display_names\n')
                        new_lines.append('    scenario_names = sorted(selection_options.keys())\n')
                        new_lines.append('    scenario_display_names = updated_display_names\n')
                        new_lines.append('    \n')
                        new_lines.append(line)  # Keep the original line
                        skip_until_scenario_names = True
                    elif skip_until_scenario_names and 'scenario_display_names = {' in line:
                        # Skip the old display names creation
                        continue
                    elif skip_until_scenario_names and 'if len(scenario_names) < 1:' in line:
                        new_lines.append('    if len(scenario_names) < 1:\n')
                        new_lines.append('        print("Error: Need at least 1 valid scenario or directory in output/ folder")\n')
                        skip_until_scenario_names = False
                    # Update load_scenarios function
                    elif 'for name in selected_names:' in line and 'Use scenario_paths to get correct file locations' in ''.join(source_lines[i:i+5]):
                        new_lines.append('            for name in selected_names:\n')
                        new_lines.append('                # Check if this is a batch directory\n')
                        new_lines.append('                if name in batch_directories:\n')
                        new_lines.append('                    # Load and average all scenarios in this directory\n')
                        new_lines.append('                    dir_scenarios = []\n')
                        new_lines.append('                    dir_dataframes = []\n')
                        new_lines.append('                    \n')
                        new_lines.append('                    for file_info in batch_directories[name]:\n')
                        new_lines.append('                        with open(file_info[\'pkl\'], "rb") as f:\n')
                        new_lines.append('                            dir_scenarios.append(pickle.load(f))\n')
                        new_lines.append('                        dir_dataframes.append(pd.read_csv(file_info[\'csv\'], low_memory=False))\n')
                        new_lines.append('                    \n')
                        new_lines.append('                    if dir_scenarios:\n')
                        new_lines.append('                        # Use first scenario as representative (they should have same config)\n')
                        new_lines.append('                        scenarios[name] = dir_scenarios[0]\n')
                        new_lines.append('                        # Average dataframes\n')
                        new_lines.append('                        dataframes[name] = average_dataframes_simple(dir_dataframes)\n')
                        new_lines.append('                        status_label.value += f"<br>✓ Averaged {len(dir_dataframes)} scenarios from directory \'{name}\'"\n')
                        new_lines.append('                elif name in scenario_paths:\n')
                        new_lines.append('                    # Single scenario - load normally\n')
                        new_lines.append('                    paths = scenario_paths[name]\n')
                        new_lines.append('                    with open(paths[\'pkl\'], "rb") as f:\n')
                        new_lines.append('                        scenarios[name] = pickle.load(f)\n')
                        new_lines.append('                    dataframes[name] = pd.read_csv(paths[\'csv\'], low_memory=False)\n')
                        new_lines.append('                else:\n')
                        new_lines.append('                    print(f"⚠️ Warning: \'{name}\' not found in scenario_paths or batch_directories")\n')
                        # Skip the old loading code
                        skip_until_load = True
                        continue
                    elif skip_until_load:
                        if 'first_scenario = scenarios[selected_names[0]]' in line:
                            new_lines.append('            # Get shared disaster info from first scenario\n')
                            new_lines.append('            first_scenario = list(scenarios.values())[0]\n')
                            skip_until_load = False
                            continue
                        elif 'Use scenario_paths to get correct file locations' in line or 'with open(paths[\'pkl\']' in line or 'dataframes[name] = pd.read_csv' in line:
                            continue  # Skip old loading code
                    elif 'first_scenario = scenarios[selected_names[0]]' in line:
                        new_lines.append('            first_scenario = list(scenarios.values())[0]\n')
                        continue
                    elif 'description=\'Select Scenarios:\'' in line:
                        new_lines.append('        description=\'Select Scenarios/Directories:\',\n')
                        continue
                    else:
                        new_lines.append(line)
                
                cell['source'] = new_lines
                print("✓ Updated create_comparison_gui function")
                break
    
    # Write updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"\n✓ Patched {notebook_path}")

if __name__ == "__main__":
    patch_notebook()


