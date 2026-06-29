#!/usr/bin/env python3
import sys
import os
import time
from multiprocessing import Process

def get_total_memory():
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if 'MemTotal' in line:
                    return int(line.split()[1]) * 1024  # return in bytes
    except Exception:
        # Fallback if not running on Linux /proc
        return 2 * 1024 * 1024 * 1024  # 2 GB fallback

def cpu_stress():
    try:
        while True:
            start = time.time()
            while time.time() - start < 0.09:
                pass  # Run CPU
            time.sleep(0.01)  # Rest to target ~90% usage
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    print("============================================================")
    print("  Resource Stress Test: Simulating 90% CPU and Memory Usage")
    print("  Press Ctrl+C to terminate the test and release resources.")
    print("============================================================")
    
    total_mem = get_total_memory()
    target_alloc = int(total_mem * 0.90)
    
    print(f"\n[1/2] Allocating memory: {target_alloc / (1024**3):.2f} GB (90% of total capacity)...")
    try:
        # Allocate and initialize bytes to force OS page allocation
        mem_block = bytearray(target_alloc)
        print("✅ Memory allocated successfully.")
    except MemoryError:
        print("⚠️  Could not allocate 90% memory directly (OS limits). Trying 80%...")
        try:
            target_alloc = int(total_mem * 0.80)
            mem_block = bytearray(target_alloc)
            print("✅ Memory allocated successfully (80%).")
        except Exception as e:
            print(f"❌ Failed to allocate memory: {e}")
            sys.exit(1)
            
    print("\n[2/2] Launching CPU processes to utilize ~90% of all cores...")
    cores = os.cpu_count() or 1
    processes = []
    
    try:
        for i in range(cores):
            p = Process(target=cpu_stress)
            p.start()
            processes.append(p)
        print(f"✅ Spawned {cores} CPU stress processes.")
        print("\n🔥 System is now under stress. Check your Prometheus/Alertmanager dashboard!")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping stress test...")
        for p in processes:
            p.terminate()
            p.join()
        del mem_block  # Release memory allocation
        print("✅ Resources released. System normalized.")
