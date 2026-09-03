# ------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# ------------------------------------------------------------
# LOAD DATA (Step 2)
# ------------------------------------------------------------
climate_path = BASE_DIR / ".." / "data" / "leh_climate.csv"

# Find the real header row (NASA POWER CSVs start with a metadata block)
with open(climate_path) as f:
    lines = f.readlines()

header_row = next(i for i, line in enumerate(lines) if line.startswith("YEAR"))

climate = pd.read_csv(climate_path, skiprows=header_row)

print("First 5 outdoor temps:", climate["T2M"].values[:5])
print("First 5 solar values:", climate["ALLSKY_SFC_SW_DWN"].values[:5])
print("Number of rows:", len(climate))

print("Climate columns:", climate.columns.tolist())
materials = pd.read_excel(
    BASE_DIR / ".." / "data" / "material_properties.xlsx",
    sheet_name="Material Properties",
    header=3
)

# Check your actual column names before running (remove after checking)
print("Climate columns:", climate.columns.tolist())

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
# MAIN SIMULATION FUNCTION (Steps 3 + 4 + 5 combined)
# ------------------------------------------------------------
def run_simulation(
    length, width, height,
    wall_material, roof_material,
    wall_thickness, roof_thickness,
    window_area, door_area,
    materials_df, climate_df
):
    # --- Step 3: Geometry ---
    area_south_wall = length * height
    area_north_wall = length * height
    area_east_wall  = width * height
    area_west_wall  = width * height
    area_roof       = length * width
    area_south_wall_net = area_south_wall - window_area - door_area
    volume = length * width * height

    # --- Step 4: Material properties + R/C ---
    k_wall, rho_wall, c_wall = get_material_properties(wall_material, materials_df)
    k_roof, rho_roof, c_roof = get_material_properties(roof_material, materials_df)

    R_south_wall = wall_thickness / (k_wall * area_south_wall_net)
    R_north_wall = wall_thickness / (k_wall * area_north_wall)
    R_east_wall  = wall_thickness / (k_wall * area_east_wall)
    R_west_wall  = wall_thickness / (k_wall * area_west_wall)
    R_roof       = roof_thickness / (k_roof * area_roof)
    R_total = 1 / (1/R_south_wall + 1/R_north_wall + 1/R_east_wall + 1/R_west_wall + 1/R_roof)

    wall_volume = wall_thickness * (area_south_wall + area_north_wall + area_east_wall + area_west_wall)
    roof_volume = roof_thickness * area_roof
    C_total = (rho_wall * wall_volume * c_wall) + (rho_roof * roof_volume * c_roof)

    # --- Step 5: Hourly simulation ---
    tau_glass = 0.83
    dt = 3600
    T_out_series = climate_df["T2M"].values             # update if your column name differs
    G_series = climate_df["ALLSKY_SFC_SW_DWN"].values    # update if your column name differs

    T_in = T_out_series[0]
    indoor_temps = [T_in]

    for hour in range(1, len(T_out_series)):
        Q_solar = G_series[hour] * window_area * tau_glass
        Q_conduction = (T_in - T_out_series[hour]) / R_total
        T_in += (Q_solar - Q_conduction) * dt / C_total
        indoor_temps.append(T_in)

    comfort_hours = sum(1 for t in indoor_temps if 20 <= t <= 24)

    return {
        "time": list(range(len(indoor_temps))),
        "indoor_temp": [round(t, 1) for t in indoor_temps],
        "comfort_hours": comfort_hours,
        "recommendation": "Design performs well." if comfort_hours >= 16 else "Consider more insulation or thermal mass."
    }

# ------------------------------------------------------------
# RUN A TEST CASE
# ------------------------------------------------------------
result = run_simulation(
    length=4.0, width=3.0, height=3.0,
    wall_material="Mud Brick (Adobe)", roof_material="Mud Brick (Adobe)",
    wall_thickness=30.0, roof_thickness=20.0,
    window_area=1.2, door_area=1.8,
    materials_df=materials, climate_df=climate
)

print(result)

# ------------------------------------------------------------
# STEP 6: DESIGN COMPARISON TESTS  ← ADD THIS PART
# ------------------------------------------------------------
test_A = run_simulation(
    length=4.0, width=3.0, height=2.5,
    wall_material="Insulated Brick (Vermiculite Insulating Brick)",
    roof_material="Insulated Brick (Vermiculite Insulating Brick)",
    wall_thickness=0.3, roof_thickness=0.2,
    window_area=1.2, door_area=1.8,
    materials_df=materials, climate_df=climate
)

test_B = run_simulation(
    length=4.0, width=3.0, height=2.5,
    wall_material="Insulated Brick (Vermiculite Insulating Brick)",
    roof_material="Insulated Brick (Vermiculite Insulating Brick)",
    wall_thickness=0.3, roof_thickness=0.2,
    window_area=2.5, door_area=1.8,
    materials_df=materials, climate_df=climate
)

test_C = run_simulation(
    length=4.5, width=3.5, height=3.0,
    wall_material="Insulated Brick (Vermiculite Insulating Brick)",
    roof_material="Insulated Brick (Vermiculite Insulating Brick)",
    wall_thickness=0.3, roof_thickness=0.2,
    window_area=2.2, door_area=1.8,
    materials_df=materials, climate_df=climate
)

print("Test A (insulated, small window) comfort hours:", test_A["comfort_hours"])
print("Test B (insulated, larger window) comfort hours:", test_B["comfort_hours"])
print("Test C (insulated, thicker wall) comfort hours:", test_C["comfort_hours"])