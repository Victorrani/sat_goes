"""
produt_plot.py - Módulo para plotagem de imagens GOES
Autor: Victor Ranieri e DeepSeek
Descrição: Funções para plotar canais individuais e composição True Color
"""

import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import warnings
from matplotlib.colors import LinearSegmentedColormap

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================

# Caminhos padrão
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
        return cmap_water_vapor, -80, 30, "Brightness Temperature (°C)"
    else:
        return cmap_noaa, -100, 55, "Brightness Temperature (°C)"

# ============================================================================
# FUNÇÕES AUXILIARES
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
    # O primeiro elemento sempre será 'goes16' ou 'goes19'
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
            # Tentar identificar o satélite
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
        
        # Verificar se é número
        if escolha.isdigit():
            idx = int(escolha) - 1
            if 0 <= idx < len(casos):
                return casos[idx]
        
        # Verificar se é nome
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
    print("Limites máximos: -115 (longitude oeste) a -25 (leste) e -55 (sul) a 34 (norte)")
    
    try:
        lon_min = float(input("Longitude mínima (Oeste, ex: -85): "))
        lon_max = float(input("Longitude máxima (Leste, ex: -30): "))
        lat_min = float(input("Latitude mínima (Sul, ex: -40): "))
        lat_max = float(input("Latitude máxima (Norte, ex: 10): "))
        
        print(f"\n✅ Área selecionada: Lon[{lon_min}° a {lon_max}°] | Lat[{lat_min}° a {lat_max}°]")
        return [lon_min, lon_max, lat_min, lat_max]
    except:
        print("❌ Valores inválidos! Usando área padrão.")
        return [-115, -25, -55, 34]

def obter_titulo_usuario():
    """Solicita ao usuário o título do gráfico"""
    print("\n" + "="*50)
    print("📝 DEFINIÇÃO DO TÍTULO")
    print("="*50)
    
    print('Evite nome com ascentuação e espaços para melhor compatibilidade de arquivos.')
    titulo = input("Digite o título do gráfico (ou pressione Enter para usar padrão): ").strip()
    if not titulo:
        return None
    return titulo

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
# FUNÇÕES DE PLOTAGEM PARA SIMPLE CHANNEL
# ============================================================================

def plot_simple_channel(caso, canal, sat, extent=None, titulo_personalizado=None):
    """
    Plota um canal individual (ex: ch13, ch06, etc.)
    
    Parâmetros:
        caso: str - nome do caso (ex: 'goes16_20240310_10')
        canal: str - nome do canal (ex: 'ch13')
        sat: str - 'goes16' ou 'goes19'
        extent: list - [lon_min, lon_max, lat_min, lat_max]
        titulo_personalizado: str - título personalizado
    """
    
    # Caminhos
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_canal = os.path.join(caminho_caso, canal)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)
    
    # Verificar se o canal existe
    if not os.path.exists(caminho_canal):
        print(f"❌ Canal {canal} não encontrado em {caminho_caso}")
        return
    
    # Obter colormap
    cmap, vmin, vmax, label = get_colormap(canal)
    
    # Listar arquivos
    arquivos = sorted([f for f in os.listdir(caminho_canal) if f.endswith('.nc')])
    
    if not arquivos:
        print(f"❌ Nenhum arquivo NetCDF encontrado em {caminho_canal}")
        return
    
    print(f"\n🎨 Plotando {len(arquivos)} imagens do canal {canal}...")
    print(f"📡 Satélite: {sat.upper()}")
    
    for i, arquivo in enumerate(arquivos, 1):
        try:
            # Abrir arquivo
            arq = xr.open_dataset(os.path.join(caminho_canal, arquivo), engine='netcdf4')
            
            # Extrair data
            data_str = arquivo.split('_')[1][:12]
            print(f"   [{i}/{len(arquivos)}] Processando: {data_str}")
            
            # Processar dados
            dados = arq.Band1
            
            # Converter para Celsius se for canal infravermelho
            if canal in ['ch13', 'ch14', 'ch15', 'ch16']:
                dados.data = dados.data / 100 - 273.15
            else:
                dados.data = dados.data / 100
                dados.data = np.clip(dados.data, 0, 100)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Adicionar features geográficas
            ax.add_feature(cfeature.LAND, edgecolor='black', alpha=0.3)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='yellow',
                            zorder=300)
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5,
                            color='yellow', zorder=301)
            
            # Adicionar shapefile dos estados
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(), 
                                 edgecolor='yellow', facecolor='none', linewidth=0.3)
            
            # Plotar dados
            if canal in ['ch13', 'ch14', 'ch15', 'ch16']:
                dados.plot(ax=ax, cmap=cmap, transform=ccrs.PlateCarree(),
                          vmin=-110, vmax=60,
                          cbar_kwargs={
                              "label": label,
                              "orientation": "vertical",
                              "pad": 0.05,
                              "aspect": 20,
                              "shrink": 0.8,
                              "ticks": np.arange(vmin, vmax+1, 10)
                          })
            else:
                # Para canais visíveis, usar 0-100%
                dados.plot(ax=ax, cmap=cmap, transform=ccrs.PlateCarree(),
                          vmin=0, vmax=100,
                          cbar_kwargs={
                              "label": label,
                              "orientation": "vertical",
                              "pad": 0.05,
                              "aspect": 20,
                              "shrink": 0.8,
                              "ticks": np.arange(0, 101, 20)
                          })
            
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
            
            # Título com satélite
            if titulo_personalizado:
                titulo = f"{titulo_personalizado} | {sat.upper()} | {canal.upper()} | {data_str} UTC"
                nome_arquivo = f"{titulo_personalizado}_{sat.upper()}_{canal}_{data_str}.png"
            else:
                titulo = f"{sat.upper()} | {canal.upper()} | {data_str} UTC"
                nome_arquivo = f"{sat.upper()}_{canal}_{data_str}.png"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            
            # Nome do arquivo com satélite
            nome_arquivo = nome_arquivo
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            arq.close()
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {arquivo}: {e}")
    
    print(f"✅ Plotagem do canal {canal} concluída!")

# ============================================================================
# FUNÇÕES DE PLOTAGEM PARA TRUE COLOR
# ============================================================================

def plot_true_color(caso, sat, extent=None, titulo_personalizado=None):
    """
    Plota composição True Color (canais 1, 2, 3)
    
    Parâmetros:
        caso: str - nome do caso (ex: 'goes16_true_color_202403_10_15')
        sat: str - 'goes16' ou 'goes19'
        extent: list - [lon_min, lon_max, lat_min, lat_max]
        titulo_personalizado: str - título personalizado
    """
    
    # Caminhos
    caminho_caso = os.path.join(DIRFIG, caso)
    caminho_fig = os.path.join(caminho_caso, 'fig')
    os.makedirs(caminho_fig, exist_ok=True)
    
    # Caminhos dos canais
    ch01_path = os.path.join(caminho_caso, 'ch01')
    ch02_path = os.path.join(caminho_caso, 'ch02')
    ch03_path = os.path.join(caminho_caso, 'ch03')
    
    # Verificar se os canais existem
    if not all(os.path.exists(p) for p in [ch01_path, ch02_path, ch03_path]):
        print(f"❌ Canais 1,2,3 não encontrados em {caminho_caso}")
        return
    
    # Listar arquivos
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
            # Extrair data
            data_str = f1.split('_')[1][:12]
            print(f"   [{i}/{len(ch01_files)}] Processando: {data_str}")
            
            # Abrir arquivos
            arq1 = xr.open_dataset(os.path.join(ch01_path, f1))
            arq2 = xr.open_dataset(os.path.join(ch02_path, f2))
            arq3 = xr.open_dataset(os.path.join(ch03_path, f3))
            
            # Processar cada canal
            ch01 = arq1.Band1
            if sat == 'goes19':
                ch01 = ch01.isel(lat=slice(0, -1), lon=slice(0, -1))
                ch01 = ch01.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch01.data = ch01.data / 100
            else:
                ch01 = ch01.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch01.data = ch01.data / 100
            
            ch02 = arq2.Band1
            ch02 = ch02.coarsen(lat=2, lon=2, boundary='trim').mean()
            ch02.data = ch02.data / 100
            
            ch03 = arq3.Band1
            if sat == 'goes19':
                ch03 = ch03.isel(lat=slice(0, -1), lon=slice(0, -1))
                ch03 = ch03.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch03.data = ch03.data / 100
            else:
                ch03 = ch03.coarsen(lat=2, lon=2, boundary='trim').mean()
                ch03.data = ch03.data / 100 
                
            # Composição RGB
            R = np.flipud(ch02.data)
            aux = 0.45 * ch02.data + 0.1 * ch03.data + 0.45 * ch01.data
            G = np.flipud(aux)
            B = np.flipud(ch01.data)
            
            # Normalização
            Rmin, Rmax = 0, 100
            Gmin, Gmax = 0, 100
            Bmin, Bmax = 0, 100
            
            R = np.clip(R, Rmin, Rmax)
            G = np.clip(G, Gmin, Gmax)
            B = np.clip(B, Bmin, Bmax)
            
            R = (R - Rmin) / (Rmax - Rmin)
            G = (G - Gmin) / (Gmax - Gmin)
            B = (B - Bmin) / (Bmax - Bmin)
            
            # Correção gamma
            gamma = 2
            R = R ** (1/gamma)
            G = G ** (1/gamma)
            B = B ** (1/gamma)
            
            RGB = np.stack([R, G, B], axis=2)
            
            # Criar figura
            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Adicionar features
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='yellow')
            ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, color='yellow')
            
            # Adicionar shapefile
            if os.path.exists(SHAPEFILE_PATH):
                shapefile = list(shpreader.Reader(SHAPEFILE_PATH).geometries())
                ax.add_geometries(shapefile, ccrs.PlateCarree(),
                                 edgecolor='yellow', facecolor='none', linewidth=0.3)
            
            # Plotar RGB
            ax.imshow(RGB[::-1], extent=[ch02.lon.min(), ch02.lon.max(),
                                          ch02.lat.min(), ch02.lat.max()],
                     transform=ccrs.PlateCarree())
            
            # Definir extent
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
            if titulo_personalizado:
                titulo = f"{titulo_personalizado} | {data_str} UTC"
            else:
                titulo = f"{sat.upper()} | True Color | {data_str} UTC"
            
            plt.title(titulo, loc='left', fontweight='bold', fontsize=12)
            
            # Salvar figura
            nome_arquivo = f"{sat.upper()}_{caso}_true_color_{data_str}.png"
            plt.savefig(os.path.join(caminho_fig, nome_arquivo), dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Fechar arquivos
            arq1.close()
            arq2.close()
            arq3.close()
            
        except Exception as e:
            print(f"   ❌ Erro ao processar {data_str}: {e}")
    
    print(f"✅ Plotagem True Color concluída!")

# ============================================================================
# FUNÇÃO PRINCIPAL EXPORTADA
# ============================================================================

def plot_prod(caso, produto, sat=None, extent=None, titulo=None):
    """
    Função principal para plotagem de produtos GOES
    """
    
    caminho_caso = os.path.join(DIRFIG, caso)
    
    # =========================================================
    # FORÇAR DETECÇÃO DO SATÉLITE PELO NOME DA PASTA
    # =========================================================
    # Ignora completamente o parâmetro 'sat' que vem de fora
    # Força a detecção pelo nome da pasta
    if caso.startswith('goes16'):
        sat = 'goes16'
    elif caso.startswith('goes19'):
        sat = 'goes19'
    else:
        # Fallback
        sat = 'goes16'
    
    print(f"\n{'='*50}")
    print(f"🎨 INICIANDO PLOTAGEM")
    print(f"{'='*50}")
    print(f"📁 Caso: {caso}")
    print(f"📦 Produto: {produto}")
    print(f"📡 Satélite: {sat.upper()}")  # <-- AGORA VAI MOSTRAR GOES19
    print(f"{'='*50}")
    
    # DETECTAR CANAIS DISPONÍVEIS
    canais_disponiveis = detectar_canais_disponiveis(caminho_caso)
    
    if produto == 'simple_channel':
        if not canais_disponiveis:
            print(f"❌ Nenhum canal encontrado em {caminho_caso}")
            return False
        
        print(f"📡 Canais disponíveis: {', '.join(canais_disponiveis)}")
        
        if len(canais_disponiveis) == 1:
            canal = canais_disponiveis[0]
            print(f"✅ Canal detectado automaticamente: {canal}")
        else:
            print("\nCanais disponíveis:")
            for i, c in enumerate(canais_disponiveis, 1):
                print(f"   {i}. {c}")
            escolha = input(f"\nEscolha o canal (1-{len(canais_disponiveis)}): ").strip()
            try:
                idx = int(escolha) - 1
                canal = canais_disponiveis[idx]
            except:
                canal = canais_disponiveis[0]
                print(f"Usando canal: {canal}")
    
    if extent:
        print(f"🌍 Extent: Lon[{extent[0]}° a {extent[1]}°] Lat[{extent[2]}° a {extent[3]}°]")
    
    print()
    
    if produto == 'simple_channel':
        plot_simple_channel(caso, canal, sat, extent, titulo)
    
    elif produto == 'true_color':
        plot_true_color(caso, sat, extent, titulo)
    
    else:
        print(f"❌ Produto '{produto}' não reconhecido!")
        return False
    
    print(f"\n✅ Plotagem concluída!")
    return True

# ============================================================================
# EXECUÇÃO DIRETA (TESTE)
# ============================================================================

if __name__ == "__main__":
    print("="*50)
    print("🧪 MODO DE TESTE - produt_plot.py")
    print("="*50)
    
    casos = listar_casos_disponiveis()
    if casos:
        caso = selecionar_caso(casos)
        if caso:
            # Detectar automaticamente o tipo de produto
            caminho_caso = os.path.join(DIRFIG, caso)
            eh_true_color = detectar_se_e_true_color(caminho_caso)
            
            if eh_true_color:
                print(f"\n🎨 Produto detectado: TRUE COLOR")
                produto = 'true_color'
            else:
                print(f"\n📡 Produto detectado: SIMPLE CHANNEL")
                produto = 'simple_channel'
            
            # Satélite será detectado automaticamente
            extent = obter_extent_usuario()
            titulo = obter_titulo_usuario()
            
            plot_prod(caso, produto, extent=extent, titulo=titulo)