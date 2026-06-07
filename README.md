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
├── get_sat.py              # Download
├── produto_download.py     # Funções de download
├── plot_sat.py             # Plotagem
├── produt_plot.py          # Funções de plotagem
├── shapefile/              # Shapefiles do Brasil
└── fig_dados/              # Dados e imagens
```

## Autoria
Victor Ranieri - Desenvolvimento, lógica e implementação

DeepSeek - Organização do código e documentação

## Próximas etapas

Criação de módulo de imagem de satélite com reanálise ERA5 ou previsões GFS (plot_model.py)

útlima atualização: 2026/06/07

