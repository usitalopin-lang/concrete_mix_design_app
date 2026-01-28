# Specification extracted from PDF Analysis
# Source: C:\Users\cridiaz\Downloads\Documentos\c71a5620-7ac8-4d53-9110-ea4d9c084e3a.pdf

The following specification was extracted from the analysis document provided. It details the logic for Faury-Joisel, Shilstone, and Aggregate Optimization.

## 1. Faury-Joisel Method

### Formulas
* **Resistencia Media (fd)**: `fd = fc + s * t`
    * `t` = 1.282 for 10% defective fraction.
    * Rounded to nearest 5 kg/cm².
* **Cement Content (C)**: `C = round(fd_kgcm2 * factor_eficiencia / 5) * 5`
* **Water/Cement Ratio (A/C)**: Interpolated from table based on `fd_kgcm2`.
* **Water Content (A)**: `A = ac_ratio * C` (Note: Current app uses ACI table)
* **Air Content (ha)**: Table based on TMN.
* **Compactness (z)**: `z = 1 - (ha/1000) - (A/1000)`
* **Cement Volume Fraction (c_vol)**: `c_vol = C / (z * density_cement)`
* **Aggregate Proportions**: 
    * `i_gruesos` (typical 0.437 for 25mm soft consistency).
    * `f = (1 - i_gruesos) - c_vol`

## 2. Shilstone Implementation

### Coarseness Factor (CF)
```python
def calcular_CF(pasa_3_8, pasa_8):
    Q = 100 - pasa_3_8 # Retained on 3/8"
    I = pasa_3_8 - pasa_8 # Retained on #8 (approx, check logic: Q=Plus 3/8, I=Minus 3/8 Plus #8)
    # The digest says: Q = 100 - pasa 3/8. I = pasa 3/8 - pasa 8.
    CF = (Q / (Q + I)) * 100
    return CF
```

### Workability Factor (W)
```python
def calcular_W(pasa_8):
    return pasa_8 # Percent passing #8
```

### Adjusted Workability Factor (W_adj)
```python
def calcular_ajuste(cemento):
    # Adj = 0.0588 * C - 19.647
    return 0.0588 * cemento - 19.647

def calcular_Wadj(W, adj):
    return W + adj
```

### Zones
* **Zone 1 (Optimal)**: A polygon defined by points (100,27), (85,27), (15,37), (0,37), (0,45), (35,45), (100,36).

## 3. Optimization (scipy.optimize)

### Objective Function
Minimize: `Error_Power45 + lambda * Error_Tarantula`

* **Error Power 45**: Sum of squared differences between Mix Curve and Ideal Power 45 Curve.
* **Error Tarantula**: Sum of violations of Tarantula limits (retained percentages).

### Constraints
1. Sum of aggregate proportions = 100%
2. Bounds for each aggregate (0-100%)
3. (Optional) Shilstone constraints (Fine fraction 24-34%, Coarse > 15%)

### Implementation Code (Snippet)
```python
from scipy.optimize import minimize, Bounds, LinearConstraint

def objetivo(x, granulometrias, ideal_power45, peso_tarantula=0.5):
    # Calculate mix, power45 error, tarantula error
    pass # Implementation details in PDF
```
