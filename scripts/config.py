#!/usr/bin/env python3
"""
Configuration management script following 12-factor app methodology.

Factor III: Config - Store config in the environment
Factor IV: Backing services - Treat backing services as attached resources
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from novitas.config.settings import Settings


def load_environment_config(environment: str) -> dict[str, str]:
    """Load environment configuration from .env file."""
    env_file = Path(f".env.{environment}")
    if not env_file.exists():
        print(f"Configuration file {env_file} not found.")
        sys.exit(1)

    config = {}
    with env_file.open() as f:
        for line in f:
            stripped_line = line.strip()
            if (
                stripped_line
                and not stripped_line.startswith("#")
                and "=" in stripped_line
            ):
                key, value = stripped_line.split("=", 1)
                config[key.strip()] = value.strip()

    return config


def validate_environment_config(environment: str) -> None:
    """
    Validate environment configuration.

    Args:
        environment: The environment to validate
    """
    print(f"Validating {environment} environment configuration...")

    # Set environment variable
    os.environ["NOVITAS_ENVIRONMENT"] = environment

    # Load configuration
    config = load_environment_config(environment)

    # Set environment variables for validation
    for key, value in config.items():
        if not key.startswith("#"):
            os.environ[key] = value

    # Create settings instance and validate
    try:
        settings = Settings()
        settings.validate_config()
        print(f"✅ {environment} configuration is valid")

        # Print key configuration
        print(f"  Database: {settings.resolved_database_url}")
        print(f"  Redis: {settings.redis_url}")
        print(f"  Environment: {settings.environment}")
        print(f"  Debug: {settings.debug}")

    except ValueError as e:
        print(f"❌ {environment} configuration validation failed: {e}")
        sys.exit(1)


def setup_environment(environment: str) -> None:
    """
    Set up environment configuration.

    Args:
        environment: The environment to set up
    """
    print(f"Setting up {environment} environment...")

    # Load configuration
    config = load_environment_config(environment)

    # Create .env file
    env_file = Path(f".env.{environment}")
    with env_file.open("w") as f:
        f.write(f"# {environment.title()} Environment Configuration\n")
        f.write("# Generated automatically - do not edit manually\n\n")

        for key, value in config.items():
            if not key.startswith("#"):
                f.write(f"{key}={value}\n")

    print(f"✅ Created {env_file}")
    print(f"📝 Please review and customize {env_file} with your actual values")


MIN_ARGS = 2
REQUIRED_ARGS = 3


def main() -> None:
    """Main function."""
    if len(sys.argv) < MIN_ARGS:
        print("Usage: python scripts/config.py <command> [environment]")
        print("Commands:")
        print("  validate <environment>  - Validate environment configuration")
        print("  setup <environment>     - Set up environment configuration")
        print("  list                    - List available environments")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        environments = ["development", "testing", "staging", "production"]
        print("Available environments:")
        for env in environments:
            env_file = Path(f"env.{env}.example")
            if env_file.exists():
                print(f"  ✅ {env}")
            else:
                print(f"  ❌ {env} (missing config file)")

    elif command in ["validate", "setup"]:
        if len(sys.argv) < REQUIRED_ARGS:
            print(f"Usage: python scripts/config.py {command} <environment>")
            sys.exit(1)

        environment = sys.argv[2]

        if command == "validate":
            validate_environment_config(environment)
        elif command == "setup":
            setup_environment(environment)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
