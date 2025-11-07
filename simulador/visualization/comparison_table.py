"""Table visualization for scenario comparison.

This module provides functions for creating interactive comparison tables
that display metrics and configuration parameters side-by-side.
"""

from __future__ import annotations

import ipywidgets as widgets
from IPython.display import display


def create_comparison_table_widget(comparison_data: dict) -> widgets.HTML:
    """Create an HTML widget displaying a styled comparison table.

    Args:
        comparison_data: Dictionary from create_comparison_data() with structure:
            {
                'performance_metrics': [...],
                'config_parameters': [...],
                'scenario1_name': str,
                'scenario2_name': str
            }

    Returns:
        ipywidgets.HTML widget containing the styled table
    """
    scenario1_name = comparison_data["scenario1_name"]
    scenario2_name = comparison_data["scenario2_name"]
    performance_metrics = comparison_data["performance_metrics"]
    config_parameters = comparison_data["config_parameters"]

    # Helper function to format values
    def format_value(value: float, fmt: str, count: int = None) -> str:
        """Format value based on format type, optionally with request count."""
        if fmt == "percentage":
            base_str = f"{value * 100:.2f}%"
            if count is not None:
                base_str += (
                    f" <span style='font-size: 0.85em; color: #666;'>({count})</span>"
                )
            return base_str
        if fmt == "decimal":
            return f"{value:.3f}"
        return f"{value:.4f}"

    # Helper function to format comparison with color coding
    def format_comparison(
        abs_diff: float,
        pct_diff: str,
        fmt: str,
        metric_name: str,
        count_diff: int = None,
    ) -> str:
        """Format comparison column with color coding."""
        # Determine if improvement is positive or negative change
        # For blocking rate, lower is better (negative change is good)
        # For availability, higher is better (positive change is good)
        is_lower_better = "Blocking" in metric_name

        if abs_diff == 0:
            color = "#666"
            symbol = "="
        elif (abs_diff > 0 and not is_lower_better) or (
            abs_diff < 0 and is_lower_better
        ):
            color = "#28a745"  # Green for improvement
            symbol = "▲" if abs_diff > 0 else "▼"
        else:
            color = "#dc3545"  # Red for degradation
            symbol = "▲" if abs_diff > 0 else "▼"

        # Format the absolute difference
        if fmt == "percentage":
            abs_str = f"{abs_diff * 100:.2f}pp"  # percentage points
        elif fmt == "decimal":
            abs_str = f"{abs_diff:+.3f}"
        else:
            abs_str = f"{abs_diff:+.4f}"

        result = f'<span style="color: {color}; font-weight: bold;">{symbol} {abs_str} ({pct_diff})</span>'

        # Add count difference if provided
        if count_diff is not None:
            result += f'<span style="font-size: 0.85em; color: #666;">({count_diff:+d})</span>'

        return result

    # Build HTML table
    html = (
        """
    <style>
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .comparison-table th {
            background-color: #343a40;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #454d55;
        }
        .comparison-table td {
            padding: 10px 12px;
            border: 1px solid #ddd;
        }
        .comparison-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .comparison-table tr:hover {
            background-color: #e9ecef;
        }
        .section-header {
            background-color: #6c757d !important;
            color: white;
            font-weight: bold;
            padding: 10px 12px;
            text-align: center;
            font-size: 15px;
        }
        .metric-name {
            font-weight: 500;
            color: #212529;
        }
        .value-cell {
            text-align: center;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }
        .comparison-cell {
            text-align: center;
            font-size: 13px;
        }
    </style>
    
    <table class="comparison-table">
        <thead>
            <tr>
                <th style="width: 35%;">Metric</th>
                <th style="width: 20%; text-align: center;">"""
        + scenario1_name
        + """</th>
                <th style="width: 20%; text-align: center;">"""
        + scenario2_name
        + """</th>
                <th style="width: 25%; text-align: center;">Comparison</th>
            </tr>
        </thead>
        <tbody>
    """
    )

    # Add performance metrics section
    if performance_metrics:
        html += """
            <tr>
                <td colspan="4" class="section-header">Performance Metrics</td>
            </tr>
        """

        for metric in performance_metrics:
            name = metric["name"]
            count1 = metric.get("scenario1_count")
            count2 = metric.get("scenario2_count")
            count_diff = metric.get("count_diff")
            val1 = format_value(metric["scenario1_value"], metric["format"], count1)
            val2 = format_value(metric["scenario2_value"], metric["format"], count2)
            comparison = format_comparison(
                metric["absolute_diff"],
                metric["percent_diff"],
                metric["format"],
                name,
                count_diff,
            )

            html += f"""
            <tr>
                <td class="metric-name">{name}</td>
                <td class="value-cell">{val1}</td>
                <td class="value-cell">{val2}</td>
                <td class="comparison-cell">{comparison}</td>
            </tr>
            """

    # Add config parameters section
    if config_parameters:
        html += """
            <tr>
                <td colspan="4" class="section-header">Configuration Parameters</td>
            </tr>
        """

        for param in config_parameters:
            name = param["name"]
            val1 = format_value(param["scenario1_value"], param["format"])
            val2 = format_value(param["scenario2_value"], param["format"])

            # For config parameters, no color coding (neutral comparison)
            abs_diff = param["absolute_diff"]
            pct_diff = param["percent_diff"]
            fmt = param["format"]

            if abs_diff == 0:
                comparison = '<span style="color: #666;">= No change</span>'
            else:
                if fmt == "percentage":
                    abs_str = f"{abs_diff * 100:+.2f}pp"
                elif fmt == "decimal":
                    abs_str = f"{abs_diff:+.3f}"
                else:
                    abs_str = f"{abs_diff:+.4f}"
                comparison = f'<span style="color: #666;">{abs_str} ({pct_diff})</span>'

            html += f"""
            <tr>
                <td class="metric-name">{name}</td>
                <td class="value-cell">{val1}</td>
                <td class="value-cell">{val2}</td>
                <td class="comparison-cell">{comparison}</td>
            </tr>
            """

    # Handle case where no config parameters available
    if not config_parameters and not performance_metrics:
        html += """
            <tr>
                <td colspan="4" style="text-align: center; padding: 20px; color: #666;">
                    No comparison data available
                </td>
            </tr>
        """
    elif not config_parameters:
        html += """
            <tr>
                <td colspan="4" class="section-header">Configuration Parameters</td>
            </tr>
            <tr>
                <td colspan="4" style="text-align: center; padding: 15px; color: #666; font-style: italic;">
                    Configuration parameters not available for these scenarios
                </td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return widgets.HTML(value=html)


def display_comparison_table(comparison_data: dict) -> None:
    """Display comparison table directly (convenience function).

    Args:
        comparison_data: Dictionary from create_comparison_data()
    """
    table_widget = create_comparison_table_widget(comparison_data)
    display(table_widget)
