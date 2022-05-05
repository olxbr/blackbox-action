import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-c", "--config", help="Action configs", default="")
    args = parser.parse_args()
    cfg = args.config
    j = json.loads(cfg)
    print(f"O valor de teste é {j['test']}")


if __name__ == '__main__':
    main()
