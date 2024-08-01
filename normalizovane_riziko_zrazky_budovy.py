# Výpočet normalizovaného rizika - zrážky/horúčavy Martin Jančovič
# matica https://miro.com/app/board/uXjVNCzAs5g=/
# indikátory https://magistratba-my.sharepoint.com/:x:/g/personal/eva_culova_bratislava_sk/ES6jR9bdjZlHvCbhXXnDVFUB56SHKUeK7lQ9RJaBk90oZA?e=WCNTdy
# podklady https://magistratba-my.sharepoint.com/:f:/g/personal/eva_culova_bratislava_sk/Erdz4xq3MZBGmdlj_U1NiUcB-OOtvOdDaBDW5R_o9vn53A?e=rCeygs

from osgeo import gdal
import os
import numpy as np

# TU ZADAJ RASTRE S KTORÝMI BUDEŠ PRACOVAŤ (KÓD JE NASTAVENÝ NA 6 RASTROV, ktoré sú tvorené podkladovými rastrami podľa potreby), rastre musia byť normalizované, pozor na hodnoty nodata, aby tam neboli nekorektné čísla, extent musia byť rovnaké pre všetky rastre

# Adresáre s rastrovými súbormi zadanie váh a ?delenie? (prvé číslo váha pre raster, ?druhé delenie súčtom všetkých váh?)     
folder_paths = [
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/EC', {"EnviroZ_N": 0.5, "Erozia_N": 1, "Nepriep_N": 1, "Pamiatky_N": 0.3, "PodZvod_N": 1, "sumarea_N": 1}, "EC"),
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/SC', {"h_neprod_N": 1, "h_nezam_N": 1,"DvHN_N_mea": 1}, "SC"),
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/EK', {"NDVI_N": 0.5, "reten_N": 1}, "EK"),
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/SDK', {"h_produk_N": 1, "h_VS_N": 1}, "SDK"),
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/H', {"Q100area_N": 1, "Z20mm_N": 1}, "H"),
    ('C:/Monika_Secap_code/zrazky/rasters/Budovy/Expo', {"budOVPriemDop_sumarea_N": 1, "obytna_rozloha_sumarea_N": 1, "topowet_N": 1}, "Expo")
]

#EC Enviroz_N - počet environmentálnych záťaží
#EC Erozia_N - územie ohrozené potenciálnou eróziou
#EC Nepriep_N - podiel nepriepustného povrchu
#EC Pamiatky_N - pamiatkovo chránené územia, ochranné pásma
#EC PodZvod_N - priemerná úroveň hladiny podzemnej vody
#EC sumarea_N - územie ohrozené zosuvmi

#SC h_neprod_N - hustota obyvateľov v neproduktívnom veku
#SC h_nezam_N - hustota nezamestnaných obyvateľov
#SC DvHN_N_mea - hustota poberateľov dávky v hmotnej núdzi

#EK NDVI_N - priemerný normalizovaný vegetačný index
#EK reten_N - priemerná retenčná kapacita na základe priepustnosti pôd a využitia krajinnej pokrývky (ekosystémovú služba)

#SDK h_produk_N - hustota obyvateľov produktívnom veku
#SDK h_VS_N - hustota obyvateľov s najvyšším stupňom vzdelania (všetky úrovne vysokoškolského vzdelania)

#H Q100area_N - rozloha záplavového územia Q100 
#H Z20mm_N - priemerný počet dní s úhrnom nad 20 mm

#Expo budOVPriemDop_sumarea_N - zastavanosť ostatnými budovami
#Expo obytna_rozloha_sumarea_N - zastavanosť budovami primárne určenými na bývanie
#Expo topowet_N - topografický index vlhkosti

# TU SA BUDÚ VYTVÁRAŤ VÝSTUPY

# Výstupný adresár
output_folder = 'C:/Monika_Secap_code/zrazky/rasters/Budovy/vystupy'


# NAČÍTANIE RASTROV A PRVOTNÉ MATEMATICKÉ OPERÁCIE SO VSTUPNÝMI SÚBORMI

def process_folder(folder_path, target_weights, summary_name, output_folder):
    # Seznam pro ukládání cest k rastrovým souborům
    raster_files = []

    # Načtěte všechny rastrové soubory
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Pokud název souboru obsahuje jeden z cílových názvů
        for target, weight in target_weights.items():
            if target in filename:
                try:
                    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)
                    if dataset is not None:
                        raster_files.append((dataset, weight))
                        print(f"Raster file loaded: {file_path}")
                except Exception as e:
                    print(f"Error loading raster file {file_path}: {e}")

    # Pokud jsou načtené alespoň dva rastrové soubory
    if len(raster_files) >= 2:
        # Načtěte první rastrový soubor a získejte jeho velikost
        first_raster, first_weight = raster_files[0]
        rows = first_raster.RasterYSize
        cols = first_raster.RasterXSize

        # Inicializujte pole pro ukládání hodnot
        result_array_sum = np.zeros((rows, cols), dtype=np.float32)

        # Násobení hodnot z rastrových souborů s příslušnými váhami a sčítání
        for raster, weight in raster_files:
            band = raster.GetRasterBand(1)
            data = band.ReadAsArray()

            # Ověřte, zda mají rastrové soubory stejné rozměry
            if data.shape == (rows, cols):
                result_array_sum += data * weight
            else:
                print(f"Skipping raster file {raster.GetDescription()} due to mismatched dimensions.")
                break

        # Vytvořte výstupní rastrový soubor pro sčítání
        output_path_sum = os.path.join(output_folder, f'{summary_name}_summary.tif')
        driver_sum = gdal.GetDriverByName('GTiff')
        output_raster_sum = driver_sum.Create(output_path_sum, cols, rows, 1, gdal.GDT_Float32)

        # Získejte band a zapíšte data pro sčítání
        output_band_sum = output_raster_sum.GetRasterBand(1)
        output_band_sum.WriteArray(result_array_sum)

        # Uložte transformaci a zavřete soubor pro sčítání
        output_raster_sum.SetGeoTransform(first_raster.GetGeoTransform())
        output_raster_sum.SetProjection(first_raster.GetProjection())
        output_raster_sum = None

        print(f"Result of summation saved to: {output_path_sum}")

        # Normalizujte výstupní rastrový soubor
        output_raster_normalized = gdal.Open(output_path_sum, gdal.GA_Update)

        if output_raster_normalized is not None:

            # Načtěte data z rastrového souboru
            band_normalized = output_raster_normalized.GetRasterBand(1)
            data_normalized = band_normalized.ReadAsArray()

            # Normalizujte hodnoty na rozsah 0 až 1
            normalized_data = (data_normalized - np.min(data_normalized)) / (np.max(data_normalized) - np.min(data_normalized))

            # Zapíšte normalizovaná data zpět do rastrového souboru
            band_normalized.WriteArray(normalized_data)

            # Uložte transformaci a zavřete soubor
            output_raster_normalized.SetGeoTransform(output_raster_normalized.GetGeoTransform())
            output_raster_normalized.SetProjection(output_raster_normalized.GetProjection())
            output_raster_normalized = None

            print(f"Normalized result saved to: {output_path_sum}")
        else:
            print(f"Error opening raster file: {output_path_sum}")
    else:
        print(f"Less than two raster files found in {folder_path}. Cannot perform summation.")


# NAČÍTANIE VÝSLEDNÝCH RASTROV Z PREDCHÁDZAJÚCEJ ČASTI KÓDU A ĎALŠIE MATEMATICKÉ OPERÁCIE

# Proces
for folder_path, target_weights, summary_name in folder_paths:
    process_folder(folder_path, target_weights, summary_name, output_folder)


# Cesty k výsledným souborům EC a SC
result_paths_EC_SC = [
    (output_folder, "EC"),
    (output_folder, "SC")
]

# Cesty k výsledným souborům EK a SDK
result_paths_EK_SDK = [
    (output_folder, "EK"),
    (output_folder, "SDK")
]

# Cesty k výslednému súboru H
result_paths_H = [
    (output_folder, "H"),
]

# Cesty k výslednému súboru Expo
result_paths_Expo = [
    (output_folder, "Expo")
]

# Načíta výsledky EC a SC
result_arrays_EC_SC = []

for result_path, result_name in result_paths_EC_SC:
    file_path = os.path.join(result_path, f'{result_name}_summary.tif')
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)

    if dataset is not None:
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        result_arrays_EC_SC.append(data)
        print(f"Result file loaded: {file_path}")
    else:
        print(f"Error loading result file {file_path}")

# Načíta výsledky EK a SDK
result_arrays_EK_SDK = []

for result_path, result_name in result_paths_EK_SDK:
    file_path = os.path.join(result_path, f'{result_name}_summary.tif')
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)

    if dataset is not None:
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        result_arrays_EK_SDK.append(data)
        print(f"Result file loaded: {file_path}")
    else:
        print(f"Error loading result file {file_path}")

# Načíta výsledky H
result_arrays_H = []

for result_path, result_name in result_paths_H:
    file_path = os.path.join(result_path, f'{result_name}_summary.tif')
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)

    if dataset is not None:
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        result_arrays_H.append(data)
        print(f"Result file loaded: {file_path}")
    else:
        print(f"Error loading result file {file_path}")

# Načíta výsledky Expo
result_arrays_Expo = []

for result_path, result_name in result_paths_Expo:
    file_path = os.path.join(result_path, f'{result_name}_summary.tif')
    dataset = gdal.Open(file_path, gdal.GA_ReadOnly)

    if dataset is not None:
        band = dataset.GetRasterBand(1)
        data = band.ReadAsArray()
        result_arrays_Expo.append(data)
        print(f"Result file loaded: {file_path}")
    else:
        print(f"Error loading result file {file_path}")

# Skontroluje či sú rozmery výsledkou rovnaké
if all(result.shape == result_arrays_EC_SC[0].shape for result in result_arrays_EC_SC) and \
   all(result.shape == result_arrays_EK_SDK[0].shape for result in result_arrays_EK_SDK) and \
   all(result.shape == result_arrays_H[0].shape for result in result_arrays_H) and \
   all(result.shape == result_arrays_Expo[0].shape for result in result_arrays_Expo):


# MATEMATICKÉ OPERÁCIE S NAČÍTANÝMI RASTRAMI
    
    # Sčítanie EC a SC
    total_result_EC_SC = sum(result_arrays_EC_SC)

    # Sčítanie EK a SDK
    total_result_EK_SDK = sum(result_arrays_EK_SDK)

    # Výsledok H
    total_result_H = result_arrays_H[0]

    # Výsledok Expo
    total_result_Expo = result_arrays_Expo[0]
    
    # Normalizácia
    total_result_EC_SC_normalized = (total_result_EC_SC - np.min(total_result_EC_SC)) / (np.max(total_result_EC_SC) - np.min(total_result_EC_SC))
    total_result_EK_SDK_normalized = (total_result_EK_SDK - np.min(total_result_EK_SDK)) / (np.max(total_result_EK_SDK) - np.min(total_result_EK_SDK))

    #AK BY SI POTREBOVAL NORMALIZOVAŤ ĎALŠIE SÚBORY
    #total_result_H_normalized = (total_result_H - np.min(total_result_H)) / (np.max(total_result_H) - np.min(total_result_H))
    #total_result_Expo_normalized = (total_result_Expo - np.min(total_result_Expo)) / (np.max(total_result_Expo) - np.min(total_result_Expo))

    # Uloženie do nového priečinka
    output_path_total_EC_SC = os.path.join(output_folder, 'CC_normalizovana_celkova_citlivost_EC_SC.tif')
    output_path_total_EK_SDK = os.path.join(output_folder, 'CDK_normalizovana_celkova_citlivost_EK_SDK.tif')

    driver_total = gdal.GetDriverByName('GTiff')

    # EC and SC
    output_raster_total_EC_SC = driver_total.Create(output_path_total_EC_SC, total_result_EC_SC.shape[1], total_result_EC_SC.shape[0], 1, gdal.GDT_Float32)
    output_band_total_EC_SC = output_raster_total_EC_SC.GetRasterBand(1)
    output_band_total_EC_SC.WriteArray(total_result_EC_SC_normalized)

    # Nastavenie geotransformácie pomocou získaného GDAL datasetu
    output_raster_total_EC_SC.SetGeoTransform(dataset.GetGeoTransform())
    output_raster_total_EC_SC.SetProjection(dataset.GetProjection())
    output_raster_total_EC_SC = None

    print(f"Normalized total result EC and SC saved to: {output_path_total_EC_SC}")

    # EK and SDK
    output_raster_total_EK_SDK = driver_total.Create(output_path_total_EK_SDK, total_result_EK_SDK.shape[1], total_result_EK_SDK.shape[0], 1, gdal.GDT_Float32)
    output_band_total_EK_SDK = output_raster_total_EK_SDK.GetRasterBand(1)
    output_band_total_EK_SDK.WriteArray(total_result_EK_SDK_normalized) 

   # Nastavenie geotransformácie pomocou získaného GDAL datasetu
    output_raster_total_EK_SDK.SetGeoTransform(dataset.GetGeoTransform())
    output_raster_total_EK_SDK.SetProjection(dataset.GetProjection())
    output_raster_total_EK_SDK = None

    print(f"Normalized total result EK and SDK saved to: {output_path_total_EK_SDK}")


# VÝPOČET CELKOVÁ ZRANITEĽNOSŤ 

# Sčítanie výsledkov CC a CDK  (CC + (1 - CDK))
total_result_CC_CDK = (total_result_EC_SC_normalized + (1 -total_result_EK_SDK_normalized))

# Normalizácia výsledku normalizovana_celkova_zranitelnost
total_result_CC_CDK = (total_result_CC_CDK - np.min(total_result_CC_CDK)) / (np.max(total_result_CC_CDK) - np.min(total_result_CC_CDK))

# Uloženie do nového priečinka
output_path_total_CC_CDK = os.path.join(output_folder, 'normalizovana_celkova_zranitelnost.tif')
driver_total_CC_CDK = gdal.GetDriverByName('GTiff')

# CC and CDK
output_raster_total_CC_CDK = driver_total_CC_CDK.Create(output_path_total_CC_CDK, total_result_CC_CDK.shape[1], total_result_CC_CDK.shape[0], 1, gdal.GDT_Float32)
output_band_total_CC_CDK = output_raster_total_CC_CDK.GetRasterBand(1)
output_band_total_CC_CDK.WriteArray(total_result_CC_CDK)

# Nastavenie geotransformácie pomocou získaného GDAL datasetu
output_raster_total_CC_CDK.SetGeoTransform(dataset.GetGeoTransform())
output_raster_total_CC_CDK.SetProjection(dataset.GetProjection())
output_raster_total_CC_CDK = None

print(f"Normalized total result CC and CDK saved to: {output_path_total_CC_CDK}")


# VÝPOČET NORMALIZOVANéHO RIZIKA

# Sčítanie výsledkov (normalizované riziko + H + EXPO)
total_result_RIZ = (total_result_CC_CDK + total_result_H + total_result_Expo)

# Normalizácia výsledku normalizovana_celkova_zranitelnost
total_result_RIZ = (total_result_RIZ - np.min(total_result_RIZ)) / (np.max(total_result_RIZ) - np.min(total_result_RIZ))

output_path_total_RIZ = os.path.join(output_folder, 'normalizovane_riziko.tif')
driver_total_RIZ = gdal.GetDriverByName('GTiff')

# Vytvorenie rastrového súboru pre normalizované riziko
output_raster_total_RIZ = driver_total_RIZ.Create(output_path_total_RIZ, total_result_RIZ.shape[1], total_result_RIZ.shape[0], 1, gdal.GDT_Float32)
output_band_total_RIZ = output_raster_total_RIZ.GetRasterBand(1)
output_band_total_RIZ.WriteArray(total_result_RIZ)

# Nastavenie geotransformácie pomocou získaného GDAL datasetu
output_raster_total_RIZ.SetGeoTransform(dataset.GetGeoTransform())
output_raster_total_RIZ.SetProjection(dataset.GetProjection())
output_raster_total_RIZ = None

print(f"Normalized total result CC and CDK saved to: {output_path_total_RIZ}")

info = gdal.Info(output_path_total_RIZ, options=["-stats"])
print(info)





