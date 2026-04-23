# Blackhole Simulation

A Python-based simulation of blackhole physics, modeling gravitational effects, event horizons, and particle interactions near a blackhole.

## Prerequisites
- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - numpy
  - matplotlib
  - scipy

## Quick Start
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the simulation: `python main.py --mass 10 --particles 1000`

## Usage Examples
```bash
# Basic simulation with default parameters
python main.py

# Custom blackhole mass (in solar masses) and particle count
python main.py --mass 20 --particles 5000

# Save visualization output
python main.py --output visualization.png
```

## Running Tests
```bash
python -m pytest tests/
```