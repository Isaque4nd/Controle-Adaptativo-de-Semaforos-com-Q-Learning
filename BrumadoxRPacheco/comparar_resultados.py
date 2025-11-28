#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

# --- Configurações de Pastas ---
QL_FOLDER = 'BrumadoxRPacheco\\resultados_qlearning'
FT_FOLDER = 'BrumadoxRPacheco\\resultados_tempo_fixo'
REPORT_FOLDER = 'BrumadoxRPacheco\\relatorios'

# --- Dicionários de Arquivos e Labels ---
METRIC_KEYS = [
    'carros_parados', 'total_paradas', 'tempo_espera', 'velocidade_media', 'densidade_media',
    'tempo_espera_emergency', 'tempo_espera_authority', 'carros_parados_prioritarios',
    'total_paradas_prioritarios', 'tempo_espera_prioritarios', 'velocidade_media_prioritarios'
]

FIXED_FILES = {
    'carros_parados': "parados_tempo_fixo.csv",
    'total_paradas': "total_paradas_tempo_fixo.csv",
    'tempo_espera': "espera_tempo_fixo.csv",
    'velocidade_media': "velocidade_tempo_fixo.csv",
    'densidade_media': "densidade_tempo_fixo.csv",
    'tempo_espera_emergency': "emergency_tempo_fixo.csv",
    'tempo_espera_authority': "authority_tempo_fixo.csv",
    'carros_parados_prioritarios': "carros_parados_prioritarios_tempo_fixo.csv",
    'total_paradas_prioritarios': "paradas_prioritarios_tempo_fixo.csv",
    'tempo_espera_prioritarios': "espera_prioritarios_tempo_fixo.csv",
    'velocidade_media_prioritarios': "velocidade_prioritarios_tempo_fixo.csv"
}

RL_FILES = {
    'carros_parados': "resultado_qlearning.csv",
    'total_paradas': "paradas_qlearning.csv",
    'tempo_espera': "espera_qlearning.csv",
    'velocidade_media': "velocidade_qlearning.csv",
    'densidade_media': "densidade_qlearning.csv",
    'tempo_espera_emergency': "emergency_qlearning.csv",
    'tempo_espera_authority': "authority_qlearning.csv",
    'carros_parados_prioritarios': "carros_parados_prioritarios_qlearning.csv",
    'total_paradas_prioritarios': "paradas_prioritarios_qlearning.csv",
    'tempo_espera_prioritarios': "espera_prioritarios_qlearning.csv",
    'velocidade_media_prioritarios': "velocidade_prioritarios_qlearning.csv"
}

METRIC_LABELS = {
    'carros_parados': 'Veículos Parados no Semáforo',
    'total_paradas': 'Total de Paradas na Simulação',
    'tempo_espera': 'Tempo de Espera Acumulado (Global)',
    'velocidade_media': 'Velocidade Média (Global)',
    'densidade_media': 'Densidade Média no Semáforo',
    'tempo_espera_emergency': 'Tempo de Espera Médio (Emergência)',
    'tempo_espera_authority': 'Tempo de Espera Médio (Autoridade)',
    'carros_parados_prioritarios': 'Veículos Prioritários Parados',
    'total_paradas_prioritarios': 'Total de Paradas (Prioritários)',
    'tempo_espera_prioritarios': 'Tempo de Espera Médio (Prioritários)',
    'velocidade_media_prioritarios': 'Velocidade Média (Prioritários)'
}

def get_column_name(metric_key):
    special_cases = {
        'tempo_espera_emergency': 'media_espera_emergency',
        'tempo_espera_authority': 'media_espera_authority'
    }
    return special_cases.get(metric_key, metric_key)

def load_all_data(ft_folder, rl_folder, ft_files, rl_files):
    dfs_fixed = {}
    dfs_rl = {}
    for key in METRIC_KEYS:
        try:
            path = os.path.join(ft_folder, ft_files.get(key, ''))
            dfs_fixed[key] = pd.read_csv(path)
        except FileNotFoundError:
            print(f"Aviso: Arquivo de tempo fixo não encontrado: '{path}'")
            dfs_fixed[key] = pd.DataFrame()
        
        try:
            path = os.path.join(rl_folder, rl_files.get(key, ''))
            dfs_rl[key] = pd.read_csv(path)
        except FileNotFoundError:
            print(f"Aviso: Arquivo de Q-learning não encontrado: '{path}'")
            dfs_rl[key] = pd.DataFrame()
    return dfs_fixed, dfs_rl

def generate_plots(dfs_fixed, dfs_rl, output_dir):
    print("📊 Gerando gráficos comparativos...")
    for metric, label in METRIC_LABELS.items():
        plt.figure(figsize=(12, 6))
        
        df_ft, df_rl = dfs_fixed.get(metric), dfs_rl.get(metric)
        column = get_column_name(metric)

        if df_ft is not None and not df_ft.empty and column in df_ft.columns:
            if 'espera' in metric and 'media' not in column:
                plt.plot(df_ft['tempo'], df_ft[column].cumsum(), label='Tempo Fixo', color='blue', alpha=0.8)
            else:
                plt.plot(df_ft['tempo'], df_ft[column], label='Tempo Fixo', color='blue', alpha=0.8)
        
        if df_rl is not None and not df_rl.empty and column in df_rl.columns:
            if 'espera' in metric and 'media' not in column:
                plt.plot(df_rl['tempo'], df_rl[column].cumsum(), label='Q-Learning', color='red', alpha=0.8)
            else:
                plt.plot(df_rl['tempo'], df_rl[column], label='Q-Learning', color='red', alpha=0.8)

        plt.title(f'Comparação: {label}', fontsize=16)
        plt.xlabel('Tempo de Simulação (s)', fontsize=12)
        plt.ylabel(label.split('(')[0].strip(), fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'comparacao_{metric}.png'))
        plt.close()
    print("✅ Gráficos gerados com sucesso.")

def generate_pdf_report(dfs_fixed, dfs_rl, output_dir):
    print("📄 Gerando relatório em PDF...")
    pdf_path = os.path.join(output_dir, 'relatorio_comparativo_completo.pdf')
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("Relatório Comparativo de Desempenho", styles['h1']))
    story.append(Paragraph("Tempo Fixo vs. Q-Learning para Semáforo Inteligente", styles['h2']))
    story.append(Spacer(1, 0.2 * inch))
    
    story.append(Paragraph("Resumo das Métricas Médias", styles['h3']))
    table_data = [['Métrica', 'Tempo Fixo (Média)', 'Q-Learning (Média)', 'Melhora com Q-Learning']]
    
    for metric, label in METRIC_LABELS.items():
        df_ft, df_rl = dfs_fixed.get(metric), dfs_rl.get(metric)
        column = get_column_name(metric)

        if all(df is not None and not df.empty and column in df for df in [df_ft, df_rl]):
            mean_ft, mean_rl = df_ft[column].mean(), df_rl[column].mean()
            melhora_str = "N/A"
            if mean_ft != 0:
                if any(k in metric for k in ['espera', 'parados', 'densidade', 'paradas']):
                    melhora_percent = ((mean_ft - mean_rl) / mean_ft) * 100
                    melhora_str = f"{abs(melhora_percent):.2f}% de redução"
                elif 'velocidade' in metric:
                    melhora_percent = ((mean_rl - mean_ft) / mean_ft) * 100
                    melhora_str = f"{abs(melhora_percent):.2f}% de aumento"
            table_data.append([label, f"{mean_ft:.2f}", f"{mean_rl:.2f}", melhora_str])

    table = Table(table_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige), ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(PageBreak())

    story.append(Paragraph("Gráficos de Desempenho ao Longo do Tempo", styles['h2']))
    for metric, label in METRIC_LABELS.items():
        story.append(Paragraph(label, styles['h3']))
        img_path = os.path.join(output_dir, f'comparacao_{metric}.png')
        if os.path.exists(img_path):
            story.append(Image(img_path, width=7 * inch, height=3.5 * inch))
        else:
            story.append(Paragraph(f"(Gráfico para '{label}' não encontrado)", styles['Italic']))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    print(f"✅ Relatório PDF completo salvo em: '{pdf_path}'")

def generate_summary_csv(dfs_fixed, dfs_rl, ql_folder_path):
    """ Gera um CSV de resumo para o 'relatorio_geral.py' ler. """
    print("💾 Gerando resumo em CSV...")
    summary_data = []
    
    for metric, label in METRIC_LABELS.items():
        df_ft, df_rl = dfs_fixed.get(metric), dfs_rl.get(metric)
        column = get_column_name(metric)

        if all(df is not None and not df.empty and column in df for df in [df_ft, df_rl]):
            mean_ft, mean_rl = df_ft[column].mean(), df_rl[column].mean()
            melhora_str = "N/A"
            if mean_ft != 0:
                # Usa 'replace' para garantir que o formato decimal seja vírgula
                if any(k in metric for k in ['espera', 'parados', 'densidade', 'paradas']):
                    melhora_percent = ((mean_ft - mean_rl) / mean_ft) * 100
                    melhora_str = f"{melhora_percent:.2f}% de redução".replace('.', ',') 
                elif 'velocidade' in metric:
                    melhora_percent = ((mean_rl - mean_ft) / mean_ft) * 100
                    melhora_str = f"{abs(melhora_percent):.2f}% de aumento".replace('.', ',')
            
            summary_data.append({
                'Métrica': label, 
                'Tempo Fixo (Média)': f"{mean_ft:.2f}".replace('.', ','), 
                'Q-Learning (Média)': f"{mean_rl:.2f}".replace('.', ','), 
                'Melhora com Q-Learning': melhora_str
            })
    
    # Cria o DataFrame e salva em CSV
    if summary_data:
        df_summary = pd.DataFrame(summary_data)
        # Salva o resumo dentro da pasta do q-learning, onde o script geral espera
        csv_path = os.path.join(ql_folder_path, "resumo_metricas_brumado.csv") 
        
        # Usa sep=';' e encoding 'utf-8-sig' para compatibilidade
        df_summary.to_csv(csv_path, sep=';', index=False, encoding='utf-8-sig')
        print(f"✅ Resumo CSV salvo em: '{csv_path}'")
    else:
        print("⚠️ Nenhum dado de resumo para salvar em CSV.")

def main():
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)
        print(f"📁 Pasta '{REPORT_FOLDER}' criada.")

    dfs_fixed, dfs_rl = load_all_data(FT_FOLDER, QL_FOLDER, FIXED_FILES, RL_FILES)

    generate_plots(dfs_fixed, dfs_rl, REPORT_FOLDER)
    generate_pdf_report(dfs_fixed, dfs_rl, REPORT_FOLDER)
    generate_summary_csv(dfs_fixed, dfs_rl, REPORT_FOLDER)

if __name__ == "__main__":
    main()