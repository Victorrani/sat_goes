import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.colors as cm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import warnings

# Ignorar todos os avisos
warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------------
# -- LENDO O SHAPEFILE E OS DADOS
# ---------------------------------------------------------------------------------
DIRFIGS = '/home/victor/USP/satelite/fig_dados/20240214_22/ch13/'
# Caminho do novo diretório 'figs'
new_dir = os.path.join(DIRFIGS, 'figs')

# Criar o diretório 'figs' se não existir
os.makedirs(new_dir, exist_ok=True)
arquivos = sorted(os.listdir(DIRFIGS))

# Lendo o shapefile do Brasil (certifique-se de que o caminho esteja correto)
shapefile_path = 'BR_UF_2019.shp'  # Coloque o caminho correto do seu shapefile

# ---------------------------------------------------------------------------------
# -- DEFININDO PALETAS DE CORES SEM CINZA
# ---------------------------------------------------------------------------------

# Paleta sem tons de cinza, ajustando as cores para temperaturas
palCO_new_adjusted = ["#000000", "#FF0000", "#FFFF00", "#00FF7F", "#0033FF", "#ADD8E6"]
cmapCO_new_adjusted = cm.LinearSegmentedColormap.from_list("IR_clean_adjusted", palCO_new_adjusted, N=20)

# Aplicando a paleta suave com 25 pontos (metade do original)
cmapCO_adjusted = cmapCO_new_adjusted(np.linspace(0, 1, 50))  # 25 divisões na paleta colorida

# Criando a paleta sem cinza com 120 pontos e adicionando as cores ajustadas
cmapPB_adjusted = cm.LinearSegmentedColormap.from_list("", ["white", "black"])
cmapPB_adjusted = cmapPB_adjusted(np.linspace(0, 1, 120))  # 120 divisões na paleta total
cmapPB_adjusted[:50, :] = cmapCO_adjusted  # Inserindo a paleta colorida nas primeiras 25 divisões

# Definindo o mapa de cores final sem tons de cinza
cmap_TbINPE_adjusted = cm.ListedColormap(cmapPB_adjusted)


# ---------------------------------------------------------------------------------
# -- PLOTEANDO OS DADOS COM A PALETA SEM CINZA E BARRA DE CORES VERTICAL
# ---------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------
# -- PLOTEANDO OS DADOS COM A BARRA DE CORES AO LADO DIREITO
# ---------------------------------------------------------------------------------
for i in arquivos:
    if i.endswith('.nc'):  # Apenas arquivos com extensão .nc
        try:
            arq_entrada = xr.open_dataset(os.path.join(DIRFIGS, i), engine='netcdf4')
            
            data_str = i.split('_')[1][:12]
            print(f'Criando a imagem da data {data_str}')

            ch13 = arq_entrada.Band1
            ch13.data = ch13.data / 100 - 273.15  # Convertendo de Kelvin para Celsius

            fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
            # Adicionando os continentes
            ax.add_feature(cfeature.LAND, edgecolor='black')
            ax.add_feature(cfeature.COASTLINE)
            ax.add_feature(cfeature.BORDERS, linestyle=':')

            # Adicionando o shapefile dos estados
            shapefile = list(shpreader.Reader(shapefile_path).geometries())
            ax.add_geometries(shapefile, ccrs.PlateCarree(), edgecolor='black', facecolor='none', linewidth=0.3)

            # Plotando os dados do canal 13
            img = ch13.plot(ax=ax, cmap=cmap_TbINPE_adjusted, transform=ccrs.PlateCarree(), vmin=-90, vmax=55,
                cbar_kwargs={
                    "label": "Brightness Temperature (°C)", 
                    "orientation": "vertical",  # Barra de cores vertical
                    "pad": 0.05,                # Distância da barra para o gráfico
                    "aspect": 30,               # Controle da espessura da barra
                    "shrink": 0.8,              # Ajustar a altura da barra de cores
                    "ticks": np.arange(-90, 60, 10),  # Personalizar os ticks
                    "extend": 'neither'  # Define os limites exatos sem estender a barra além do vmin e vmax
                })

            # Ajustando os limites do gráfico para o intervalo desejado
            ax.set_extent([-60, -30, -40, -15], crs=ccrs.PlateCarree())

            # Linhas de grade
            gl = ax.gridlines()
            gl.bottom_labels = True
            gl.left_labels = True

            # Título
            plt.title(f"Akará GOES16 CH13 - {data_str} UTC", loc='left') 
            file_name = f"AKARA_{data_str}.png"
            plt.savefig(os.path.join(new_dir, file_name), dpi=300)
            plt.close(fig)
        except Exception as e:
            print(f"Erro ao processar o arquivo {i}: {e}")
    else:
        print(f"Ignorando arquivo não NetCDF: {i}")
