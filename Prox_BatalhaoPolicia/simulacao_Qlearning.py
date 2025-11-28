#!/usr/bin/env python3
import traci
import pickle
import os
import sys
from collections import defaultdict
import numpy as np
import pandas as pd

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

# --- Configurações ---
SUMO_CFG_FILE = "Prox_BatalhaoPolicia.sumocfg"
TRAFFIC_LIGHT_ID = "2078102664"
Q_TABLE_FILE = "q_table_prox_batalhao.pkl"
OUTPUT_FOLDER = "resultados_qlearning"

GREEN_DURATION = 15
YELLOW_DURATION = 4

ACTION_TO_PHASE = {0: 0, 1: 2}
NUM_ACTIONS = len(ACTION_TO_PHASE)

# --- Funções Auxiliares ---
def get_controlled_lanes_by_phase(tl_id):
    logic = traci.trafficlight.getAllProgramLogics(tl_id)[0]
    lanes = traci.trafficlight.getControlledLanes(tl_id)
    phase_lanes = defaultdict(list)
    for i, phase in enumerate(logic.phases):
        if 'G' in phase.state or 'g' in phase.state:
            for j, state_char in enumerate(phase.state):
                if state_char in ('G', 'g'):
                    lane = lanes[j]
                    if lane not in phase_lanes[i]: phase_lanes[i].append(lane)
    return {action: phase_lanes.get(phase_idx, []) for action, phase_idx in ACTION_TO_PHASE.items()}

def get_state(phase_controlled_lanes):
    state = []
    for action in sorted(phase_controlled_lanes.keys()):
        lanes = phase_controlled_lanes[action]
        stopped_vehicles = sum(traci.lane.getLastStepHaltingNumber(lane) for lane in lanes)
        state.append(min(stopped_vehicles // 3, 5))
    return tuple(state)

def get_priority_action(phase_controlled_lanes):
    priority_per_action = defaultdict(int)
    for action, lanes in phase_controlled_lanes.items():
        for lane in lanes:
            if traci.lane.getLastStepHaltingNumber(lane) > 0:
                for vid in traci.lane.getLastStepVehicleIDs(lane):
                    try:
                        v_class = traci.vehicle.getVehicleClass(vid)
                        if v_class == "emergency": priority_per_action[action] = max(priority_per_action[action], 2)
                        elif v_class == "authority": priority_per_action[action] = max(priority_per_action[action], 1)
                    except traci.TraCIException: continue
    if not priority_per_action: return None
    return max(priority_per_action, key=priority_per_action.get)

def collect_metrics(sim_time, lists):
    (carros_parados_por_tempo, total_paradas_por_tempo, tempo_espera_por_tempo, 
     velocidade_media_por_tempo, densidade_por_tempo, tempo_espera_emergency_por_tempo, 
     tempo_espera_authority_por_tempo, carros_parados_prioritarios_por_tempo, 
     total_paradas_prioritarios_por_tempo, tempo_espera_prioritarios_por_tempo, 
     velocidade_media_prioritarios_por_tempo) = lists

    carros_parados_tls = sum(traci.lane.getLastStepHaltingNumber(l) for l in traci.trafficlight.getControlledLanes(TRAFFIC_LIGHT_ID))
    carros_parados_por_tempo.append({'tempo': sim_time, 'carros_parados': carros_parados_tls})
    
    vehicle_ids = traci.vehicle.getIDList()
    total_paradas = sum(1 for vid in vehicle_ids if traci.vehicle.getSpeed(vid) < 0.1)
    total_tempo_espera = sum(traci.vehicle.getWaitingTime(vid) for vid in vehicle_ids)
    velocidades = [traci.vehicle.getSpeed(vid) for vid in vehicle_ids if traci.vehicle.getSpeed(vid) > 0]
    velocidade_media = sum(velocidades) / len(velocidades) if velocidades else 0
    densidades = [(traci.lane.getLastStepVehicleNumber(l) / traci.lane.getLength(l)) * 1000 for l in traci.trafficlight.getControlledLanes(TRAFFIC_LIGHT_ID) if traci.lane.getLength(l) > 0]
    densidade_media = sum(densidades) / len(densidades) if densidades else 0

    emergency_ids = [v for v in vehicle_ids if traci.vehicle.getVehicleClass(v) == "emergency"]
    authority_ids = [v for v in vehicle_ids if traci.vehicle.getVehicleClass(v) == "authority"]
    
    num_emergency = len(emergency_ids); total_espera_emergency = sum(traci.vehicle.getWaitingTime(v) for v in emergency_ids); media_espera_emergency = total_espera_emergency / num_emergency if num_emergency else 0
    num_authority = len(authority_ids); total_espera_authority = sum(traci.vehicle.getWaitingTime(v) for v in authority_ids); media_espera_authority = total_espera_authority / num_authority if num_authority else 0
    
    priority_ids = emergency_ids + authority_ids
    if priority_ids:
        carros_parados_prioritarios = sum(1 for v in priority_ids if traci.vehicle.getSpeed(v)<0.1)
        total_paradas_prioritarios = carros_parados_prioritarios
        tempo_espera_prioritarios = sum(traci.vehicle.getWaitingTime(v) for v in priority_ids) / len(priority_ids)
        velocidades_prioritarios = [traci.vehicle.getSpeed(v) for v in priority_ids if traci.vehicle.getSpeed(v) > 0]
        velocidade_media_prioritarios = sum(velocidades_prioritarios) / len(velocidades_prioritarios) if velocidades_prioritarios else 0
    else:
        carros_parados_prioritarios, total_paradas_prioritarios, tempo_espera_prioritarios, velocidade_media_prioritarios = 0,0,0,0
    
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

def run_simulation(max_steps=5400):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"📁 Pasta '{OUTPUT_FOLDER}' pronta.")
    print("Iniciando simulação com controle Q-learning (modo avaliação).")
    
    try:
        with open(Q_TABLE_FILE, "rb") as f: q_table = pickle.load(f)
        print("✅ Q-table carregada com sucesso.")
    except FileNotFoundError:
        print(f"⚠️ Arquivo '{Q_TABLE_FILE}' não encontrado. Usando estratégia aleatória.")
        q_table = defaultdict(lambda: np.zeros(NUM_ACTIONS))

    traci.start(["sumo-gui", "-c", SUMO_CFG_FILE, "--step-length", "1.0"])
    total_sim_steps = 0
    phase_lanes = get_controlled_lanes_by_phase(TRAFFIC_LIGHT_ID)
    lists = [[] for _ in range(11)]
    current_action = 0
    current_phase = ACTION_TO_PHASE[current_action]
    traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
    phase_timer = 0

    while traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps:
        priority_action = get_priority_action(phase_lanes)
        action_chosen_this_step = False # Flag para saber se uma ação foi decidida

        if priority_action is not None and priority_action != current_action:
            action_to_take = priority_action
            action_chosen_this_step = True
        elif phase_timer >= GREEN_DURATION:
            state = get_state(phase_lanes)
            previous_action = current_action # GUARDA A AÇÃO ATUAL
            # No modo avaliação, sempre pega a melhor ação (argmax)
            action_to_take = np.argmax(q_table.get(state, np.zeros(NUM_ACTIONS)))
            action_chosen_this_step = True

            # --- INÍCIO DA ALTERAÇÃO ---
            if action_to_take == previous_action:
                # A ação escolhida é a mesma que a atual, reinicia o timer e pula a transição
                phase_timer = 0
                traci.simulationStep() # Avança a simulação
                total_sim_steps += 1
                collect_metrics(total_sim_steps, lists) # Coleta métricas para este passo
                continue # Pula o resto do loop e vai para a próxima iteração
            # --- FIM DA ALTERAÇÃO ---

        else: # Se não há prioridade e phase_timer < GREEN_DURATION
            traci.simulationStep()
            total_sim_steps += 1
            phase_timer += 1
            collect_metrics(total_sim_steps, lists)
            continue # Pula o resto do loop e vai para a próxima iteração

        # ----- Se chegou aqui, uma AÇÃO DIFERENTE foi escolhida (ou por prioridade ou por Q-learning) -----
        # Executa a transição com amarelo
        yellow_phase = current_phase + 1
        traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, yellow_phase)
        for _ in range(YELLOW_DURATION):
            # Verifica se a simulação deve continuar dentro do loop amarelo
            if not (traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps):
                break
            traci.simulationStep()
            total_sim_steps += 1
            collect_metrics(total_sim_steps, lists)
        # Verifica novamente após o loop amarelo
        if not (traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps):
            break

        current_action = action_to_take # Atualiza para a nova ação
        current_phase = ACTION_TO_PHASE[current_action]
        traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
        phase_timer = 0

        # Dá um passo inicial na nova fase verde e coleta métricas
        if traci.simulation.getMinExpectedNumber() > 0 and total_sim_steps < max_steps:
            traci.simulationStep()
            total_sim_steps += 1
            phase_timer += 1 # Já conta 1 passo na nova fase verde
            collect_metrics(total_sim_steps, lists)
            continue

        yellow_phase = current_phase + 1
        traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, yellow_phase)
        for _ in range(YELLOW_DURATION):
            traci.simulationStep(); total_sim_steps += 1; collect_metrics(total_sim_steps, lists)
        
        current_action = action_to_take
        current_phase = ACTION_TO_PHASE[current_action]
        traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
        phase_timer = 0
        
    traci.close()
    print(f"✅ Simulação finalizada com {total_sim_steps} passos.")

    # Salva os dados
    (carros_parados_por_tempo, total_paradas_por_tempo, tempo_espera_por_tempo, 
     velocidade_media_por_tempo, densidade_por_tempo, tempo_espera_emergency_por_tempo, 
     tempo_espera_authority_por_tempo, carros_parados_prioritarios_por_tempo, 
     total_paradas_prioritarios_por_tempo, tempo_espera_prioritarios_por_tempo, 
     velocidade_media_prioritarios_por_tempo) = lists

    resultados_dfs = {
        "resultado_qlearning.csv": carros_parados_por_tempo, "paradas_qlearning.csv": total_paradas_por_tempo,
        "espera_qlearning.csv": tempo_espera_por_tempo, "velocidade_qlearning.csv": velocidade_media_por_tempo,
        "densidade_qlearning.csv": densidade_por_tempo, "emergency_qlearning.csv": tempo_espera_emergency_por_tempo,
        "authority_qlearning.csv": tempo_espera_authority_por_tempo, "carros_parados_prioritarios_qlearning.csv": carros_parados_prioritarios_por_tempo,
        "paradas_prioritarios_qlearning.csv": total_paradas_prioritarios_por_tempo, "espera_prioritarios_qlearning.csv": tempo_espera_prioritarios_por_tempo,
        "velocidade_prioritarios_qlearning.csv": velocidade_media_prioritarios_por_tempo
    }
    for nome_arquivo, dados in resultados_dfs.items():
        caminho_arquivo = os.path.join(OUTPUT_FOLDER, nome_arquivo)
        pd.DataFrame(dados).to_csv(caminho_arquivo, index=False)

    print(f"📁 Resultados salvos na pasta '{OUTPUT_FOLDER}'.")

if __name__ == "__main__":
    run_simulation()