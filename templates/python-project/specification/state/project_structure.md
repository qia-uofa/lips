# Project Structure

```
blackhole-simulation/
├── main.py                # Main simulation entry point
├── blackhole.py           # Blackhole physics models
├── particles.py           # Particle generation and tracking
├── visualization.py       # Data visualization functions
├── utils/                 # Utility functions
│   ├── physics.py         # Physics calculations
│   └── io.py              # Input/output helpers
├── tests/                 # Unit tests
│   ├── test_blackhole.py
│   └── test_particles.py
├── requirements.txt       # Python dependencies
└── docs/                  # Documentation
    ├── README.md
    ├── features.md
    └── flowchart.mermaid
```

## File Descriptions
- **main.py**: Command-line interface and simulation orchestrator
- **blackhole.py**: Core blackhole physics implementation
- **particles.py**: Particle system management
- **visualization.py**: Plotting and visualization functions
- **utils/**: Helper functions for physics calculations and I/O
- **tests/**: Unit tests for core functionality
- **docs/**: Project documentation