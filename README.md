# 🚦 Otimização de Semáforos com Q-Learning (SUMO)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![SUMO](https://img.shields.io/badge/Simulator-SUMO-yellow)
![Status](https://img.shields.io/badge/Status-Concluído-green)

Este repositório contém a implementação de um Trabalho de Conclusão de Curso (TCC) focado no **controle inteligente de tráfego urbano priorizando a passagem de veículos prioritários**. O projeto utiliza **Aprendizado por Reforço (Q-Learning)** para otimizar semáforos em interseções complexas, visando reduzir o tempo de espera e priorizar veículos de emergência (ambulâncias, bombeiros, polícia).

As simulações são realizadas utilizando o simulador **SUMO (Simulation of Urban MObility)** integrado ao Python via **TraCI**.

---

## 🗺️ Cenários de Estudo

O sistema foi validado em quatro cenários reais da cidade de Vitória da Conquista/BA:

* **Prox_Samur:** Interseção crítica próxima ao hospital/SAMU.
* **Prox_EstadioLomanto:** Região distante do centro da cidade.
* **Prox_BatalhaoPolicia:** Rota frequente de veículos militares e policiais.
* **BrumadoxRPacheco:** Cruzamento de avenidas arteriais.

---

## 🛠️ Tecnologias

* [Python 3.8+](https://www.python.org/)
* [SUMO (Simulation of Urban MObility)](https://eclipse.dev/sumo/)
* **Bibliotecas Python:** `traci`, `sumolib`, `pandas`, `numpy`, `matplotlib`.

## 📦 Instalação

1.  **Instale o SUMO:**
    Baixe e instale a versão mais recente do SUMO para seu sistema operacional [aqui](https://sumo.dlr.de/docs/Downloads.php).
    *Certifique-se de configurar a variável de ambiente `SUMO_HOME`.*

2.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/Isaque4nd/Controle-Adaptativo-de-Semaforos-com-Q-Learning.git)
    cd seu-repositorio
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
---

## 🚀 Guia de Execução (Passo a Passo)

O projeto é modular. Cada pasta de cenário (ex: `Prox_Samur`) funciona de forma independente. Siga este fluxo para rodar os experimentos:

### Passo 1: Treinamento do Agente (Q-Learning)
Antes de visualizar a simulação inteligente, é necessário "ensinar" o agente. O script de treinamento roda centenas de episódios sem interface gráfica (para ser mais rápido) e salva o conhecimento em um arquivo `.pkl`.

1. Entre na pasta do cenário desejado:
    ```bash
    cd "mapas TCC/Prox_Samur"
    ```

2. Execute o treinamento:
    ```bash
    python treinamento_Qlearning.py
    ```
    *Saída:* Isso criará ou atualizará o arquivo `q_table_prox_samur.pkl`.

### Passo 2: Executar Simulação Comparativa
Agora você pode rodar a simulação visual (`sumo-gui`) para ver o resultado prático.

* **Para rodar com a IA Treinada:**
    ```bash
    python simulacao_Qlearning.py
    ```
    > *O que acontece:* Abre o SUMO, carrega o `q_table_*.pkl` e controla o semáforo baseada na recompensa aprendida.

* **Para rodar o Controle Convencional (Tempo Fixo):**
    ```bash
    python tempo_fixo.py
    ```
    > *O que acontece:* Roda a mesma simulação, mas com o plano semafórico estático (convencional).

### Passo 3: Geração de Gráficos e Métricas
Durante as simulações, arquivos `.csv` são gerados automaticamente nas pastas `resultados_qlearning` e `resultados_tempo_fixo`. Para processar esses dados:

* **Análise Individual (Por Cenário):**
    Dentro da pasta do cenário, rode:
    ```bash
    python comparar_resultados.py
    ```
    Isso gera gráficos (PNG) na pasta `relatorios/` comparando fila, espera e emissão de CO2.

* **Análise Global (Todos os Cenários):**
    Na raiz do projeto, rode:
    ```bash
    python relatorio_geral.py
    ```
    Isso compila os dados de todas as pastas e gera um PDF consolidado (`relatorio_comparativo_geral.pdf`).

---

## ⚙️ Parâmetros do Q-Learning

Caso queira alterar o comportamento da IA, você pode editar as variáveis constantes no início do arquivo `treinamento_Qlearning.py`:

* **ALPHA (Taxa de aprendizado):** Define quão rápido o agente substitui informações antigas por novas.
* **GAMMA (Fator de desconto):** Define a importância que o agente dá para recompensas futuras.
* **EPSILON (Exploração):** Probabilidade de tomar uma ação aleatória para descobrir novos estados (vs. usar o melhor caminho conhecido).
* **EPISODES:** Quantidade de rodadas de treinamento a serem executadas.

---

## 📂 Estrutura do Projeto

Entenda onde está cada arquivo importante dentro do repositório:

```text
├── Controle Adaptativo de Semaforos com-Q-Learning/
│   ├── relatorio_geral.py           # Gera o PDF final com todos os dados
│   │
│   ├── Prox_Samur/                  # [Exemplo de Cenário]
│   │   ├── *.net.xml                # Arquivo de rede (ruas e semáforos)
│   │   ├── *.rou.xml                # Arquivo de demanda (rotas dos carros)
│   │   ├── *.sumocfg                # Configuração de execução do SUMO
│   │   │
│   │   ├── treinamento_Qlearning.py # Script de treino (gera o .pkl)
│   │   ├── simulacao_Qlearning.py   # Script de teste (usa o .pkl)
│   │   ├── tempo_fixo.py            # Script de controle (baseline)
│   │   ├── comparar_resultados.py   # Gera gráficos locais
│   │   │
│   │   ├── q_table_*.pkl            # Matriz Q salva (Cérebro da IA)
│   │   ├── resultados_qlearning/    # Logs CSV da IA
│   │   ├── resultados_tempo_fixo/   # Logs CSV do Tempo Fixo
│   │   └── relatorios/              # Gráficos PNG gerados
│   │
│   ├── Prox_EstadioLomanto/         # [Outros cenários...]
│   ├── Prox_BatalhaoPolicia/
│   └── BrumadoxRPacheco/


❓ Troubleshooting (Problemas Comuns)
Erro: "sumolib not found" ou "traci not found"

Verifique se instalou as dependências: pip install -r requirements.txt.

Verifique se a variável de ambiente SUMO_HOME está configurada corretamente no seu sistema.

Erro: O treinamento demora muito

O treinamento roda sem interface gráfica, mas dependendo do número de EPISODES e da complexidade do mapa, pode levar tempo. Reduza o número de episódios no script para testes rápidos de validação.

Erro: Os carros não se movem ou somem

Verifique se os arquivos de rota (.rou.xml) estão na mesma pasta e referenciados corretamente no arquivo de configuração (.sumocfg).

📄 Licença e Créditos
Desenvolvido por Isaque Ribeiro de Andrade como requisito para conclusão do curso superior de Bacharelado em Sistema de Informação.

Simulador: Eclipse SUMO

Orientador: Djan Almeida Santos
