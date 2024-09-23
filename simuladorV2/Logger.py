


class Logger:

    instance: 'Logger' = None

    def __init__(self, ativo :bool) -> None:
        self.ativo = ativo
        self.isps_sendo_acompanhada: dict[int, list] = {}
        Logger.instance = self

    def get_instance():
        return Logger.instance
    
    def mensagem_finaliza_migracao( isp_id :int, time :int, percentual :float):
        instance = Logger.get_instance()

        if instance.ativo:
            print(f"ISP {isp_id} finalizou migração no tempo {time}, {percentual*100}% da migração concluída")
        
    def mensagem_acompanha_requisicoes( reqid :int, time :int, numero_requisicoes:int):
        instance = Logger.get_instance()

        if instance.ativo and reqid % numero_requisicoes == 0:
            print(f'{reqid} requests processed, time : {time}')

    def mensagem_inicia_migracao( isp_id :int, source :int, destination :int, time :int):
        instance = Logger.get_instance()

        if instance.ativo:
            print(f"ISP {isp_id} iniciando migração de {source} para {destination} no tempo {time}")


    def mensagem_acompanha_status_migracao(isp_id :int, percentual :int, time :int):
        instance = Logger.get_instance()

        if instance.ativo:

            if isp_id not in instance.isps_sendo_acompanhada:
                instance.isps_sendo_acompanhada[isp_id] = [ 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
            print(percentual)
            if percentual >= instance.isps_sendo_acompanhada[isp_id][0]:
                print(f"Status ISP {isp_id}, {percentual*100}% da migração concluída no tempo {time}")
                instance.isps_sendo_acompanhada[isp_id].pop(0)

    def mensagem_acompanha_link_desastre( src :int, dst :int, time :int):
        instance = Logger.get_instance()

        if instance.ativo:
            print(f"Link {src} -> {dst} falhou no tempo {time}")

    def mensagem_acompanha_node_desastre( node :int, time :int):
        instance = Logger.get_instance()

        if instance.ativo:
            print(f"Node {node} falhou no tempo {time}")
    
    def mensagem_desastre_finalizado( time :int):
        instance = Logger.get_instance()

        if instance.ativo:
            print(f"Desastre finalizado no tempo {time}")
           