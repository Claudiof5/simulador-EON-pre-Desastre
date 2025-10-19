"""Topology visualization functions for network graphs.

This module provides utilities for visualizing network topologies, including
nodes, edges, ISP allocations, disaster impacts, and datacenters.
"""

from __future__ import annotations

from collections import Counter

import matplotlib.pyplot as plt
import networkx as nx

# Default color palette
DEFAULT_COLORS = [
    (255 / 255, 0 / 255, 0 / 255),  # Red
    (0 / 255, 255 / 255, 0 / 255),  # Green
    (0 / 255, 255 / 255, 255 / 255),  # Cyan
    (255 / 255, 0 / 255, 255 / 255),  # Magenta
    (255 / 255, 255 / 255, 0 / 255),  # Yellow
    (255 / 255, 128 / 255, 0 / 255),  # Orange
    (128 / 255, 0 / 255, 255 / 255),  # Purple
    (0 / 255, 128 / 255, 255 / 255),  # Light Blue
]

BLUE = (100 / 255, 149 / 255, 237 / 255)
GRAY = (128 / 255, 128 / 255, 128 / 255)
RED = (220 / 255, 20 / 255, 60 / 255)
GREEN = (34 / 255, 139 / 255, 34 / 255)


def plot_basic_topology(
    topology: nx.Graph,
    figsize: tuple[int, int] = (14, 10),
    node_size: int = 300,
    with_labels: bool = True,
    seed: int = 7,
) -> plt.Figure:
    """Plot basic network topology.

    Args:
        topology: NetworkX graph
        figsize: Figure size
        node_size: Size of nodes
        with_labels: Whether to show node labels
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    nx.draw_networkx_nodes(topology, pos, node_size=node_size, node_color=BLUE, ax=ax)
    nx.draw_networkx_edges(topology, pos, edge_color=GRAY, width=1.5, ax=ax)

    if with_labels:
        nx.draw_networkx_labels(
            topology, pos, font_size=10, font_family="sans-serif", ax=ax
        )

    ax.set_title("Network Topology")
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_nodes_and_links(
    topology: nx.Graph,
    nodes: list[int] | None = None,
    links: list[tuple[int, int]] | None = None,
    color=RED,
    node_size: int = 200,
    edge_width: float = 2.5,
    show_weights: bool = False,
    figsize: tuple[int, int] = (14, 10),
    seed: int = 7,
) -> plt.Figure:
    """Draw specific nodes and links on topology with highlighting.

    Args:
        topology: NetworkX graph
        nodes: List of nodes to highlight
        links: List of edges to highlight
        color: Color for highlighted elements
        node_size: Size of nodes
        edge_width: Width of edges
        show_weights: Whether to show edge weights
        figsize: Figure size
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    # Draw base topology
    nx.draw_networkx_nodes(
        topology, pos, node_size=node_size, node_color=BLUE, alpha=0.3, ax=ax
    )
    nx.draw_networkx_edges(topology, pos, edge_color=GRAY, width=1.0, alpha=0.3, ax=ax)

    # Highlight specified nodes
    if nodes:
        nx.draw_networkx_nodes(
            topology, pos, nodelist=nodes, node_size=node_size, node_color=color, ax=ax
        )

    # Highlight specified links
    if links:
        nx.draw_networkx_edges(
            topology, pos, edgelist=links, edge_color=color, width=edge_width, ax=ax
        )

    # Show edge weights
    if show_weights:
        edge_labels = nx.get_edge_attributes(topology, "weight")
        nx.draw_networkx_edge_labels(topology, pos, edge_labels=edge_labels, ax=ax)

    # Always show labels
    nx.draw_networkx_labels(
        topology, pos, font_size=11, font_family="sans-serif", ax=ax
    )

    ax.set_title("Highlighted Nodes and Links")
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_isp_view(
    topology: nx.Graph,
    isp_nodes: list[int],
    isp_edges: list[tuple[int, int]],
    global_vision: bool = True,
    show_weights: bool = False,
    color=RED,
    figsize: tuple[int, int] = (14, 10),
    title: str = "ISP View",
    seed: int = 7,
) -> plt.Figure:
    """Visualize ISP allocation in the network.

    Args:
        topology: NetworkX graph
        isp_nodes: Nodes allocated to ISP
        isp_edges: Edges allocated to ISP
        global_vision: If True, show entire topology; if False, show only ISP
        show_weights: Whether to show edge weights
        color: Color for ISP elements
        figsize: Figure size
        title: Plot title
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    if global_vision:
        # Show full topology with ISP highlighted
        nx.draw_networkx_nodes(topology, pos, node_size=200, node_color=BLUE, ax=ax)
        nx.draw_networkx_edges(topology, pos, edge_color=BLUE, width=2.5, ax=ax)

        # Highlight ISP nodes and edges
        nx.draw_networkx_nodes(
            topology, pos, nodelist=isp_nodes, node_size=200, node_color=color, ax=ax
        )
        nx.draw_networkx_edges(
            topology, pos, edgelist=isp_edges, edge_color=color, width=2.5, ax=ax
        )
    else:
        # Show only ISP subgraph
        isp_subgraph = topology.subgraph(isp_nodes)
        nx.draw_networkx_nodes(
            isp_subgraph, pos, node_size=200, node_color=color, ax=ax
        )
        nx.draw_networkx_edges(isp_subgraph, pos, edge_color=color, width=2.5, ax=ax)

    nx.draw_networkx_labels(
        topology, pos, font_size=11, font_family="sans-serif", ax=ax
    )

    if show_weights:
        edge_labels = nx.get_edge_attributes(topology, "weight")
        nx.draw_networkx_edge_labels(topology, pos, edge_labels=edge_labels, ax=ax)

    ax.set_title(title)
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_isps_separately(
    topology: nx.Graph,
    isp_data: dict[int, dict] | object,
    colors: list[tuple] | None = None,
    figsize: tuple[int, int] = (20, 12),
    seed: int = 7,
) -> plt.Figure:
    """Show each ISP in its own subplot."""
    # Extract ISP dict if needed
    if hasattr(isp_data, "lista_de_isps"):
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {"nodes": list(isp.nodes), "edges": list(isp.edges)}
    else:
        isp_dict = isp_data

    if colors is None:
        colors = DEFAULT_COLORS

    num_isps = len(isp_dict)
    cols = 3
    rows = (num_isps + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    axes = axes.flatten() if num_isps > 1 else [axes]

    pos = nx.spring_layout(topology, seed=seed)

    for idx, (isp_id, isp_info) in enumerate(isp_dict.items()):
        ax = axes[idx]

        # Draw full topology faded
        nx.draw_networkx_nodes(
            topology, pos, node_size=200, node_color=GRAY, alpha=0.2, ax=ax
        )
        nx.draw_networkx_edges(
            topology, pos, edge_color=GRAY, width=1.0, alpha=0.2, ax=ax
        )

        # Highlight this ISP
        color = colors[idx % len(colors)]
        if isp_info.get("nodes"):
            nx.draw_networkx_nodes(
                topology,
                pos,
                nodelist=isp_info["nodes"],
                node_size=300,
                node_color=color,
                ax=ax,
            )
        if isp_info.get("edges"):
            nx.draw_networkx_edges(
                topology,
                pos,
                edgelist=isp_info["edges"],
                edge_color=color,
                width=2.5,
                ax=ax,
            )

        nx.draw_networkx_labels(topology, pos, font_size=9, ax=ax)
        ax.set_title(f"ISP {isp_id}", fontsize=12, fontweight="bold")
        ax.axis("off")

    # Hide unused subplots
    for idx in range(num_isps, len(axes)):
        axes[idx].axis("off")

    plt.suptitle("ISPs - Individual Views", fontsize=16, fontweight="bold")
    plt.tight_layout()


def plot_all_isps(
    topology: nx.Graph,
    isp_data: dict[int, dict] | object,
    colors: list[tuple] | None = None,
    figsize: tuple[int, int] = (16, 12),
    seed: int = 7,
) -> plt.Figure:
    """Visualize all ISPs in the network with different colors.

    Args:
        topology: NetworkX graph
        isp_data: Either ISP dict {isp_id: {"nodes": [...], "edges": [...]}}
                  OR a Scenario object with lista_de_isps attribute
        colors: List of colors for each ISP (defaults to DEFAULT_COLORS)
        figsize: Figure size
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    # Extract ISP dictionary from Scenario if needed
    if hasattr(isp_data, "lista_de_isps"):
        # It's a Scenario object - extract ISP info
        isp_dict = {}
        for isp in isp_data.lista_de_isps:
            isp_dict[isp.isp_id] = {
                "nodes": list(isp.nodes)
                if hasattr(isp.nodes, "__iter__")
                else [isp.nodes],
                "edges": list(isp.edges) if hasattr(isp.edges, "__iter__") else [],
            }
    else:
        # It's already a dictionary
        isp_dict = isp_data

    if colors is None:
        colors = DEFAULT_COLORS

    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    # Calculate node and edge sizes based on number of ISPs
    num_isps = len(isp_dict)
    node_size = 400
    edge_width = 3.5
    node_range = 200
    edge_range = 2.0

    # Draw each ISP with decreasing size for visibility
    for i, (isp_id, isp_info) in enumerate(isp_dict.items()):
        isp_nodes = isp_info.get("nodes", [])
        isp_edges = isp_info.get("edges", [])

        current_node_size = node_size - (i * node_range / num_isps)
        current_edge_width = edge_width - (i * edge_range / num_isps)
        current_color = colors[i % len(colors)]

        if isp_nodes:
            nx.draw_networkx_nodes(
                topology,
                pos,
                nodelist=isp_nodes,
                node_size=current_node_size,
                node_color=current_color,
                label=f"ISP {isp_id}",
                ax=ax,
            )

        if isp_edges:
            nx.draw_networkx_edges(
                topology,
                pos,
                edgelist=isp_edges,
                edge_color=current_color,
                width=current_edge_width,
                ax=ax,
            )

    nx.draw_networkx_labels(
        topology, pos, font_size=11, font_family="sans-serif", ax=ax
    )

    ax.set_title("All ISPs View")
    ax.legend(loc="upper right")
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_disaster_and_datacenters(
    topology: nx.Graph,
    disaster_node: int | None = None,
    disaster_edges: list[tuple[int, int]] | None = None,
    datacenter_nodes: list[int] | None = None,
    components: tuple[set, set] | None = None,
    scenario: object | None = None,
    figsize: tuple[int, int] = (16, 12),
    seed: int = 7,
) -> plt.Figure:
    """Visualize disaster impact and datacenter locations.

    Args:
        topology: NetworkX graph
        disaster_node: Node that fails (or pass scenario to auto-extract)
        disaster_edges: Edges affected by disaster
        datacenter_nodes: Nodes with datacenters (or pass scenario to auto-extract)
        components: Tuple of (component1, component2) after disaster
        scenario: Optional Scenario object to auto-extract disaster and datacenter info
        figsize: Figure size
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    # Extract info from Scenario if provided
    if scenario is not None and hasattr(scenario, "desastre"):
        if disaster_node is None and hasattr(scenario.desastre, "node"):
            disaster_node = scenario.desastre.node

        # Extract datacenter nodes from ISPs
        if datacenter_nodes is None and hasattr(scenario, "lista_de_isps"):
            datacenter_nodes = []
            for isp in scenario.lista_de_isps:
                if (
                    hasattr(isp, "datacenter")
                    and isp.datacenter is not None
                    and hasattr(isp.datacenter, "node")
                ):
                    datacenter_nodes.append(isp.datacenter.node)

    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    # Draw base topology
    nx.draw_networkx_nodes(topology, pos, node_size=1000, node_color=BLUE, ax=ax)
    nx.draw_networkx_edges(topology, pos, edge_color=GRAY, width=5, ax=ax)

    # Highlight components if provided
    if components:
        comp1, comp2 = components
        nx.draw_networkx_nodes(
            topology,
            pos,
            nodelist=list(comp1),
            node_size=1000,
            node_color=GREEN,
            label="Component 1",
            ax=ax,
        )
        nx.draw_networkx_nodes(
            topology,
            pos,
            nodelist=list(comp2),
            node_size=1000,
            node_color=(255 / 255, 165 / 255, 0 / 255),
            label="Component 2",
            ax=ax,
        )

    # Highlight disaster node
    if disaster_node is not None:
        nx.draw_networkx_nodes(
            topology,
            pos,
            nodelist=[disaster_node],
            node_size=500,
            node_color=RED,
            node_shape="X",
            label="Disaster Node",
            ax=ax,
        )

    # Highlight disaster edges (cut edges)
    if disaster_edges:
        nx.draw_networkx_edges(
            topology,
            pos,
            edgelist=disaster_edges,
            edge_color=RED,
            width=3.0,
            style="dashed",
            label="Cut Edges",
            ax=ax,
        )

    # Highlight datacenters
    if datacenter_nodes:
        nx.draw_networkx_nodes(
            topology,
            pos,
            nodelist=datacenter_nodes,
            node_size=600,
            node_color="yellow",
            node_shape="s",
            edgecolors="black",
            linewidths=2,
            label="Datacenters",
            ax=ax,
        )

    nx.draw_networkx_labels(
        topology, pos, font_size=10, font_family="sans-serif", ax=ax
    )

    ax.set_title("Disaster Impact and Datacenters")
    ax.legend(loc="upper right")
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_path_on_topology(
    topology: nx.Graph,
    path: list[int],
    source: int,
    destination: int,
    figsize: tuple[int, int] = (14, 10),
    seed: int = 7,
) -> plt.Figure:
    """Highlight a specific path in the topology.

    Args:
        topology: NetworkX graph
        path: List of nodes in the path
        source: Source node
        destination: Destination node
        figsize: Figure size
        seed: Random seed for layout

    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    pos = nx.spring_layout(topology, seed=seed)

    # Draw base topology
    nx.draw_networkx_nodes(
        topology, pos, node_size=200, node_color=BLUE, alpha=0.3, ax=ax
    )
    nx.draw_networkx_edges(topology, pos, edge_color=GRAY, width=1.0, alpha=0.3, ax=ax)

    # Highlight path nodes
    path_nodes = set(path)
    nx.draw_networkx_nodes(
        topology, pos, nodelist=list(path_nodes), node_size=300, node_color=GREEN, ax=ax
    )

    # Highlight path edges
    path_edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    nx.draw_networkx_edges(
        topology, pos, edgelist=path_edges, edge_color=GREEN, width=3.0, ax=ax
    )

    # Highlight source and destination
    nx.draw_networkx_nodes(
        topology,
        pos,
        nodelist=[source],
        node_size=500,
        node_color="lime",
        node_shape="o",
        edgecolors="black",
        linewidths=2,
        label="Source",
        ax=ax,
    )
    nx.draw_networkx_nodes(
        topology,
        pos,
        nodelist=[destination],
        node_size=500,
        node_color="darkgreen",
        node_shape="s",
        edgecolors="black",
        linewidths=2,
        label="Destination",
        ax=ax,
    )

    nx.draw_networkx_labels(
        topology, pos, font_size=10, font_family="sans-serif", ax=ax
    )

    ax.set_title(f"Path from {source} to {destination}")
    ax.legend()
    ax.axis("off")

    plt.tight_layout()
    return fig


def plot_node_degree_distribution(
    topology: nx.Graph, figsize: tuple[int, int] = (12, 6)
) -> plt.Figure:
    """Plot node degree distribution of the topology.

    Args:
        topology: NetworkX graph
        figsize: Figure size

    Returns:
        Matplotlib figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    degrees = [d for _, d in topology.degree()]

    # Histogram
    ax1.hist(
        degrees,
        bins=max(degrees) - min(degrees) + 1,
        color="steelblue",
        edgecolor="black",
    )
    ax1.set_xlabel("Degree")
    ax1.set_ylabel("Frequency")
    ax1.set_title("Node Degree Distribution")
    ax1.grid(alpha=0.3)

    # Bar chart of degree counts
    degree_counts = Counter(degrees)
    degrees_sorted = sorted(degree_counts.keys())
    counts = [degree_counts[d] for d in degrees_sorted]

    ax2.bar(degrees_sorted, counts, color="steelblue", edgecolor="black")
    ax2.set_xlabel("Degree")
    ax2.set_ylabel("Number of Nodes")
    ax2.set_title("Nodes per Degree")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    return fig


def create_topology_layout(
    topology: nx.Graph, layout_type: str = "spring", seed: int = 7
) -> dict:
    """Create a layout for the topology.

    Args:
        topology: NetworkX graph
        layout_type: Type of layout ('spring', 'circular', 'kamada_kawai', 'shell')
        seed: Random seed for reproducibility

    Returns:
        Dictionary of node positions
    """
    if layout_type == "spring":
        return nx.spring_layout(topology, seed=seed)
    if layout_type == "circular":
        return nx.circular_layout(topology)
    if layout_type == "kamada_kawai":
        return nx.kamada_kawai_layout(topology)
    if layout_type == "shell":
        return nx.shell_layout(topology)
    raise ValueError(f"Unknown layout type: {layout_type}")
