# SAT_GOES - Download e Plotagem de Dados GOES (fase 1)

**Scripts para download e visualização de imagens dos satélites GOES-16 e GOES-19, desenvolvidos para a comunidade brasileira de meteorologia.**

> **Autor:** Victor Ranieri (IAG/USP) | Mestrando em Meteorologia no PGMET/CPTEC/INPE  
> **Objetivo:** Criar um repositório **aberto**, **customizável**, **simples** e totalmente em **português** para facilitar a utilização e divulgação de ferramentas de análise de satélite e chuva entre estudantes e profissionais de meteorologia no Brasil.

---
Funcionalidades

Download de canais individuais - Single_Band (ch01 a ch16);

Download de True_Color (composição RGB - canais 1, 2 e 3);

Download de AirMass RGB (canais 8, 10, 12 e 13 - faixas oficiais NASA SPoRT);

Download de SWD - Split Window Difference (canais 13 e 15);

Download de CPD - Cloud Phase Difference (canais 11 e 14, fórmula CH14-CH11 conforme guia oficial CIMSS);

Download de WVD - Water Vapor - IR Difference (canais 8 e 13), plotado como destaque de overshooting top (fundo IR + máscara acima de um limiar em K, baseado no ATBD oficial);

Download de SOD - Split Ozone Difference (canais 12 e 13);

Download de SWVD - Split Water Vapor Difference (canais 8 e 10, faixa oficial -26,2 a 0,9K);

Período de download aceita datas completas (AAAAMMDDHH) e cruza meses/anos sem problema;

Detecção automática de todos os produtos disponíveis num caso já baixado (uma pasta pode conter canais de vários produtos ao mesmo tempo);

Plotagem automática com shapefile do Brasil e linhas de contorno com cor ajustada por produto (dourado ou preto, conforme o que for mais visível no fundo de cada um);

Título das figuras em duas linhas (data/hora em cima, identificação embaixo);

Paleta de cores customizável;

Domínio focado na América do Sul e Central, com suporte a área personalizada (extent);

Integração com dados de precipitação (MERGE e IMERG – em desenvolvimento).
---

## 📦 Como usar

Crie o ambiente Conda com todas as dependências:

```bash
conda env create -f environment.yml
```

Ou, se preferir pip/venv, instale as dependências essenciais:

```bash
pip install -r requirements.txt
```
Download dos dados de satélite

```bash
python 1.get_sat.py
```
Plotagem das imagens

```bash
python 2.plot_sat.py
```

📁 Estrutura do repositório (Ainda será melhorado)
```bash
├── 1.get_sat.py
├── 2.plot_sat.py
├── docs
├── environment.yml
├── fig_dados
├── produto_download.py
├── produto_plot.py
├── produtos_abi
├── README.md
├── requirements.txt
├── scripts
│   ├── get_IMERG.py
│   ├── get_MERGE.py
│   └── model_sat.py
└── shapefile

```
O que funciona 100%:

Download e plotagem de canais individuais - Single_Band (ch01 a ch16) para GOES-16 e GOES-19;

Download e plotagem True_Color para GOES-16 e GOES-19;

Download e plotagem AirMass RGB para GOES-16 e GOES-19;

Download e plotagem SWD (Split Window Difference) para GOES-16 e GOES-19;

Download e plotagem CPD (Cloud Phase Difference) para GOES-16 e GOES-19;

Download e plotagem WVD (Water Vapor - IR Difference / destaque de overshooting top) para GOES-16 e GOES-19;

Download e plotagem SOD (Split Ozone Difference) para GOES-16 e GOES-19;

Download e plotagem SWVD (Split Water Vapor Difference) para GOES-16 e GOES-19;

__________________________________________________________________

🚀 Próximos passos:

-> IMERG: imagens de acumulado de chuva e GIFs animados

-> MERGE: imagens de acumulado de chuva e GIFs animados

-> Full Disk GOES: download diretamente do AWS (imagens continentais completas)

-> Novos satélites: expansão para outros sensores e plataformas

-> Integração futura: módulo de satélite + reanálise ERA5 ou previsões GFS (plot_model.py)

-> SatView (fase 2) - Mudança de ambiente e programação mais avançada 

📸 Exemplos de plotagem
Furacão Melissa (GOES-19, 2025-10-28 16h UTC)

True_Color
![Furacão Melissa - GOES-19 - True Color](/docs/MELISSA_GOES19_202510281600.png)

Single_Band ch13 com paleta NOAA (IR realçado)
![Furacão Melissa - GOES-19 - ch13 NOAA](/docs/MELISSA_GOES19_ch13_noaa_202510281600.png)

AirMass RGB
![Furacão Melissa - GOES-19 - AirMass](/docs/MELISSA_GOES19_airmass_202510281600.png)

SWD (Split Window Difference)
![Furacão Melissa - GOES-19 - SWD](/docs/MELISSA_GOES19_swd_202510281600.png)

CPD (Cloud Phase Difference)
![Furacão Melissa - GOES-19 - CPD](/docs/MELISSA_GOES19_cpd_202510281600.png)

WVD (Water Vapor - IR Difference / destaque de overshooting top)
![Furacão Melissa - GOES-19 - WVD](/docs/MELISSA_GOES19_wvd_202510281600.png)

SOD (Split Ozone Difference)
![Furacão Melissa - GOES-19 - SOD](/docs/MELISSA_GOES19_sod_202510281600.png)

SWVD (Split Water Vapor Difference)
![Furacão Melissa - GOES-19 - SWVD](/docs/MELISSA_GOES19_swvd_202510281600.png)



👥 Autoria
Victor Ranieri – Desenvolvimento inicial, lógica inicial e implementação inicial

Claude ia – Organização do código, lógica avançada e documentação

DeepSeek ia - Organização do código, lógica avançada e documentação

📅 Última atualização
2026/09/23

Ajude a encontrar/criar paletas de cores para as imagens.

Contato: victor.ranieri@inpe.br | victor.ranieri90@gmail.com


