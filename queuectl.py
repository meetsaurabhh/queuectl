#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(prog='queuectl', description='queuectl - background job queue CLI')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('hello', help='Simple test command')

    args = parser.parse_args()

    if args.command == 'hello':
        print("✅ queuectl is set up successfully!")
        print("Run `python queuectl.py --help` to see available commands (we’ll add more soon).")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
