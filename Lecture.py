import numpy as np

file_name = input("Enter filename: ")

data = np.loadtxt(file_name, delimiter=",", skiprows=1)
zones = np.loadtxt(file_name, delimiter=",", dtype=str, max_rows=1)

# Total energy consumption for each day
print("Total energy consumption for each day:")

daily_total = np.sum(data, axis=1)

for i, total in enumerate(daily_total, 1):
    print(f" Day {i} -> {total:.2f}")

print()

# Average energy consumption for each zone
print("Average energy consumption for each zone:")

zone_average = np.mean(data, axis=0)

for zone, average in zip(zones, zone_average):
    print(f" {zone} -> {average:.2f}")

print()

# Highest energy consumption
max_position = np.unravel_index(np.argmax(data), data.shape)

day = max_position[0] + 1
zone = zones[max_position[1]]
value = data[max_position]

print("Highest energy consumption:")
print(f" Day {day}, {zone} -> {value:.2f}")

print()

# Lowest energy consumption
min_position = np.unravel_index(np.argmin(data), data.shape)

day = min_position[0] + 1
zone = zones[min_position[1]]
value = data[min_position]

print("Lowest energy consumption:")
print(f" Day {day}, {zone} -> {value:.2f}")

print()

# Number of measurements greater than 160
count = np.sum(data > 160)

print(f"Number of measurements greater than 160: {count}")