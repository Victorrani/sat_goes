"""
get_sat.py - Script principal para download de imagens GOES
"""

import os
from produto_download import select_prod

def main():
    # Criar diretório base
    os.makedirs(os.path.join(os.getcwd(), 'fig_dados'), exist_ok=True)
    
    print()
    print('#'*50)
    print('# SCRIPT GET_SAT.PY')
    print('#'*50)
    print()

    # Selecionar satélite
    sat = input('Escolha o satélite (goes16 ou goes19): ').lower()
    
    if sat not in ['goes16', 'goes19']:
        print('❌ Satélite inválido!')
        return
    
    print(f'\n✅ Satélite {sat.upper()} selecionado\n')

    # Selecionar produto
    prod = input('Escolha o produto (true_color, simple_chanel ou swd): ').lower()
    
    if prod not in ['true_color', 'simple_chanel', 'swd']:  # CORRIGIDO: adicionei a aspa e corrigi o nome
        print('❌ Produto inválido!')
        print('   Opções válidas: true_color, simple_chanel, swd')
        return
    
    # Chamar função de download
    select_prod(sat, prod)

if __name__ == "__main__":
    main()