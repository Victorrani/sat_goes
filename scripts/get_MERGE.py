import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import wget

print()
print('###################')
print('SCRIPT get_MERGE.py')
print('###################')
print()

url_base = 'https://ftp1.cptec.inpe.br/modelos/tempo/MERGE/GPM/HOURLY/'

print(f'Fazendo download das imagens disponíveis no endereço:\n{url_base}\n')

# Entrada da data inicial
print('Escreva a data inicial para o início do download (formato: YYYYMMDDHH):')
data_inicial = input().strip()

# Entrada da data final
print('Escreva a data final para o fim do download (formato: YYYYMMDDHH):')
data_final = input().strip()

# Entrada do diretório de destino
print('Escreva o nome do diretório onde os arquivos serão salvos:')
diretorio_destino = input().strip()

# Converter as entradas para objetos datetime
try:
    dt_inicial = datetime.strptime(data_inicial, '%Y%m%d%H')
    dt_final = datetime.strptime(data_final, '%Y%m%d%H')
except ValueError:
    print('Erro: Formato de data inválido. Use o formato YYYYMMDDHH.')
    exit()

# Verificar se a data final é maior ou igual à inicial
if dt_final < dt_inicial:
    print('Erro: A data final deve ser maior ou igual à data inicial.')
    exit()

# Criar a pasta para os downloads
os.makedirs(diretorio_destino, exist_ok=True)

# Iterar pelas datas no intervalo
data_atual = dt_inicial
while data_atual <= dt_final:
    # Construir o nome do arquivo e o URL
    ano = data_atual.strftime('%Y')
    mes = data_atual.strftime('%m')
    dia = data_atual.strftime('%d')
    hora = data_atual.strftime('%H')

    arquivo_nome = f'MERGE_CPTEC_{ano}{mes}{dia}{hora}.grib2'
    url_arquivo = f'{url_base}{ano}/{mes}/{dia}/{arquivo_nome}'
    print(f'Baixando: {url_arquivo}')
    
    # Caminho local do arquivo
    caminho_arquivo = os.path.join(diretorio_destino, arquivo_nome)
    
    # Baixar o arquivo se ele não existir localmente
    if not os.path.exists(caminho_arquivo):
        try:
            wget.download(url_arquivo, caminho_arquivo)
            print(f'\nDownload concluído: {caminho_arquivo}')
        except Exception as e:
            print(f'\nErro ao baixar {url_arquivo}: {e} O arquivo provavelmente não existe')
    else:
        print(f'O arquivo {caminho_arquivo} já existe. Pulando download.')

    # Incrementar para a próxima hora (ou intervalo desejado)
    data_atual += timedelta(hours=24)

print('\nDownload concluído para todas as datas no intervalo!')
