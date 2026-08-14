import os
import sys
import time
import argparse
import subprocess
import signal
import glob

# Global list of running processes
processes = []

def signal_handler(sig, frame):
    print("\n[Universal Launcher] Shutting down all nodes gracefully...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    print("[Universal Launcher] Shutdown complete.")
    sys.exit(0)

def find_executable_nodes(directory):
    nodes = []
    if not os.path.exists(directory):
        return nodes
        
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and not file.startswith("__init__"):
                filepath = os.path.join(root, file)
                # Check if it has a main block
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        if "if __name__ == '__main__':" in f.read():
                            nodes.append(filepath)
                except Exception:
                    pass
    return nodes

def find_machine_dir(machine_name):
    # Machines are under machines/<category>/<machine_name>
    # We can search through machines/ to find the directory matching machine_name
    machines_dir = os.path.join(os.getcwd(), "machines")
    if not os.path.exists(machines_dir):
        return None
        
    for category in os.listdir(machines_dir):
        cat_path = os.path.join(machines_dir, category)
        if os.path.isdir(cat_path):
            machine_path = os.path.join(cat_path, machine_name)
            if os.path.isdir(machine_path):
                return machine_path
    return None

def main():
    parser = argparse.ArgumentParser(description="AGRO-AI Universal Launcher")
    parser.add_argument("--machine", type=str, required=True, help="Machine specific brain to load (e.g., sprayer, excavator)")
    args = parser.parse_args()

    print(f"=== AGRO-AI Universal Launcher ===")
    print(f"[INFO] Initializing One Platform Strategy for: {args.machine.upper()}")

    # 1. Discover Core Nodes
    core_dir = os.path.join(os.getcwd(), "core")
    core_nodes = find_executable_nodes(core_dir)
    print(f"[INFO] Found {len(core_nodes)} core platform nodes.")

    # 2. Discover Machine Nodes
    machine_dir = find_machine_dir(args.machine)
    if not machine_dir:
        print(f"[ERROR] Could not find machine profile for '{args.machine}'.")
        print(f"Make sure a directory exists at machines/<category>/{args.machine}")
        sys.exit(1)
        
    machine_nodes = find_executable_nodes(machine_dir)
    print(f"[INFO] Found {len(machine_nodes)} specialized nodes for {args.machine}.")

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    all_nodes = core_nodes + machine_nodes
    if not all_nodes:
        print("[WARNING] No nodes found to launch.")
        sys.exit(0)
    
    print("\n--- Starting Nodes ---")
    for node in all_nodes:
        rel_path = os.path.relpath(node, os.getcwd())
        print(f"Launching {rel_path}...")
        p = subprocess.Popen([sys.executable, node], cwd=os.getcwd())
        processes.append(p)
        time.sleep(0.5) # Slight stagger for startup
        
    print("\n[Universal Launcher] All nodes running. Press Ctrl+C to terminate.")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass # Caught by signal_handler

if __name__ == "__main__":
    main()
