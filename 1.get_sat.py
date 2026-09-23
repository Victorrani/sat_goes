"""
get_sat.py - Script principal para download de imagens GOES
"""

import os
from produto_download import select_prod, normalizar_produto, PRODUTOS_VALIDOS

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
    print('\nOpções de produtos:')
    print('    Single_Band - Download de canal único')
    print('    True_Color  - Composição RGB (canais 1, 2, 3)')
    print('    AirMass     - Airmass RGB (canais 08, 10, 12, 13)')
    print('    SWD         - Split Window Difference (canais 13, 15)')
    print('    CPD         - Cloud Phase Difference (canais 11, 14)')
    print('    WVD         - Water Vapor - IR Difference (canais 08, 13)')
    print('    SOD         - Split Ozone Difference (canais 12, 13)')
    print('    SWVD        - Split Water Vapor Difference (canais 08, 10)')

    prod = normalizar_produto(input('\nEscolha o produto: '))

    if prod is None:
        print('❌ Produto inválido!')
        print(f"   Opções válidas: {', '.join(PRODUTOS_VALIDOS)}")
        return

    print(f'\n✅ Produto {prod} selecionado\n')
    
    # Chamar função de download
    select_prod(sat, prod)

if __name__ == "__main__":
    main()