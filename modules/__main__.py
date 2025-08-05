# modules/__main__.py

from .scanner import run_all_scanners

if __name__ == "__main__":
    print("Running Echo Oculus scanners...")
    results = run_all_scanners()
    print(f"Collected {len(results)} alerts:")
    for alert in results:
        print(alert)
