import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timedelta
import wget


# Criando os diretórios para figuras e dados baseados no diretório atual
DIRSCRIPT = os.getcwd()

DIRFIG = os.path.join(DIRSCRIPT, 'fig_dados')
os.makedirs(DIRFIG, exist_ok=True)

print()
print('#################')
print('SCRIPT get_sat.py')
print('#################')
print()

# Base da URL para download das imagens de satélite GOES16 do CPTEC
url_base = 'https://ftp1.cptec.inpe.br/goes/goes16/retangular/'
print(f'Fazendo download das imagens disponíveis no endereço:\n{url_base}\n')

# Verificando os canais disponíveis
response = requests.get(url_base)
soup = BeautifulSoup(response.text, 'html.parser')

# Extraindo os canais disponíveis
canais_disponiveis = [link.get('href')[:-1] for link in soup.find_all('a') if link.get('href').startswith('ch')]
print('Os canais disponíveis para download são:')
print(', '.join(canais_disponiveis), '\n')

# Escolha do canal pelo usuário
canal_download = input('Insira o canal que deseja fazer o Download: ')
url_canal = f"{url_base}{canal_download}/"
print()

# Verificando os anos disponíveis para o canal selecionado
response = requests.get(url_canal)
soup = BeautifulSoup(response.text, 'html.parser')
ano_disponivel = [link.get('href')[:-1] for link in soup.find_all('a') if link.get('href').startswith('2')]

print('Os anos disponíveis são:')
print(', '.join(ano_disponivel), '\n')

# Escolha do ano pelo usuário
ano_download = input('Insira o ano que deseja fazer o Download: ')
url_ano = f"{url_canal}{ano_download}/"

# Verificando os meses disponíveis para o ano selecionado
response = requests.get(url_ano)
soup = BeautifulSoup(response.text, 'html.parser')
mes_disponivel = [link.get('href')[:-1] for link in soup.find_all('a') if link.get('href').startswith(('0', '1'))]

print('Os meses disponíveis são:')
print(', '.join(mes_disponivel), '\n')

# Escolha do mês pelo usuário
mes_download = input('Insira o mês que deseja fazer o Download: ').zfill(2)
url_mes = f"{url_ano}{mes_download}/"
url_base_download = url_mes
raiz_dado = url_mes

# Escolha dos dias e horários de início e fim para o download
dia_inicio = input('Escolha o dia do início para o download: ').zfill(2)
hora_inicio = input('Escolha a hora do início para o download: ').zfill(2)

dia_fim = input('Escolha o dia do fim para o download: ').zfill(2)
hora_fim = input('Escolha a hora do fim para o download: ').zfill(2)

# Criando os diretórios para armazenar os dados
diretorio_data = os.path.join(DIRFIG, f"{ano_download}{mes_download}{dia_inicio}_{dia_fim}")
diretorio_canal = os.path.join(diretorio_data, canal_download)

# Verifica se os diretórios existem e os cria se não existirem
os.makedirs(diretorio_data, exist_ok=True)
os.makedirs(diretorio_canal, exist_ok=True)

passo = int(input('Digite o passo de tempo em minutos: '))
# Definindo o passo de tempo em minutos
passo_tempo = passo

# Construindo as strings de data para início e fim
dado_inicio = f"{ano_download}{mes_download}{dia_inicio}{hora_inicio}00"
dado_fim = f"{ano_download}{mes_download}{dia_fim}{hora_fim}00"

# Mensagem informativa sobre a seleção do canal e datas
print(f'\nFoi selecionado o canal "{canal_download}" para as datas:')
print(f' - Data de início: {dado_inicio}')
print(f' - Data final:    {dado_fim}')
print(f' - Passo de tempo: {passo_tempo} minutos\n')
332483
# Verificando a existência das datas escolhidas
print(f'Será verificado a existência das datas escolhidas...\n')

# Coletando os dados disponíveis
dado_disponivel = []
response = requests.get(raiz_dado)
soup = BeautifulSoup(response.text, 'html.parser')

for link in soup.find_all('a'):
    href = link.get('href')
    if href.startswith('S10'):
        prefixo = href[:10]  # Prefixo do arquivo
        sufixo = href[-3:]   # Sufixo (extensão do arquivo)
        data = href.split('_')[1].replace(sufixo, '')  # Extrai a data do nome do arquivo
        dado_disponivel.append(data)

# Convertendo dado_inicio e dado_fim para datetime
inicio = datetime.strptime(dado_inicio, '%Y%m%d%H%M')
fim = datetime.strptime(dado_fim, '%Y%m%d%H%M')

# Gerando a lista de timestamps a serem verificados
dados_download = []
while inicio <= fim:
    dados_download.append(inicio.strftime('%Y%m%d%H%M'))
    inicio += timedelta(minutes=passo_tempo)

# Verificando a existência dos dados e fazendo o download
for timestamp in dados_download:
    if timestamp in dado_disponivel:
        print(f'O dado {timestamp} existe na lista de dados disponíveis.')
        print('Fazendo o Download...')
        
        # Constrói a URL de download
        download = f"{raiz_dado}{prefixo}{timestamp}{sufixo}"
        arquivo_local = os.path.join(diretorio_canal, f"{prefixo}{timestamp}{sufixo}")

        # Fazendo o download e salvando no caminho especificado
        wget.download(download, arquivo_local)
        
    else:
        print(f'O dado {timestamp} NÃO existe na lista de dados disponíveis. Seguindo para a próxima data.')
