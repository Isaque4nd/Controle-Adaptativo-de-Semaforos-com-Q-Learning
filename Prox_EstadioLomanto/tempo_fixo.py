#!/usr/bin/env python3
import traci
import pandas as pd
import os
import sys

# Caminho para as ferramentas do SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

# --- Configurações ---
SUMO_CFG_FILE = "Prox_EstadioLomanto.sumocfg"
TRAFFIC_LIGHT_ID = ["2713368224"]
OUTPUT_FOLDER = "resultados_tempo_fixo"

# Tempos para o controle de tempo fixo
GREEN_DURATION = 15
YELLOW_DURATION = 4
CYCLE = (GREEN_DURATION + YELLOW_DURATION) * 2

# Sinais
SIGNALS = {
    "green_A": "rrrGGgrrrGGg",
    "yellow_A": "rrryyyrrryyy",
    "green_B": "GGgrrrGGgrrr",
    "yellow_B": "yyyrrryyyrrr",
}

def run_fixed_time_simulation():
    # Cria a pasta de saída se ela não existir
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"📁 Pasta '{OUTPUT_FOLDER}' criada.")

    traci.start(["sumo-gui", "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
    print("🟢 Simulação com tempo fixo iniciada.")
    
    sim_time = 0
    
    # Listas para métricas
    (carros_parados_por_tempo, total_paradas_por_tempo, tempo_espera_por_tempo, 
     velocidade_media_por_tempo, densidade_por_tempo, tempo_espera_emergency_por_tempo, 
     tempo_espera_authority_por_tempo, carros_parados_prioritarios_por_tempo, 
     total_paradas_prioritarios_por_tempo, tempo_espera_prioritarios_por_tempo, 
     velocidade_media_prioritarios_por_tempo) = ([] for _ in range(11))

    while traci.simulation.getMinExpectedNumber() > 0:
        phase_time = sim_time % CYCLE
        for tl_id in TRAFFIC_LIGHT_ID:
            if phase_time < GREEN_DURATION:
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["green_A"])
            elif phase_time < GREEN_DURATION + YELLOW_DURATION:
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["yellow_A"])
            elif phase_time < (GREEN_DURATION * 2) + YELLOW_DURATION:
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["green_B"])
            else:
                traci.trafficlight.setRedYellowGreenState(tl_id, SIGNALS["yellow_B"])

        traci.simulationStep()
        sim_time += 1
        
        # --- Lógica de Coleta de Dados ---
        total_parados = sum(
            traci.lane.getLastStepHaltingNumber(lane)
            for tl in TRAFFIC_LIGHT_ID
            for lane in traci.trafficlight.getControlledLanes(tl)
        )
        carros_parados_por_tempo.append({'tempo': sim_time, 'carros_parados': total_parados})

        vehicle_ids = traci.vehicle.getIDList()
        total_paradas = sum(1 for vid in vehicle_ids if traci.vehicle.getSpeed(vid) < 0.1)
        total_tempo_espera = sum(traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids)
        velocidades = [traci.vehicle.getSpeed(vid) for vid in vehicle_ids if traci.vehicle.getSpeed(vid) > 0]
        velocidade_media = sum(velocidades) / len(velocidades) if velocidades else 0

        densidades = []
        for tl in TRAFFIC_LIGHT_ID:
            for lane in traci.trafficlight.getControlledLanes(tl):
                num_veiculos = traci.lane.getLastStepVehicleNumber(lane)
                comprimento = traci.lane.getLength(lane)
                if comprimento > 0:
                    densidades.append((num_veiculos / comprimento) * 1000)
        densidade_media = sum(densidades) / len(densidades) if densidades else 0

        emergency_ids = [vid for vid in vehicle_ids if traci.vehicle.getVehicleClass(vid) == "emergency"]
        authority_ids = [vid for vid in vehicle_ids if traci.vehicle.getVehicleClass(vid) == "authority"]
        
        num_emergency = len(emergency_ids)
        total_espera_emergency = sum(traci.vehicle.getWaitingTime(vid) for vid in emergency_ids)
        media_espera_emergency = total_espera_emergency / num_emergency if num_emergency else 0
        
        num_authority = len(authority_ids)
        total_espera_authority = sum(traci.vehicle.getWaitingTime(vid) for vid in authority_ids)
        media_espera_authority = total_espera_authority / num_authority if num_authority else 0

        priority_ids = emergency_ids + authority_ids
        if priority_ids:
            carros_parados_prioritarios = sum(1 for vid in priority_ids if traci.vehicle.getSpeed(vid) < 0.1)
            total_paradas_prioritarios = sum(1 for vid in priority_ids if traci.vehicle.getSpeed(vid) < 0.1)
            tempo_espera_prioritarios = sum(traci.vehicle.getWaitingTime(vid) for vid in priority_ids) / len(priority_ids)
            velocidades_prioritarios = [traci.vehicle.getSpeed(vid) for vid in priority_ids if traci.vehicle.getSpeed(vid) > 0]
            velocidade_media_prioritarios = sum(velocidades_prioritarios) / len(velocidades_prioritarios) if velocidades_prioritarios else 0
        else:
            carros_parados_prioritarios, total_paradas_prioritarios, tempo_espera_prioritarios, velocidade_media_prioritarios = 0, 0, 0, 0

        # Armazenar resultados
        total_paradas_por_tempo.append({'tempo': sim_time, 'total_paradas': total_paradas})
        tempo_espera_por_tempo.append({'tempo': sim_time, 'tempo_espera': total_tempo_espera})
        velocidade_media_por_tempo.append({'tempo': sim_time, 'velocidade_media': velocidade_media})
        densidade_por_tempo.append({'tempo': sim_time, 'densidade_media': densidade_media})
        tempo_espera_emergency_por_tempo.append({'tempo': sim_time, 'num_emergency': num_emergency, 'total_espera_emergency': total_espera_emergency, 'media_espera_emergency': media_espera_emergency})
        tempo_espera_authority_por_tempo.append({'tempo': sim_time, 'num_authority': num_authority, 'total_espera_authority': total_espera_authority, 'media_espera_authority': media_espera_authority})
        carros_parados_prioritarios_por_tempo.append({'tempo': sim_time, 'carros_parados_prioritarios': carros_parados_prioritarios})
        total_paradas_prioritarios_por_tempo.append({'tempo': sim_time, 'total_paradas_prioritarios': total_paradas_prioritarios})
        tempo_espera_prioritarios_por_tempo.append({'tempo': sim_time, 'tempo_espera_prioritarios': tempo_espera_prioritarios})
        velocidade_media_prioritarios_por_tempo.append({'tempo': sim_time, 'velocidade_media_prioritarios': velocidade_media_prioritarios})

    traci.close()
    print("✅ Simulação finalizada (tempo fixo).")

    # Mapeamento de nomes de arquivos para DataFrames
    resultados = {
        "parados_tempo_fixo.csv": carros_parados_por_tempo,
        "total_paradas_tempo_fixo.csv": total_paradas_por_tempo,
        "espera_tempo_fixo.csv": tempo_espera_por_tempo,
        "velocidade_tempo_fixo.csv": velocidade_media_por_tempo,
        "densidade_tempo_fixo.csv": densidade_por_tempo,
        "emergency_tempo_fixo.csv": tempo_espera_emergency_por_tempo,
        "authority_tempo_fixo.csv": tempo_espera_authority_por_tempo,
        "carros_parados_prioritarios_tempo_fixo.csv": carros_parados_prioritarios_por_tempo,
        "paradas_prioritarios_tempo_fixo.csv": total_paradas_prioritarios_por_tempo,
        "espera_prioritarios_tempo_fixo.csv": tempo_espera_prioritarios_por_tempo,
        "velocidade_prioritarios_tempo_fixo.csv": velocidade_media_prioritarios_por_tempo
    }
    
    for nome_arquivo, dados in resultados.items():
        caminho_arquivo = os.path.join(OUTPUT_FOLDER, nome_arquivo)
        pd.DataFrame(dados).to_csv(caminho_arquivo, index=False)

    print(f"📁 Resultados salvos na pasta '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    run_fixed_time_simulation()