# Draws the 24-node topology with the disaster node and the links that fail with
# it (overleaf/figures/topology.pdf), with the spring layout of modeloProblema.ipynb.
# Usage: .venv/bin/python make_topology_figure.py overleaf/figures [preview.png]
import sys

import matplotlib
import networkx as nx

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

OUT = sys.argv[1]
NO_D = 9  # disaster node of every base scenario
G = nx.read_weighted_edgelist("topology/usa", nodetype=int)
# Same layout as modeloProblema.ipynb
POS = nx.spring_layout(G, seed=7)
# Small nudges so the short links around nodes 3-5 and 15-20 keep their labels legible
POS[5] = POS[5] + [-0.08, 0.06]
POS[3] = POS[3] + [-0.08, -0.04]
# Node 4 sits right of link 5-3, so link 4-7 does not cross it
POS[4] = (POS[5] + POS[3]) / 2 + [0.10, 0.07]
POS[20] = POS[20] + [0.06, -0.04]
links_d = [e for e in G.edges if NO_D in e]
outros = [e for e in G.edges if NO_D not in e]

plt.rcParams.update({"font.family": "serif", "font.serif": ["cmr10"], "pdf.fonttype": 42,
                     "mathtext.fontset": "cm"})
RED, BLUE, TXT = "#d03b3b", "#6f95e0", "#0b0b0b"
fig, ax = plt.subplots(figsize=(6.0, 4.4))
nx.draw_networkx_edges(G, POS, edgelist=outros, edge_color="#3d3c39", width=1.2, ax=ax)
nx.draw_networkx_edges(G, POS, edgelist=links_d, edge_color=RED, width=2.0, ax=ax)
nx.draw_networkx_edge_labels(
    G, POS, edge_labels={(u, v): f"{d['weight']:g}" for u, v, d in G.edges(data=True)},
    font_size=7.5, font_family="serif", font_color=TXT, rotate=False, ax=ax,
    bbox={"boxstyle": "round,pad=0.1", "fc": "white", "ec": "none"})
nx.draw_networkx_nodes(G, POS, nodelist=[n for n in G if n != NO_D], node_size=170,
                       node_color=BLUE, ax=ax)
nx.draw_networkx_nodes(G, POS, nodelist=[NO_D], node_size=230, node_color=RED, ax=ax)
nx.draw_networkx_labels(G, POS, font_size=7.5, font_family="serif", font_color=TXT, ax=ax)
nx.draw_networkx_labels(G, POS, labels={NO_D: str(NO_D)}, font_size=7.5, font_family="serif",
                        font_color="white", font_weight="bold", ax=ax)
ax.legend(handles=[
    Line2D([], [], marker="o", ls="", ms=8, color=RED, label=f"disaster node {NO_D}"),
    Line2D([], [], color=RED, lw=2.6, label="links that fail with it"),
], loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=2, frameon=False, fontsize=8)
ax.set_axis_off()
fig.tight_layout()
fig.savefig(f"{OUT}/topology.pdf", bbox_inches="tight")
if len(sys.argv) > 2:
    fig.savefig(sys.argv[2], dpi=200, bbox_inches="tight")
