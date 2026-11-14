import sys

def main() -> int:
    print("Hello from tool.py")
    print("\nArguments received:")
    for index, argument in enumerate(sys.argv[1:], start=1):
        print(f"{index}. {argument}")

    if "--fail" in sys.argv:
        print("\nSimulating tool failure")
        return 42
    return 0

if __name__ == "__main__":
    sys.exit(main())