import numpy as np
from helpers import regression, mean_std  # mu, delta2 = regression(x, y)

def entwurf():
    # Aufgabe 1: Ohmsches Gesetz - U(I) Kennlinie eines Widerstands
    I = np.array([0.10, 0.20, 0.30, 0.40, 0.50])  # Strom mit Einheit A
    U = np.array([1.02, 2.05, 3.01, 4.08, 5.03])  # Spannung mit Einheit V
    # Analysieren
    R, dR2 = regression(I, U)  # Steigung = Widerstand in Ohm

    # Aufgabe 2: Periodendauer eines Fadenpendels (10 Messungen)
    T = np.array([2.01, 1.99, 2.03, 2.00, 1.98, 2.02, 2.00, 2.01, 1.99, 2.02])  # Periode mit Einheit s
    # Analysieren
    T_mean, T_std = mean_std(T)
    g = 4*np.pi**2 * 1.00 / T_mean**2  # Erdbeschleunigung mit Einheit m/s^2, L=1.00 m
    ...

    # Protokollentwurf als String zurueckgeben
    report = f'''# Versuch E1 - Elektrische und mechanische Messungen
## Einleitung

...

## Section 1 - Ohmsches Gesetz
R = ({R:.3f} +- {np.sqrt(dR2):.3f}) Ohm

...

## Section 2 ...

...

## Fazit
...
'''
    return report