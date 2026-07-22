"""
produto_download.py - Módulo para download de imagens GOES
Autor: Victor Ranieri e DeepSeek
Descrição: Funções para download de canais individuais e composição True Color
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import wget
import time
import glob

# ============================================================================
# FUNÇÕES DE CONEXÃO E DIRETÓRIOS
# ============================================================================

def verificar_conexao(sat, timeout=10):
    """Verifica se consegue acessar o servidor do CPTEC"""
    url_base = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/'
    print(f"🔄 Testando conexão com: {url_base}")
    
    try:
        response = requests.get(url_base, timeout=timeout)
        if response.status_code == 200:
            print("✅ Conexão estabelecida com sucesso!")
            return True, url_base
        else:
            print(f"❌ Servidor respondeu com código: {response.status_code}")
            return False, None
    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO DE CONEXÃO: Não foi possível acessar o servidor.")
        print("   Verifique sua internet e tente novamente.")
        return False, None
    except requests.exceptions.Timeout:
        print("\n❌ ERRO: Tempo de conexão esgotado.")
        return False, None
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {type(e).__name__}")
        return False, None

def criar_diretorios_base():
    """Cria diretório base para salvar as figuras"""
    dir_script = os.getcwd()
    dir_fig = os.path.join(dir_script, 'fig_dados')
    os.makedirs(dir_fig, exist_ok=True)
    return dir_fig

def criar_diretorios_download(dir_fig, sat, ano, mes, dia_inicio, dia_fim, canal):
    """Cria diretórios para armazenar os downloads com nome do satélite"""
    diretorio_data = os.path.join(dir_fig, f"{sat}_{ano}{mes}{dia_inicio}_{dia_fim}")
    diretorio_canal = os.path.join(diretorio_data, canal)
    os.makedirs(diretorio_data, exist_ok=True)
    os.makedirs(diretorio_canal, exist_ok=True)
    return diretorio_canal

def salvar_metadados(diretorio, sat, prod_select, canal=None, inicio_str=None, 
                     fim_str=None, passo=None, timestamps=None, info_extra=None):
    """Salva metadados do download em um arquivo"""
    metadata_file = os.path.join(diretorio, 'metadados.txt')
    
    with open(metadata_file, 'w') as f:
        f.write("="*50 + "\n")
        f.write("METADADOS DO DOWNLOAD - GOES\n")
        f.write("="*50 + "\n\n")
        f.write(f"Satélite: {sat.upper()}\n")
        f.write(f"Produto: {prod_select}\n")
        f.write(f"Data do download: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if prod_select == 'simple_chanel':
            f.write(f"Canal: {canal}\n")
        elif prod_select == 'true_color':
            f.write(f"Canais: ch01, ch02, ch03 (True Color - RGB)\n")
            f.write(f"Composição: Vermelho (0.64µm), Verde (0.86µm), Azul (0.47µm)\n")
        elif prod_select == 'swd':
            f.write(f"Canais: ch13, ch15 (Split Window Difference)\n")
            f.write(f"Fórmula: SWD = ch13 - ch15\n")
            f.write(f"Aplicações: Detecção de nuvens baixas, fogo e neblina\n")
        
        if info_extra:
            f.write("\nInformações adicionais:\n")
            for key, value in info_extra.items():
                f.write(f"  {key}: {value}\n")
        
        if inicio_str and fim_str:
            f.write(f"\nPeríodo: {inicio_str} a {fim_str}\n")
        if passo:
            f.write(f"Passo: {passo} minutos\n")
        if timestamps:
            f.write(f"\nTotal de timestamps: {len(timestamps)}\n")
            if len(timestamps) <= 10:
                for ts in timestamps:
                    f.write(f"  {ts}\n")
            else:
                f.write("Primeiros 10 timestamps:\n")
                for ts in timestamps[:10]:
                    f.write(f"  {ts}\n")
                f.write(f"  ... e mais {len(timestamps)-10} timestamps\n")
    
    print(f"📄 Metadados salvos em: {metadata_file}")

# ============================================================================
# FUNÇÕES DE OBTENÇÃO DE INFORMAÇÕES DO SERVIDOR
# ============================================================================

def obter_canais_disponiveis(sat):
    """Obtém lista de canais disponíveis para o satélite"""
    url_base = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/'
    response = requests.get(url_base)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    canais = [link.get('href')[:-1] for link in soup.find_all('a') 
              if link.get('href').startswith('ch')]
    return canais, url_base

def obter_anos_disponiveis(url_canal):
    """Obtém anos disponíveis para o canal selecionado"""
    response = requests.get(url_canal)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    anos = [link.get('href')[:-1] for link in soup.find_all('a') 
            if link.get('href').startswith('2')]
    return anos

def obter_meses_disponiveis(url_ano):
    """Obtém meses disponíveis para o ano selecionado"""
    response = requests.get(url_ano)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    meses = [link.get('href')[:-1] for link in soup.find_all('a') 
             if link.get('href').startswith(('0', '1'))]
    return meses

def obter_dados_disponiveis(raiz_dado):
    """Obtém lista de dados disponíveis no servidor"""
    response = requests.get(raiz_dado)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    dados_disponiveis = []
    prefixo = None
    sufixo = None
    
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and href.startswith('S10'):
            prefixo = href[:10]
            sufixo = href[-3:]
            data = href.split('_')[1].replace(sufixo, '')
            dados_disponiveis.append(data)
    
    return dados_disponiveis, prefixo, sufixo

# ============================================================================
# FUNÇÕES DE INTERAÇÃO COM O USUÁRIO
# ============================================================================

def selecionar_canal(canais):
    """Solicita ao usuário que escolha um canal"""
    print('\nOs canais disponíveis para download são:')
    print(', '.join(canais), '\n')
    canal = input('Insira o canal que deseja fazer o Download: ')
    return canal

def selecionar_ano(anos):
    """Solicita ao usuário que escolha um ano"""
    print('\nOs anos disponíveis são:')
    print(', '.join(anos), '\n')
    ano = input('Insira o ano que deseja fazer o Download: ')
    return ano

def selecionar_mes(meses):
    """Solicita ao usuário que escolha um mês"""
    print('\nOs meses disponíveis são:')
    print(', '.join(meses), '\n')
    mes = input('Insira o mês que deseja fazer o Download: ').zfill(2)
    return mes

def obter_periodo():
    """Obtém datas e horários de início e fim do usuário"""
    print('\n' + '='*50)
    print('DEFINIÇÃO DO PERÍODO DE DOWNLOAD')
    print('='*50)
    
    dia_inicio = input('Escolha o dia do início para o download: ').zfill(2)
    hora_inicio = input('Escolha a hora do início para o download: ').zfill(2)
    dia_fim = input('Escolha o dia do fim para o download: ').zfill(2)
    hora_fim = input('Escolha a hora do fim para o download: ').zfill(2)
    passo = int(input('Digite o passo de tempo em minutos: '))
    
    return dia_inicio, hora_inicio, dia_fim, hora_fim, passo

# ============================================================================
# FUNÇÕES DE TIMESTAMP E DOWNLOAD
# ============================================================================

def gerar_timestamps(ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo):
    """Gera lista de timestamps para download baseado no período"""
    dado_inicio = f"{ano}{mes}{dia_inicio}{hora_inicio}00"
    dado_fim = f"{ano}{mes}{dia_fim}{hora_fim}00"
    
    inicio = datetime.strptime(dado_inicio, '%Y%m%d%H%M')
    fim = datetime.strptime(dado_fim, '%Y%m%d%H%M')
    
    timestamps = []
    while inicio <= fim:
        timestamps.append(inicio.strftime('%Y%m%d%H%M'))
        inicio += timedelta(minutes=passo)
    
    return timestamps, dado_inicio, dado_fim

def baixar_arquivo(raiz_dado, prefixo, timestamp, sufixo, diretorio_canal):
    """Faz o download de um arquivo específico"""
    url_download = f"{raiz_dado}{prefixo}{timestamp}{sufixo}"
    arquivo_local = os.path.join(diretorio_canal, f"{prefixo}{timestamp}{sufixo}")
    
    if os.path.exists(arquivo_local):
        print(f'⏭️  {timestamp} - já existe, pulando')
        return True
    
    try:
        print(f'📥 Baixando: {timestamp}')
        wget.download(url_download, arquivo_local, bar=None)
        print()  # Pula linha após o download
        return True
    except Exception as e:
        print(f'❌ Erro ao baixar {timestamp}: {str(e)[:50]}')
        return False

def processar_downloads(raiz_dado, timestamps, dados_disponiveis, prefixo, sufixo, diretorio_canal):
    """Processa a verificação e download dos arquivos"""
    print('\n🔍 Verificando existência das datas escolhidas...\n')
    
    baixados = 0
    for timestamp in timestamps:
        if timestamp in dados_disponiveis:
            print(f'✅ O dado {timestamp} existe.')
            if baixar_arquivo(raiz_dado, prefixo, timestamp, sufixo, diretorio_canal):
                baixados += 1
        else:
            print(f'❌ O dado {timestamp} NÃO existe. Pulando...')
    
    print(f'\n📊 Resumo: {baixados}/{len(timestamps)} arquivos baixados')

# ============================================================================
# FUNÇÕES ESPECÍFICAS PARA TRUE COLOR
# ============================================================================

def gerar_timestamps_true_color(ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo):
    """Gera lista de timestamps para download do True Color"""
    dado_inicio = f"{ano}{mes}{dia_inicio}{hora_inicio}00"
    dado_fim = f"{ano}{mes}{dia_fim}{hora_fim}00"
    
    inicio = datetime.strptime(dado_inicio, '%Y%m%d%H%M')
    fim = datetime.strptime(dado_fim, '%Y%m%d%H%M')
    
    timestamps = []
    while inicio <= fim:
        timestamps.append(inicio.strftime('%Y%m%d%H%M'))
        inicio += timedelta(minutes=passo)
    
    return timestamps, dado_inicio, dado_fim

def baixar_true_color(sat, ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo, dir_fig):
    """
    Baixa os canais 1, 2 e 3 para composição True Color
    GARANTE que os MESMOS timestamps sejam baixados em todos os canais
    """
    canais_true_color = ['ch01', 'ch02', 'ch03']
    nome_canais = {'ch01': 'Vermelho (0.64µm)', 'ch02': 'Verde (0.86µm)', 'ch03': 'Azul (0.47µm)'}
    
    print(f"\n{'='*60}")
    print("🎨 DOWNLOAD TRUE COLOR")
    print(f"{'='*60}")
    print("Composição RGB:")
    for canal, nome in nome_canais.items():
        print(f"   📍 {canal.upper()} - {nome}")
    print(f"{'='*60}\n")
    
    # Gerar timestamps
    timestamps, dado_inicio, dado_fim = gerar_timestamps_true_color(
        ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo
    )
    
    print(f"📅 Período: {dado_inicio} a {dado_fim} | Passo: {passo}min")
    print(f"📊 Total de timestamps: {len(timestamps)}\n")
    
    # Verificar disponibilidade em cada canal
    print("🔍 Verificando disponibilidade...")
    timestamps_por_canal = {}
    
    for canal in canais_true_color:
        url_canal = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/{canal}/{ano}/{mes}/'
        dados_disponiveis, prefixo, sufixo = obter_dados_disponiveis(url_canal)
        
        timestamps_existentes = [ts for ts in timestamps if ts in dados_disponiveis]
        timestamps_por_canal[canal] = {
            'timestamps': timestamps_existentes,
            'prefixo': prefixo,
            'sufixo': sufixo,
            'raiz_dado': url_canal,
            'total': len(timestamps_existentes)
        }
        print(f"   {canal}: {len(timestamps_existentes)}/{len(timestamps)} disponíveis")
    
    # Encontrar timestamps comuns
    timestamps_comuns = sorted(set(timestamps_por_canal['ch01']['timestamps']) &
                                set(timestamps_por_canal['ch02']['timestamps']) &
                                set(timestamps_por_canal['ch03']['timestamps']))
    
    print(f"\n✨ Timestamps comuns aos 3 canais: {len(timestamps_comuns)}")
    
    if not timestamps_comuns:
        print("\n❌ ERRO: Nenhum timestamp comum encontrado!")
        return None
    
    # Criar diretório base com nome do satélite
    dir_base = os.path.join(dir_fig, f"{sat}_true_color_{ano}{mes}_{dia_inicio}_{dia_fim}")
    os.makedirs(dir_base, exist_ok=True)
    
    # Salvar metadados
    salvar_metadados(dir_base, sat, 'true_color', 
                     inicio_str=dado_inicio, fim_str=dado_fim, 
                     passo=passo, timestamps=timestamps_comuns)
    
    # Salvar timestamps comuns em arquivo separado
    arquivo_timestamps = os.path.join(dir_base, "timestamps_comuns.txt")
    with open(arquivo_timestamps, 'w') as f:
        f.write("\n".join(timestamps_comuns))
    
    # Baixar arquivos
    print("\n⬇️ INICIANDO DOWNLOAD...\n")
    resultados = {}
    
    for canal in canais_true_color:
        print(f"\n📡 Canal {canal.upper()}:")
        dir_canal = os.path.join(dir_base, canal)
        os.makedirs(dir_canal, exist_ok=True)
        
        info = timestamps_por_canal[canal]
        baixados = 0
        
        for ts in timestamps_comuns:
            arquivo_local = os.path.join(dir_canal, f"{info['prefixo']}{ts}{info['sufixo']}")
            
            if os.path.exists(arquivo_local):
                print(f"   ⏭️  {ts} - já existe")
                baixados += 1
            else:
                url = f"{info['raiz_dado']}{info['prefixo']}{ts}{info['sufixo']}"
                try:
                    print(f"   📥 {ts} - baixando...", end=" ")
                    wget.download(url, arquivo_local, bar=None)
                    print("✅")
                    baixados += 1
                except Exception as e:
                    print(f"❌ Erro: {str(e)[:40]}")
        
        resultados[canal] = {'baixados': baixados, 'total': len(timestamps_comuns)}
        print(f"   📊 Resumo: {baixados}/{len(timestamps_comuns)}")
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RESUMO TRUE COLOR")
    print(f"{'='*60}")
    for canal, info in resultados.items():
        status = "✅" if info['baixados'] == info['total'] else "⚠️"
        print(f"{status} {canal}: {info['baixados']}/{info['total']}")
    
    print(f"\n📁 Pasta: {dir_base}")
    print(f"📄 Metadados: {os.path.join(dir_base, 'metadados.txt')}")
    
    if all(info['baixados'] == info['total'] for info in resultados.values()):
        print("\n🎉 TRUE COLOR COMPLETO!")
    else:
        print("\n⚠️ True Color incompleto - alguns timestamps faltando")
    
    print(f"{'='*60}\n")
    
    return resultados, timestamps_comuns

# ============================================================================
# FUNÇÕES ESPECÍFICAS PARA SWD (SPLIT WINDOW DIFFERENCE)
# ============================================================================

def baixar_swd(sat, ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo, dir_fig):
    """
    Baixa os canais 13 e 15 para composição SWD (Split Window Difference)
    GARANTE que os MESMOS timestamps sejam baixados em todos os canais
    SWD = ch13 - ch15 (diferença entre os canais do infravermelho)
    """
    canais_swd = ['ch13', 'ch15']
    nome_canais = {
        'ch13': 'IR 10.3µm - Canal Clean Window', 
        'ch15': 'IR 12.3µm - Canal Dirty Window'
    }
    
    print(f"\n{'='*60}")
    print("🌡️ DOWNLOAD SWD (SPLIT WINDOW DIFFERENCE)")
    print(f"{'='*60}")
    print("Canais para SWD:")
    for canal, nome in nome_canais.items():
        print(f"   📍 {canal.upper()} - {nome}")
    print(f"   📊 SWD = CH13 - CH15 (diferença split window)")
    print(f"{'='*60}\n")
    
    # Gerar timestamps
    timestamps, dado_inicio, dado_fim = gerar_timestamps_true_color(
        ano, mes, dia_inicio, hora_inicio, dia_fim, hora_fim, passo
    )
    
    print(f"📅 Período: {dado_inicio} a {dado_fim} | Passo: {passo}min")
    print(f"📊 Total de timestamps: {len(timestamps)}\n")
    
    # Verificar disponibilidade em cada canal
    print("🔍 Verificando disponibilidade...")
    timestamps_por_canal = {}
    
    for canal in canais_swd:
        url_canal = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/{canal}/{ano}/{mes}/'
        dados_disponiveis, prefixo, sufixo = obter_dados_disponiveis(url_canal)
        
        timestamps_existentes = [ts for ts in timestamps if ts in dados_disponiveis]
        timestamps_por_canal[canal] = {
            'timestamps': timestamps_existentes,
            'prefixo': prefixo,
            'sufixo': sufixo,
            'raiz_dado': url_canal,
            'total': len(timestamps_existentes)
        }
        print(f"   {canal}: {len(timestamps_existentes)}/{len(timestamps)} disponíveis")
    
    # Encontrar timestamps comuns
    timestamps_comuns = sorted(set(timestamps_por_canal['ch13']['timestamps']) &
                                set(timestamps_por_canal['ch15']['timestamps']))
    
    print(f"\n✨ Timestamps comuns aos 2 canais: {len(timestamps_comuns)}")
    
    if not timestamps_comuns:
        print("\n❌ ERRO: Nenhum timestamp comum encontrado!")
        return None
    
    # Criar diretório base com nome do satélite
    dir_base = os.path.join(dir_fig, f"{sat}_swd_{ano}{mes}_{dia_inicio}_{dia_fim}")
    os.makedirs(dir_base, exist_ok=True)
    
    # Salvar metadados
    salvar_metadados(dir_base, sat, 'swd', 
                     inicio_str=dado_inicio, fim_str=dado_fim, 
                     passo=passo, timestamps=timestamps_comuns)
    
    # Salvar timestamps comuns em arquivo separado
    arquivo_timestamps = os.path.join(dir_base, "timestamps_comuns.txt")
    with open(arquivo_timestamps, 'w') as f:
        f.write("\n".join(timestamps_comuns))
    
    # Baixar arquivos
    print("\n⬇️ INICIANDO DOWNLOAD...\n")
    resultados = {}
    
    for canal in canais_swd:
        print(f"\n📡 Canal {canal.upper()}:")
        dir_canal = os.path.join(dir_base, canal)
        os.makedirs(dir_canal, exist_ok=True)
        
        info = timestamps_por_canal[canal]
        baixados = 0
        
        for ts in timestamps_comuns:
            arquivo_local = os.path.join(dir_canal, f"{info['prefixo']}{ts}{info['sufixo']}")
            
            if os.path.exists(arquivo_local):
                print(f"   ⏭️  {ts} - já existe")
                baixados += 1
            else:
                url = f"{info['raiz_dado']}{info['prefixo']}{ts}{info['sufixo']}"
                try:
                    print(f"   📥 {ts} - baixando...", end=" ")
                    wget.download(url, arquivo_local, bar=None)
                    print("✅")
                    baixados += 1
                except Exception as e:
                    print(f"❌ Erro: {str(e)[:40]}")
        
        resultados[canal] = {'baixados': baixados, 'total': len(timestamps_comuns)}
        print(f"   📊 Resumo: {baixados}/{len(timestamps_comuns)}")
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RESUMO SWD")
    print(f"{'='*60}")
    for canal, info in resultados.items():
        status = "✅" if info['baixados'] == info['total'] else "⚠️"
        print(f"{status} {canal}: {info['baixados']}/{info['total']}")
    
    print(f"\n📁 Pasta: {dir_base}")
    print(f"📄 Metadados: {os.path.join(dir_base, 'metadados.txt')}")
    
    if all(info['baixados'] == info['total'] for info in resultados.values()):
        print("\n🎉 SWD COMPLETO!")
        print("📐 Fórmula: SWD = ch13 - ch15")
        print("💡 Aplicação: Detecção de nuvens de baixo nível, fogo e neblina")
    else:
        print("\n⚠️ SWD incompleto - alguns timestamps faltando")
    
    print(f"{'='*60}\n")
    
    return resultados, timestamps_comuns

# ============================================================================
# FUNÇÕES AUXILIARES PARA VERIFICAÇÃO
# ============================================================================

def verificar_datas_correspondentes(diretorio_true_color):
    """Verifica se as datas correspondem entre os 3 canais"""
    print(f"\n{'='*60}")
    print("🔍 VERIFICANDO CORRESPONDÊNCIA DAS DATAS")
    print(f"{'='*60}")
    
    canais = ['ch01', 'ch02', 'ch03']
    timestamps_por_canal = {}
    
    for canal in canais:
        caminho = os.path.join(diretorio_true_color, canal)
        if os.path.exists(caminho):
            arquivos = glob.glob(os.path.join(caminho, "*.nc"))
            timestamps = [os.path.basename(f).split('_')[1].replace('.nc', '') for f in arquivos]
            timestamps_por_canal[canal] = sorted(timestamps)
            print(f"{canal}: {len(timestamps_por_canal[canal])} arquivos")
    
    if len(timestamps_por_canal) == 3:
        if (timestamps_por_canal['ch01'] == timestamps_por_canal['ch02'] == 
            timestamps_por_canal['ch03']):
            print(f"\n✅ PERFEITO! Todos os canais têm as MESMAS datas!")
            return True
        else:
            print(f"\n⚠️ ATENÇÃO: Canais com datas diferentes!")
            return False
    else:
        print(f"\n❌ Canais faltando!")
        return False

# ============================================================================
# FUNÇÃO PRINCIPAL EXPORTADA
# ============================================================================

def select_prod(sat, prod_select):
    """
    Função principal que orquestra todo o processo de download
    Parâmetros:
        sat: str - 'goes16' ou 'goes19'
        prod_select: str - 'simple_chanel', 'true_color' ou 'swd'
    """
    print(f"\n{'='*50}")
    print(f"🚀 INICIANDO DOWNLOAD")
    print(f"📡 Satélite: {sat.upper()}")
    print(f"📦 Produto: {prod_select}")
    print(f"{'='*50}\n")
    
    # Verificar conexão
    conexao, url_base = verificar_conexao(sat)
    if not conexao:
        return False
    
    # Criar diretório base
    dir_fig = criar_diretorios_base()
    
    # ===== TRUE COLOR =====
    if prod_select == 'true_color':
        url_temp = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/ch01/'
        anos = obter_anos_disponiveis(url_temp)
        ano = selecionar_ano(anos)
        url_mes = f"{url_temp}{ano}/"
        meses = obter_meses_disponiveis(url_mes)
        mes = selecionar_mes(meses)
        dia_ini, hora_ini, dia_fim, hora_fim, passo = obter_periodo()
        baixar_true_color(sat, ano, mes, dia_ini, hora_ini, dia_fim, hora_fim, passo, dir_fig)
    
    # ===== SWD =====
    elif prod_select == 'swd':
        url_temp = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/ch13/'
        anos = obter_anos_disponiveis(url_temp)
        ano = selecionar_ano(anos)
        url_mes = f"{url_temp}{ano}/"
        meses = obter_meses_disponiveis(url_mes)
        mes = selecionar_mes(meses)
        dia_ini, hora_ini, dia_fim, hora_fim, passo = obter_periodo()
        baixar_swd(sat, ano, mes, dia_ini, hora_ini, dia_fim, hora_fim, passo, dir_fig)
    
    # ===== SIMPLE CHANNEL =====
    elif prod_select == 'simple_chanel':
        canais, url_base = obter_canais_disponiveis(sat)
        canal = selecionar_canal(canais)
        url_canal = f"{url_base}{canal}/"
        anos = obter_anos_disponiveis(url_canal)
        ano = selecionar_ano(anos)
        url_ano = f"{url_canal}{ano}/"
        meses = obter_meses_disponiveis(url_ano)
        mes = selecionar_mes(meses)
        url_mes = f"{url_ano}{mes}/"
        dia_ini, hora_ini, dia_fim, hora_fim, passo = obter_periodo()
        dir_canal = criar_diretorios_download(dir_fig, sat, ano, mes, dia_ini, dia_fim, canal)
        timestamps, inicio_str, fim_str = gerar_timestamps(ano, mes, dia_ini, hora_ini, 
                                                            dia_fim, hora_fim, passo)
        diretorio_data = os.path.join(dir_fig, f"{sat}_{ano}{mes}{dia_ini}_{dia_fim}")
        salvar_metadados(diretorio_data, sat, 'simple_chanel', 
                         canal=canal, inicio_str=inicio_str, fim_str=fim_str, 
                         passo=passo, timestamps=timestamps)
        print(f"\n📊 RESUMO: Satélite {sat.upper()} | Canal {canal} | {inicio_str} a {fim_str} | Passo: {passo}min\n")
        dados_disponiveis, prefixo, sufixo = obter_dados_disponiveis(url_mes)
        processar_downloads(url_mes, timestamps, dados_disponiveis, prefixo, sufixo, dir_canal)
    
    else:
        print(f"❌ Produto '{prod_select}' inválido!")
        print("   Opções válidas: 'simple_chanel', 'true_color', 'swd'")
        return False
    
    print(f"\n{'='*50}")
    print("✅ PROCESSO CONCLUÍDO!")
    print(f"{'='*50}\n")
    
    return True

# ============================================================================
# EXECUÇÃO DIRETA
# ============================================================================

if __name__ == "__main__":
    print("="*50)
    print("📡 SCRIPT DE DOWNLOAD GOES")
    print("="*50)
    
    sat = input('\nDigite o satélite (goes16 ou goes19): ').lower()
    prod = input('Digite o produto (simple_chanel, true_color ou swd): ').lower()
    
    select_prod(sat, prod)