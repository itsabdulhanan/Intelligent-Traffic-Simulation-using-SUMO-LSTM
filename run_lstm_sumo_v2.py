# Script to run LSTM SUMO simulation
# Script to run LSTM SUMO simulation
import os
import sys
import torch
import torch.nn as nn
import numpy as np
import json
import platform
import pygame

# Check if SUMO_HOME is set
if 'SUMO_HOME' not in os.environ:
    # Attempt to locate locally associated SUMO
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_sumo_path = os.path.join(base_dir, "sumo-1.26.0")
    if os.path.exists(local_sumo_path):
        os.environ['SUMO_HOME'] = local_sumo_path
        print(f"SUMO_HOME set to local path: {local_sumo_path}")
    else:
        # User might have "sumo" in path but no SUMO_HOME (less likely to work for tools but worth a try if traci installed)
        pass

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    # Try to deduce SUMO_HOME if not set (common in some installs)
    # Check common paths? No, easier to rely on 'sumo' being in path if traci fails.
    # But we need 'tools' in path for traci usage if not installed via pip.
    # If the user has 'sumo' in path, 'traci' might be installed via pip.
    try:
        import traci
    except ImportError:
        sys.exit("Please declare environment variable 'SUMO_HOME' or install traci override")

import traci

# --- Model Definition (Must match training script) ---
class LSTMCarFollowing(nn.Module):
    def __init__(self, n_features, seq_length, pred_horizon, n_targets,
                 hidden_size=128, num_layers=2, dropout=0.3):
        super(LSTMCarFollowing, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.pred_horizon = pred_horizon
        self.n_targets = n_targets
        self.seq_length = seq_length

        # Bidirectional LSTM layers
        self.lstm1 = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0
        )

        self.dropout1 = nn.Dropout(dropout)

        self.lstm2 = nn.LSTM(
            input_size=hidden_size * 2,
            hidden_size=hidden_size // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=0
        )

        self.dropout2 = nn.Dropout(dropout)

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout3 = nn.Dropout(dropout * 0.7)
        self.fc2 = nn.Linear(64, pred_horizon * n_targets)

    def forward(self, x):
        lstm_out, _ = self.lstm1(x)
        lstm_out = self.dropout1(lstm_out)

        lstm_out, _ = self.lstm2(lstm_out)
        lstm_out = self.dropout2(lstm_out)

        lstm_out = torch.select(lstm_out, 1, self.seq_length - 1)

        out = self.fc1(lstm_out)
        out = self.relu(out)
        out = self.dropout3(out)
        out = self.fc2(out)

        out = out.view(-1, self.pred_horizon, self.n_targets)
        return out

class CustomScaler:
    def __init__(self, mean, std):
        self.mean = np.array(mean)
        self.std = np.array(std)
        
    def transform(self, x):
        return (x - self.mean) / self.std
        
    def inverse_transform(self, x):
        return (x * self.std) + self.mean

# --- MODULE 3: INTELLIGENT AGENT MODULE ---
class SafetyAgent:
    def __init__(self, vehicle_id):
        self.id = vehicle_id
        self.safe_distance = 15.0 # meters
        self.desired_speed = 0.0
        self.lane_change_cooldown = 0
        
    def step(self, user_target_speed, lane_change_request):
        self.desired_speed = user_target_speed
        
        # --- MODULE 4: TRAFFIC OBSERVATION MODULE ---
        try:
            current_speed = traci.vehicle.getSpeed(self.id)
            leader_info = traci.vehicle.getLeader(self.id) # (vehicleID, distress)
            current_lane = traci.vehicle.getLaneIndex(self.id)
            tls_list = traci.vehicle.getNextTLS(self.id) # List of (tlsID, tlsIndex, dist, state)
        except:
            return 0.0, "Error Sensing"

        # --- MODULE 5: DECISION-MAKING MODULE ---
        
        # 1. Adaptive Cruise Control (ACC)
        safe_speed = self.desired_speed
        status_msg = "Cruising"
        
        if leader_info is not None:
            leader_id, dist = leader_info
            if dist < self.safe_distance:
                # Rule: Vehicle ahead too close -> Stop/Slow
                safe_speed = min(self.desired_speed, traci.vehicle.getSpeed(leader_id) * 0.9) 
                if dist < 5: safe_speed = 0 
                status_msg = f"ACC: Following {leader_id}"

        # 2. Intersection/Traffic Light Logic
        # Rule: Intersection free -> Cross (Implicitly: If not free/Red, Stop)
        if tls_list:
             # Sort by distance
             tls_list.sort(key=lambda x: x[2])
             next_tls = tls_list[0]
             tls_id, tls_idx, dist, state = next_tls
             
             if dist < 40.0: # Approaching intersection
                 if state in ['r', 'y', 'R', 'Y']: # Red or Yellow
                     # Rule: Road not clear -> Stop
                     safe_speed = 0.0
                     status_msg = "Intersection: Red Light"
                 else:
                     # Green
                     pass # Proceed (keep ACC speed)

        # 3. Lane Change Logic
        # Rule: Safe to change lane -> Change lane
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= 1
            
        if lane_change_request != 0 and self.lane_change_cooldown == 0:
            target_lane = current_lane + lane_change_request
            if 0 <= target_lane <= 2:
                # Check for neighbors (blind spot check could be added here via getNeighbors)
                traci.vehicle.changeLane(self.id, target_lane, duration=2)
                self.lane_change_cooldown = 50 
                status_msg = f"Changing Lane"
            else:
                 status_msg = "Lane Invalid"

        # 4. Actuation
        traci.vehicle.setSpeed(self.id, safe_speed)
        
        return safe_speed, status_msg

def run_simulation():
    print("Initializing Simulation...")
    
    # ... (Rest of Init Code remains similar until loop) ...
    # 1. Load Resources
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    weights_dir = os.path.join(base_dir, "weights")
    
    model_path = os.path.join(weights_dir, "best_lstm_model.pth")
    config_path = os.path.join(weights_dir, "model_config.json")

    # Load Config for Scalers
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        norm_params = config["normalization"]
        scaler_X = CustomScaler(norm_params["scaler_X_mean"], norm_params["scaler_X_std"])
        scaler_y = CustomScaler(norm_params["scaler_y_mean"], norm_params["scaler_y_std"])
        print("Scalers initialized.")
        
    except Exception as e:
        print(f"Error loading config/scalers: {e}")
        return

    # Constants
    SEQ_LENGTH = 50
    PRED_HORIZON = 10
    N_FEATURES = 6
    N_TARGETS = 4
    HIDDEN_SIZE = 128
    NUM_LAYERS = 2
    
    # Load Model
    model = LSTMCarFollowing(
        n_features=N_FEATURES,
        seq_length=SEQ_LENGTH,
        pred_horizon=PRED_HORIZON,
        n_targets=N_TARGETS,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS
    ).to(device)
    
    try:
        model.load_state_dict(torch.load(model_path, map_location=device))
        print("Model weights loaded.")
    except Exception as e:
        print(f"Error loading model weights: {e}")
        return

    model.eval()

    # 2. Setup TRACI
    sumo_bin_dir = os.path.join(os.environ['SUMO_HOME'], 'bin')
    sumo_binary = os.path.join(sumo_bin_dir, "sumo-gui")
    
    os.environ['PATH'] += os.pathsep + sumo_bin_dir
    
    sumo_cmd = [sumo_binary, "-c", "simulation_v2.sumocfg", "--start"]
    
    try:
        traci.start(sumo_cmd)
        print("SUMO GUI started.")
    except Exception as e:
        print(f"Failed to start SUMO GUI: {e}")
        return

    # 3. Simulation Loop
    step = 0
    follower_id = "follower"
    leader_id = "leader"
    
    # History buffer
    history = [] 
    prev_speed = 0
    prev_accel = 0

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((400, 150))
    pygame.display.set_caption("Intelligent Safety Agent Control")
    font = pygame.font.Font(None, 24)

    # Initialize Safety Agent
    agent = SafetyAgent(leader_id)
    target_speed_leader = 13.0
    
    print("Starting simulation loop...")
    print("CONTROLS: UP/DOWN=Speed, LEFT/RIGHT=Lane Change")
    
    while step < 3600:
        traci.simulationStep()
        
        # --- Manual Control Input ---
        lane_request = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                start_loop = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    lane_request = 1 # +1 index usually means left in SUMO (depending on setup, often left is higher index)
                elif event.key == pygame.K_RIGHT:
                    lane_request = -1
                
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            target_speed_leader += 0.2
        if keys[pygame.K_DOWN]:
            target_speed_leader -= 0.5
            
        target_speed_leader = max(0.0, min(target_speed_leader, 30.0))
        
        # --- Check Simulation State ---
        vehicle_ids = traci.vehicle.getIDList()
        if follower_id not in vehicle_ids or leader_id not in vehicle_ids:
            if step > 3600: 
                if leader_id not in vehicle_ids:
                    print("Leader vehicle exited network.")
                    break
            if step % 100 == 0 and step > 100:
                 print(f"Waiting for vehicles... Step {step}")
            step += 1
            continue

        # --- SAFETY AGENT CONTROL ---
        safe_actual_speed, status = agent.step(target_speed_leader, lane_request)
        
        # Display Controls and Status
        screen.fill((0, 0, 0))
        txt_tgt = font.render(f"User Target: {target_speed_leader:.1f} m/s", True, (255, 255, 255))
        txt_act = font.render(f"Agent Safe Speed: {safe_actual_speed:.1f} m/s", True, (0, 255, 0))
        txt_status = font.render(f"Status: {status}", True, (255, 200, 100))
        
        screen.blit(txt_tgt, (20, 20))
        screen.blit(txt_act, (20, 50))
        screen.blit(txt_status, (20, 90))
        pygame.display.flip()

        # Track leader
        if step % 10 == 0:
            try: traci.gui.trackVehicle("View #0", leader_id)
            except: pass

        # --- Follower Logic (LSTM) ---
        try:
            pos = traci.vehicle.getDistance(follower_id)
            speed = traci.vehicle.getSpeed(follower_id)
            length = traci.vehicle.getLength(follower_id)
        except:
            step += 1
            continue
            
        local_time = traci.simulation.getTime()
        accel = (speed - prev_speed) / 0.1
        jerk = (accel - prev_accel) / 0.1
        prev_speed = speed
        prev_accel = accel
        
        feature_row = [pos, speed, accel, jerk, length, local_time]
        history.append(feature_row)
        
        if len(history) > SEQ_LENGTH:
            history.pop(0)
            
        if len(history) == SEQ_LENGTH:
            input_data = np.array([history])
            input_reshaped = input_data.reshape(-1, N_FEATURES)
            input_scaled = scaler_X.transform(input_reshaped)
            input_tensor = torch.FloatTensor(input_scaled).reshape(1, SEQ_LENGTH, N_FEATURES).to(device)
            
            with torch.no_grad():
                output = model(input_tensor)
                
            output_numpy = output.cpu().numpy()
            output_reshaped = output_numpy.reshape(-1, N_TARGETS)
            output_descaled = scaler_y.inverse_transform(output_reshaped)
            next_speed = output_descaled[0, 1] 
            
            if next_speed < 0: next_speed = 0
            if next_speed > 30: next_speed = 30 
            
            traci.vehicle.setSpeed(follower_id, next_speed)

        step += 1
    
    pygame.quit()
    traci.close()
    print("Simulation finished.")

if __name__ == "__main__":
    run_simulation()
