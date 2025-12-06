"""Coordination modules for multi-ISP cooperation.

This package provides coordination mechanisms for managing cooperative
behavior between ISPs during disaster scenarios. The main component is
the CooperationCoordinator, which tracks ISP cooperation status and
triggers weight recalculation as ISPs join the cooperation network.
"""

from simulador.coordination.cooperation_coordinator import CooperationCoordinator

__all__ = ["CooperationCoordinator"]
