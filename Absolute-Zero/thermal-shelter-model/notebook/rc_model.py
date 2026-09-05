# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
climate_path = BASE_DIR / ".." / "data" / "leh_climate.csv"

with open(climate_path) as f:
    lines = f.readlines()

header_row = next(i for i, line in enumerate(lines) if line.startswith("YEAR"))
climate = pd.read_csv(climate_path, skiprows=header_row)

materials = pd.read_excel(
    BASE_DIR / ".." / "data" / "material_properties.xlsx",
    sheet_name="Material Properties",
    header=3
)

# ------------------------------------------------------------
# MATERIAL LOOKUP HELPER
# ------------------------------------------------------------
def get_material_properties(material_name, df):
    row = df[df["Material"] == material_name].iloc[0]
    k = row["Thermal Conductivity, k (W/m·K)"]
    rho = row["Density, ρ (kg/m³)"]
    c = row["Specific Heat, c (J/kg·K)"]
    return k, rho, c

# ------------------------------------------------------------
# PASSIVE SIMULATION ENGINE WITH COMPOSITE INSULATION
# ------------------------------------------------------------
def run_passive_simulation(
    length, width, height,
    wall_material, roof_material,
    wall_thickness, roof_thickness,
    window_area, door_area,
    materials_df, climate_df,
    insulation_thickness=0.0,       # Added insulation layer (e.g., Straw/Wood wool)
    insulation_k=0.04,              # Straw/wool conductivity (W/m·K)
    u_window_day=1.0,
    u_window_night=0.12,
    tau_glass=0.85,
    sim_days=20,                     # Warm-up period to stabilize thermal mass
    comfort_min=10.0                 # Comfort threshold (°C)
):
    # Geometry
    area_south_wall = length * height
    area_north_wall = length * height
    area_east_wall  = width * height
    area_west_wall  = width * height
    area_roof       = length * width
    
    area_south_wall_net = max(0.1, area_south_wall - window_area - door_area)

    # Material Properties
    k_wall, rho_wall, c_wall = get_material_properties(wall_material, materials_df)
    k_roof, rho_roof, c_roof = get_material_properties(roof_material, materials_df)

    # Composite Wall Unit Resistance (R = t_mud/k_mud + t_insulation/k_insulation)
    r_unit_wall = (wall_thickness / k_wall) + (insulation_thickness / insulation_k)
    r_unit_roof = (roof_thickness / k_roof) + (insulation_thickness / insulation_k)

    # Fixed Opaque Wall Resistances
    R_south_wall = r_unit_wall / area_south_wall_net
    R_north_wall = r_unit_wall / area_north_wall
    R_east_wall  = r_unit_wall / area_east_wall
    R_west_wall  = r_unit_wall / area_west_wall
    R_roof       = r_unit_roof / area_roof

    # Base Conductance of Opaque Shell
    G_opaque = (1.0 / R_south_wall) + (1.0 / R_north_wall) + (1.0 / R_east_wall) + (1.0 / R_west_wall) + (1.0 / R_roof)

    # Thermal Mass Storage Capacitance
    wall_volume = wall_thickness * (area_south_wall + area_north_wall + area_east_wall + area_west_wall)
    roof_volume = roof_thickness * area_roof
    C_total = (rho_wall * wall_volume * c_wall) + (rho_roof * roof_volume * c_roof)

    # Climate Data
    dt = 3600
    T_out_base = climate_df["T2M"].values
    G_base = climate_df["ALLSKY_SFC_SW_DWN"].values
    
    if G_base.max() < 5.0:
        G_base = G_base * 1000.0

    T_out_series = list(T_out_base) * sim_days
    G_series = list(G_base) * sim_days

    T_in = T_out_series[0]
    indoor_temps = []

    # Hourly Simulation Loop
    for step in range(len(T_out_series)):
        hour_of_day = step % 24
        
        # Insulated shutters closed overnight (17:00 to 08:00)
        if 8 <= hour_of_day <= 17:
            u_win = u_window_day
        else:
            u_win = u_window_night

        # Dynamic Resistance
        R_win = 1.0 / (u_win * max(0.1, window_area))
        R_total = 1.0 / (G_opaque + (1.0 / R_win))

        # Heat Balance
        Q_solar = G_series[step] * window_area * tau_glass
        Q_conduction = (T_in - T_out_series[step]) / R_total
        
        Q_net = Q_solar - Q_conduction
        T_in += (Q_net * dt) / C_total
        indoor_temps.append(T_in)

    final_24_temps = indoor_temps[-24:]
    comfort_hours = sum(1 for t in final_24_temps if comfort_min <= t <= 24.0)

    return {
        "time": list(range(24)),
        "indoor_temp": [round(float(t), 1) for t in final_24_temps],
        "comfort_hours": comfort_hours,
        "min_temp": min(final_24_temps),
        "max_temp": max(final_24_temps),
    }

# ------------------------------------------------------------
# RUN OPTIMIZED DESIGN PROGRESSION
# ------------------------------------------------------------

# Test A: Solar Adobe (45 cm Mud Brick + 12 cm Straw Insulation Layer)
test_A = run_passive_simulation(
    length=4.5, width=3.5, height=2.6,
    wall_material="Mud Brick (Adobe)",
    roof_material="Mud Brick (Adobe)",
    wall_thickness=0.45, roof_thickness=0.40,
    insulation_thickness=0.12,      # 12 cm Straw/Wool render layer
    insulation_k=0.04,              # Straw k-value
    window_area=8.5, door_area=1.8,
    materials_df=materials, climate_df=climate,
    u_window_day=1.0, u_window_night=0.12,
    tau_glass=0.85,
    sim_days=20
)

# Test B: Mid-Tier Insulated Brick Structure
test_B = run_passive_simulation(
    length=4.0, width=3.0, height=2.5,
    wall_material="Insulated Brick (Vermiculite Insulating Brick)",
    roof_material="Insulated Brick (Vermiculite Insulating Brick)",
    wall_thickness=0.65, roof_thickness=0.45,
    insulation_thickness=0.0,
    window_area=7.0, door_area=1.8,
    materials_df=materials, climate_df=climate,
    u_window_day=1.2, u_window_night=0.20,
    tau_glass=0.75,
    sim_days=20
)

# Test C: Passivhaus Super-Insulated Passive Solar Standard
test_C = run_passive_simulation(
    length=4.5, width=3.5, height=2.6,
    wall_material="Insulated Brick (Vermiculite Insulating Brick)",
    roof_material="Insulated Brick (Vermiculite Insulating Brick)",
    wall_thickness=0.75, roof_thickness=0.50,
    insulation_thickness=0.0,
    window_area=8.5, door_area=1.8,
    materials_df=materials, climate_df=climate,
    u_window_day=1.0, u_window_night=0.12,
    tau_glass=0.75,
    sim_days=20
)

# ------------------------------------------------------------
# RESULTS OUTPUT
# ------------------------------------------------------------
print("--- PASSIVE SOLAR PERFORMANCE GRADIENT ---")
print("Test A (Solar Adobe + Straw) Comfort Hours (>=10°C):", test_A["comfort_hours"])
print("Test B (Insulated Brick)     Comfort Hours (>=10°C):", test_B["comfort_hours"])
print("Test C (Passivhaus Solar)    Comfort Hours (>=10°C):", test_C["comfort_hours"])

print("\n--- DETAILED SUMMARY ---")
print(f"Test A Temp Range: {round(test_A['min_temp'], 1)}°C to {round(test_A['max_temp'], 1)}°C")
print(f"Test B Temp Range: {round(test_B['min_temp'], 1)}°C to {round(test_B['max_temp'], 1)}°C")
print(f"Test C Temp Range: {round(test_C['min_temp'], 1)}°C to {round(test_C['max_temp'], 1)}°C")

print("\nTest A Indoor Temp Profile (°C):", test_A["indoor_temp"])
print("Test B Indoor Temp Profile (°C):", test_B["indoor_temp"])
print("Test C Indoor Temp Profile (°C):", test_C["indoor_temp"])