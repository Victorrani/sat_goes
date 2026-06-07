"""
plot_sat.py - Script principal para plotagem de imagens GOES
"""

import os
from produt_plot import (
    listar_casos_disponiveis,
    selecionar_caso,
    obter_extent_usuario,
    obter_titulo_usuario,
    plot_prod,
    detectar_canais_disponiveis
)

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
    
    # Verificar o que tem dentro do caso
    caminho_caso = os.path.join('fig_dados', caso)
    canais = detectar_canais_disponiveis(caminho_caso)
    
    # 3. Detectar automaticamente se é True Color ou Simple Channel
    print("\n" + "="*50)
    print("🔍 DETECTANDO PRODUTO")
    print("="*50)
    
    # Verificar se tem ch01, ch02, ch03
    if 'ch01' in canais and 'ch02' in canais and 'ch03' in canais:
        print("✅ Detectado: TRUE COLOR (canais 01, 02, 03 disponíveis)")
        print("\nOpções disponíveis:")
        print("   1. Plotar True Color")
        print("   2. Plotar canal individual")
        opcao = input("\nEscolha (1/2): ").strip()
        
        if opcao == '1':
            produto = 'true_color'
        else:
            produto = 'simple_channel'
    else:
        print("✅ Detectado: SIMPLE CHANNEL (canal único)")
        produto = 'simple_channel'
    
    # =========================================================
    # SATÉLITE É DETECTADO AUTOMATICAMENTE PELO NOME DA PASTA
    # Não precisa perguntar ao usuário!
    # =========================================================
    
    # 4. Definir extent (opcional)
    print("\n" + "="*50)
    print("🌍 CONFIGURAÇÃO DA ÁREA")
    print("="*50)
    opcao_extent = input("Deseja definir área personalizada? (s/n): ").strip().lower()
    
    extent = None
    if opcao_extent == 's':
        extent = obter_extent_usuario()
    
    # 5. Definir título (opcional)
    print("\n" + "="*50)
    print("📝 CONFIGURAÇÃO DO TÍTULO")
    print("="*50)
    opcao_titulo = input("Deseja título personalizado? (s/n): ").strip().lower()
    
    titulo = None
    if opcao_titulo == 's':
        titulo = obter_titulo_usuario()
    
    # 6. Executar plotagem (satélite será detectado automaticamente)
    plot_prod(caso, produto, extent=extent, titulo=titulo)

if __name__ == "__main__":
    main()