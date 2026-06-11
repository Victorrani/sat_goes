# SAT_GOES - Download e Plotagem de Dados GOES

Scripts para baixar e plotar imagens dos satélites **GOES-16** e **GOES-19** do CPTEC/INPE.

## Funcionalidades

- Download de canais individuais (ch01 a ch16);
- Download de True Color (canais 1,2,3);
- Plotagem automática com shapefile do Brasil;
- Domínio América do Sul e Central;

## Como usar

Criar o ambiente conda com dependências

```bash
conda env create -f environment.yml

### Download

python get_sat.py

### Plot

python plot_sat.py
```

## Estrutura
```bash
sat_goes/
├── environment.yml # ambiente estável
├── fig_dados # diretório para dados e imagens
├── get_IMERG.py # download IMERG half Hourly
├── get_MERGE.py # download MERGE 
├── get_sat.py # download dados de satélite
├── IMERG_data # diretório para dados IMERG
├── model_sat.py # script em desenvolvimento
├── plot_sat.py # script de plot
├── produto_download.py # script auxiliar download
├── produt_plot.py # script auxiliar plot
├── README.md
└── shapefile # shapefile BR


```

## Autoria
Victor Ranieri - Desenvolvimento, lógica e implementação

DeepSeek - Organização do código e documentação

## Próximas etapas

Criação de módulo de imagem de satélite com reanálise ERA5 ou previsões GFS (plot_model.py)

útlima atualização: 2026/06/07

O que funciona 100%
-Downloads e plots True color GOES16 e GOES19
-Downloads e plots ch02 e ch13 GOES16 e GOES19
-Download dados MERGE e IMERGE -> ainda faltam alguns ajustes mas da para usar


