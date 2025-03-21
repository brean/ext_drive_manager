import argparse
from .ui import main as main_ui


def main():
    parser = argparse.ArgumentParser()
    main_ui()


if __name__ == "__main__":
    main()