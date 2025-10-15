"""Logging utilities for EON network simulation.

Provides centralized logging functionality for simulation events including:
- Migration status tracking
- Request processing progress
- Disaster event notifications
- Link and node failure logging
"""

from __future__ import annotations


class Logger:
    """Singleton logger for simulation event tracking.

    Manages logging output for various simulation events with configurable
    activation status. Uses singleton pattern to ensure consistent logging
    across the entire simulation.

    Attributes:
        instance: Singleton instance of Logger
        ativo: Whether logging is currently active
        isps_sendo_acompanhada: Tracking dict for ISP migration progress

    """

    instance: Logger | None = None

    def __init__(self, ativo: bool) -> None:
        """Initialize the logger with activation status.

        Args:
            ativo: Whether logging should be active

        """
        self.ativo = ativo
        self.isps_sendo_acompanhada: dict[int, list] = {}
        Logger.instance = self

    @staticmethod
    def __get_instance() -> Logger | None:
        """Get the singleton logger instance.

        Returns:
            Logger: The singleton logger instance

        """
        return Logger.instance

    @staticmethod
    def mensagem_finaliza_migracao(isp_id: int, time: int, percentual: float) -> None:
        """Log ISP migration completion message.

        Args:
            isp_id: ISP identifier
            time: Simulation time when migration finished
            percentual: Percentage of migration completed

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            print(
                f"ISP {isp_id} finalizou migração no tempo {time}, {percentual * 100}% da migração concluída"
            )

    @staticmethod
    def mensagem_acompanha_requisicoes(
        reqid: int, time: int, numero_requisicoes: int
    ) -> None:
        """Log request processing progress at intervals.

        Args:
            reqid: Current request ID being processed
            time: Current simulation time
            numero_requisicoes: Interval for logging frequency

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo and reqid % numero_requisicoes == 0:
            print(f"{reqid} requests processed, time : {time}")

    @staticmethod
    def mensagem_inicia_migracao(
        isp_id: int, source: int, destination: int, time: int
    ) -> None:
        """Log ISP migration initiation message.

        Args:
            isp_id: ISP identifier
            source: Source node for migration
            destination: Destination node for migration
            time: Simulation time when migration started

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            print(
                f"ISP {isp_id} iniciando migração de {source} para {destination} no tempo {time}"
            )

    @staticmethod
    def mensagem_acompanha_status_migracao(
        isp_id: int, percentual: int, time: int
    ) -> None:
        """Log ISP migration progress status.

        Args:
            isp_id: ISP identifier
            percentual: Current migration percentage completed
            time: Current simulation time

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            if isp_id not in instance.isps_sendo_acompanhada:
                # Thresholds in percentage (0-100) to match the passed percentual value
                instance.isps_sendo_acompanhada[isp_id] = [
                    10,
                    20,
                    30,
                    40,
                    50,
                    60,
                    70,
                    80,
                    90,
                    100,
                ]
            # Check if list is not empty before accessing
            if (
                instance.isps_sendo_acompanhada[isp_id]
                and percentual >= instance.isps_sendo_acompanhada[isp_id][0]
            ):
                print(
                    f"Status ISP {isp_id}, {percentual}% da migração concluída no tempo {time}"
                )
                instance.isps_sendo_acompanhada[isp_id].pop(0)

    @staticmethod
    def mensagem_acompanha_link_desastre(src: int, dst: int, time: int) -> None:
        """Log link failure during disaster.

        Args:
            src: Source node of failed link
            dst: Destination node of failed link
            time: Simulation time when link failed

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            print(f"Link {src} -> {dst} falhou no tempo {time}")

    @staticmethod
    def mensagem_acompanha_node_desastre(node: int, time: int) -> None:
        """Log node failure during disaster.

        Args:
            node: Node identifier that failed
            time: Simulation time when node failed

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            print(f"Node {node} falhou no tempo {time}")

    @staticmethod
    def mensagem_desastre_finalizado(time: int) -> None:
        """Log disaster completion message.

        Args:
            time: Simulation time when disaster ended

        """
        instance = Logger.__get_instance()

        if instance and instance.ativo:
            print(f"Disaster finalizado no tempo {time}")
