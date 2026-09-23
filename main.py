import requests
import numpy as np
import matplotlib.pyplot as plt

url = "https://api.open-elevation.com/api/v1/lookup?locations=48.164214,24.536044|48.164983,24.534836|48.165605,24.534068|48.166228,24.532915|48.166777,24.531927|48.167326,24.530884|48.167011,24.530061|48.166053,24.528039|48.166655,24.526064|48.166497,24.523574|48.166128,24.520214|48.165416,24.517170|48.164546,24.514640|48.163412,24.512980|48.162331,24.511715|48.162015,24.509462|48.162147,24.506932|48.161751,24.504244|48.161197,24.501793|48.160580,24.500537|48.160250,24.500106"

response = requests.get(url, verify=False)
data = response.json()
results = data["results"]
n = len(results)
print("Кількість вузлів:", n)
filename = "tabulation.txt"

with open(filename, "w", encoding="utf-8") as f:
    header = "№  | Latitude  | Longitude | Elevation (m)\n"
    print("\nТабуляція вузлів:")
    print(header.strip())
    f.write(header)
    
    for i, point in enumerate(results):
        lat = point['latitude']
        lon = point['longitude']
        ele = point['elevation']
        line = f"{i:2d} | {lat:.6f} | {lon:.6f} | {ele:.2f}"
        print(line)
        f.write(line + "\n")

print(f"\nЕкспорт завершено. Дані збережено у файл: {filename}")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlambda/2)**2
    return 2*R*np.arctan2(np.sqrt(a), np.sqrt(1-a))

coords = [(p["latitude"], p["longitude"]) for p in results]
elevations = [p["elevation"] for p in results]

distances = [0]
for i in range(1, n):
    d = haversine(*coords[i-1], *coords[i])
    distances.append(distances[-1] + d)

print("\nТабуляція (відстань, висота):")
print("№  | Distance (m) | Elevation (m)")

for i in range(n):
    print(f"{i:2d} | {distances[i]:10.2f} | {elevations[i]:8.2f}")

x = np.array(distances)
y = np.array(elevations)
n = len(x)
h = np.diff(x)

alpha = np.zeros(n)
beta = np.zeros(n)
gamma = np.zeros(n)
delta = np.zeros(n)

beta[0] = 1.0
gamma[0] = 0.0
delta[0] = 0.0

beta[-1] = 1.0
alpha[-1] = 0.0
delta[-1] = 0.0

for i in range(1, n - 1):
    alpha[i] = h[i-1]
    beta[i] = 2 * (h[i-1] + h[i])
    gamma[i] = h[i]
    delta[i] = 3 * ((y[i+1] - y[i]) / h[i] - (y[i] - y[i-1]) / h[i-1])

print("\nКоефіцієнти системи лінійних алгебраїчних рівнянь")
print(f"{'i':>2} | {'Альфа (α)':>12} | {'Бета (β)':>12} | {'Гамма (γ)':>12} | {'Дельта (δ)':>12}")
print("-" * 63)
for i in range(n):
    print(f"{i:2d} | {alpha[i]:12.4f} | {beta[i]:12.4f} | {gamma[i]:12.4f} | {delta[i]:12.4f}")

def thomas_algorithm(alpha, beta, gamma, delta):
    n = len(delta)
    A = np.zeros(n)
    B = np.zeros(n)
    c = np.zeros(n)

    # Пряма прогонка (ітерація від 0 до n-2)
    A[0] = -gamma[0] / beta[0]
    B[0] = delta[0] / beta[0]

    for i in range(1, n - 1):
        denominator = alpha[i] * A[i-1] + beta[i]
        A[i] = -gamma[i] / denominator
        B[i] = (delta[i] - alpha[i] * B[i-1]) / denominator

    # Зворотна прогонка
    # Обчислення останнього вузла n-1
    denominator_n = alpha[-1] * A[-2] + beta[-1]
    c[-1] = (delta[-1] - alpha[-1] * B[-2]) / denominator_n

    # Послідовне обчислення решти коефіцієнтів від n-2 до 0
    for i in range(n - 2, -1, -1):
        c[i] = A[i] * c[i+1] + B[i]

    return c

# Виконання обчислень та вивід результатів
c = thomas_algorithm(alpha, beta, gamma, delta)

a = np.zeros(n - 1)
b = np.zeros(n - 1)
d = np.zeros(n - 1)

for i in range(n - 1):
    a[i] = y[i]
    b[i] = (y[i+1] - y[i]) / h[i] - (h[i] / 3.0) * (2.0 * c[i] + c[i+1])
    d[i] = (c[i+1] - c[i]) / (3.0 * h[i])

print("\nКоефіцієнти кубічних сплайнів")
print(f"{'Інтервал':>8} | {'a':>10} | {'b':>12} | {'c':>12} | {'d':>15}")
print("-" * 65)
for i in range(n - 1):
    print(f"{i:8d} | {a[i]:10.2f} | {b[i]:12.6f} | {c[i]:12.6f} | {d[i]:15.8f}")

plt.figure()
plt.plot(distances, elevations, marker='o', linestyle='-', color='green')
plt.xlabel("Кумулятивна відстань (м)")
plt.ylabel("Висота (м)")
plt.title("Залежність висоти маршруту від кумулятивної відстані")
plt.grid(True)
plt.show()

