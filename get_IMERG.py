import earthaccess
import os
import xarray as xr
from pathlib import Path
import re
import h5py
import subprocess
from datetime import datetime
import numpy as np

start_time = datetime.now()
print('Get IMERG data from NASA Earthdata half-hourly precipitation product (GPM_3IMERGHH)')
print(f'Inicio do programa: {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

diretorio_atual = os.getcwd()
auth = earthaccess.login(strategy="interactive")

data_inicial = input("Digite a data inicial (formato YYYY-MM-DD): ")
data_final = input("Digite a data final (formato YYYY-MM-DD): ")
#dominio = input("Digite o domínio (formato: lon_min,lat_min,lon_max,lat_max): ")
#lon_min, lat_min, lon_max, lat_max = map(float, dominio.split(","))

results = earthaccess.search_data(
    short_name="GPM_3IMERGHH",
    version="07",
    temporal=(f"{data_inicial} 00:00:00", f"{data_final} 23:30:00") 
)

download_path = os.path.join(diretorio_atual, "IMERG_data")
os.makedirs(download_path, exist_ok=True)

downloaded_files = earthaccess.download(results, local_path=download_path)
print("Download concluído com sucesso!")
print()
print("Processando os dados HDF5 e transformando em netCDF")
print()

# Converter HDF5 para NetCDF
dir_path = Path(download_path)
files = list(dir_path.rglob("*.HDF5"))
files.sort()  

nc_files = []  # Lista para guardar os arquivos netCDF criados

for f in files:
    print("Processando:", f.name)
    
    match = re.search(r"(IMERG\.\d{8}-S\d{6})", f.name)
    if not match:
        print(f"  → Padrão não encontrado, pulando...")
        continue
    
    new_name = str(dir_path / (match.group(1) + ".nc"))
    time_str = match.group(1)
    
    # Converte para datetime
    dt = datetime.strptime(time_str, "IMERG.%Y%m%d-S%H%M%S")
    
    with h5py.File(f, "r") as h:
        precip = h["Grid/precipitation"][:]
        lat = h["Grid/lat"][:]
        lon = h["Grid/lon"][:]
    
    precip = precip[0]
    
    if precip.shape == (lon.shape[0], lat.shape[0]):
        precip = precip.T
    
    ds = xr.Dataset(
        data_vars={
            "precip": (("time", "lat", "lon"), precip[np.newaxis, :, :])
        },
        coords={
            "time": [dt],
            "lat": lat,
            "lon": lon
        }
    )
    
    ds["lat"].attrs["units"] = "degrees_north"
    ds["lon"].attrs["units"] = "degrees_east"
    ds["precip"].attrs["units"] = "mm"
    
    # Salva como NetCDF
    ds.to_netcdf(new_name)
    print(f"  → Salvo: {new_name}")
    nc_files.append(Path(new_name))

# Apagar arquivos HDF5 originais
for f in files:
    print("Apagando:", f.name)
    f.unlink()

#print()
#print("Reduzindo domínio dos arquivos NetCDF...")
#print()
#
## Reduzindo o domínio
#reduced_files = []
#for file in nc_files:
#    out_file = file.with_name(file.stem + "_reduced.nc")
#    cmd = f"cdo sellonlatbox,{lon_min},{lon_max},{lat_min},{lat_max} {file} {out_file}"
#    print(f"Executando: {cmd}")
#    subprocess.run(cmd, shell=True, check=True)
#    reduced_files.append(out_file)
#    print(f"  → Criado: {out_file.name}")
#
## Apagar arquivos NetCDF originais (não reduzidos)
#for file in nc_files:
#    print("Apagando arquivo original:", file.name)
#    file.unlink()
#
## Juntar todos os arquivos reduzidos em um único arquivo
#merged_file = dir_path / "IMERG_clima.nc"
#input_files = " ".join(str(f) for f in reduced_files)
#cmd_merge = f"cdo mergetime {input_files} {merged_file}"
#print()
#print("Juntando todos os arquivos...")
#print(f"Comando: {cmd_merge}")
#subprocess.run(cmd_merge, shell=True, check=True)
#print(f"  → Arquivo final criado: {merged_file}")
#
## Apagar os arquivos reduzidos individuais
#for file in reduced_files:
#    print("Apagando arquivo reduzido:", file.name)
#    file.unlink()

#print()
#print("Concluído! Arquivo final:", merged_file)

end_time = datetime.now()
print("Fim:", end_time)

duration = end_time - start_time
print("Duração total:", duration)