"""CLI entry point for local testing and scheduler generation."""

import argparse
import json
import os
import sys

import boto3

from .config.loader import load_config
from .config.validator import validate_config
from .scheduler.generator import SchedulerGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description="aws-lambda-shutdown CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate-schedulers", help="Generate EventBridge Schedulers from config.json")
    gen.add_argument("--config", default=None, help="Path to config.json (default: CONFIG_FILE env or config.json)")
    rm = sub.add_parser("remove-schedulers", help="Delete all EventBridge Schedulers (shutdown-*)")
    args = parser.parse_args()

    if args.command == "generate-schedulers":
        config = validate_config(load_config(args.config))
        generator = SchedulerGenerator(
            scheduler=boto3.client("scheduler"),
            lambda_arn=os.environ["LAMBDA_ARN"],
            scheduler_role_arn=os.environ["SCHEDULER_ROLE_ARN"],
        )
        result = generator.generate(config)
        print(json.dumps(result, indent=2))
    elif args.command == "remove-schedulers":
        generator = SchedulerGenerator(scheduler=boto3.client("scheduler"))
        result = generator.remove_all()
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())