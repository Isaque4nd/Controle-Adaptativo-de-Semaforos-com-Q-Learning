#!/usr/bin/env python3
import traci
import pickle
import os
import random
import sys
from collections import defaultdict
import numpy as np

# Adiciona o caminho para as ferramentas do SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

# --- Configurações Otimizadas ---
SUMO_CFG_FILE = "Prox_EstadioLomanto.sumocfg"
TRAFFIC_LIGHT_ID = "2713368224"

# Duração das fases com ciclos mais curtos para mais decisões
GREEN_DURATION = 15
YELLOW_DURATION = 4

# --- HIPERPARÂMETROS AJUSTADOS PARA APRENDIZADO RÁPIDO ---
EPOCHS = 500           # etapas para treinamento
MAX_STEPS = 5400
ALPHA = 0.2            # Taxa de aprendizado
GAMMA = 0.95           # Fator de desconto
EPSILON = 1.0          # Exploração inicial
EPSILON_DECAY = 0.999  # Decaimento
MIN_EPSILON = 0.01

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
                    if lane not in phase_lanes[i]:
                        phase_lanes[i].append(lane)
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
                        if v_class == "emergency":
                            priority_per_action[action] = max(priority_per_action[action], 2)
                        elif v_class == "authority":
                            priority_per_action[action] = max(priority_per_action[action], 1)
                    except traci.TraCIException:
                        continue
    if not priority_per_action:
        return None
    return max(priority_per_action, key=priority_per_action.get)

def choose_action(state, q_table, epsilon):
    if random.random() < epsilon:
        return random.randrange(NUM_ACTIONS)
    else:
        return np.argmax(q_table.get(state, np.zeros(NUM_ACTIONS)))

# ---------- TREINAMENTO ----------
def train():
    q_table = defaultdict(lambda: np.zeros(NUM_ACTIONS))
    sumo_cmd = ["sumo", "-c", SUMO_CFG_FILE, "--step-length", "1.0", "--waiting-time-memory", "1000"]
    best_reward_avg = -float('inf')
    patience, patience_limit = 0, 150
    epsilon = EPSILON
    rewards_history = []

    for ep in range(EPOCHS):
        traci.start(sumo_cmd)
        phase_lanes = get_controlled_lanes_by_phase(TRAFFIC_LIGHT_ID)
        total_steps, total_reward = 0, 0
        
        current_action = random.randrange(NUM_ACTIONS)
        current_phase = ACTION_TO_PHASE[current_action]
        traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
        phase_timer = 0

        while traci.simulation.getMinExpectedNumber() > 0 and total_steps < MAX_STEPS:
            # Lógica de Interrupção Prioritária
            priority_action = get_priority_action(phase_lanes)
            if priority_action is not None and priority_action != current_action:
                yellow_phase = current_phase + 1
                traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, yellow_phase)
                for _ in range(YELLOW_DURATION): traci.simulationStep(); total_steps += 1
                current_action = priority_action
                current_phase = ACTION_TO_PHASE[current_action]
                traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
                phase_timer = 0

            if phase_timer >= GREEN_DURATION:
                state = get_state(phase_lanes)
                previous_action = current_action # GUARDA A AÇÃO ATUAL
                action = choose_action(state, q_table, epsilon)

                # --- Recompensa Direta e Simplificada ---
                total_stopped = sum(traci.lane.getLastStepHaltingNumber(l) for l in traci.trafficlight.getControlledLanes(TRAFFIC_LIGHT_ID))
                reward = -total_stopped
                total_reward += reward

                if action == previous_action:
                    # A ação escolhida é a mesma que a atual, apenas reinicia o timer verde
                    phase_timer = 0
                    # Não há transição de fase, então precisamos avançar a simulação manualmente aqui
                    traci.simulationStep()
                    total_steps += 1
                else:
                    # A ação mudou, executa a transição com amarelo
                    yellow_phase = current_phase + 1
                    traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, yellow_phase)
                    for _ in range(YELLOW_DURATION):
                        traci.simulationStep()
                        total_steps += 1

                    current_action = action # Atualiza para a nova ação
                    current_phase = ACTION_TO_PHASE[current_action]
                    traci.trafficlight.setPhase(TRAFFIC_LIGHT_ID, current_phase)
                    phase_timer = 0

                # Atualização da Q-table (usando o estado anterior e a ação anterior)
                next_state = get_state(phase_lanes) # O estado é observado após a decisão/passo
                old_value = q_table[state][previous_action] # Usa a ação ANTERIOR que levou a esta recompensa
                next_max = np.max(q_table.get(next_state, np.zeros(NUM_ACTIONS))) # O máximo Q do próximo estado
                # A atualização usa o 'reward' calculado antes da transição/passo
                new_value = (1 - ALPHA) * old_value + ALPHA * (reward + GAMMA * next_max - old_value)
                q_table[state][previous_action] = new_value # previous_action

            else: # Se phase_timer < GREEN_DURATION (nenhuma decisão de Q-learning aqui)
                traci.simulationStep()
                total_steps += 1
                phase_timer += 1
        
        traci.close()
        rewards_history.append(total_reward)

        # Usa a média das últimas 20 recompensas para uma avaliação mais estável
        avg_reward = np.mean(rewards_history[-20:])
        
        if avg_reward > best_reward_avg:
            best_reward_avg, patience = avg_reward, 0
            with open("q_table_prox_estadio.pkl", "wb") as f: pickle.dump(dict(q_table), f)
            print(f"🌟 Nova melhor recompensa média: {best_reward_avg:.2f}. Q-table salva.")
        else:
            patience += 1

        epsilon = max(MIN_EPSILON, epsilon * EPSILON_DECAY)
        print(f"Episódio {ep+1}/{EPOCHS} — Passos: {total_steps}, Recompensa: {total_reward:.2f} (Média: {avg_reward:.2f}), Epsilon: {epsilon:.3f}, Paciência: {patience}/{patience_limit}")
        
        if patience >= patience_limit:
            print(f"\n🛑 Parada antecipada no episódio {ep+1}.")
            break
            
    print("✅ Treinamento concluído.")

if __name__ == "__main__":
    train()