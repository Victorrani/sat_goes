# SAT_GOES - Download e Plotagem de Dados GOES

**Scripts para download e visualização de imagens dos satélites GOES-16 e GOES-19, desenvolvidos para a comunidade brasileira de meteorologia.**

> **Autor:** Victor Ranieri (IAG/USP) | Mestrando em Meteorologia no PGMET/CPTEC/INPE  
> **Objetivo:** Criar um repositório **aberto**, **customizável**, **simples** e totalmente em **português** para facilitar a utilização e divulgação de ferramentas de análise de satélite e chuva entre estudantes e profissionais de meteorologia no Brasil.

---
Funcionalidades
Download de canais individuais (ch01 a ch16);

Download de True Color (composição RGB - canais 1, 2 e 3);

Download de SWD (Split Window Difference - canais 13 e 15);

Download de CPD (Cloud Phase Difference - canais 11 e 14);

Plotagem automática com shapefile do Brasil;

Paleta de cores customizável;

Domínio focado na América do Sul e Central;

Integração com dados de precipitação (MERGE e IMERG – em desenvolvimento).
---

## 📦 Como usar

Crie o ambiente Conda com todas as dependências:

```bash
conda env create -f environment.yml
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
├── produt_plot.py
├── README.md
├── scripts
│   ├── get_IMERG.py
│   ├── get_MERGE.py
│   └── model_sat.py
└── shapefile

```

O que funciona 100%
Download e plotagem True Color para GOES-16 e GOES-19;

Download e plotagem SWD (Split Window Difference) para GOES-16 e GOES-19;

Download e plotagem CPD (Cloud Phase Difference) para GOES-16 e GOES-19;

Download e plotagem de canais individuais (ch01 a ch16) para GOES-16 e GOES-19;

Download de dados de precipitação MERGE e IMERG;
__________________________________________________________________

🚀 Próximos passos:
-> IMERG: imagens de acumulado de chuva e GIFs animados

-> MERGE: imagens de acumulado de chuva e GIFs animados

-> Full Disk GOES: download diretamente do AWS (imagens continentais completas)

-> Novos satélites: expansão para outros sensores e plataformas

-> Script exclusivo para GIFs: automatizar animações temporais

-> Integração futura: módulo de satélite + reanálise ERA5 ou previsões GFS (plot_model.py)

📸 Exemplos de plotagem
Furacão Melissa (GOES-19 True Color)
![Furacão Melissa - GOES-19 True Color](/docs/MELISSA_GOES19_202510261500.png)

Ciclone Akará (GOES-16 ch02)
![Ciclone Akará - GOES-16 ch02](/docs/AKARA_GOES16_ch02_202402191600.png)

Exemplo ch04 cor personalizada
![Domínio completo - GOES-19 ch04](/docs/GOES19_ch04_202507101500.png)


👥 Autoria
Victor Ranieri – Desenvolvimento, lógica e implementação

DeepSeek – Organização do código e documentação

📅 Última atualização
2026/06/12

Ajude a encontrar/criar paletas de cores para as imagens.

Contato: victor.ranieri@inpe.br | victor.ranieri90@gmail.com


