"""
produto_plot.py - Módulo para plotagem de imagens GOES
Autor: Victor Ranieri e DeepSeek
Descrição: Funções para plotar canais individuais, composições True Color, SWD e CPD
"""

import os
import numpy as np
import xarray as xr
import matplotlib
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import warnings
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Patch

# Configuração inicial
matplotlib.use('Agg')
warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

DIRSCRIPT = os.getcwd()
DIRSHAPE = os.path.join(DIRSCRIPT, 'shapefile')
DIRFIG = os.path.join(DIRSCRIPT, 'fig_dados')
SHAPEFILE_PATH = os.path.join(DIRSHAPE, 'BR_UF_2019.shp')

# ============================================================================
# COLORMAPS PERSONALIZADOS
# ============================================================================

def get_colormap(canal, usar_noaa=False):
    """
    Retorna o colormap apropriado para cada canal
    
    Parâmetros:
        canal: str - nome do canal
        usar_noaa: bool - Força uso da paleta NOAA para ch13
    """
    # Colormap NOAA para ch13 (opcional)
    cmap_noaa = LinearSegmentedColormap.from_list('noaa', (
        (0.000, (0.961, 0.961, 0.961)),  # Branco
        (0.068, (0.961, 0.961, 0.961)),
        (0.070, (0.541, 0.043, 0.522)),  # Roxo
        (0.110, (0.820, 0.820, 0.820)),  # Cinza claro
        (0.150, (0.012, 0.012, 0.012)),  # Preto
        (0.190, (0.957, 0.024, 0.000)),  # Vermelho
        (0.220, (0.937, 1.000, 0.000)),  # Amarelo
        (0.280, (0.016, 0.957, 0.000)),  # Verde
        (0.300, (0.000, 0.341, 0.298)),
        (0.300, (0.000, 0.161, 0.380)),
        (0.399, (0.200, 1.000, 1.000)),  # Ciano
        (0.400, (1.000, 1.000, 1.000)),  # Branco
        (1.000, (0.000, 0.000, 0.000))   # Preto
    ))
    
    # Colormap em escala de cinza
    cmap_gray = plt.cm.gray
    cmap_gray_r = plt.cm.gray_r
    
    # Colormap para canais de vapor d'água
    cmap_water_vapor = plt.cm.OrRd
    
    # Colormap para diferenças (SWD e CPD)
    cmap_diff = 'Spectral'
    cmap_cpd = 'jet'
    cmap_wvd = 'nipy_spectral'

    
    # Definição por canal
    canais_infravermelho = ['ch07', 'ch13','ch11', 'ch12', 'ch14', 'ch15', 'ch16']
    canais_visiveis = ['ch01', 'ch02']
    canais_vapor = ['ch08', 'ch09', 'ch10']
    canais_nir = ['ch03', 'ch04', 'ch05', 'ch06']
    
    if canal in canais_infravermelho:
        if canal == 'ch13' and usar_noaa:
            # Paleta NOAA tem os estágios de cor calibrados para essa faixa
            # específica - usar -80/60 (igual ao cinza padrão) satura a imagem.
            return cmap_noaa, -100, 100, "Brightness Temperature (C)"
        else:
            return cmap_gray_r, -80, 60, "Brightness Temperature (C)"
    elif canal in canais_visiveis:
        return cmap_gray, 0, 100, "Reflectance (%)"
    elif canal in canais_nir:
        return cmap_gray,  0, 100, "Reflectance (%)"
    elif canal in canais_vapor:
        return cmap_water_vapor, -80, 0, "Brightness Temperature (C)"
    elif canal == 'swd':
        return cmap_diff, -6, 6, "SWD (K)"
    elif canal == 'cpd':
        return cmap_cpd, -12, 4, "CPD (K)"
    elif canal == 'wvd':
        return cmap_wvd, -2.5, 2.5, "WVD (K)"
    elif canal == 'sod':
        # Faixa aproximada: o guia (ABIQuickGuide_SplitOzoneDiff.pdf) não informa
        # valores numéricos, só descreve qualitativamente (nuvens altas ~0/positivo,
        # céu claro bem negativo). Ajustar se surgir uma referência com stops oficiais.
        return 'RdBu_r', -30, 10, "SOD (K)"
    elif canal == 'swvd':
        return 'nipy_spectral', -30, 5, "SWVD (K)"
    else:
        return cmap_gray_r, -40, 80, "Brightness Temperature (C)"

# ============================================================================
# FUNÇÕES AUXILIARES DE DETECÇÃO
# ============================================================================

def extrair_satelite_do_nome(nome_pasta):
    """
    Extrai o satélite do nome da pasta
    """
    partes = nome_pasta.split('_')
    if partes and partes[0].startswith('goes'):
        return partes[0].lower()
    return None

def ler_metadados_satelite(caminho_caso):
    """
    Tenta ler o satélite do arquivo de metadados
    """
    metadata_file = os.path.join(caminho_caso, 'metadados.txt')
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                for linha in f:
                    if 'Satélite:' in linha:
                        sat = linha.split(':')[1].strip().lower()
                        return sat
        except:
            pass
    return None

def detectar_satelite(caminho_caso, nome_pasta):
    """
    Detecta o satélite automaticamente
    """
    sat = ler_metadados_satelite(caminho_caso)
    if sat:
        print(f"   Satélite detectado pelo metadado: {sat.upper()}")
        return sat
    
    sat = extrair_satelite_do_nome(nome_pasta)
    if sat:
        print(f"   Satélite detectado pelo nome da pasta: {sat.upper()}")
        return sat
    
    print(f"   ATENCAO: Nao foi possivel detectar o satelite!")
    return None

def detectar_canais_disponiveis(caminho_caso):
    """
    Detecta automaticamente quais canais estão disponíveis
    """
    if not os.path.exists(caminho_caso):
        return []
    
    canais = []
    for item in os.listdir(caminho_caso):
        item_path = os.path.join(caminho_caso, item)
        if os.path.isdir(item_path) and item.startswith('ch'):
            canais.append(item)
    
    return sorted(canais)

# ============================================================================
# FUNÇÕES DE INTERAÇÃO COM USUÁRIO
# ============================================================================

def listar_casos_disponiveis():
    """Lista todos os casos disponíveis para plotagem"""
    if not os.path.exists(DIRFIG):
        print(f"ERRO: Diretorio {DIRFIG} nao encontrado!")
        return []
    
    casos = [d for d in os.listdir(DIRFIG) if os.path.isdir(os.path.join(DIRFIG, d))]
    
    if not casos:
        print("ERRO: Nenhum caso encontrado no diretorio de figuras.")
    else:
        print("\nCasos disponiveis:")
        for i, caso in enumerate(casos, 1):
            caminho_caso = os.path.join(DIRFIG, caso)
            sat = detectar_satelite(caminho_caso, caso)

            # Detecta TODOS os produtos possíveis para o caso (pode ser mais de um)
            produtos = detectar_produtos_disponiveis(caminho_caso)
            tipo = ', '.join(produtos) if produtos else "Canal(ais) individual(is)"
            
            if sat:
                print(f"   {i}. {caso} [{sat.upper()}] - {tipo}")
            else:
                print(f"   {i}. {caso} - {tipo}")
    
    return casos

def selecionar_caso(casos):
    """Permite ao usuário selecionar um caso"""
    if not casos:
        return None
    
    try:
        escolha = input('\nEscolha o caso (nome ou numero): ').strip()
        
        if escolha.isdigit():
            idx = int(escolha) - 1
            if 0 <= idx < len(casos):
                return casos[idx]
        
        if escolha in casos:
            return escolha
        
        print(f"ERRO: Caso '{escolha}' nao encontrado!")
        return None
    except:
        return None

def obter_extent_usuario():
    """Solicita ao usuário os limites de longitude e latitude"""
    print("\n" + "="*50)
    print("DEFINICAO DA AREA DE PLOTAGEM")
    print("="*50)
    print("Limites maximos: -115 (oeste) a -25 (leste) e -55 (sul) a 34 (norte)")
    
    try:
        lon_min = float(input("Longitude minima (Oeste, ex: -85): "))
        lon_max = float(input("Longitude maxima (Leste, ex: -30): "))
        lat_min = float(input("Latitude minima (Sul, ex: -40): "))
        lat_max = float(input("Latitude maxima (Norte, ex: 10): "))
        
        print(f"\nArea selecionada: Lon[{lon_min} a {lon_max}] | Lat[{lat_min} a {lat_max}]")
        return [lon_min, lon_max, lat_min, lat_max]
    except:
        print("ERRO: Valores invalidos! Usando area padrao.")
        return None

def obter_titulo_usuario():
    """Solicita ao usuário o título do gráfico"""
    print("\n" + "="*50)
    print("DEFINICAO DO TITULO")
    print("="*50)
    print('Evite acentuacao e espacos para melhor compatibilidade.')
    titulo = input("Digite o titulo (ou Enter para padrao): ").strip()
    return titulo if titulo else None

def obter_colormap_usuario():
    """
    Solicita ao usuário um colormap personalizado
    """
    print("Aceita colormaps matplotlib")
    
    while True:
        opcao = input("\nDeseja usar colormap personalizado? (s/n): ").strip().lower()
        
        if opcao == 's':
            cmap = input("Digite o nome do colormap: ").strip()
            print(f"   Usando colormap: {cmap}")
            return cmap
        elif opcao == 'n':
            print("   Usando colormap padrao do produto")
            return None
        else:
            print("   Opcao invalida! Digite 's' para sim ou 'n' para nao.")

# ============================================================================
# FUNÇÕES DE PLOTAGEM
# ============================================================================

def plot_simple_channel(caso, canal, sat, extent=None, titulo_personalizado=None, cmap=None, usar_noaa_ch13=False):
    """
    Plota um canal individual do GOES
    """
    
    # Configurações iniciais
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_canal = os.path.join(caminho_caso, canal)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)
    
    if not os.path.exists(caminho_canal):
        print(f"ERRO: Canal {canal} nao encontrado em {caminho_caso}")
        return
    
    # Classificação dos canais
    canais_visiveis = ['ch01', 'ch02']
    canais_nir = ['ch03', 'ch04', 'ch05', 'ch06']
    canais_vapor = ['ch08', 'ch09', 'ch10']
    canais_ir = ['ch07', 'ch11', 'ch12', 'ch13', 'ch14', 'ch15', 'ch16']
    
    # Configurações por tipo
    if canal in canais_visiveis:
        tipo_canal = 'visivel'
        cmap_padrao = 'Greys_r'
        vmin, vmax = 0, 100
        label = 'Reflectancia (%)'
        converte_celsius = False
    elif canal in canais_vapor:
        tipo_canal = 'water_vapor'
        cmap_padrao = 'Greys'
        vmin, vmax = -80, 0
        label = 'Brightness Temperature (C)'
        converte_celsius = True
    elif canal in canais_nir:
        tipo_canal = 'nir'
        cmap_padrao = 'Greys_r'
        vmin, vmax = 0, 100
        label = 'Reflectancia (%)'
        converte_celsius = False
    elif canal in canais_ir:
        tipo_canal = 'ir'
        cmap_padrao, vmin, vmax, label = get_colormap(canal, usar_noaa=usar_noaa_ch13)
        converte_celsius = True
    else:
        tipo_canal = 'outro'
        cmap_padrao = 'Greys'
        vmin, vmax = -100, 100
        label = 'Dados'
        converte_celsius = False
    
    cmap_uso = cmap if cmap else cmap_padrao
    
    # Listar arquivos
    arquivos = sorted([f for f in os.listdir(caminho_canal) if f.endswith('.nc')])
    
    if not arquivos:
        print(f"ERRO: Nenhum arquivo NetCDF encontrado em {caminho_canal}")
        return
    
    print(f"\nPlotando {len(arquivos)} imagens do canal {canal}...")
    print(f"Satelite: {sat.upper()}")
    print(f"Tipo: {tipo_canal.upper()}")
    
    # Loop de plotagem
    for i, arquivo in enumerate(arquivos, 1):
        try:
            arq = xr.open_dataset(os.path.join(caminho_canal, arquivo), engine='netcdf4')
            data_str = arquivo.split('_')[1][:12]
            print(f"   [{i}/{len(arquivos)}] Processando: {data_str}")
            
            dados = arq.Band1
            
            # Conversão
            if converte_celsius:
                dados.data = dados.data / 100 - 273.15
            else:
                dados.data = dados.data / 100
                dados.data = np.clip(dados.data, 0, 100)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Features
            ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color='gold', zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.6, color='gold', zorder=301)
            
            # Shapefile
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(), 
                                 edgecolor='gold', facecolor='none', linewidth=0.6)
            
            # Plot
            ticks = np.arange(0, 101, 20) if tipo_canal in ['visivel', 'nir'] else np.arange(vmin, vmax+1, 20)

            dados.plot(ax=ax, cmap=cmap_uso, transform=ccrs.PlateCarree(),
                      vmin=vmin, vmax=vmax,
                      cbar_kwargs={"label": label, "orientation": "vertical",
                                  "pad": 0.05, "aspect": 20, "shrink": 0.8, "ticks": ticks}, extend='neither')
            
            # Extent
            if extent:
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent([-115, -25, -55, 34], crs=ccrs.PlateCarree())
            
            # Gridlines
            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'fontsize': 14}
            gl.ylabel_style = {'fontsize': 14}
            
            # Título
            tipo_str = {'visivel': 'VIS', 'water_vapor': 'WV', 'ir': 'IR', 'nir': 'NIR'}.get(tipo_canal, canal.upper())
            sufixo_noaa = '_noaa' if (canal == 'ch13' and usar_noaa_ch13) else ''
            tipo_str_titulo = f"{tipo_str} NOAA" if sufixo_noaa else tipo_str

            if titulo_personalizado:
                titulo = f"{data_str} UTC\n{titulo_personalizado} | {sat.upper()} | {canal.upper()} ({tipo_str_titulo})"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{canal}{sufixo_noaa}_{data_str}.png"
            else:
                titulo = f"{data_str} UTC\n{sat.upper()} | {canal.upper()} ({tipo_str_titulo})"
                nome_arquivo = f"{sat.upper()}_{canal}{sufixo_noaa}_{data_str}.png"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=300, bbox_inches='tight')
            plt.close(fig)
            arq.close()
            
        except Exception as e:
            print(f"   ERRO ao processar {arquivo}: {e}")
    
    print(f"Plotagem do canal {canal} concluida!")

def plot_true_color(caso, sat, extent=None, titulo_personalizado=None):
    """
    Plota composição True Color (canais 1, 2, 3)
    """
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)
    
    ch01_path = os.path.join(caminho_caso, 'ch01')
    ch02_path = os.path.join(caminho_caso, 'ch02')
    ch03_path = os.path.join(caminho_caso, 'ch03')
    
    if not all(os.path.exists(p) for p in [ch01_path, ch02_path, ch03_path]):
        print(f"ERRO: Canais 1,2,3 nao encontrados em {caminho_caso}")
        return
    
    ch01_files = sorted(os.listdir(ch01_path))
    ch02_files = sorted(os.listdir(ch02_path))
    ch03_files = sorted(os.listdir(ch03_path))
    
    if not ch01_files:
        print(f"ERRO: Nenhum arquivo encontrado")
        return
    
    print(f"\nPlotando {len(ch01_files)} imagens True Color...")
    print(f"Satelite: {sat.upper()}")
    
    for i, (f1, f2, f3) in enumerate(zip(ch01_files, ch02_files, ch03_files), 1):
        try:
            data_str = f1.split('_')[1][:12]
            print(f"   [{i}/{len(ch01_files)}] Processando: {data_str}")
            
            arq1 = xr.open_dataset(os.path.join(ch01_path, f1))
            arq2 = xr.open_dataset(os.path.join(ch02_path, f2))
            arq3 = xr.open_dataset(os.path.join(ch03_path, f3))
            
            # Processar ch01
            ch01 = arq1.Band1
            if sat == 'goes19':
                ch01 = ch01.isel(lat=slice(0, -1), lon=slice(0, -1))
                ch01 = ch01.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch01.data = ch01.data / 100
            else:
                ch01 = ch01.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch01.data = ch01.data / 100
            ch01 = ch01.isel(lat=slice(None, None, -1))
            
            # Processar ch02
            ch02 = arq2.Band1
            ch02 = ch02.coarsen(lat=2, lon=2, boundary='trim').mean()
            ch02.data = ch02.data / 100
            ch02 = ch02.isel(lat=slice(None, None, -1))
            
            # Processar ch03
            ch03 = arq3.Band1
            if sat == 'goes19':
                ch03 = ch03.isel(lat=slice(0, -1), lon=slice(0, -1))
                ch03 = ch03.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch03.data = ch03.data / 100
            else:
                ch03 = ch03.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch03.data = ch03.data / 100
            ch03 = ch03.isel(lat=slice(None, None, -1))
            
            # Composição RGB
            R = np.flipud(ch02.data)
            aux = 0.45 * ch02.data + 0.1 * ch03.data + 0.45 * ch01.data
            G = np.flipud(aux)
            B = np.flipud(ch01.data)
            
            # Normalização
            R = np.clip(R, 0, 100)
            G = np.clip(G, 0, 100)
            B = np.clip(B, 0, 100)
            
            R = R / 100
            G = G / 100
            B = B / 100
            
            # Correção gamma
            gamma = 2
            R = R ** (1/gamma)
            G = G ** (1/gamma)
            B = B ** (1/gamma)
            
            RGB = np.stack([R, G, B], axis=2)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
            ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color='gold')
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.6, color='gold')
            
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor='gold', facecolor='none', linewidth=0.6)
            
            ax.imshow(RGB[::-1], extent=[ch02.lon.min(), ch02.lon.max(),
                                          ch02.lat.min(), ch02.lat.max()],
                     transform=ccrs.PlateCarree())
            
            if extent:
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent([-115, -25, -55, 34], crs=ccrs.PlateCarree())
            
            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'fontsize': 14}
            gl.ylabel_style = {'fontsize': 14}
            
            if titulo_personalizado:
                titulo = f"{data_str} UTC\n{titulo_personalizado} | {sat.upper()} | True Color RGB"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{data_str}.png"
            else:
                titulo = f"{data_str} UTC\n{sat.upper()} | True Color RGB"
                nome_arquivo = f"{sat.upper()}_true_color_{data_str}.png"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            arq1.close()
            arq2.close()
            arq3.close()
            
        except Exception as e:
            print(f"   ERRO ao processar {data_str}: {e}")
    
    print(f"Plotagem True Color concluida!")

# ============================================================================
# AIRMASS RGB (ch08, ch10, ch12, ch13)
# ============================================================================

def plot_airmass(caso, sat, extent=None, titulo_personalizado=None):
    """
    Plota o produto Airmass RGB, usado para monitorar ciclogênese, jatos e
    anomalias de vorticidade potencial (PV).

    Red   = WV6.2 - WV7.3 (ch08 - ch10), faixa -26.2 a 0.6°C    [= mesmos canais do SWVD]
    Green = IR9.7 - IR10.8 (ch12 - ch13), faixa -43.2 a 6.7°C   [= mesmos canais do SOD]
    Blue  = WV6.2 (ch08) invertido, faixa -29.25 a -64.65°C
    Sem correção de gama.

    Fonte: QuickGuide_GOESR_AirMassRGB_final.pdf (NASA SPoRT, específico do GOES-R)
    """
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)

    canais = ['ch08', 'ch10', 'ch12', 'ch13']
    paths = {c: os.path.join(caminho_caso, c) for c in canais}

    if not all(os.path.exists(p) for p in paths.values()):
        print(f"ERRO: Canais ch08, ch10, ch12 e ch13 nao encontrados em {caminho_caso}")
        return

    arquivos = {c: sorted([f for f in os.listdir(paths[c]) if f.endswith('.nc')]) for c in canais}
    if not all(arquivos.values()):
        print(f"ERRO: Nenhum arquivo encontrado em um dos canais")
        return

    timestamps_por_canal = {c: set(f.split('_')[1][:12] for f in arquivos[c]) for c in canais}
    timestamps_comuns = sorted(set.intersection(*timestamps_por_canal.values()))

    if not timestamps_comuns:
        print("ERRO: Nenhum timestamp comum entre ch08, ch10, ch12 e ch13!")
        return

    print(f"\nPlotando {len(timestamps_comuns)} imagens Airmass RGB...")
    print(f"Satelite: {sat.upper()}")
    print("Red = ch08-ch10 (-26.2/0.6C) | Green = ch12-ch13 (-43.2/6.7C) | Blue = ch08 invertido (-29.25/-64.65C)")

    for i, ts in enumerate(timestamps_comuns, 1):
        try:
            arq_nome = {c: [f for f in arquivos[c] if ts in f][0] for c in canais}

            print(f"   [{i}/{len(timestamps_comuns)}] Processando: {ts}")

            ds = {c: xr.open_dataset(os.path.join(paths[c], arq_nome[c]), engine='netcdf4') for c in canais}

            c_temp = {c: ds[c].Band1.data / 100 - 273.15 for c in canais}

            red_raw = c_temp['ch08'] - c_temp['ch10']
            green_raw = c_temp['ch12'] - c_temp['ch13']
            blue_raw = c_temp['ch08']

            # Faixas oficiais: QuickGuide_GOESR_AirMassRGB_final.pdf (NASA SPoRT)
            R = np.clip((red_raw - (-26.2)) / (0.6 - (-26.2)), 0, 1)
            G = np.clip((green_raw - (-43.2)) / (6.7 - (-43.2)), 0, 1)
            B = np.clip((-29.25 - blue_raw) / (-29.25 - (-64.65)), 0, 1)

            RGB = np.stack([R, G, B], axis=2)

            lats = ds['ch08'].lat.data
            lons = ds['ch08'].lon.data

            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})

            ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color='gold', zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.6, color='gold', zorder=301)

            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor='gold', facecolor='none', linewidth=0.6)

            ax.imshow(RGB, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), origin='lower')

            if extent:
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent([-115, -25, -55, 34], crs=ccrs.PlateCarree())

            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'fontsize': 14}
            gl.ylabel_style = {'fontsize': 14}

            if titulo_personalizado:
                titulo = f"{ts} UTC\n{titulo_personalizado} | {sat.upper()} | Airmass RGB"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_airmass_{ts}.png"
            else:
                titulo = f"{ts} UTC\n{sat.upper()} | Airmass RGB"
                nome_arquivo = f"{sat.upper()}_airmass_{ts}.png"

            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)

            for c in canais:
                ds[c].close()

        except Exception as e:
            print(f"   ERRO ao processar {ts}: {e}")

    print(f"Plotagem Airmass RGB concluida!")

# ============================================================================
# PRODUTOS DE DIFERENÇA (SWD, CPD, WVD, SOD, SWVD)
# ============================================================================

DIFERENCA_INFO = {
    'swd': {
        'canal_a': 'ch13',
        'canal_b': 'ch15',
        'titulo': 'Split Window Difference (SWD)',
        'formula_texto': 'SWD = ch13 - ch15',
        'aplicacao': 'Deteccao de nuvens baixas, fogo e neblina',
        'cor_linha': 'black',
    },
    'cpd': {
        'canal_a': 'ch14',
        'canal_b': 'ch11',
        'titulo': 'Cloud Phase Difference (CPD)',
        'formula_texto': 'CPD = ch14 - ch11',
        'aplicacao': 'Deteccao de fase de nuvens (gelo/agua) - fonte: ABIQuickGuide_G16_CloudPhaseBTD.pdf',
        'cor_linha': 'black',
    },
    'wvd': {
        'canal_a': 'ch08',
        'canal_b': 'ch13',
        'titulo': 'Water Vapor - IR Difference (WVD)',
        'formula_texto': 'WVD = ch08 - ch13',
        'aplicacao': "Deteccao de overshooting top (topos convectivos que penetram a tropopausa)",
        'cor_linha': 'gold',
    },
    'sod': {
        'canal_a': 'ch12',
        'canal_b': 'ch13',
        'titulo': 'Split Ozone Difference (SOD)',
        'formula_texto': 'SOD = ch12 - ch13',
        'aplicacao': "Influencia do ozonio estratosferico; componente verde do Airmass RGB - fonte: ABIQuickGuide_SplitOzoneDiff.pdf",
        'cor_linha': 'black',
    },
    'swvd': {
        'canal_a': 'ch08',
        'canal_b': 'ch10',
        'titulo': 'Split Water Vapor Difference (SWVD)',
        'formula_texto': 'SWVD = ch08 - ch10',
        'aplicacao': "Deteccao de cirros finos e umidade em niveis medios/altos; componente vermelho do Airmass RGB - fonte: ABIQuickGuide_SplitWV_BTDiffv2.pdf",
        'cor_linha': 'black',
        'tick_step': 2,
    },
}

# Canais necessários por produto - usado pela detecção automática em 2.plot_sat.py.
# Derivado de DIFERENCA_INFO (fonte única) + True_Color/AirMass, que não são
# diferenças simples de 2 canais.
PRODUTOS_CANAIS = {
    'True_Color': ['ch01', 'ch02', 'ch03'],
    'AirMass': ['ch08', 'ch10', 'ch12', 'ch13'],
}
for _tipo, _info in DIFERENCA_INFO.items():
    PRODUTOS_CANAIS[_tipo.upper()] = [_info['canal_a'], _info['canal_b']]

def detectar_produtos_disponiveis(caminho_caso):
    """
    Retorna a lista de produtos (True_Color, AirMass, SWD, CPD, WVD, SOD, SWVD)
    cujos canais necessários estão TODOS presentes no caso - um caso pode
    satisfazer vários produtos ao mesmo tempo (ex: uma pasta com os 16 canais).
    A ordem segue PRODUTOS_CANAIS: produtos com mais canais (mais específicos)
    primeiro, para exibição mais intuitiva.
    """
    canais_disponiveis = set(detectar_canais_disponiveis(caminho_caso))
    produtos = [p for p, requeridos in PRODUTOS_CANAIS.items()
                if set(requeridos).issubset(canais_disponiveis)]
    return sorted(produtos, key=lambda p: -len(PRODUTOS_CANAIS[p]))

def plot_diferenca(caso, sat, tipo, extent=None, titulo_personalizado=None, cmap=None):
    """
    Plota um produto de diferença de temperatura de brilho entre dois canais.
    diff = canal_a - canal_b, conforme definido em DIFERENCA_INFO[tipo].
    Cobre SWD, CPD, WVD, Ozone e SWVD com a mesma lógica (evita duplicar
    a mesma sequência de codigo 5 vezes, que foi a causa do bug de sinal do CPD).
    """
    info = DIFERENCA_INFO[tipo]
    canal_a, canal_b = info['canal_a'], info['canal_b']

    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)

    path_a = os.path.join(caminho_caso, canal_a)
    path_b = os.path.join(caminho_caso, canal_b)

    if not all(os.path.exists(p) for p in [path_a, path_b]):
        print(f"ERRO: Canais {canal_a} e {canal_b} nao encontrados em {caminho_caso}")
        return

    files_a = sorted([f for f in os.listdir(path_a) if f.endswith('.nc')])
    files_b = sorted([f for f in os.listdir(path_b) if f.endswith('.nc')])

    if not files_a or not files_b:
        print(f"ERRO: Nenhum arquivo encontrado nos canais")
        return

    timestamps_a = [f.split('_')[1][:12] for f in files_a]
    timestamps_b = [f.split('_')[1][:12] for f in files_b]
    timestamps_comuns = sorted(set(timestamps_a) & set(timestamps_b))

    if not timestamps_comuns:
        print(f"ERRO: Nenhum timestamp comum entre {canal_a} e {canal_b}!")
        return

    print(f"\nPlotando {len(timestamps_comuns)} imagens {info['titulo']}...")
    print(f"Satelite: {sat.upper()}")
    print(f"Formula: {info['formula_texto']}")

    cmap_uso, vmin, vmax, label = get_colormap(tipo)
    if cmap:
        cmap_uso = cmap
    if 'tick_step' in info:
        ticks = np.arange(vmin, vmax + info['tick_step'], info['tick_step'])
    else:
        ticks = np.linspace(vmin, vmax, 9)
    cor_linha = info.get('cor_linha', 'gold')

    for i, ts in enumerate(timestamps_comuns, 1):
        try:
            arq_a_nome = [f for f in files_a if ts in f][0]
            arq_b_nome = [f for f in files_b if ts in f][0]

            print(f"   [{i}/{len(timestamps_comuns)}] Processando: {ts}")

            arq_a = xr.open_dataset(os.path.join(path_a, arq_a_nome), engine='netcdf4')
            arq_b = xr.open_dataset(os.path.join(path_b, arq_b_nome), engine='netcdf4')

            dados_a = arq_a.Band1.data / 100 - 273.15
            dados_b = arq_b.Band1.data / 100 - 273.15

            diff = dados_a - dados_b
            diff = np.where(np.abs(diff) > 50, np.nan, diff)

            lats = arq_a.lat.data
            lons = arq_a.lon.data

            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})

            ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color=cor_linha, zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.6, color=cor_linha, zorder=301)

            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor=cor_linha, facecolor='none', linewidth=0.6)

            im = ax.imshow(diff, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                          transform=ccrs.PlateCarree(), cmap=cmap_uso,
                          vmin=vmin, vmax=vmax, origin='lower')

            cbar = plt.colorbar(im, ax=ax, orientation='vertical',
                               pad=0.05, aspect=20, shrink=0.8,
                               extend='both', ticks=ticks)
            cbar.set_label(label, fontsize=12)
            cbar.ax.tick_params(labelsize=10)

            if extent:
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent([-115, -25, -55, 34], crs=ccrs.PlateCarree())

            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'fontsize': 14}
            gl.ylabel_style = {'fontsize': 14}

            if titulo_personalizado:
                titulo = f"{ts} UTC\n{titulo_personalizado} | {sat.upper()} | {tipo.upper()}"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{tipo}_{ts}.png"
            else:
                titulo = f"{ts} UTC\n{sat.upper()} | {info['titulo']}"
                nome_arquivo = f"{sat.upper()}_{tipo}_{ts}.png"

            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)

            arq_a.close()
            arq_b.close()

        except Exception as e:
            print(f"   ERRO ao processar {ts}: {e}")

    print(f"Plotagem {info['titulo']} concluida!")

# ============================================================================
# WVD COMO DESTAQUE DE OVERSHOOTING TOP (fundo IR + máscara acima do limiar)
# ============================================================================

def plot_wvd_overshooting(caso, sat, extent=None, titulo_personalizado=None, limiar=3.0):
    """
    Plota o WVD (Water Vapor - IR Difference, ch08 - ch13) como destaque de
    overshooting top: fundo em tons de cinza do canal IR (ch13) e realce colorido
    apenas onde BTD > limiar (K).

    Por que não como campo contínuo? O ATBD oficial (ABIQuickGuide_OvershootingTop_
    ATBD.pdf, "Overshooting Top and Enhanced-V Detection") mostra que um limiar de
    +2K já identifica boa parte da bigorna convectiva inteira como "overshooting"
    (não só o topo de fato) e testa entre 2K e 4K; nenhum limiar único é perfeito.
    Colorir o campo contínuo nessa faixa estreita satura em branco/preto em
    qualquer cena com convecção profunda espalhada. A técnica operacional é essa
    máscara: destaca só os pixels acima do limiar sobre um fundo IR de referência.
    """
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)

    ch08_path = os.path.join(caminho_caso, 'ch08')
    ch13_path = os.path.join(caminho_caso, 'ch13')

    if not all(os.path.exists(p) for p in [ch08_path, ch13_path]):
        print(f"ERRO: Canais 8 e 13 nao encontrados em {caminho_caso}")
        return

    ch08_files = sorted([f for f in os.listdir(ch08_path) if f.endswith('.nc')])
    ch13_files = sorted([f for f in os.listdir(ch13_path) if f.endswith('.nc')])

    if not ch08_files or not ch13_files:
        print(f"ERRO: Nenhum arquivo encontrado nos canais")
        return

    timestamps_ch08 = [f.split('_')[1][:12] for f in ch08_files]
    timestamps_ch13 = [f.split('_')[1][:12] for f in ch13_files]
    timestamps_comuns = sorted(set(timestamps_ch08) & set(timestamps_ch13))

    if not timestamps_comuns:
        print("ERRO: Nenhum timestamp comum entre ch08 e ch13!")
        return

    print(f"\nPlotando {len(timestamps_comuns)} imagens WVD (destaque de overshooting top)...")
    print(f"Satelite: {sat.upper()}")
    print(f"Formula: WVD = ch08 - ch13 | Limiar de destaque: {limiar}K")
    print(f"Fonte do limiar: ABIQuickGuide_OvershootingTop_ATBD.pdf (testado entre 2K e 4K)")

    for i, ts in enumerate(timestamps_comuns, 1):
        try:
            ch08_file = [f for f in ch08_files if ts in f][0]
            ch13_file = [f for f in ch13_files if ts in f][0]

            print(f"   [{i}/{len(timestamps_comuns)}] Processando: {ts}")

            arq08 = xr.open_dataset(os.path.join(ch08_path, ch08_file), engine='netcdf4')
            arq13 = xr.open_dataset(os.path.join(ch13_path, ch13_file), engine='netcdf4')

            dados08 = arq08.Band1.data / 100 - 273.15
            dados13 = arq13.Band1.data / 100 - 273.15

            wvd = dados08 - dados13
            wvd = np.where(np.abs(wvd) > 50, np.nan, wvd)

            lats = arq08.lat.data
            lons = arq08.lon.data

            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})

            ax.add_feature(cfeature.COASTLINE, linewidth=0.6, color='gold', zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.6, color='gold', zorder=301)

            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor='gold', facecolor='none', linewidth=0.6)

            # Fundo: canal IR (ch13) em tons de cinza, mesma faixa dos demais IR
            ax.imshow(dados13, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), cmap='gray_r',
                      vmin=-80, vmax=60, origin='lower', zorder=1)

            # Realce: só os pixels com WVD acima do limiar (overshooting top).
            # Cor sólida bem contrastante (magenta) em vez de gradiente - destaca
            # melhor contra o fundo cinza. Os pixels de OT são raros e minúsculos
            # (1-3 pixels), então dilata um pouco pra ficarem visíveis no mapa.
            mask = (wvd > limiar) & ~np.isnan(wvd)
            try:
                from scipy.ndimage import binary_dilation
                mask = binary_dilation(mask, iterations=2)
            except ImportError:
                pass
            destaque = np.ma.masked_where(~mask, np.ones_like(wvd))
            ax.imshow(destaque, extent=[lons.min(), lons.max(), lats.min(), lats.max()],
                      transform=ccrs.PlateCarree(), cmap=ListedColormap(['magenta']),
                      vmin=0, vmax=1, origin='lower', zorder=2)

            legenda = [Patch(facecolor='magenta', edgecolor='none',
                             label=f'WVD > {limiar}K (overshooting top)')]
            ax.legend(handles=legenda, loc='lower left', fontsize=9, framealpha=0.85)

            if extent:
                ax.set_extent(extent, crs=ccrs.PlateCarree())
            else:
                ax.set_extent([-115, -25, -55, 34], crs=ccrs.PlateCarree())

            gl = ax.gridlines(draw_labels=True)
            gl.top_labels = False
            gl.right_labels = False
            gl.xlabel_style = {'fontsize': 14}
            gl.ylabel_style = {'fontsize': 14}

            if titulo_personalizado:
                titulo = f"{ts} UTC\n{titulo_personalizado} | {sat.upper()} | WVD (OT > {limiar}K)"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_wvd_{ts}.png"
            else:
                titulo = f"{ts} UTC\n{sat.upper()} | Water Vapor - IR Difference (OT > {limiar}K)"
                nome_arquivo = f"{sat.upper()}_wvd_{ts}.png"

            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)

            arq08.close()
            arq13.close()

        except Exception as e:
            print(f"   ERRO ao processar {ts}: {e}")

    print(f"Plotagem WVD (overshooting top) concluida!")

# ============================================================================
# FUNÇÃO PRINCIPAL EXPORTADA
# ============================================================================

def plot_prod(caso, produto, extent=None, titulo=None, cmap=None, usar_noaa_ch13=False):
    """
    Função principal para plotagem de produtos GOES
    
    Parâmetros:
        caso: str - nome do caso
        produto: str - 'True_Color', 'Single_Band', 'SWD', 'CPD', 'WVD', 'SOD' ou 'SWVD'
        extent: list - [lon_min, lon_max, lat_min, lat_max]
        titulo: str - título personalizado
        cmap: str - colormap personalizado (apenas para Single_Band)
        usar_noaa_ch13: bool - Força uso da paleta NOAA para ch13
    """
    
    print("\n" + "="*50)
    print(f"INICIANDO PLOTAGEM: {produto.upper()}")
    print("="*50)
    
    # Detectar satélite
    caminho_caso = os.path.join(DIRFIG, caso)
    
    if 'goes16' in caso.lower():
        sat = 'goes16'
        print(f"Satelite detectado: GOES-16")
    elif 'goes19' in caso.lower():
        sat = 'goes19'
        print(f"Satelite detectado: GOES-19")
    else:
        print(f"ATENCAO: Satelite nao identificado no nome: {caso}")
        if os.path.exists(caminho_caso):
            arquivos = os.listdir(caminho_caso)
            if any('goes16' in f.lower() for f in arquivos):
                sat = 'goes16'
                print("   Satelite detectado: GOES-16")
            elif any('goes19' in f.lower() for f in arquivos):
                sat = 'goes19'
                print("   Satelite detectado: GOES-19")
            else:
                sat = input("   Digite o satelite (goes16/goes19): ").strip().lower()
        else:
            sat = input("   Digite o satelite (goes16/goes19): ").strip().lower()
    
    # Executar plotagem
    if produto == 'True_Color':
        plot_true_color(caso, sat, extent=extent, titulo_personalizado=titulo)

    elif produto == 'AirMass':
        plot_airmass(caso, sat, extent=extent, titulo_personalizado=titulo)

    elif produto == 'SWD':
        plot_diferenca(caso, sat, 'swd', extent=extent, titulo_personalizado=titulo, cmap=cmap)

    elif produto == 'CPD':
        plot_diferenca(caso, sat, 'cpd', extent=extent, titulo_personalizado=titulo, cmap=cmap)

    elif produto == 'WVD':
        plot_wvd_overshooting(caso, sat, extent=extent, titulo_personalizado=titulo)

    elif produto == 'SOD':
        plot_diferenca(caso, sat, 'sod', extent=extent, titulo_personalizado=titulo, cmap=cmap)

    elif produto == 'SWVD':
        plot_diferenca(caso, sat, 'swvd', extent=extent, titulo_personalizado=titulo, cmap=cmap)

    elif produto == 'Single_Band':
        print("\nPlotando canal individual...")
        
        canais = []
        for item in os.listdir(caminho_caso):
            item_path = os.path.join(caminho_caso, item)
            if os.path.isdir(item_path) and item.startswith('ch'):
                canais.append(item)
        
        if not canais:
            print(f"ERRO: Nenhum canal encontrado em {caminho_caso}")
            return
        
        print(f"\nCanais disponiveis em {caso}:")
        for i, canal in enumerate(canais, 1):
            caminho_canal = os.path.join(caminho_caso, canal)
            num_arquivos = len([f for f in os.listdir(caminho_canal) if f.endswith('.nc')])
            if canal in ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06']:
                tipo = "VIS"
            elif canal in ['ch08', 'ch09', 'ch10']:
                tipo = "WV"
            elif canal in ['ch07', 'ch13', 'ch14', 'ch15', 'ch16']:
                tipo = "IR"
            else:
                tipo = "??"
            print(f"   {i}. {canal.upper()} [{tipo}] ({num_arquivos} arquivos)")
        
        while True:
            try:
                escolha = input(f"\nEscolha o canal (1-{len(canais)} ou nome ex: ch13): ").strip()
                
                if escolha.isdigit():
                    idx = int(escolha) - 1
                    if 0 <= idx < len(canais):
                        canal = canais[idx]
                        break
                    else:
                        print(f"Opcao invalida! Escolha entre 1 e {len(canais)}")
                else:
                    if escolha in canais:
                        canal = escolha
                        break
                    else:
                        print(f"Canal {escolha} nao encontrado! Disponiveis: {', '.join(canais)}")
            except ValueError:
                print("Entrada invalida!")
        
        # Perguntar se quer usar NOAA para ch13
        if canal == 'ch13':
            usar_noaa = input("\nUsar colormap NOAA para ch13? (s/n): ").strip().lower()
            usar_noaa_ch13 = usar_noaa == 's'
            if usar_noaa_ch13:
                print("   Usando paleta NOAA colorida")
            else:
                print("   Usando escala de cinza")
        
        # Se o usuário forneceu cmap, sobrescreve tudo
        if cmap:
            print(f"\nUsando colormap personalizado: {cmap}")
        elif canal in ['ch07', 'ch13', 'ch14', 'ch15', 'ch16']:
            if canal == 'ch13' and usar_noaa_ch13:
                print(f"\nUsando paleta NOAA colorida para {canal.upper()}")
            else:
                print(f"\nUsando escala de cinza para {canal.upper()} (IR)")
        elif canal in ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06']:
            print(f"\nUsando escala de cinza para {canal.upper()} (VIS)")
        elif canal in ['ch08', 'ch09', 'ch10']:
            print(f"\nUsando paleta OrRd para {canal.upper()} (WV)")
        else:
            print(f"\nUsando colormap padrao para {canal.upper()}")
        
        plot_simple_channel(caso, canal, sat, extent=extent, 
                           titulo_personalizado=titulo, cmap=cmap,
                           usar_noaa_ch13=usar_noaa_ch13)
    else:
        print(f"ERRO: Produto desconhecido: {produto}")
        return
    
    print("\n" + "="*50)
    print("PLOTAGEM CONCLUIDA!")
    print("="*50)
