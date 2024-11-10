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

caminho_fig = os.path.join(caminho_escolha, 'fig')
if not os.path.exists(caminho_fig):
    os.makedirs(caminho_fig)
    print(f'Diretório "fig" criado em: {caminho_fig}')
else:
    print(f'O diretório "fig" já existe em: {caminho_fig}')

ch01 = sorted(os.listdir(os.path.join(caminho_escolha, 'ch01')))
ch02 = sorted(os.listdir(os.path.join(caminho_escolha, 'ch02')))
ch03 = sorted(os.listdir(os.path.join(caminho_escolha, 'ch03')))

Rmin = 0
Rmax = 100.0
# Máximos e mínimos da componente Green
Gmin = 0
Gmax = 100.0
# Máximos e mínimos da componente Blue
Bmin = 0
Bmax = 100

shapefile_path = os.path.join(DIRSHAPE, 'BR_UF_2019.shp')
# Iterando sobre os arquivos em cada diretório ao mesmo tempo
for arquivo1, arquivo2, arquivo3 in zip(ch01, ch02, ch03):
    caminho_arquivo1 = os.path.join(caminho_escolha, 'ch01', arquivo1)
    caminho_arquivo2 = os.path.join(caminho_escolha, 'ch02', arquivo2)
    caminho_arquivo3 = os.path.join(caminho_escolha, 'ch03', arquivo3)
    
    data_str = arquivo1.split('_')[1][:12]
    print(data_str)
    arq1 = xr.open_dataset(caminho_arquivo1)
    ch01 = arq1.Band1
    ch01 = ch01.coarsen(lat=2, lon=2).mean()
    ch01.data = ch01.data/100
    arq2 = xr.open_dataset(caminho_arquivo2)
    ch02 = arq2.Band1
    ch02 = ch02.coarsen(lat=2, lon=2).mean()
    ch02.data = ch02.data/100
    arq3 = xr.open_dataset(caminho_arquivo3)
    ch03 = arq3.Band1
    ch03 = ch03.coarsen(lat=2, lon=2).mean()
    ch03.data = ch03.data/100


    R = np.flipud(ch02.data)
    aux = 0.45*ch02.data + 0.1*ch03.data + 0.45*ch01.data
    G = np.flipud(aux)
    B = np.flipud(ch01.data)

    R[R>Rmax] = Rmax
    G[G>Gmax] = Gmax
    B[B>Bmax] = Bmax
    R[R<Rmin] = Rmin
    G[G<Gmin] = Gmin
    B[B<Bmin] = Bmin

    R = (R - Rmin) / (Rmax - Rmin)
    G = (G - Gmin) / (Gmax - Gmin)
    B = (B - Bmin) / (Bmax - Bmin)

    gamma_R = 2
    gamma_G = 2
    gamma_B = 2
    R = R ** (1/gamma_R)
    G = G ** (1/gamma_G)
    B = B ** (1/gamma_B)

    RGB_NTC = np.stack([R, G, B], axis=2)

    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw={'projection': ccrs.PlateCarree()})
            
    # Adicionando os continentes
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    # Adicionando o shapefile dos estados
    shapefile = list(shpreader.Reader(shapefile_path).geometries())
    ax.add_geometries(shapefile, ccrs.PlateCarree(), edgecolor='black', facecolor='none', linewidth=0.3)
    # Plotando os dados do canal 13
    ax.pcolormesh(ch02.lon, ch02.lat, RGB_NTC[::-1])
    # Ajustando os limites do gráfico para o intervalo desejado
    ax.set_extent([-60, -30, -40, -15], crs=ccrs.PlateCarree())
    # Linhas de grade
    gl = ax.gridlines()
    gl.bottom_labels = True
    gl.left_labels = True
    # Título
    plt.title(f"Akará GOES16 True Color - {data_str} UTC", loc='left') 
    file_name = f"AKARA_{data_str}.png"
    plt.savefig(os.path.join(caminho_fig, file_name), dpi=100)
    plt.close(fig)
    arq1.close()
    arq2.close()
    arq3.close()


  
    


    