# Physics Model Notes — Thermal Shelter Project (Ladakh)

## Master Equation

Q_stored = Q_solar − Q_conduction − Q_infiltration

This says: the heat that stays inside the shelter (and changes its temperature)
equals the heat gained from the sun, minus the heat lost through walls/roof/floor,
minus the heat lost through air leaks.

## Term Definitions

### Q_solar (heat gained from sunlight)
Q_solar = G(t) × A_window × τ_glass

- G(t) = solar irradiance hitting the shelter at time t, in W/m²
  (this changes hour by hour — zero at night, peak around midday)
- A_window = area of south-facing window(s) that let sunlight in, in m²
- τ_glass = transmittance of the glazing material (fraction of sunlight that
  actually passes through, e.g. ~0.8 for clear glass — 1.0 = all light passes,
  0 = none does)

### Q_conduction (heat lost through walls/roof/floor)
Q_conduction = U × A × (T_in − T_out)

- U = U-value of the wall/roof/floor material, in W/m²·K
  (lower U = better insulation = less heat escapes)
- A = surface area of that wall/roof/floor, in m²
- T_in = indoor air temperature, T_out = outdoor air temperature (°C)
- Do this separately for each surface (south wall, north wall, roof, floor, etc.)
  and add them all up

### Q_infiltration (heat lost through air leaks/drafts)
Q_infiltration = ACH × V × ρ_air × c_air × (T_in − T_out)

- ACH = air changes per hour (how many times the shelter's full air volume
  gets replaced by outside air each hour, due to gaps/drafts)
- V = volume of the shelter, in m³
- ρ_air = density of air (~1.2 kg/m³)
- c_air = specific heat of air (~1005 J/kg·K)

### Q_stored (how the stored heat changes the temperature)
Q_stored = m × c_material × (dT/dt)

- m = mass of the material storing heat (walls, floor, or added thermal mass
  like water tanks/stone), in kg
- c_material = specific heat of that material, in J/kg·K
- dT/dt = how fast temperature is changing over time — this is what we're
  ultimately solving for, since it tells us the indoor temperature at every hour

## Unknowns / Data Needed
(fill in as you find real numbers — this is your checklist for Step 3)

- [ ] G(t): hourly solar irradiance for Leh, Ladakh, winter day
- [ ] T_out(t): hourly outdoor temperature for Leh, winter day
- [ ] Wall/roof/floor material + thickness (decides U and m, c_material)
- [ ] Window area and glazing type (decides A_window and τ_glass)
- [ ] ACH estimate (typical range for tents/huts vs sealed structures)
- [ ] Shelter dimensions (L × W × H → gives A and V)
- [ ] Comfort target: 20–24°C indoor (ASHRAE 55)

## Shelter Sketch / Assumptions
- Shape: [e.g. simple rectangular box]
- Orientation: [which wall faces south — largest window here]
- Rough dimensions: [L x W x H — fill in once decided]
- Single room / single zone assumption for now
