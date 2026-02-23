# 🚦 Intelligent Traffic Simulation using SUMO & LSTM

An intelligent traffic simulation system combining **SUMO (Simulation of Urban Mobility)** with an **LSTM-based AI follower** and a **rule-based Safety Agent** for realistic autonomous driving behavior.

---

## 📋 Features

✅ **3x3 Urban Grid** - Complex road network with multiple intersections  
✅ **LSTM Car-Following** - AI vehicle that learns to follow using deep learning  
✅ **Intelligent Safety Agent** - Rule-based driver with:
- Adaptive Cruise Control (ACC)
- Traffic light detection
- Safe lane changing
- Collision avoidance

✅ **Manual Control** - Drive the leader car with keyboard inputs  
✅ **Real-time Visualization** - SUMO GUI + Pygame control panel

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- SUMO 1.26.0+ (included in project directory)

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### 1. Generate SUMO Network & Routes
```bash
cd SUMO_Simulation_v2
python generate_sumo_files_v2.py
```

### 2. Run the Simulation
```bash
python run_lstm_sumo_v2.py
```

### 3. Control the Agent
- **UP/DOWN**: Accelerate/Brake
- **LEFT/RIGHT**: Change lanes
- Watch the Pygame window for agent status

---

## 📁 Project Structure

```
SUMO_Simulation_v2/
├── generate_sumo_files_v2.py    # Network/route generator
├── run_lstm_sumo_v2.py           # Main simulation script
├── simulation_v2.sumocfg         # SUMO configuration
├── v2.net.xml                    # Generated network (3x3 grid)
├── v2.rou.xml                    # Generated routes
├── view_settings.xml             # SUMO GUI settings
├── weights/                      # LSTM model files
│   ├── best_lstm_model.pth
│   └── model_config.json
├── sumo-1.26.0/                  # Local SUMO installation
├── PROJECT_REPORT.md             # Full documentation
└── README.md                     # This file
```

---

## 🎯 How It Works

### System Architecture
**User Input → Safety Agent → SUMO Simulation → LSTM Follower**

1. **Traffic Observation Module**: Reads vehicle positions, speeds, traffic lights
2. **Intelligent Agent Module**: Makes safe driving decisions
3. **Decision-Making Logic**:
   - Road congested → Slow down
   - Vehicle ahead → Stop
   - Road clear → Accelerate
   - Safe gap → Change lane
   - Red light → Stop

4. **LSTM Follower**: Deep learning model controls green car to follow leader

---

## 📊 Results

**Agent Behaviors Observed:**
- ✅ Stops at red traffic lights
- ✅ Maintains safe distance (15m) from vehicles ahead
- ✅ Smoothly accelerates when road clears
- ✅ Only changes lanes when safe gap exists
- ✅ Overrides dangerous user commands

---

## 📖 Documentation

For complete project details, see [PROJECT_REPORT.md](PROJECT_REPORT.md)

---

## 🔧 Troubleshooting

**Issue: Vehicles not appearing**
- Solution: Check that `v2.net.xml` and `v2.rou.xml` are generated correctly

**Issue: SUMO GUI won't open**
- Solution: Verify SUMO_HOME is set to `sumo-1.26.0` directory

**Issue: Pygame window black**
- Solution: Click on the window to give it focus

---

## 🎓 Applications

- Autonomous vehicle research
- Traffic signal optimization
- Smart city simulations
- AI driver training

---

## 📝 License

This project is for educational purposes.

---

## 👨‍💻 Author

Created for AI/Traffic Simulation coursework.
