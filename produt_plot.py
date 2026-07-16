"""
produt_plot.py - Módulo para plotagem de imagens GOES
Autor: Victor Ranieri e DeepSeek
Descrição: Funções para plotar canais individuais e composição True Color
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
from matplotlib.colors import LinearSegmentedColormap

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

def get_colormap(canal):
    """
    Retorna o colormap apropriado para cada canal
    """
    # Colormap NOAA para canais infravermelho (ch13, ch14, etc.)
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
    
    # Colormap em escala de cinza para canais visíveis
    cmap_gray = plt.cm.gray
    
    # Colormap para canais de vapor d'água
    cmap_water_vapor = plt.cm.OrRd
    
    # Definição por canal
    canais_infravermelho = ['ch13', 'ch14', 'ch15', 'ch16']
    canais_visiveis = ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06']
    canais_vapor = ['ch08', 'ch09', 'ch10']
    
    if canal in canais_infravermelho:
        return cmap_noaa, -100, 55, "Brightness Temperature (°C)"
    elif canal in canais_visiveis:
        return cmap_gray, 0, 100, "Reflectance (%)"
    elif canal in canais_vapor:
        return cmap_water_vapor, -80, 50, "Brightness Temperature (°C)"
    else:
        return cmap_noaa, -100, 55, "Brightness Temperature (°C)"

# ============================================================================
# FUNÇÕES AUXILIARES DE DETECÇÃO
# ============================================================================

def extrair_satelite_do_nome(nome_pasta):
    """
    Extrai o satélite do nome da pasta
    Exemplos:
        'goes16_20240310_10' -> 'goes16'
        'goes19_true_color_202403_10_15' -> 'goes19'
        'goes19_20250410_10' -> 'goes19'
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
    Detecta o satélite automaticamente (primeiro por metadado, depois pelo nome da pasta)
    """
    sat = ler_metadados_satelite(caminho_caso)
    if sat:
        print(f"   📄 Satélite detectado pelo metadado: {sat.upper()}")
        return sat
    
    sat = extrair_satelite_do_nome(nome_pasta)
    if sat:
        print(f"   📁 Satélite detectado pelo nome da pasta: {sat.upper()}")
        return sat
    
    print(f"   ⚠️ Não foi possível detectar o satélite!")
    return None

def detectar_canais_disponiveis(caminho_caso):
    """
    Detecta automaticamente quais canais estão disponíveis no caso
    Retorna lista de canais encontrados
    """
    if not os.path.exists(caminho_caso):
        return []
    
    canais = []
    for item in os.listdir(caminho_caso):
        item_path = os.path.join(caminho_caso, item)
        if os.path.isdir(item_path) and item.startswith('ch'):
            canais.append(item)
    
    return sorted(canais)

def detectar_se_e_true_color(caminho_caso):
    """
    Detecta se o caso é True Color (tem ch01, ch02, ch03)
    """
    canais = detectar_canais_disponiveis(caminho_caso)
    return 'ch01' in canais and 'ch02' in canais and 'ch03' in canais

# ============================================================================
# FUNÇÕES DE INTERAÇÃO COM USUÁRIO
# ============================================================================

def listar_casos_disponiveis():
    """Lista todos os casos disponíveis para plotagem"""
    if not os.path.exists(DIRFIG):
        print(f"❌ Diretório {DIRFIG} não encontrado!")
        return []
    
    casos = [d for d in os.listdir(DIRFIG) if os.path.isdir(os.path.join(DIRFIG, d))]
    
    if not casos:
        print("❌ Nenhum caso encontrado no diretório de figuras.")
    else:
        print("\n📂 Casos disponíveis:")
        for i, caso in enumerate(casos, 1):
            caminho_caso = os.path.join(DIRFIG, caso)
            sat = detectar_satelite(caminho_caso, caso)
            if sat:
                print(f"   {i}. {caso} [{sat.upper()}]")
            else:
                print(f"   {i}. {caso}")
    
    return casos

def selecionar_caso(casos):
    """Permite ao usuário selecionar um caso"""
    if not casos:
        return None
    
    try:
        escolha = input('\n📁 Escolha o caso (nome ou número): ').strip()
        
        if escolha.isdigit():
            idx = int(escolha) - 1
            if 0 <= idx < len(casos):
                return casos[idx]
        
        if escolha in casos:
            return escolha
        
        print(f"❌ Caso '{escolha}' não encontrado!")
        return None
    except:
        return None

def obter_extent_usuario():
    """Solicita ao usuário os limites de longitude e latitude"""
    print("\n" + "="*50)
    print("🌍 DEFINIÇÃO DA ÁREA DE PLOTAGEM")
    print("="*50)
    print("Limites máximos: -115 (oeste) a -25 (leste) e -55 (sul) a 34 (norte)")
    
    try:
        lon_min = float(input("Longitude mínima (Oeste, ex: -85): "))
        lon_max = float(input("Longitude máxima (Leste, ex: -30): "))
        lat_min = float(input("Latitude mínima (Sul, ex: -40): "))
        lat_max = float(input("Latitude máxima (Norte, ex: 10): "))
        
        print(f"\n✅ Área selecionada: Lon[{lon_min}° a {lon_max}°] | Lat[{lat_min}° a {lat_max}°]")
        return [lon_min, lon_max, lat_min, lat_max]
    except:
        print("❌ Valores inválidos! Usando área padrão.")
        return None

def obter_titulo_usuario():
    """Solicita ao usuário o título do gráfico"""
    print("\n" + "="*50)
    print("📝 DEFINIÇÃO DO TÍTULO")
    print("="*50)
    print('Evite acentuação e espaços para melhor compatibilidade.')
    titulo = input("Digite o título (ou Enter para padrão): ").strip()
    return titulo if titulo else None

def obter_colormap_usuario():
    """
    Solicita ao usuário um colormap personalizado.
    
    Retorna:
        str: Nome do colormap ou None para usar o padrão
    """
    print("Aceita colormaps matplotlib")
    
    while True:
        opcao = input("\nDeseja usar colormap personalizado? (s/n): ").strip().lower()
        
        if opcao == 's':
            cmap = input("Digite o nome do colormap: ").strip()
            print(f"   ✅ Usando colormap: {cmap}")
            return cmap
        elif opcao == 'n':
            print("   ✅ Usando colormap padrão do produto")
            return None
        else:
            print("   ❌ Opção inválida! Digite 's' para sim ou 'n' para não.")
# ============================================================================
# FUNÇÕES DE PLOTAGEM
# ============================================================================

def plot_simple_channel(caso, canal, sat, extent=None, titulo_personalizado=None, cmap=None):
    """
    Plota um canal individual do GOES
    
    Parâmetros:
        caso: str - nome do caso
        canal: str - nome do canal (ex: 'ch13', 'ch02')
        sat: str - 'goes16' ou 'goes19'
        extent: list - [lon_min, lon_max, lat_min, lat_max]
        titulo_personalizado: str - título personalizado
        cmap: str - colormap personalizado
    """
    
    # Configurações iniciais
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_canal = os.path.join(caminho_caso, canal)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)
    
    if not os.path.exists(caminho_canal):
        print(f"❌ Canal {canal} não encontrado em {caminho_caso}")
        return
    
    # Classificação dos canais
    canais_visiveis = ['ch01', 'ch02', 'ch03', 'ch04', 'ch05', 'ch06']
    canais_vapor = ['ch08', 'ch09', 'ch10']
    canais_ir = ['ch13', 'ch14', 'ch15', 'ch16']
    canal_curto_ir = 'ch07'
    
    # Configurações por tipo
    if canal in canais_visiveis:
        tipo_canal = 'visivel'
        cmap_padrao = 'Greys_r'
        vmin, vmax = 0, 100
        label = 'Reflectância (%)'
        converte_celsius = False
    elif canal in canais_vapor:
        tipo_canal = 'vapor'
        cmap_padrao = 'Greys'
        vmin, vmax = -80, 0
        label = 'Temperatura (°C)'
        converte_celsius = True
    elif canal in canais_ir:
        tipo_canal = 'ir'
        cmap_padrao, vmin, vmax, label = get_colormap(canal)
        converte_celsius = True
    elif canal == canal_curto_ir:
        tipo_canal = 'curto_ir'
        cmap_padrao = 'Greys'
        vmin, vmax = -80, 50
        label = 'Temperatura (°C)'
        converte_celsius = True
    else:
        tipo_canal = 'outro'
        cmap_padrao = 'Greys'
        vmin, vmax = 0, 100
        label = 'Dados'
        converte_celsius = False
    
    cmap_uso = cmap if cmap else cmap_padrao
    
    # Listar arquivos
    arquivos = sorted([f for f in os.listdir(caminho_canal) if f.endswith('.nc')])
    
    if not arquivos:
        print(f"❌ Nenhum arquivo NetCDF encontrado em {caminho_canal}")
        return
    
    print(f"\n🎨 Plotando {len(arquivos)} imagens do canal {canal}...")
    print(f"📡 Satélite: {sat.upper()}")
    print(f"📊 Tipo: {tipo_canal.upper()} | Escala: {vmin} a {vmax}")
    print(f"🎨 Colormap: {cmap_uso}")
    
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
            #ax.add_feature(cfeature.LAND, edgecolor='black', alpha=0.3)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='yellow', zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, color='yellow', zorder=301)
            
            # Shapefile
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(), 
                                 edgecolor='yellow', facecolor='none', linewidth=0.3)
            
            # Plot
            ticks = np.arange(0, 101, 20) if tipo_canal == 'visivel' else np.arange(vmin, vmax+1, 20)
            
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
            tipo_str = {'visivel': 'VIS', 'vapor': 'WV', 'ir': 'IR', 'curto_ir': 'CIR'}.get(tipo_canal, canal.upper())
            
            if titulo_personalizado:
                titulo = f"{titulo_personalizado} | {sat.upper()} | {canal.upper()} ({tipo_str}) | {data_str} UTC"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{canal}_{data_str}.png"
            else:
                titulo = f"{sat.upper()} | {canal.upper()} ({tipo_str}) | {data_str} UTC"
                nome_arquivo = f"{sat.upper()}_{canal}_{data_str}.png"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=300, bbox_inches='tight')
            plt.close(fig)
            arq.close()
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {arquivo}: {e}")
    
    print(f"✅ Plotagem do canal {canal} concluída!")

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
        print(f"❌ Canais 1,2,3 não encontrados em {caminho_caso}")
        return
    
    ch01_files = sorted(os.listdir(ch01_path))
    ch02_files = sorted(os.listdir(ch02_path))
    ch03_files = sorted(os.listdir(ch03_path))
    
    if not ch01_files:
        print(f"❌ Nenhum arquivo encontrado")
        return
    
    print(f"\n🎨 Plotando {len(ch01_files)} imagens True Color...")
    print(f"📡 Satélite: {sat.upper()}")
    
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
            
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='yellow')
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, color='yellow')
            
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor='yellow', facecolor='none', linewidth=0.3)
            
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
                titulo = f"{titulo_personalizado} | {sat.upper()} | {data_str} UTC"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{data_str}.png"
            else:
                titulo = f"{sat.upper()} | True Color | {data_str} UTC"
                nome_arquivo = f"{sat.upper()}_true_color_{data_str}.png"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            arq1.close()
            arq2.close()
            arq3.close()
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {data_str}: {e}")
    
    print(f"✅ Plotagem True Color concluída!")

# ============================================================================
# FUNÇÃO PRINCIPAL EXPORTADA
# ============================================================================

def plot_prod(caso, produto, extent=None, titulo=None, cmap=None):
    """
    Função principal para plotagem de produtos GOES
    
    Parâmetros:
        caso: str - nome do caso
        produto: str - 'true_color' ou 'simple_channel'
        extent: list - [lon_min, lon_max, lat_min, lat_max]
        titulo: str - título personalizado
        cmap: str - colormap personalizado (apenas para simple_channel)
    """
    
    print("\n" + "="*50)
    print(f"🎨 INICIANDO PLOTAGEM: {produto.upper()}")
    print("="*50)
    
    # Detectar satélite
    caminho_caso = os.path.join(DIRFIG, caso)
    
    if 'goes16' in caso.lower():
        sat = 'goes16'
        print(f"📡 Satélite detectado: GOES-16")
    elif 'goes19' in caso.lower():
        sat = 'goes19'
        print(f"📡 Satélite detectado: GOES-19")
    else:
        print(f"⚠️ Satélite não identificado no nome: {caso}")
        if os.path.exists(caminho_caso):
            arquivos = os.listdir(caminho_caso)
            if any('goes16' in f.lower() for f in arquivos):
                sat = 'goes16'
                print("   ✅ Satélite detectado: GOES-16")
            elif any('goes19' in f.lower() for f in arquivos):
                sat = 'goes19'
                print("   ✅ Satélite detectado: GOES-19")
            else:
                sat = input("   Digite o satélite (goes16/goes19): ").strip().lower()
        else:
            sat = input("   Digite o satélite (goes16/goes19): ").strip().lower()
    
    # Executar plotagem
    if produto == 'true_color':
        plot_true_color(caso, sat, extent=extent, titulo_personalizado=titulo)
        
    elif produto == 'simple_channel':
        print("\n🎨 Plotando canal individual...")
        
        canais = []
        for item in os.listdir(caminho_caso):
            item_path = os.path.join(caminho_caso, item)
            if os.path.isdir(item_path) and item.startswith('ch'):
                canais.append(item)
        
        if not canais:
            print(f"❌ Nenhum canal encontrado em {caminho_caso}")
            return
        
        print(f"\n📡 Canais disponíveis em {caso}:")
        for i, canal in enumerate(canais, 1):
            caminho_canal = os.path.join(caminho_caso, canal)
            num_arquivos = len([f for f in os.listdir(caminho_canal) if f.endswith('.nc')])
            print(f"   {i}. {canal.upper()} ({num_arquivos} arquivos)")
        
        while True:
            try:
                escolha = input(f"\nEscolha o canal (1-{len(canais)} ou nome ex: ch13): ").strip()
                
                if escolha.isdigit():
                    idx = int(escolha) - 1
                    if 0 <= idx < len(canais):
                        canal = canais[idx]
                        break
                    else:
                        print(f"❌ Opção inválida! Escolha entre 1 e {len(canais)}")
                else:
                    if escolha in canais:
                        canal = escolha
                        break
                    else:
                        print(f"❌ Canal {escolha} não encontrado! Disponíveis: {', '.join(canais)}")
            except ValueError:
                print("❌ Entrada inválida!")
        
        if cmap:
            print(f"\n🎨 Usando colormap personalizado: {cmap}")
        else:
            print(f"\n🎨 Usando colormap padrão para {canal.upper()}")
        
        plot_simple_channel(caso, canal, sat, extent=extent, 
                           titulo_personalizado=titulo, cmap=cmap)
    else:
        print(f"❌ Produto desconhecido: {produto}")
        return
    
    print("\n" + "="*50)
    print("✅ PLOTAGEM CONCLUÍDA!")
    print("="*50)