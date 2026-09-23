"""
plot_sat.py - Script principal para plotagem de imagens GOES
"""

from produto_plot import (
    listar_casos_disponiveis,
    selecionar_caso,
    obter_extent_usuario,
    obter_titulo_usuario,
    obter_colormap_usuario,
    plot_prod,
    detectar_produtos_disponiveis,
    detectar_canais_disponiveis,
)
import os

def main():
    print()
    print('#'*50)
    print('# SCRIPT PLOT_SAT.PY')
    print('#'*50)
    print()

    # 1. Listar casos disponíveis
    casos = listar_casos_disponiveis()

    if not casos:
        print("\n❌ Nenhum caso encontrado! Execute o download primeiro.")
        return

    # 2. Selecionar caso
    caso = selecionar_caso(casos)
    if not caso:
        return

    # 3. Detectar todos os produtos possíveis para este caso (uma pasta pode
    # satisfazer vários ao mesmo tempo, ex: um caso com os 16 canais baixados)
    caminho_caso = os.path.join('fig_dados', caso)
    canais = detectar_canais_disponiveis(caminho_caso)
    produtos_disponiveis = detectar_produtos_disponiveis(caminho_caso)

    print("\n" + "="*50)
    print("🔍 PRODUTOS DISPONÍVEIS PARA ESTE CASO")
    print("="*50)

    opcoes = list(produtos_disponiveis)
    if canais:
        opcoes.append('Single_Band')

    if not opcoes:
        print("❌ Nenhum canal encontrado neste caso!")
        return

    for i, p in enumerate(opcoes, 1):
        print(f"   {i}. {p}")

    escolha = input("\nEscolha o produto (número): ").strip()
    try:
        produto = opcoes[int(escolha) - 1]
    except (ValueError, IndexError):
        print(f"❌ Opção inválida! Escolha entre 1 e {len(opcoes)}.")
        return

    print(f"\n✅ Produto selecionado: {produto}")

    cmap = obter_colormap_usuario() if produto == 'Single_Band' else None

    # 4. Configurar extent
    print("\n" + "="*50)
    print("🌍 CONFIGURAÇÃO DA ÁREA")
    print("="*50)
    opcao_extent = input("Deseja definir área personalizada? (s/n): ").strip().lower()
    extent = obter_extent_usuario() if opcao_extent == 's' else None

    # 5. Configurar título
    print("\n" + "="*50)
    print("📝 CONFIGURAÇÃO DO TÍTULO")
    print("="*50)
    opcao_titulo = input("Deseja título personalizado? (s/n): ").strip().lower()
    titulo = obter_titulo_usuario() if opcao_titulo == 's' else None

    # 6. Executar plotagem
    print("\n" + "="*50)
    print(f"🚀 INICIANDO PLOTAGEM: {produto.upper()}")
    print("="*50)
    plot_prod(caso, produto, extent=extent, titulo=titulo, cmap=cmap)

if __name__ == "__main__":
    main()
