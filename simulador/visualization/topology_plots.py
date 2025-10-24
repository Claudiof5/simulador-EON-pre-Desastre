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


def visualize_migration_analysis(
    topology_graph: nx.Graph,
    lista_de_isps: list,
    disaster_node: int,
    max_paths_per_isp: int = 10,
    figsize: tuple[int, int] = (20, 10),
) -> tuple[list[dict], dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    """Visualize datacenter migration analysis across ISPs.

    Args:
        topology_graph: NetworkX graph of the topology
        lista_de_isps: List of ISP objects
        disaster_node: Node affected by disaster
        max_paths_per_isp: Maximum paths to calculate per ISP
        figsize: Figure size tuple

    Returns:
        Tuple of (migration_paths, link_usage_count, directed_link_usage)
    """
    from collections import defaultdict
    from itertools import islice

    migration_paths = []
    link_usage_count = defaultdict(int)
    directed_link_usage = defaultdict(int)
    datacenters_info = []

    # Collect migration paths from all ISPs
    for isp in lista_de_isps:
        if not hasattr(isp, "datacenter") or isp.datacenter is None:
            continue

        datacenter = isp.datacenter
        src = datacenter.source
        dst = datacenter.destination

        # Build ISP subgraph
        isp_subgraph = topology_graph.subgraph(isp.nodes).copy()
        for edge in isp.edges:
            if (
                edge[0] in isp.nodes
                and edge[1] in isp.nodes
                and not isp_subgraph.has_edge(edge[0], edge[1])
                and topology_graph.has_edge(edge[0], edge[1])
            ):
                edge_data = topology_graph[edge[0]][edge[1]].copy()
                isp_subgraph.add_edge(edge[0], edge[1], **edge_data)

        # Calculate k-shortest paths dynamically
        try:
            paths = list(
                islice(
                    nx.shortest_simple_paths(isp_subgraph, src, dst, weight="weight"),
                    max_paths_per_isp,
                )
            )

            for path in paths:
                migration_paths.append(
                    {
                        "isp_id": isp.isp_id,
                        "source": src,
                        "destination": dst,
                        "path": path,
                    }
                )

                # Count link usage
                for i in range(len(path) - 1):
                    link = tuple(sorted([path[i], path[i + 1]]))
                    link_usage_count[link] += 1

                    # Track directed edge for arrow drawing
                    directed_edge = (path[i], path[i + 1])
                    directed_link_usage[directed_edge] += 1

        except nx.NetworkXNoPath:
            print(f"Warning: No path found for ISP {isp.isp_id} from {src} to {dst}")

        datacenters_info.append(
            {"isp_id": isp.isp_id, "source": src, "destination": dst}
        )

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # ========== LEFT PLOT: Topology with migration paths ==========
    ax1.set_title(
        "Network Topology - Datacenter Migration Paths", fontsize=16, fontweight="bold"
    )

    # Layout
    pos = nx.spring_layout(topology_graph, seed=7)

    # LAYER 1: Background nodes
    nx.draw_networkx_nodes(
        topology_graph,
        pos,
        node_color="lightgray",
        node_size=500,
        edgecolors="black",
        linewidths=1,
        alpha=0.5,
        ax=ax1,
    )

    # LAYER 2: Background edges (light gray)
    nx.draw_networkx_edges(
        topology_graph, pos, edge_color="lightgray", width=1, alpha=0.3, ax=ax1
    )

    # LAYER 3: Migration path edges with directional arrows
    if directed_link_usage:
        max_usage = max(directed_link_usage.values())

        for directed_edge, count in directed_link_usage.items():
            u, v = directed_edge
            if topology_graph.has_edge(u, v) or topology_graph.has_edge(v, u):
                width = 2 + (count / max_usage) * 8
                alpha = 0.5 + (count / max_usage) * 0.4

                nx.draw_networkx_edges(
                    topology_graph,
                    pos,
                    edgelist=[(u, v)],
                    edge_color="steelblue",
                    width=width,
                    alpha=alpha,
                    arrows=True,
                    arrowsize=15 + (count / max_usage) * 10,
                    arrowstyle="->",
                    connectionstyle="arc3,rad=0.1",
                    ax=ax1,
                )

    # LAYER 4: Source nodes (datacenter sources)
    source_nodes = [dc["source"] for dc in datacenters_info]
    if source_nodes:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=source_nodes,
            node_color="orange",
            node_size=800,
            edgecolors="darkorange",
            linewidths=3,
            ax=ax1,
            label="Datacenter Source",
        )

    # LAYER 5: Destination nodes (datacenter destinations)
    dest_nodes = [dc["destination"] for dc in datacenters_info]
    if dest_nodes:
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=dest_nodes,
            node_color="limegreen",
            node_size=800,
            edgecolors="darkgreen",
            linewidths=3,
            ax=ax1,
            label="Datacenter Destination",
        )

    # LAYER 6: Disaster node (red X)
    if disaster_node in topology_graph.nodes():
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=[disaster_node],
            node_color="red",
            node_size=1000,
            node_shape="X",
            edgecolors="darkred",
            linewidths=3,
            ax=ax1,
            label="Disaster Node",
        )

    # Node labels
    nx.draw_networkx_labels(
        topology_graph, pos, font_size=9, font_weight="bold", ax=ax1
    )

    ax1.axis("off")
    ax1.legend(loc="upper right", fontsize=11, framealpha=0.9)

    # ========== RIGHT PLOT: Migration statistics ==========
    ax2.set_title("Migration Statistics", fontsize=16, fontweight="bold")
    ax2.axis("off")

    # Summary
    y_pos = 0.95
    ax2.text(
        0.5,
        y_pos,
        "Datacenter Migrations Summary",
        ha="center",
        va="top",
        fontsize=14,
        fontweight="bold",
        transform=ax2.transAxes,
        bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
    )

    y_pos -= 0.1
    ax2.text(
        0.5,
        y_pos,
        f"Total ISPs with datacenters: {len(datacenters_info)}",
        ha="center",
        va="top",
        fontsize=12,
        transform=ax2.transAxes,
    )

    y_pos -= 0.05
    ax2.text(
        0.5,
        y_pos,
        f"Total migration paths: {len(migration_paths)}",
        ha="center",
        va="top",
        fontsize=12,
        transform=ax2.transAxes,
    )

    y_pos -= 0.05
    ax2.text(
        0.5,
        y_pos,
        f"Unique links used: {len(link_usage_count)}",
        ha="center",
        va="top",
        fontsize=12,
        transform=ax2.transAxes,
    )

    # Most used links
    if link_usage_count:
        y_pos -= 0.1
        ax2.text(
            0.1,
            y_pos,
            "Most Used Links:",
            fontsize=12,
            fontweight="bold",
            transform=ax2.transAxes,
        )

        # Top 10 links
        sorted_links = sorted(
            link_usage_count.items(), key=lambda x: x[1], reverse=True
        )[:10]
        y_pos -= 0.06
        for link, count in sorted_links:
            ax2.text(
                0.15,
                y_pos,
                f"{link[0]} ↔ {link[1]}: {count} paths",
                fontsize=10,
                family="monospace",
                transform=ax2.transAxes,
            )
            y_pos -= 0.045

    # ISP-specific migrations
    if datacenters_info:
        y_pos -= 0.05
        ax2.text(
            0.1,
            y_pos,
            "Migrations by ISP:",
            fontsize=12,
            fontweight="bold",
            transform=ax2.transAxes,
        )

        y_pos -= 0.06
        for dc in datacenters_info:
            isp_paths = [p for p in migration_paths if p["isp_id"] == dc["isp_id"]]
            ax2.text(
                0.15,
                y_pos,
                f"ISP {dc['isp_id']}: {dc['source']} → {dc['destination']} ({len(isp_paths)} paths)",
                fontsize=10,
                family="monospace",
                transform=ax2.transAxes,
            )
            y_pos -= 0.045

    plt.tight_layout()
    plt.show()

    return migration_paths, link_usage_count, directed_link_usage


def visualize_isp_usage_analysis(
    topology_graph: nx.Graph,
    lista_de_isps: list,
    selected_link: tuple[int, int] | None = None,
    figsize: tuple[int, int] = (20, 10),
) -> None:
    """Visualize ISP usage across the network.

    Left plot: Full topology with edges colored by number of ISPs using them
    Right plot: Details about selected link showing which ISPs use it

    Args:
        topology_graph: NetworkX graph
        lista_de_isps: List of ISP objects
        selected_link: Tuple (u, v) representing selected link
        figsize: Figure size tuple
    """
    from collections import defaultdict

    # Calculate ISP usage per link
    link_isp_count = defaultdict(set)

    for isp in lista_de_isps:
        for edge in isp.edges:
            # Normalize edge direction
            normalized_edge = tuple(sorted(edge))
            link_isp_count[normalized_edge].add(isp.isp_id)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # ========== LEFT PLOT: Topology with ISP usage coloring ==========
    ax1.set_title(
        "Network Topology - Link Sharing Across ISPs", fontsize=16, fontweight="bold"
    )

    # Layout
    pos = nx.spring_layout(topology_graph, seed=7)

    # Draw all nodes
    nx.draw_networkx_nodes(
        topology_graph,
        pos,
        node_color="lightgray",
        node_size=600,
        edgecolors="black",
        linewidths=1.5,
        ax=ax1,
    )

    # Draw edges colored by ISP count
    edge_colors = []
    edge_widths = []
    edges_to_draw = []

    for u, v in topology_graph.edges():
        normalized_edge = tuple(sorted([u, v]))
        isp_count = len(link_isp_count.get(normalized_edge, set()))

        edges_to_draw.append((u, v))
        edge_colors.append(isp_count)
        edge_widths.append(2 + isp_count * 2)  # Thicker = more ISPs

    # Color map
    max_isps = max(edge_colors) if edge_colors else 1
    cmap = plt.colormaps["YlOrRd"]

    nx.draw_networkx_edges(
        topology_graph,
        pos,
        edgelist=edges_to_draw,
        edge_color=edge_colors,
        edge_cmap=cmap,
        edge_vmin=0,
        edge_vmax=max_isps,
        width=edge_widths,
        alpha=0.8,
        ax=ax1,
    )

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max_isps))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax1, shrink=0.8)
    cbar.set_label("Number of ISPs Using Link", fontsize=12)

    # Node labels
    nx.draw_networkx_labels(
        topology_graph, pos, font_size=9, font_weight="bold", ax=ax1
    )

    ax1.axis("off")

    # ========== RIGHT PLOT: Selected link details ==========
    ax2.set_title("Link Usage Details", fontsize=16, fontweight="bold")
    ax2.axis("off")

    if selected_link:
        normalized_link = tuple(sorted(selected_link))
        isps_using_link = link_isp_count.get(normalized_link, set())

        # Summary
        ax2.text(
            0.5,
            0.95,
            f"Link {selected_link[0]} ↔ {selected_link[1]}",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
            transform=ax2.transAxes,
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
        )

        ax2.text(
            0.5,
            0.85,
            f"Used by {len(isps_using_link)} ISP(s)",
            ha="center",
            va="top",
            fontsize=12,
            transform=ax2.transAxes,
        )

        # List ISPs using this link
        if isps_using_link:
            ax2.text(
                0.1,
                0.75,
                "ISPs using this link:",
                fontsize=12,
                fontweight="bold",
                transform=ax2.transAxes,
            )

            y_pos = 0.7
            for isp_id in sorted(isps_using_link):
                ax2.text(
                    0.15,
                    y_pos,
                    f"ISP {isp_id}",
                    fontsize=10,
                    family="monospace",
                    transform=ax2.transAxes,
                )
                y_pos -= 0.05
        else:
            ax2.text(
                0.5,
                0.6,
                "No ISPs use this link",
                ha="center",
                va="top",
                fontsize=12,
                transform=ax2.transAxes,
            )
    else:
        ax2.text(
            0.5,
            0.5,
            "Select a link from the dropdown\nto see usage details",
            ha="center",
            va="center",
            fontsize=12,
            transform=ax2.transAxes,
        )

    plt.tight_layout()
    plt.show()


def visualize_link_criticality_analysis(
    topology_graph: nx.Graph,
    lista_de_isps: list,
    disaster_node: int,
    weights_by_link_by_isp: dict,
    selected_link: tuple[int, int] | None = None,
    show_bridges_only: bool = False,
    min_criticality: float = 0.0,
    disaster_mode: bool = False,
    figsize: tuple[int, int] = (20, 10),
) -> dict:
    """Visualize link criticality analysis with bridge detection.

    Args:
        topology_graph: NetworkX graph
        lista_de_isps: List of ISP objects
        disaster_node: Node affected by disaster
        weights_by_link_by_isp: Dictionary of weight components by link and ISP
        selected_link: Tuple (u, v) for selected link to analyze
        show_bridges_only: If True, only show bridge edges
        min_criticality: Minimum gamma weight threshold to display
        disaster_mode: If True, analyze with disaster node removed
        figsize: Figure size tuple

    Returns:
        Dictionary with bridge analysis results
    """
    from collections import defaultdict

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # Use consistent layout
    pos = nx.spring_layout(topology_graph, seed=7, k=0.3)

    # ========== Calculate link criticality scores ==========
    link_criticality = defaultdict(float)
    link_isp_usage = defaultdict(set)

    # weights_by_link_by_isp is actually current_weights dict
    if "link_criticality" in weights_by_link_by_isp:
        for link, crit_weight in weights_by_link_by_isp["link_criticality"].items():
            normalized_link = tuple(sorted(link))
            link_criticality[normalized_link] = crit_weight

    # Calculate ISP usage for each link
    for isp in lista_de_isps:
        for edge in isp.edges:
            normalized_edge = tuple(sorted(edge))
            link_isp_usage[normalized_edge].add(isp.isp_id)

    # ========== LEFT PLOT: Topology with criticality coloring ==========
    mode_text = "Disaster Mode" if disaster_mode else "Normal Mode"
    ax1.set_title(
        f"Network Topology - Link Criticality Heatmap [{mode_text}]",
        fontsize=16,
        fontweight="bold",
    )

    # Draw base topology (nodes)
    nx.draw_networkx_nodes(
        topology_graph, pos, node_color="lightblue", node_size=300, ax=ax1
    )

    # Draw disaster node with X marker if disaster mode is active
    if disaster_mode and disaster_node in topology_graph.nodes():
        nx.draw_networkx_nodes(
            topology_graph,
            pos,
            nodelist=[disaster_node],
            node_color="red",
            node_size=1000,
            node_shape="X",
            edgecolors="darkred",
            linewidths=3,
            ax=ax1,
            label="Disaster Node",
        )

    # Draw edges with criticality coloring
    edges_to_draw = []
    edge_colors = []
    edge_widths = []

    for u, v in topology_graph.edges():
        normalized_edge = tuple(sorted([u, v]))
        criticality = link_criticality.get(normalized_edge, 0.0)

        # Filter by minimum criticality
        if criticality < min_criticality:
            continue

        # Filter bridges only if requested
        if show_bridges_only and criticality == 0.0:
            continue

        edges_to_draw.append((u, v))
        edge_colors.append(criticality)
        edge_widths.append(2 + criticality * 5)  # Thicker for higher criticality

    if edges_to_draw:
        # Color mapping
        max_crit = max(edge_colors) if edge_colors else 1.0
        cmap = plt.cm.RdYlGn_r

        nx.draw_networkx_edges(
            topology_graph,
            pos,
            edgelist=edges_to_draw,
            edge_color=edge_colors,
            edge_cmap=cmap,
            edge_vmin=0,
            edge_vmax=max_crit,
            width=edge_widths,
            alpha=0.8,
            ax=ax1,
        )

        # Colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=max_crit))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax1, shrink=0.8)
        cbar.set_label("Link Criticality (γ)", fontsize=12)

    # Node labels
    nx.draw_networkx_labels(
        topology_graph, pos, font_size=8, font_weight="bold", ax=ax1
    )

    ax1.axis("off")
    if disaster_mode and disaster_node in topology_graph.nodes():
        ax1.legend(loc="upper right")

    # ========== RIGHT PLOT: Bridge analysis or link details ==========
    if selected_link:
        # Show details for selected link
        ax2.set_title(
            f"Link Analysis: {selected_link[0]} ↔ {selected_link[1]}",
            fontsize=16,
            fontweight="bold",
        )
        ax2.axis("off")

        normalized_link = tuple(sorted(selected_link))
        criticality = link_criticality.get(normalized_link, 0.0)
        isps_using = link_isp_usage.get(normalized_link, set())

        # Summary
        ax2.text(
            0.5,
            0.95,
            f"Link {selected_link[0]} ↔ {selected_link[1]}",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
            transform=ax2.transAxes,
            bbox=dict(boxstyle="round", facecolor="lightcoral", alpha=0.8),
        )

        ax2.text(
            0.5,
            0.85,
            f"Criticality: {criticality:.3f}",
            ha="center",
            va="top",
            fontsize=12,
            transform=ax2.transAxes,
        )

        ax2.text(
            0.5,
            0.8,
            f"Used by {len(isps_using)} ISP(s)",
            ha="center",
            va="top",
            fontsize=12,
            transform=ax2.transAxes,
        )

        # List ISPs
        if isps_using:
            ax2.text(
                0.1,
                0.7,
                "ISPs using this link:",
                fontsize=12,
                fontweight="bold",
                transform=ax2.transAxes,
            )

            y_pos = 0.65
            for isp_id in sorted(isps_using):
                ax2.text(
                    0.15,
                    y_pos,
                    f"ISP {isp_id}",
                    fontsize=10,
                    family="monospace",
                    transform=ax2.transAxes,
                )
                y_pos -= 0.05
    else:
        # Show bridge ranking
        ax2.set_title("Bridge Links Ranked by Impact", fontsize=16, fontweight="bold")
        ax2.axis("off")

        # Get bridges sorted by ISP count
        bridges_with_isp_count = []
        for link, criticality in link_criticality.items():
            if criticality > 0:  # Only bridges
                isp_count = len(link_isp_usage.get(link, set()))
                bridges_with_isp_count.append((link, criticality, isp_count))

        # Sort by ISP count (descending)
        bridges_with_isp_count.sort(key=lambda x: x[2], reverse=True)

        if bridges_with_isp_count:
            ax2.text(
                0.5,
                0.95,
                f"Found {len(bridges_with_isp_count)} Bridge Links",
                ha="center",
                va="top",
                fontsize=14,
                fontweight="bold",
                transform=ax2.transAxes,
                bbox=dict(boxstyle="round", facecolor="lightcoral", alpha=0.8),
            )

            y_pos = 0.85
            for i, (link, criticality, isp_count) in enumerate(
                bridges_with_isp_count[:15]
            ):  # Top 15
                ax2.text(
                    0.1,
                    y_pos,
                    f"{i + 1}. {link[0]} ↔ {link[1]}",
                    fontsize=10,
                    family="monospace",
                    transform=ax2.transAxes,
                )
                ax2.text(
                    0.6,
                    y_pos,
                    f"γ={criticality:.3f}",
                    fontsize=10,
                    family="monospace",
                    transform=ax2.transAxes,
                )
                ax2.text(
                    0.8,
                    y_pos,
                    f"{isp_count} ISPs",
                    fontsize=10,
                    family="monospace",
                    transform=ax2.transAxes,
                )
                y_pos -= 0.05
        else:
            ax2.text(
                0.5,
                0.5,
                "No bridge links found",
                ha="center",
                va="center",
                fontsize=12,
                transform=ax2.transAxes,
            )

    plt.tight_layout()
    plt.show()

    return {
        "link_criticality": dict(link_criticality),
        "link_isp_usage": dict(link_isp_usage),
        "bridges": bridges_with_isp_count if not selected_link else [],
    }
