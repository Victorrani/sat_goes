"""
produto_download.py - Módulo para download de imagens GOES
Autor: Victor Ranieri e DeepSeek
Descrição: Funções para download de canais individuais e composições True Color, SWD, CPD e WVD
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import wget

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

        if prod_select == 'Single_Band':
            f.write(f"Canal: {canal}\n")
        elif prod_select == 'True_Color':
            f.write(f"Canais: ch01, ch02, ch03 (True Color - RGB)\n")
            f.write(f"Composição: Vermelho (0.64µm), Verde (0.86µm), Azul (0.47µm)\n")
        elif prod_select in PRODUTOS_COMPOSTOS:
            # SWD, CPD, WVD, Ozone, SWVD - metadados derivados de PRODUTOS_COMPOSTOS
            # (fonte única, evita descrições desatualizadas ou incompletas)
            info = PRODUTOS_COMPOSTOS[prod_select]
            f.write(f"Canais: {', '.join(info['canais'])} ({info['titulo']})\n")
            if 'formula' in info:
                f.write(f"Fórmula: {info['formula']}\n")
            if 'aplicacao' in info:
                f.write(f"Aplicação: {info['aplicacao']}\n")

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
    """Obtém a lista de anos com dados disponíveis no servidor para um canal"""
    response = requests.get(url_canal)
    soup = BeautifulSoup(response.text, 'html.parser')

    anos = [link.get('href')[:-1] for link in soup.find_all('a')
            if link.get('href').startswith('2')]
    return sorted(anos)

def obter_dados_disponiveis(raiz_dado, tentativas=3, espera=5):
    """
    Obtém lista de dados disponíveis no servidor para uma pasta canal/ano/mês.
    Tenta novamente em caso de falha de conexão (rede instável, DNS, timeout).
    """
    response = None
    for tentativa in range(1, tentativas + 1):
        try:
            response = requests.get(raiz_dado, timeout=15)
            break
        except requests.exceptions.RequestException as e:
            if tentativa < tentativas:
                print(f"   ⚠️ Falha ao consultar o servidor (tentativa {tentativa}/{tentativas}): "
                      f"{type(e).__name__}. Tentando novamente em {espera}s...")
                time.sleep(espera)
            else:
                print(f"   ❌ Não foi possível consultar {raiz_dado} após {tentativas} tentativas.")
                return [], None, None

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

def mostrar_anos_disponiveis(sat, canal):
    """Mostra, apenas para referência, os anos com dados disponíveis no servidor para o canal"""
    url_canal = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/{canal}/'
    try:
        anos = obter_anos_disponiveis(url_canal)
        if anos:
            print(f"📅 Anos disponíveis no servidor para {canal}: {', '.join(anos)}")
        else:
            print(f"⚠️ Não foi possível listar os anos disponíveis para {canal}.")
    except Exception:
        print(f"⚠️ Não foi possível consultar os anos disponíveis para {canal} (prossiga normalmente).")

def obter_periodo(sat, canal):
    """
    Solicita ao usuário o período de download informando data e hora completas
    (início e fim). Como as duas datas carregam ano/mês/dia próprios, o período
    pode cruzar meses e anos sem exigir nada especial do usuário.
    """
    print('\n' + '='*50)
    print('DEFINIÇÃO DO PERÍODO DE DOWNLOAD')
    print('='*50)
    mostrar_anos_disponiveis(sat, canal)
    print('Formato: YYYYMMDDHH (ano, mês, dia e hora)')
    print('Exemplo: 2025013122  =  31/01/2025 às 22h\n')

    while True:
        try:
            dt_inicio = datetime.strptime(input('Data/hora de início (YYYYMMDDHH): ').strip(), '%Y%m%d%H')
            dt_fim = datetime.strptime(input('Data/hora de fim (YYYYMMDDHH): ').strip(), '%Y%m%d%H')

            if dt_fim < dt_inicio:
                print('\n❌ A data de fim deve ser igual ou posterior à data de início. Tente novamente.\n')
                continue

            passo = int(input('Passo de tempo em minutos: ').strip())
            if passo <= 0:
                print('\n❌ O passo deve ser maior que zero. Tente novamente.\n')
                continue

            return dt_inicio, dt_fim, passo
        except ValueError:
            print('\n❌ Data/hora ou passo em formato inválido! Use YYYYMMDDHH (ex: 2025013122). Tente novamente.\n')

# ============================================================================
# TIMESTAMPS E AGRUPAMENTO POR MÊS
# ============================================================================

def gerar_timestamps(dt_inicio, dt_fim, passo):
    """Gera a lista de timestamps (YYYYMMDDHHMM) entre duas datas, podendo cruzar meses/anos"""
    timestamps = []
    atual = dt_inicio
    while atual <= dt_fim:
        timestamps.append(atual.strftime('%Y%m%d%H%M'))
        atual += timedelta(minutes=passo)
    return timestamps

def agrupar_por_mes(timestamps):
    """Agrupa timestamps por (ano, mes), já que o servidor organiza os dados nessas pastas"""
    grupos = {}
    for ts in timestamps:
        chave = (ts[:4], ts[4:6])
        grupos.setdefault(chave, []).append(ts)
    return grupos

# ============================================================================
# FUNÇÕES DE DOWNLOAD (SUPORTAM PERÍODOS COM VÁRIOS MESES/ANOS)
# ============================================================================

def verificar_disponibilidade(sat, canal, timestamps):
    """
    Verifica quais timestamps existem no servidor para um canal, consultando
    a pasta ano/mês correspondente a cada grupo de timestamps separadamente.
    Retorna a lista de timestamps disponíveis e um dicionário
    {(ano, mes): (url_canal, prefixo, sufixo)} usado depois para o download.
    """
    grupos = agrupar_por_mes(timestamps)
    disponiveis = []
    info_por_mes = {}

    for (ano, mes), ts_grupo in sorted(grupos.items()):
        url_canal = f'https://ftp1.cptec.inpe.br/goes/{sat}/retangular/{canal}/{ano}/{mes}/'
        dados_disponiveis, prefixo, sufixo = obter_dados_disponiveis(url_canal)

        if not prefixo:
            print(f"   ⚠️ {canal}: nenhum dado encontrado em {ano}/{mes}")
            continue

        info_por_mes[(ano, mes)] = (url_canal, prefixo, sufixo)
        disponiveis.extend(ts for ts in ts_grupo if ts in dados_disponiveis)

    return sorted(disponiveis), info_por_mes

def baixar_timestamps_canal(canal, timestamps, info_por_mes, dir_canal):
    """Baixa os arquivos de um canal para os timestamps informados (já filtrados como disponíveis)"""
    baixados = 0
    for ts in timestamps:
        chave = (ts[:4], ts[4:6])
        if chave not in info_por_mes:
            continue

        url_canal, prefixo, sufixo = info_por_mes[chave]
        arquivo_local = os.path.join(dir_canal, f"{prefixo}{ts}{sufixo}")

        if os.path.exists(arquivo_local):
            print(f"   ⏭️  {ts} - já existe")
            baixados += 1
            continue

        url = f"{url_canal}{prefixo}{ts}{sufixo}"
        try:
            print(f"   📥 {ts} - baixando...", end=" ")
            wget.download(url, arquivo_local, bar=None)
            print("✅")
            baixados += 1
        except Exception as e:
            print(f"❌ Erro: {str(e)[:40]}")

    return baixados

def baixar_canal(sat, canal, timestamps, dir_canal):
    """Verifica a existência e baixa um canal para a lista de timestamps informada"""
    disponiveis, info_por_mes = verificar_disponibilidade(sat, canal, timestamps)
    disponiveis_set = set(disponiveis)

    print('\n🔍 Verificando existência das datas escolhidas...\n')
    for ts in timestamps:
        if ts in disponiveis_set:
            print(f'✅ O dado {ts} existe.')
        else:
            print(f'❌ O dado {ts} NÃO existe. Pulando...')

    baixados = baixar_timestamps_canal(canal, [ts for ts in timestamps if ts in disponiveis_set],
                                        info_por_mes, dir_canal)
    print(f'\n📊 Resumo: {baixados}/{len(timestamps)} arquivos baixados')
    return baixados

# ============================================================================
# PRODUTOS COMPOSTOS (TRUE COLOR, SWD, CPD, WVD)
# ============================================================================

PRODUTOS_COMPOSTOS = {
    'True_Color': {
        'canais': ['ch01', 'ch02', 'ch03'],
        'nome_canais': {
            'ch01': 'Vermelho (0.64µm)',
            'ch02': 'Verde (0.86µm)',
            'ch03': 'Azul (0.47µm)',
        },
        'titulo': 'TRUE COLOR',
        'emoji': '🎨',
    },
    'AirMass': {
        'canais': ['ch08', 'ch10', 'ch12', 'ch13'],
        'nome_canais': {
            'ch08': "WV 6.2µm - Vapor d'Água de Alto Nível",
            'ch10': "WV 7.3µm - Vapor d'Água de Baixo Nível",
            'ch12': 'IR 9.6µm - Canal de Ozônio',
            'ch13': 'IR 10.3µm - Canal de Janela Limpa',
        },
        'titulo': 'AIRMASS RGB',
        'formula': 'Red=CH08-CH10 (-26.2/0.6C) | Green=CH12-CH13 (-43.2/6.7C) | Blue=CH08 invertido (-29.25/-64.65C)',
        'aplicacao': 'Monitoramento de ciclogênese, jatos e anomalias de vorticidade potencial (PV) - fonte: QuickGuide_GOESR_AirMassRGB_final.pdf (NASA SPoRT)',
        'emoji': '🌪️',
    },
    'SWD': {
        'canais': ['ch13', 'ch15'],
        'nome_canais': {
            'ch13': 'IR 10.3µm - Canal Clean Window',
            'ch15': 'IR 12.3µm - Canal Dirty Window',
        },
        'titulo': 'SWD (SPLIT WINDOW DIFFERENCE)',
        'formula': 'SWD = CH13 - CH15',
        'aplicacao': 'Detecção de nuvens baixas, fogo e neblina',
        'emoji': '🌡️',
    },
    'CPD': {
        'canais': ['ch11', 'ch14'],
        'nome_canais': {
            'ch11': 'IR 8.5µm - Canal de Absorção de Gelo',
            'ch14': 'IR 11.2µm - Canal de Janela',
        },
        'titulo': 'CPD (CLOUD PHASE DIFFERENCE)',
        'formula': 'CPD = CH14 - CH11',
        'aplicacao': 'Detecção de fase de nuvens (gelo/água)',
        'emoji': '☁️',
    },
    'WVD': {
        'canais': ['ch08', 'ch13'],
        'nome_canais': {
            'ch08': "WV 6.2µm - Canal de Vapor d'Água (alta troposfera)",
            'ch13': 'IR 10.3µm - Canal de Janela',
        },
        'titulo': 'WVD (WATER VAPOR DIFFERENCE)',
        'formula': 'WVD = CH08 - CH13',
        'aplicacao': "Detecção de vapor d'água e umidade na alta troposfera",
        'emoji': '💧',
    },
    'SOD': {
        'canais': ['ch12', 'ch13'],
        'nome_canais': {
            'ch12': 'IR 9.6µm - Canal de Ozônio',
            'ch13': 'IR 10.3µm - Canal de Janela Limpa',
        },
        'titulo': 'SPLIT OZONE DIFFERENCE',
        'formula': 'SOD = CH12 - CH13',
        'aplicacao': 'Influência do ozônio estratosférico; componente verde do Airmass RGB',
        'emoji': '🌀',
    },
    'SWVD': {
        'canais': ['ch08', 'ch10'],
        'nome_canais': {
            'ch08': "WV 6.2µm - Vapor d'Água de Alto Nível",
            'ch10': "WV 7.3µm - Vapor d'Água de Baixo Nível",
        },
        'titulo': 'SPLIT WATER VAPOR DIFFERENCE (SWVD)',
        'formula': 'SWVD = CH08 - CH10',
        'aplicacao': "Detecção de cirros finos e umidade em níveis médios/altos; componente vermelho do Airmass RGB",
        'emoji': '💦',
    },
}

# Nomes canônicos dos produtos aceitos pelo sistema (Single_Band + as chaves de PRODUTOS_COMPOSTOS)
PRODUTOS_VALIDOS = ['Single_Band'] + list(PRODUTOS_COMPOSTOS.keys())

def normalizar_produto(prod_input):
    """
    Aceita o nome do produto digitado em qualquer capitalização (ex: 'true_color',
    'TRUE_COLOR', 'True_color') e devolve a forma canônica (ex: 'True_Color').
    Retorna None se o produto não existir.
    """
    mapa = {p.lower(): p for p in PRODUTOS_VALIDOS}
    return mapa.get(str(prod_input).strip().lower())

def baixar_composicao(sat, prod_select, dt_inicio, dt_fim, passo, dir_fig):
    """
    Baixa os canais necessários para um produto composto (True_Color, SWD, CPD ou WVD),
    garantindo que os MESMOS timestamps sejam baixados em todos os canais.
    Suporta períodos que cruzam meses e/ou anos.
    """
    info = PRODUTOS_COMPOSTOS[prod_select]
    canais = info['canais']

    print(f"\n{'='*60}")
    print(f"{info['emoji']} DOWNLOAD {info['titulo']}")
    print(f"{'='*60}")
    for canal in canais:
        print(f"   📍 {canal.upper()} - {info['nome_canais'][canal]}")
    if 'formula' in info:
        print(f"   📊 {info['formula']}")
    if 'aplicacao' in info:
        print(f"   💡 Aplicação: {info['aplicacao']}")
    print(f"{'='*60}\n")

    timestamps = gerar_timestamps(dt_inicio, dt_fim, passo)
    print(f"📅 Período: {dt_inicio.strftime('%Y-%m-%d %H:%M')} a {dt_fim.strftime('%Y-%m-%d %H:%M')} | Passo: {passo}min")
    print(f"📊 Total de timestamps: {len(timestamps)}\n")

    print("🔍 Verificando disponibilidade...")
    disponibilidade = {}
    info_por_mes_canal = {}
    for canal in canais:
        disp, info_por_mes = verificar_disponibilidade(sat, canal, timestamps)
        disponibilidade[canal] = set(disp)
        info_por_mes_canal[canal] = info_por_mes
        print(f"   {canal}: {len(disp)}/{len(timestamps)} disponíveis")

    timestamps_comuns = sorted(set.intersection(*disponibilidade.values()))
    print(f"\n✨ Timestamps comuns aos {len(canais)} canais: {len(timestamps_comuns)}")

    if not timestamps_comuns:
        print("\n❌ ERRO: Nenhum timestamp comum encontrado!")
        return None

    dir_base = os.path.join(dir_fig, f"{sat}_{prod_select}_{dt_inicio.strftime('%Y%m%d')}_{dt_fim.strftime('%Y%m%d')}")
    os.makedirs(dir_base, exist_ok=True)

    salvar_metadados(dir_base, sat, prod_select,
                     inicio_str=dt_inicio.strftime('%Y%m%d%H%M'), fim_str=dt_fim.strftime('%Y%m%d%H%M'),
                     passo=passo, timestamps=timestamps_comuns)

    arquivo_timestamps = os.path.join(dir_base, "timestamps_comuns.txt")
    with open(arquivo_timestamps, 'w') as f:
        f.write("\n".join(timestamps_comuns))

    print("\n⬇️ INICIANDO DOWNLOAD...\n")
    resultados = {}

    for canal in canais:
        print(f"\n📡 Canal {canal.upper()}:")
        dir_canal = os.path.join(dir_base, canal)
        os.makedirs(dir_canal, exist_ok=True)

        baixados = baixar_timestamps_canal(canal, timestamps_comuns, info_por_mes_canal[canal], dir_canal)
        resultados[canal] = {'baixados': baixados, 'total': len(timestamps_comuns)}
        print(f"   📊 Resumo: {baixados}/{len(timestamps_comuns)}")

    print(f"\n{'='*60}")
    print(f"📊 RESUMO {info['titulo']}")
    print(f"{'='*60}")
    for canal, res in resultados.items():
        status = "✅" if res['baixados'] == res['total'] else "⚠️"
        print(f"{status} {canal}: {res['baixados']}/{res['total']}")

    print(f"\n📁 Pasta: {dir_base}")
    print(f"📄 Metadados: {os.path.join(dir_base, 'metadados.txt')}")

    if all(res['baixados'] == res['total'] for res in resultados.values()):
        print(f"\n🎉 {info['titulo']} COMPLETO!")
        if 'formula' in info:
            print(f"📐 Fórmula: {info['formula']}")
        if 'aplicacao' in info:
            print(f"💡 Aplicação: {info['aplicacao']}")
    else:
        print(f"\n⚠️ {info['titulo']} incompleto - alguns timestamps faltando")

    print(f"{'='*60}\n")

    return resultados, timestamps_comuns

# ============================================================================
# CANAL ÚNICO (SIMPLE CHANNEL)
# ============================================================================

def baixar_canal_simples(sat, canal, dt_inicio, dt_fim, passo, dir_fig):
    """Baixa um canal único do GOES para o período informado (pode cruzar meses/anos)"""
    timestamps = gerar_timestamps(dt_inicio, dt_fim, passo)

    dir_data = os.path.join(dir_fig, f"{sat}_{dt_inicio.strftime('%Y%m%d')}_{dt_fim.strftime('%Y%m%d')}")
    dir_canal = os.path.join(dir_data, canal)
    os.makedirs(dir_canal, exist_ok=True)

    salvar_metadados(dir_data, sat, 'Single_Band', canal=canal,
                     inicio_str=dt_inicio.strftime('%Y%m%d%H%M'), fim_str=dt_fim.strftime('%Y%m%d%H%M'),
                     passo=passo, timestamps=timestamps)

    print(f"\n📊 RESUMO: Satélite {sat.upper()} | Canal {canal} | "
          f"{dt_inicio.strftime('%Y-%m-%d %H:%M')} a {dt_fim.strftime('%Y-%m-%d %H:%M')} | Passo: {passo}min\n")

    baixar_canal(sat, canal, timestamps, dir_canal)

# ============================================================================
# FUNÇÃO PRINCIPAL EXPORTADA
# ============================================================================

def select_prod(sat, prod_select):
    """
    Função principal que orquestra todo o processo de download
    Parâmetros:
        sat: str - 'goes16' ou 'goes19'
        prod_select: str - 'Single_Band', 'True_Color', 'SWD', 'CPD' ou 'WVD'
                     (aceito em qualquer capitalização, é normalizado internamente)
    """
    prod_select = normalizar_produto(prod_select)
    if prod_select is None:
        print(f"❌ Produto inválido!")
        print(f"   Opções válidas: {', '.join(PRODUTOS_VALIDOS)}")
        return False

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

    if prod_select in PRODUTOS_COMPOSTOS:
        canal_referencia = PRODUTOS_COMPOSTOS[prod_select]['canais'][0]
        dt_inicio, dt_fim, passo = obter_periodo(sat, canal_referencia)
        baixar_composicao(sat, prod_select, dt_inicio, dt_fim, passo, dir_fig)

    elif prod_select == 'Single_Band':
        canais, _ = obter_canais_disponiveis(sat)
        canal = selecionar_canal(canais)
        dt_inicio, dt_fim, passo = obter_periodo(sat, canal)
        baixar_canal_simples(sat, canal, dt_inicio, dt_fim, passo, dir_fig)

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
    prod = input(f"Digite o produto ({', '.join(PRODUTOS_VALIDOS)}): ")

    select_prod(sat, prod)
