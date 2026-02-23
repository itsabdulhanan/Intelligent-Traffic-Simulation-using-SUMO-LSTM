# Script to generate SUMO configuration files
import os
import sys
import subprocess

def generate_sumo_files():
    print("Generating SUMO files...")
    
    # Setup Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try to find local SUMO
    local_sumo_bin = os.path.join(base_dir, "sumo-1.26.0", "bin")
    netgenerate_binary = "netgenerate"
    
    if os.path.exists(os.path.join(local_sumo_bin, "netgenerate.exe")):
         netgenerate_binary = os.path.join(local_sumo_bin, "netgenerate.exe")
         print(f"Using local netgenerate: {netgenerate_binary}")

    # 1. Generate Network (3x3 Grid)
    # --grid: creates a grid network
    # --grid.x-number: number of junctions in X
    # --grid.y-number: number of junctions in Y
    # --grid.length: length of each street section
    cmd_net = [netgenerate_binary, 
               "--grid", 
               "--grid.x-number", "3", 
               "--grid.y-number", "3", 
               "--grid.length", "300", 
               "--output-file", "v2.net.xml",
               "--default.lanenumber", "3"]
    
    try:
        subprocess.run(cmd_net, check=True)
        print("Generated v2.net.xml (3x3 Grid) using netgenerate")
    except Exception as e:
        print(f"Error running netgenerate: {e}")
        return

    # 4. Generate Routes (v2.rou.xml)
    # We'll use a longer route across the grid
    # Edge IDs in netgenerate grid are usually numeric or A0B0 etc. 
    # Let's inspect the generated network or use randomTrips if available.
    # To be safe and deterministic, let's create a route that we know exists in a 3x3 grid.
    # Typically: bottom-left to top-right.
    
    routes_xml = """<?xml version="1.0" encoding="UTF-8"?>
<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">
    <!-- Vehicle Types -->
    <vType id="leader_type" vClass="passenger" color="1,0,0" length="4.5" maxSpeed="30" accel="3.0" decel="6.0" sigma="0.0"/>
    <vType id="follower_type" vClass="passenger" color="0,1,0" length="4.5" maxSpeed="30" accel="3.0" decel="6.0" sigma="0.0"/>
    <vType id="bg_car" vClass="passenger" color="random" length="4.5" maxSpeed="25"/>

    <!-- Routes using actual edge IDs -->
    
    <!-- Horizontal Routes (West to East) -->
    <route id="route_h1" edges="A0B0 B0C0"/>
    <route id="route_h2" edges="A1B1 B1C1"/>
    <route id="route_h3" edges="A2B2 B2C2"/>
    
    <!-- Horizontal Routes (East to West) -->
    <route id="route_h4" edges="C0B0 B0A0"/>
    <route id="route_h5" edges="C1B1 B1A1"/>
    <route id="route_h6" edges="C2B2 B2A2"/>
    
    <!-- Vertical Routes (South to North) -->
    <route id="route_v1" edges="A0A1 A1A2"/>
    <route id="route_v2" edges="B0B1 B1B2"/>
    <route id="route_v3" edges="C0C1 C1C2"/>
    
    <!-- Vertical Routes (North to South) -->
    <route id="route_v4" edges="A2A1 A1A0"/>
    <route id="route_v5" edges="B2B1 B1B0"/>
    <route id="route_v6" edges="C2C1 C1C0"/>
    
    <!-- Long Routes across grid -->
    <route id="long_route" edges="A0B0 B0C0 C0C1 C1C2"/>
    <route id="long_route2" edges="A0A1 A1B1 B1C1 C1C2"/>
    
    <!-- Traffic Flows -->
    <flow id="flow_1" type="bg_car" route="route_h1" begin="0" end="3600" probability="0.12" departLane="random" departSpeed="random"/>
    <flow id="flow_2" type="bg_car" route="route_h2" begin="0" end="3600" probability="0.12" departLane="random" departSpeed="random"/>
    <flow id="flow_3" type="bg_car" route="route_h3" begin="0" end="3600" probability="0.12" departLane="random" departSpeed="random"/>
    
    <flow id="flow_4" type="bg_car" route="route_h4" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    <flow id="flow_5" type="bg_car" route="route_h5" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    <flow id="flow_6" type="bg_car" route="route_h6" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    
    <flow id="flow_7" type="bg_car" route="route_v1" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    <flow id="flow_8" type="bg_car" route="route_v2" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    <flow id="flow_9" type="bg_car" route="route_v3" begin="0" end="3600" probability="0.10" departLane="random" departSpeed="random"/>
    
    <flow id="flow_10" type="bg_car" route="route_v4" begin="0" end="3600" probability="0.08" departLane="random" departSpeed="random"/>
    <flow id="flow_11" type="bg_car" route="route_v5" begin="0" end="3600" probability="0.08" departLane="random" departSpeed="random"/>
    <flow id="flow_12" type="bg_car" route="route_v6" begin="0" end="3600" probability="0.08" departLane="random" departSpeed="random"/>

    <!-- Main Experiment Vehicles -->
    <vehicle id="leader" type="leader_type" route="long_route" depart="1" departLane="1" departSpeed="13" departPos="free"/>
    <vehicle id="follower" type="follower_type" route="long_route" depart="2" departLane="1" departSpeed="10" departPos="free"/>

</routes>
"""
    with open("v2.rou.xml", "w") as f:
        f.write(routes_xml)
    print("Generated v2.rou.xml")
    
    # 5. View Settings
    view_xml = """<viewsettings>
    <scheme name="real world"/>
    <delay value="50"/>
    <viewport zoom="150" x="300" y="300"/>
</viewsettings>
"""
    with open("view_settings.xml", "w") as f:
        f.write(view_xml)
    print("Generated view_settings.xml")


if __name__ == "__main__":
    generate_sumo_files()
