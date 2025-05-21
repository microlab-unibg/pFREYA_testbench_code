import numpy as np

def filtro(scatti):
    vett = []
    for i in scatti:
        if scatti[i] == 0 and scatti[i] == scatti[i+1]:
            print(f'{i} skippato')
        else:
            vett.append(scatti[i])
    return vett

current = np.array([
    -0.2500, -0.2600, -0.2700, -0.2800, -0.2900, -0.3000, -0.3100, -0.3125, -0.3150, -0.3175, -0.3200, -0.3225, -0.3250, -0.3275,
    -0.3300, -0.3325, -0.3350, -0.3375, -0.3400, -0.3425, -0.3450, -0.3475, -0.3500, -0.3525, -0.3550, -0.3575, -0.3600, -0.3625,
    -0.3650, -0.3675, -0.3700, -0.3800, -0.3900, -0.4000, -0.4100
])
current = current * (-1)


scatti = np.array([
    0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.001, 0.004, 0.020, 0.120, 0.276, 0.748, 2.965, 6.517,
    12.615, 20.769, 39.804, 53.804, 62.965, 76.406, 89.427, 95.874, 96.643, 98.671, 99.455, 99.762, 99.804, 99.870,
    99.873, 99.874, 99.877, 99.876, 99.877
])
scatti = scatti / 100


sdev = np.array([
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.011826188788394225, 0.023529411764705882, 0.052729417452377174,
    0.4096289565190565, 0.6105166113934668, 0.9030813118356668, 1.8714326733912776, 2.935005590868147, 3.465979872407771,
    4.801822219357332, 6.146288497684594, 6.435729585183396, 6.420465304166904, 5.1718472300020215, 3.214503997302682,
    1.345318455217989, 0.9513193795992587, 0.6702594114047627, 0.5241582072001558, 0.35005401481710163, 0.3402797744874216,
    0.1310787464169484, 0.13160984935616013, 0.1310787464169484, 0.1310087464169484, 0.13100084935616013, 0.1310000464169484
])
sdev = sdev / 100

def filtro(scatti):
    # --- 1. Trova dove iniziano i valori diversi da 0
    non_zero = np.where(scatti > 0)[0]
    start_index = non_zero[0] - 3 if non_zero[0] >= 3 else 0

    # --- 2. Trova dove iniziano i valori >99
    over_99 = np.where(scatti > 0.99)[0]
    end_index = over_99[3] if len(over_99) > 3 else len(scatti)

    return start_index, end_index


# --- 3. Slice i dati tra start_index e end_index
start, end = filtro(scatti)
scatti_filtered = scatti[start:end]
current_filtered = current[start:end]

# --- (Opzionale) stampa o verifica
print("scatti filtrato:", scatti_filtered)
print("current filtrato:", current_filtered)
