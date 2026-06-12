"""
plot_sat.py - Script principal para plotagem de imagens GOES
"""

from produt_plot import (
    listar_casos_disponiveis,
    selecionar_caso,
    obter_extent_usuario,
    obter_titulo_usuario,
    obter_colormap_usuario,
    plot_prod,
    detectar_se_e_true_color,
    detectar_canais_disponiveis
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
    
    # 3. Verificar produto disponível
    caminho_caso = os.path.join('fig_dados', caso)
    canais = detectar_canais_disponiveis(caminho_caso)
    eh_true_color = detectar_se_e_true_color(caminho_caso)
    
    print("\n" + "="*50)
    print("🔍 DETECTANDO PRODUTO")
    print("="*50)
    
    cmap = None
    
    if eh_true_color:
        print("✅ Detectado: TRUE COLOR (canais 01, 02, 03 disponíveis)")
        print("\nOpções disponíveis:")
        print("   1. Plotar True Color")
        print("   2. Plotar canal individual")
        opcao = input("\nEscolha (1/2): ").strip()
        
        if opcao == '1':
            produto = 'true_color'
        else:
            produto = 'simple_channel'
            cmap = obter_colormap_usuario()
    else:
        print("✅ Detectado: SIMPLE CHANNEL (canal único)")
        produto = 'simple_channel'
        cmap = obter_colormap_usuario()
    
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
    plot_prod(caso, produto, extent=extent, titulo=titulo, cmap=cmap)

if __name__ == "__main__":
    main()