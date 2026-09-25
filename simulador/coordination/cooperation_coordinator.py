"""Cooperation coordinator for managing ISP information sharing during disasters.

This module implements a coordinator that tracks which ISPs are cooperating
and triggers real-time weight recalculation as ISPs join the cooperation network.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import networkx as nx

    from simulador.config.simulation_settings import ScenarioConfig
    from simulador.entities.isp import ISP


class CooperationCoordinator:
    """Manages ISP cooperation and weight recalculation during disaster.

    This coordinator tracks which ISPs have started cooperating (reached their
    reaction time) and triggers weight recalculation for all cooperating ISPs
    whenever a new ISP joins the cooperation network.

    Attributes:
        lista_de_isps: List of all ISPs in the network
        topology: Network topology graph
        disaster_node: Node affected by disaster
        config: Scenario configuration with weight parameters
        cooperating_isps: Set of ISP IDs currently cooperating
        allowed_isps: ISP IDs allowed to cooperate (K). None means every ISP.
    """

    def __init__(
        self,
        lista_de_isps: list[ISP],
        topology: nx.Graph,
        disaster_node: int,
        config: ScenarioConfig,
        allowed_isps: set[int] | None = None,
    ) -> None:
        """Initialize the cooperation coordinator.

        Args:
            lista_de_isps: List of all ISPs in the network
            topology: Network topology graph
            disaster_node: Node that will fail during disaster
            config: Scenario configuration with weight parameters (α, β, γ)
            allowed_isps: ISP IDs in the cooperating set K. ISPs outside it still
                react (switch to disaster routing) but keep their isolated
                weights. None means every ISP may cooperate.
        """
        self.lista_de_isps = lista_de_isps
        self.topology = topology
        self.disaster_node = disaster_node
        self.config = config
        self.cooperating_isps: set[int] = set()  # ISP IDs that are cooperating
        self.allowed_isps: set[int] | None = (
            None if allowed_isps is None else set(allowed_isps)
        )

    def can_cooperate(self, isp_id: int) -> bool:
        """Return True if the ISP belongs to the cooperating set K."""
        return self.allowed_isps is None or isp_id in self.allowed_isps

    def register_cooperation(self, isp_id: int, current_time: float) -> bool:
        """Register an ISP as cooperating and trigger weight updates.

        Called when an ISP reaches its reaction time. If the ISP is in the
        cooperating set K, this triggers recalculation of weights for all
        currently cooperating ISPs to incorporate the new information. ISPs
        outside K are left isolated and nothing is recalculated.

        Args:
            isp_id: ID of the ISP that reached its reaction time
            current_time: Current simulation time

        Returns:
            True if the ISP joined the cooperation, False if it stays isolated.
        """
        if not self.can_cooperate(isp_id):
            print(
                f"[Cooperation] ISP {isp_id} reacted at t={current_time:.2f} "
                "but is not in K: stays isolated"
            )
            return False

        self.cooperating_isps.add(isp_id)
        print(f"[Cooperation] ISP {isp_id} started cooperating at t={current_time:.2f}")
        print(f"[Cooperation] Total cooperating ISPs: {len(self.cooperating_isps)}")

        # Recalculate weights for all cooperating ISPs with updated cooperation list
        self._recalculate_weights_for_all_cooperating(current_time)
        return True

    def get_cooperating_isps_for(self, isp_id: int) -> list[ISP]:
        """Get list of ISPs cooperating with the given ISP.

        If the ISP is cooperating, returns all cooperating ISPs (including itself).
        If the ISP is not cooperating, returns only itself (isolated view).

        Args:
            isp_id: ID of the ISP to get cooperation list for

        Returns:
            List of ISP objects that are cooperating with the given ISP
        """
        if isp_id in self.cooperating_isps:
            # ISP is cooperating: can see all other cooperating ISPs
            return [
                isp for isp in self.lista_de_isps if isp.isp_id in self.cooperating_isps
            ]
        # ISP is not cooperating: can only see itself
        return [isp for isp in self.lista_de_isps if isp.isp_id == isp_id]

    def _recalculate_weights_for_all_cooperating(self, current_time: float) -> None:
        """Recalculate weights for all cooperating ISPs with updated cooperation list.

        This method is called whenever a new ISP joins cooperation. It updates
        the weighted paths for all cooperating ISPs to reflect the newly available
        information from the entire cooperation network.

        Args:
            current_time: Current simulation time
        """
        print(
            f"[Cooperation] Recalculating weights for {len(self.cooperating_isps)} ISPs..."
        )

        for isp in self.lista_de_isps:
            if isp.isp_id in self.cooperating_isps:
                # Get the list of ISPs cooperating with this ISP
                cooperating_list = self.get_cooperating_isps_for(isp.isp_id)

                # Update this ISP's weights using the cooperative data
                isp.update_cooperative_weights(
                    cooperating_list, self.topology, self.disaster_node, self.config
                )

        print(f"[Cooperation] Weight recalculation complete at t={current_time:.2f}")
