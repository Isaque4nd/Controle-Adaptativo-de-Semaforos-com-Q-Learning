import pandas as pd
import matplotlib.pyplot as plt
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos # Importação para a nova sintaxe
from datetime import datetime

# --- Configurações ---
# Define os nomes de exibição e os nomes das pastas de cada mapa
MAP_DIRS = {
    "Prox. Samur": "Prox_Samur",
    "Prox. Estádio": "Prox_EstadioLomanto",
    "Prox. Batalhão": "Prox_BatalhaoPolicia",
    "Brumado x R. Pacheco": "BrumadoxRPacheco"
}

# Mapeia pastas para seus arquivos de resumo
SUMMARY_FILES = {
    "Prox_Samur": "resumo_metricas_samur.csv",
    "Prox_EstadioLomanto": "resumo_metricas_lomanto.csv",
    "Prox_BatalhaoPolicia": "resumo_metricas_batalhao.csv",
    "BrumadoxRPacheco": "resumo_metricas_brumado.csv"
}

OUTPUT_FILENAME = "relatorio_comparativo_geral.pdf"
FONT_PATH = "DejaVuSans.ttf"

# --- Classe PDF ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona a fonte (parâmetro 'uni' removido)
        self.add_font('DejaVu', '', FONT_PATH)
        self.add_font('DejaVu', 'B', FONT_PATH)
        self.set_font('DejaVu', '', 12)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # O header só aparece da segunda página em diante
        if self.page_no() > 1:
            self.set_font('DejaVu', 'B', 12)
            self.cell(0, 10, 'Relatório Comparativo Geral - Q-Learning vs. Tempo Fixo', 
                      border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')
            self.ln(10)

    def footer(self):
        # O footer só aparece da segunda página em diante
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('DejaVu', '', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 
                      border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    def add_title_page(self):
        """ Cria a Página de Rosto """
        self.add_page()
        self.set_font('DejaVu', 'B', 24)
        self.cell(0, 30, 'Relatório Comparativo Geral', 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('DejaVu', 'B', 16)
        self.cell(0, 15, 'Q-Learning vs. Tempo Fixo', 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.set_font('DejaVu', '', 12)
        self.cell(0, 10, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(20)
        
        self.set_font('DejaVu', 'B', 14)
        self.cell(0, 10, 'Mapas Analisados:', 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.set_font('DejaVu', '', 12)
        for map_name in MAP_DIRS.keys():
            self.cell(0, 8, f'- {map_name}', 
                      border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.ln(10)
        self.set_font('DejaVu', '', 10)
        self.multi_cell(0, 5, 
            "Este relatório agrega os resultados das simulações de quatro cenários de tráfego. "
            "Ele compara o desempenho de um controlador de semáforo baseado em Q-Learning contra um "
            "controlador de tempo fixo, focando nas melhorias percentuais em métricas chave.")
        # Adiciona a primeira página de conteúdo
        self.add_page()

    def add_table_as_image(self, df_agg):
        """ Cria a tabela de resumo como uma imagem e a insere no PDF. """
        print("Gerando tabela de resumo como imagem...")
        
        # 1. Preparar o DataFrame para a tabela
        df_for_table = df_agg.set_index('Mapa').copy()
        
        cols_to_show = ['Melhora Espera Global', 'Melhora Paradas Globais', 
                        'Melhora Espera Prioritarios', 'Melhora Paradas Prioritarios', 
                        'Melhora Espera Emergency', 'Melhora Espera Authority', 
                        'Melhora Velocidade Global']
        
        df_for_table = df_for_table[cols_to_show]
        
        # Adiciona a linha de Média Geral
        df_for_table.loc['MÉDIA GERAL'] = df_for_table.mean()
        
        # Formata todos os valores como string com '%'
        df_for_table = df_for_table.applymap(lambda x: f'{x:.2f}%')
        
        # --- Rótulos das colunas ---
        col_labels = ['Redução Tempo\n de Espera Global', 'Redução Total\n de Paradas Globais', 'Redução Tempo de Espera\n Veículos Prioritários', 'Redução Total de\n Paradas Veículos Prioritários',
                      'Redução Tempo\n de Espera Emergência', 'Redução Tempo\n de Espera Autoridade', 'Aumento Velocidade\n Média Global']

        row_labels = df_for_table.index.tolist()
        
        # 2. Criar a Figura e Tabela Matplotlib

        # --- Tamanho da figura ---
        fig, ax = plt.subplots(figsize=(20, 4)) # Era (14, 3)
        ax.axis('off') # Esconde os eixos do gráfico

        # --- Largura das colunas ---
        table = ax.table(cellText=df_for_table.values, 
                         rowLabels=row_labels, 
                         colLabels=col_labels, 
                         loc='center', 
                         cellLoc='center',
                         colWidths=[0.14, 0.14, 0.17, 0.17, 0.13, 0.13, 0.12]) 
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)

        # --- Altura da célula ---
        table.scale(1, 3.0) # Era 2.5


        # Lógica de cor (já estava correta)
        for (row, col), cell in table.get_celld().items():
            cell.set_text_props(color='black')
            if (row == 0): 
                cell.set_facecolor('#003f5c')
                cell.set_text_props(color='white', weight='bold')
            if (col == -1): 
                cell.set_text_props(color='black', weight='bold', ha='right')
            if (row > 0 and row_labels[row-1] == 'MÉDIA GERAL'):
                cell.set_text_props(color='black', weight='bold')
                if (col == -1):
                   cell.set_text_props(color='black', weight='bold', ha='right')
                if (col != -1):
                    cell.set_facecolor('#f0f0f0')
        
        img_path = "tabela_resumo_geral.png"
        fig.tight_layout()
        fig.savefig(img_path, dpi=300) # Salva com alta resolução
        plt.close(fig)
        
        # 3. Adicionar Título e Imagem da Tabela ao PDF (com verificação de página)
        title_text = 'Resumo Comparativo das Métricas (Melhoria % do Q-Learning)'
        title_height = 10
        padding = 5
        img_w = 190 # Largura da imagem no PDF

        # --- Altura da imagem proporção (20:4) ---
        img_h = (img_w * 4) / 20
        
        total_height = title_height + padding + img_h
        
        # Verifica se o bloco (título + imagem) cabe na página atual
        if self.get_y() + total_height > self.h - self.b_margin:
            self.add_page()
            
        self.set_font('DejaVu', 'B', 16)
        self.cell(0, title_height, title_text, 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(padding)
        
        x_pos = (self.w - img_w) / 2
        self.image(img_path, x=x_pos, w=img_w)
        
        
        self.ln(10)
        
    def add_comparison_chart(self, df_agg, metric_col, title, filename):
        """ Cria e insere um gráfico de barras comparativo (CORRIGIDO PARA TÍTULOS ÓRFÃOS) """
        
        # 1. Gera o gráfico e salva em disco PRIMEIRO
        plt.figure(figsize=(10, 5))
        colors = ['#003f5c', '#58508d', '#bc5090', '#ff6361']
        bars = plt.bar(df_agg['Mapa'], df_agg[metric_col], color=colors[:len(df_agg)])
        
        plt.title(title, fontsize=16)
        plt.ylabel('Melhoria Percentual (%)', fontsize=12)
        plt.xlabel('Cenário (Mapa)', fontsize=12)
        plt.xticks(rotation=10, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        for bar in bars:
            yval = bar.get_height()
            offset = max(yval * 0.01, 0.5)
            plt.text(bar.get_x() + bar.get_width()/2.0, yval + offset, f'{yval:.2f}%', ha='center', va='bottom')

        plt.tight_layout()
        img_path = f"temp_{filename}.png"
        plt.savefig(img_path)
        plt.close()
        
        # 2. Define as alturas e faz a verificação de página
        title_height = 10
        padding = 5
        img_w = 180
        img_h = (img_w * 5) / 10 # Proporção 10:5
        total_height = title_height + padding + img_h
        
        # Verifica se o bloco (título + imagem) cabe na página atual
        if self.get_y() + total_height > self.h - self.b_margin: 
            self.add_page()
        
        # 3. Agora desenha o Título e o Gráfico, sabendo que cabem
        self.set_font('DejaVu', 'B', 16)
        self.cell(0, title_height, title, 
                  border=0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(padding)
        
        x_pos = (self.w - img_w) / 2
        self.image(img_path, x=x_pos, w=img_w)
        os.remove(img_path) # Deleta os gráficos temporários (isso está correto)
        self.ln(5)

# --- Funções de Processamento de Dados ---
def processar_dados_mapa(mapa_nome, mapa_path):
    """ Carrega dados de um mapa e calcula métricas resumidas. """
    path_q = os.path.join(mapa_path, "relatorios") 

    summary_filename = SUMMARY_FILES.get(mapa_path)
    
    if not summary_filename:
        print(f"ERRO: Nome do arquivo de resumo não definido no dicionário SUMMARY_FILES para a pasta: {mapa_path}")
        return None
        
    resumo_path = os.path.join(path_q, summary_filename)

    if not os.path.exists(resumo_path):
        print(f"ERRO: Arquivo de resumo não encontrado para {mapa_nome}: {resumo_path}")
        return None
    
    try:
        # O CSV é separado por ponto e vírgula (;)
        df_resumo = pd.read_csv(resumo_path, sep=';')
        
        metricas = {}
        metricas['Mapa'] = mapa_nome

        def get_metric_value(metric_name):
            # Procura pela métrica limpando espaços em branco
            row = df_resumo[df_resumo['Métrica'].str.strip() == metric_name]
            if row.empty:
                print(f"Aviso: Métrica '{metric_name}' não encontrada em {mapa_nome} (Arquivo: {resumo_path}).")
                return 0.0
                
            val = row['Melhora com Q-Learning'].values[0]
            
            # Remove o "de redução" ou "de aumento" e o "%"
            val_clean = str(val).split('%')[0].strip().replace(',', '.')
            
            # Lida com caso "N/A" ou outros valores não numéricos
            try:
                val_float = float(val_clean)
            except ValueError:
                print(f"Aviso: Valor não numérico ('{val}') para '{metric_name}' em {mapa_nome}. Usando 0.0.")
                return 0.0
            
            # Se for "aumento" (como em densidade), a melhoria é negativa
            # Se for "redução" (como em espera), a melhoria é positiva
            if "aumento" in str(val).lower():
                # Exceção: Velocidade Média, onde aumento é bom
                if "Velocidade Média" in metric_name:
                    return val_float # Aumento é melhoria
                else:
                    return -val_float # Aumento é piora (ex: densidade)
            else:
                return val_float # Redução é melhoria

        # Mapeia exatamente como no seu PDF de exemplo
        metricas['Melhora Espera Global'] = get_metric_value('Tempo de Espera Acumulado (Global)')
        metricas['Melhora Paradas Globais'] = get_metric_value('Total de Paradas na Simulação')
        metricas['Melhora Espera Prioritarios'] = get_metric_value('Tempo de Espera Médio (Prioritários)')
        metricas['Melhora Paradas Prioritarios'] = get_metric_value('Total de Paradas (Prioritários)')
        metricas['Melhora Espera Emergency'] = get_metric_value('Tempo de Espera Médio (Emergência)')
        metricas['Melhora Espera Authority'] = get_metric_value('Tempo de Espera Médio (Autoridade)')
        metricas['Melhora Velocidade Global'] = get_metric_value('Velocidade Média (Global)')

        return metricas

    except Exception as e:
        print(f"ERRO ao processar o arquivo de resumo para {mapa_nome} ({resumo_path}): {e}")
        try:
            temp_df = pd.read_csv(resumo_path, sep=';')
            print(f"Colunas encontradas: {temp_df.columns.tolist()}")
        except:
            pass
        return None

# --- Função Principal ---
def main():
    print("Iniciando geração do relatório comparativo geral...")
    
    # 1. Coletar dados de todos os mapas
    todos_resultados = []
    for mapa_nome, mapa_path in MAP_DIRS.items():
        print(f"Processando dados de: {mapa_nome} (Pasta: {mapa_path})")
        metricas = processar_dados_mapa(mapa_nome, mapa_path)
        if metricas:
            todos_resultados.append(metricas)
    
    if not todos_resultados:
        print("Nenhum dado foi processado. Abortando.")
        return

    df_agregado = pd.DataFrame(todos_resultados)
    
    # 2. Gerar PDF em modo Paisagem (Landscape)
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_title_page()
    
    # 3. Adicionar Tabela Resumo (AGORA COMO IMAGEM)
    pdf.add_table_as_image(df_agregado)
    
    # 4. Adicionar Gráficos Comparativos (Dois por página)
    pdf.add_page()
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Espera Global', 
                             'Comparativo: Redução Tempo de Espera (Global)', 
                             'melhora_espera_global')
    
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Paradas Globais', 
                             'Comparativo: Redução Total de Paradas (Global)', 
                             'melhora_paradas_global')
    
    pdf.add_page()
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Espera Prioritarios', 
                             'Comparativo: Redução Tempo de Espera (Veículos Prioritários)', 
                             'melhora_espera_prioritarios')

    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Paradas Prioritarios', 
                             'Comparativo: Redução Total de Paradas (Veículos Prioritários)', 
                             'melhora_paradas_prioritarios')
                             
    pdf.add_page()
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Espera Emergency', 
                             'Comparativo: Redução Tempo de Espera (Emergência)', 
                             'melhora_sem_espera_emergency') # Nome de arquivo único
                             
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Espera Authority', 
                             'Comparativo: Redução Tempo de Espera (Autoridade)', 
                             'melhora_espera_authority')

    pdf.add_page()
    pdf.add_comparison_chart(df_agregado, 
                             'Melhora Velocidade Global', 
                             'Comparativo: Aumento Velocidade Média (Global)', 
                             'melhora_velocidade_global')

    # 5. Salvar PDF
    try:
        pdf.output(OUTPUT_FILENAME)
        print(f"✅ Relatório comparativo geral salvo como '{OUTPUT_FILENAME}'")
        print(f"✅ Tabela de resumo salva como 'tabela_resumo_geral.png'")
    except Exception as e:
        print(f"ERRO AO SALVAR O PDF: {e}")
        print("Verifique se o arquivo PDF não está aberto em outro programa.")


if __name__ == "__main__":
    if not os.path.exists(FONT_PATH):
        print(f"ERRO: Arquivo de fonte '{FONT_PATH}' não encontrado.")
        print("Por favor, copie o arquivo 'DejaVuSans.ttf' para o mesmo diretório deste script.")
    else:
        main()