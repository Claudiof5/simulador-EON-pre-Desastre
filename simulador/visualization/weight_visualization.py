"""Weight-specific visualization functions for network analysis.

This module provides visualization utilities specifically for weight-related
analysis, including ISP topology visualization, weight decomposition plots,
and path visualization with weights.
"""

from __future__ import annotations

from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx

# ============================================================================
# SEPARATED VISUALIZATION FUNCTIONS
# ============================================================================


def plot_isp_topology(
    ax,
    isp,
    topology_graph,
    disaster_node,
    isp_id,
    edge_weights,
    link_frequency,
    remove_disaster_node=True,
):
    """Plot ISP topology on the left side (colored by weights, sized by frequency).

    Args:
        ax: Matplotlib axis to plot on
        isp: ISP object
        topology_graph: Full network topology
        disaster_node: Node affected by disaster
        isp_id: ISP ID
        edge_weights: Dict of link -> total weight
        link_frequency: Dict of link -> frequency in shortest paths
        remove_disaster_node: If True, removes disaster node from graph (default: True)
    """
    # Get ISP nodes
    isp_nodes_set = set(isp.nodes)
    isp_nodes_active = (
        isp_nodes_set - {disaster_node} if remove_disaster_node else isp_nodes_set
    )

    # Build ISP graph
    isp_graph = topology_graph.subgraph(isp_nodes_active).copy()
    for edge in isp.edges:
        if (
            edge[0] in isp_nodes_active
            and edge[1] in isp_nodes_active
            and not isp_graph.has_edge(edge[0], edge[1])
            and topology_graph.has_edge(edge[0], edge[1])
        ):
            edge_data = topology_graph[edge[0]][edge[1]].copy()
            isp_graph.add_edge(edge[0], edge[1], **edge_data)

    is_connected = nx.is_connected(isp_graph)
    components = list(nx.connected_components(isp_graph)) if not is_connected else []

    # Title
    view_mode = "Disaster View" if remove_disaster_node else "Normal View"
    title = f"ISP {isp_id} - Topologia [{view_mode}] "
    title += "(PARTICIONADA)" if not is_connected else "com Pesos"
    ax.set_title(title, fontsize=16, fontweight="bold")

    # Layout (consistent with full topology)
    pos = nx.spring_layout(topology_graph, seed=7)

    # Background nodes
    all_nodes = list(topology_graph.nodes())
    background_nodes = [
        n for n in all_nodes if n not in isp_nodes_set and n != disaster_node
    ]

    # LAYER 1: Background topology (gray)
    if background_nodes:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=background_nodes,
            node_color="lightgray",
            node_size=500,
            edgecolors="gray",
            linewidths=1,
            alpha=0.3,
            ax=ax,
        )

    all_edges = list(topology_graph.edges())
    nx.draw_networkx_edges(
        topology_graph,
        pos,
        edgelist=all_edges,
        edge_color="lightgray",
        width=1,
        alpha=0.3,
        ax=ax,
    )

    # LAYER 2: ISP nodes (highlighted)
    isp_nodes_list = list(isp_nodes_active)
    if isp_nodes_list:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=isp_nodes_list,
            node_color="lightblue",
            node_size=800,
            edgecolors="black",
            linewidths=2,
            ax=ax,
        )

    # Datacenter destination node
    if isp.datacenter.destination:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=[isp.datacenter.destination],
            node_color="lightgreen",
            node_size=800,
            edgecolors="black",
            linewidths=2,
            ax=ax,
        )

    # LAYER 3: Disaster node (red X) - only in disaster view
    if remove_disaster_node and disaster_node in isp_nodes_set:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=[disaster_node],
            node_color="red",
            node_size=1000,
            node_shape="X",
            edgecolors="darkred",
            linewidths=3,
            ax=ax,
            label="Nó do Desastre",
        )

    # Node labels
    nx.draw_networkx_labels(topology_graph, pos, font_size=9, font_weight="bold", ax=ax)

    # LAYER 4: ISP edges (colored by weight, thickness by frequency)
    edges = list(isp_graph.edges())
    weights_list = [edge_weights.get((u, v), 1.0) for u, v in edges]

    # Calculate widths based on frequency
    max_freq = max(link_frequency.values()) if link_frequency else 1
    widths = []
    for u, v in edges:
        link = tuple(sorted([u, v]))
        freq = link_frequency.get(link, 0)
        width = 2 + (freq / max_freq) * 6 if max_freq > 0 else 3
        widths.append(width)

    # Color mapping
    vmin = 1.0
    vmax = max(weights_list) if weights_list else 1.8

    nx.draw_networkx_edges(
        topology_graph,
        pos,
        edgelist=edges,
        edge_color=weights_list,
        edge_cmap=plt.cm.RdYlGn_r,
        edge_vmin=vmin,
        edge_vmax=vmax,
        width=widths,
        alpha=0.8,
        ax=ax,
    )

    # Colorbar
    sm = plt.cm.ScalarMappable(
        cmap=plt.cm.RdYlGn_r, norm=plt.Normalize(vmin=vmin, vmax=vmax)
    )
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Peso Total", rotation=270, labelpad=20, fontsize=12)

    # Partition warning
    if not is_connected:
        ax.text(
            0.5,
            0.05,
            f"[!] Rede particionada em {len(components)} componentes",
            transform=ax.transAxes,
            ha="center",
            fontsize=11,
            color="red",
            fontweight="bold",
            bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.7),
        )

    ax.axis("off")
    if remove_disaster_node and disaster_node in isp_nodes_set:
        ax.legend(loc="upper left", fontsize=10)

    return is_connected, components


def plot_weight_decomposition(
    ax, isp_id, edge_weights, edge_components, is_connected, components, top_n=10
):
    """Plot weight decomposition bar chart on the right side.

    Args:
        ax: Matplotlib axis to plot on
        isp_id: ISP ID
        edge_weights: Dict of link -> total weight
        edge_components: Dict of link -> {isp_usage, migration, criticality, total}
        is_connected: Whether ISP is connected
        components: List of connected components (if partitioned)
        top_n: Number of top links to show
    """
    if not edge_weights:
        # Fallback: No weights
        ax.set_title(
            f"ISP {isp_id} - Sem Dados de Pesos", fontsize=16, fontweight="bold"
        )
        ax.text(
            0.5,
            0.5,
            "Pesos não foram calculados para esta ISP",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.axis("off")
        return

    # Title
    title = f"ISP {isp_id} - Top {top_n} Links por Peso (Únicos)"
    if not is_connected:
        title += f" ({len(components)} Componentes)"
    ax.set_title(title, fontsize=16, fontweight="bold")

    # Normalize edges to avoid duplicates (always store as (min, max))
    unique_edges = {}
    for (u, v), weight in edge_weights.items():
        normalized_edge = (min(u, v), max(u, v))
        if normalized_edge not in unique_edges:
            unique_edges[normalized_edge] = weight

    # Get top N links by weight
    sorted_edges = sorted(unique_edges.items(), key=lambda x: x[1], reverse=True)[
        :top_n
    ]

    if not sorted_edges:
        ax.text(
            0.5,
            0.5,
            "Sem links para mostrar",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax.transAxes,
        )
        ax.axis("off")
        return

    link_names = [f"{u}↔{v}" for (u, v), _ in sorted_edges]  # Use ↔ to show undirected

    # Extract weight components (try both directions since edge_components may have either)
    def get_edge_component(link, component_name):
        """Get component value, trying both edge directions."""
        if link in edge_components:
            return edge_components[link][component_name]
        # Try reverse direction
        reverse_link = (link[1], link[0])
        if reverse_link in edge_components:
            return edge_components[reverse_link][component_name]
        return 0.0

    isp_usage_vals = [get_edge_component(link, "isp_usage") for link, _ in sorted_edges]
    migration_vals = [get_edge_component(link, "migration") for link, _ in sorted_edges]
    criticality_vals = [
        get_edge_component(link, "criticality") for link, _ in sorted_edges
    ]

    x = range(len(link_names))
    bar_height = 0.6

    # Stacked bar chart - build cumulative positions
    base_vals = [1.0] * len(x)
    left_isp = base_vals
    left_migration = [
        base + isp for base, isp in zip(base_vals, isp_usage_vals, strict=False)
    ]
    left_criticality = [
        base + isp + mig
        for base, isp, mig in zip(
            base_vals, isp_usage_vals, migration_vals, strict=False
        )
    ]

    # Draw stacked bars
    ax.barh(
        x,
        base_vals,
        bar_height,
        label="Base (1.0)",
        color="lightgray",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.barh(
        x,
        isp_usage_vals,
        bar_height,
        left=left_isp,
        label="ISP Usage",
        color="skyblue",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.barh(
        x,
        migration_vals,
        bar_height,
        left=left_migration,
        label="Migration",
        color="lightgreen",
        edgecolor="black",
        linewidth=0.5,
    )
    ax.barh(
        x,
        criticality_vals,
        bar_height,
        left=left_criticality,
        label="Criticality",
        color="salmon",
        edgecolor="black",
        linewidth=0.5,
    )

    # Formatting
    ax.set_yticks(x)
    ax.set_yticklabels(link_names, fontsize=10)
    ax.set_xlabel("Peso Total", fontsize=12, fontweight="bold")
    ax.set_ylabel("Link", fontsize=12, fontweight="bold")
    vmax = max(w for w in edge_weights.values())
    ax.set_xlim(0.9, vmax * 1.05)
    ax.legend(loc="lower right", fontsize=10, framealpha=0.9)
    ax.grid(axis="x", alpha=0.3, linestyle="--")

    # Add total weight values
    for i, (link, total_weight) in enumerate(sorted_edges):
        ax.text(
            total_weight + 0.02,
            i,
            f"{total_weight:.2f}",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    # Add note about unique edges
    ax.text(
        0.98,
        0.02,
        "Links únicos (↔ = não-direcionais)",
        transform=ax.transAxes,
        fontsize=8,
        ha="right",
        va="bottom",
        style="italic",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )


# ============================================================================
# MAIN WRAPPER FUNCTION (combines both plots)
# ============================================================================


def visualize_isp_topology_with_weights(
    isp,
    topology_graph,
    disaster_node,
    isp_id,
    weights_by_link_by_isp,
    figsize=(18, 10),
    remove_disaster_node=True,
):
    """Visualize ISP topology with weights (wrapper for two separate plots).

    Args:
        isp: ISP object
        topology_graph: Main topology graph (full network)
        disaster_node: Node to remove (disaster)
        isp_id: ID of the ISP
        weights_by_link_by_isp: Computed weights for all ISPs
        figsize: Figure size tuple
        remove_disaster_node: If True, removes disaster node from visualization (default: True)
    """
    # === PREPARE DATA ===
    isp_nodes_set = set(isp.nodes)
    isp_nodes_active = (
        isp_nodes_set - {disaster_node} if remove_disaster_node else isp_nodes_set
    )

    # Build ISP graph
    isp_graph = topology_graph.subgraph(isp_nodes_active).copy()
    for edge in isp.edges:
        if (
            edge[0] in isp_nodes_active
            and edge[1] in isp_nodes_active
            and not isp_graph.has_edge(edge[0], edge[1])
            and topology_graph.has_edge(edge[0], edge[1])
        ):
            edge_data = topology_graph[edge[0]][edge[1]].copy()
            isp_graph.add_edge(edge[0], edge[1], **edge_data)

    is_connected = nx.is_connected(isp_graph)
    components = list(nx.connected_components(isp_graph)) if not is_connected else []

    if not is_connected:
        pass

    # Calculate link frequency (for thickness)
    link_frequency = defaultdict(int)
    if is_connected:
        nodes = sorted(isp_graph.nodes())
        for src in nodes:
            for dst in nodes:
                if src >= dst:
                    continue
                try:
                    path = nx.shortest_path(isp_graph, src, dst, weight="weight")
                    for i in range(len(path) - 1):
                        link = tuple(sorted([path[i], path[i + 1]]))
                        link_frequency[link] += 1
                except nx.NetworkXNoPath:
                    continue
    else:
        for component in nx.connected_components(isp_graph):
            comp_nodes = sorted(component)
            for src in comp_nodes:
                for dst in comp_nodes:
                    if src >= dst:
                        continue
                    try:
                        path = nx.shortest_path(isp_graph, src, dst, weight="weight")
                        for i in range(len(path) - 1):
                            link = tuple(sorted([path[i], path[i + 1]]))
                            link_frequency[link] += 1
                    except nx.NetworkXNoPath:
                        continue

    # Calculate weights
    edge_weights = {}
    edge_components = {}
    for u, v in isp_graph.edges():
        for link in [(u, v), (v, u)]:
            if isp_id in weights_by_link_by_isp and weights_by_link_by_isp[isp_id]:
                weights = weights_by_link_by_isp.get(isp_id, {}).get(link, {})
                edge_weights[link] = weights["total"]
                edge_components[link] = weights
            else:
                edge_weights[link] = 1.0
                edge_components[link] = {
                    "isp_usage": 1.0,
                    "migration": 0.0,
                    "criticality": 0.0,
                    "total": 1.0,
                }

    # === CREATE FIGURE WITH TWO PLOTS ===
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # LEFT PLOT: Topology
    is_connected, components = plot_isp_topology(
        ax1,
        isp,
        topology_graph,
        disaster_node,
        isp_id,
        edge_weights,
        link_frequency,
        remove_disaster_node=remove_disaster_node,
    )

    # RIGHT PLOT: Weight Decomposition
    plot_weight_decomposition(
        ax2,
        isp_id,
        edge_weights,
        edge_components,
        is_connected,
        components,
        top_n=len(isp.edges),
    )

    plt.tight_layout()
    plt.show()

    # Print statistics
    print(f"\n{'=' * 80}")
    print(f"ESTATÍSTICAS - ISP {isp_id}")
    print(f"{'=' * 80}")
    print(f"Nós da ISP (total): {len(isp_nodes_set)}")
    print(f"Nós após remover desastre: {len(isp_nodes_active)}")
    print(f"Links da ISP: {isp_graph.number_of_edges()}")
    print(f"Conectada: {'Sim' if is_connected else 'Não'}")
