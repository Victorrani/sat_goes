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

DIRSCRIPT = os.getcwd()
DIRSHAPE = os.path.join(DIRSCRIPT, 'shapefile')
DIRFIG = os.path.join(DIRSCRIPT, 'fig_dados')

# Listando casos disponíveis
casos = os.listdir(DIRFIG)

if not casos:
    print("Nenhum caso encontrado no diretório de figuras.")
else:
    print("Casos disponíveis:")
    print("\n".join(casos))

    # Interação com o usuário para escolha do caso
    escolha_mapa = input('Qual caso você deseja plotar o mapa? ')
    
    if escolha_mapa in casos:
        print(f'Você escolheu o caso: {escolha_mapa}')
    else:
        print(f'O caso "{escolha_mapa}" não foi encontrado.')

caminho_escolha = os.path.join(DIRFIG, escolha_mapa)

canais = [arquivo for arquivo in os.listdir(caminho_escolha) if arquivo.startswith('ch')]

print("\nCanais disponíveis:")
print("\n".join(canais))
escolha_canal = input('Qual canal você deseja plotar o mapa? ')
canal_escolha = os.path.join(caminho_escolha, escolha_canal)

print(canal_escolha)

caminho_fig = os.path.join(caminho_escolha, 'fig')
if not os.path.exists(caminho_fig):
    os.makedirs(caminho_fig)
    print(f'Diretório "fig" criado em: {caminho_fig}')
else:
    print(f'O diretório "fig" já existe em: {caminho_fig}')

# Lendo o shapefile do Brasil (certifique-se de que o caminho esteja correto)
shapefile_path = os.path.join(DIRSHAPE, 'BR_UF_2019.shp')

# ----------------------------------------------------------------------
# -- DEFININDO PALETAS DE CORES SEM CINZA
# ----------------------------------------------------------------------

# Paleta sem tons de cinza, ajustando as cores para temperaturas
palCO_new_adjusted = ["#FF0000", "#FFC0CB", "#ADD8E6", "#00008B", "#FFFF00", "#FFA500"]


cmapCO_new_adjusted = cm.LinearSegmentedColormap.from_list("IR_clean_adjusted", palCO_new_adjusted, N=20)

# Aplicando a paleta suave com 25 pontos (metade do original)
cmapCO_adjusted = cmapCO_new_adjusted(np.linspace(0, 1, 80))  # 25 divisões na paleta colorida

# Criando a paleta sem cinza com 120 pontos e adicionando as cores ajustadas
cmapPB_adjusted = cm.LinearSegmentedColormap.from_list("", ["white", "black"])
cmapPB_adjusted = cmapPB_adjusted(np.linspace(0, 1, 145))  # 120 divisões na paleta total
cmapPB_adjusted[:80, :] = cmapCO_adjusted  # Inserindo a paleta colorida nas primeiras 25 divisões

# Definindo o mapa de cores final sem tons de cinza
cmap_TbINPE_adjusted = cm.ListedColormap(cmapPB_adjusted)

arquivos_netCDF = sorted([f for f in os.listdir(canal_escolha) if f.endswith('.nc')])
for i in arquivos_netCDF:
    if i.endswith('.nc'):  # Apenas arquivos com extensão .nc
        try:
            arq_entrada = xr.open_dataset(os.path.join(canal_escolha, i), engine='netcdf4')
            
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
            file_name = f"ch13_AKARA_{data_str}.png"
            plt.savefig(os.path.join(caminho_fig, file_name), dpi=300)
            plt.close(fig)
        except Exception as e:
            print(f"Erro ao processar o arquivo {i}: {e}")
    else:
        print(f"Ignorando arquivo não NetCDF: {i}")
