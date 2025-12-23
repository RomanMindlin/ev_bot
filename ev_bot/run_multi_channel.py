#!/usr/bin/env python3
"""
Multi-channel runner script for telegram_sender.py

This script executes telegram_sender.py multiple times with different configurations
for multiple Telegram channels. Configurations can be loaded from a JSON file or
environment variables.
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import subprocess


def load_config_from_file(config_file: str) -> List[Dict[str, Any]]:
    """
    Load channel configurations from a JSON file.
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        List of channel configurations
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Support both direct array and object with 'channels' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'channels' in data:
        return data['channels']
    else:
        raise ValueError("Invalid config format. Expected array or object with 'channels' key")


def load_config_from_env() -> List[Dict[str, Any]]:
    """
    Load channel configurations from CHANNELS_CONFIG environment variable.
    
    Returns:
        List of channel configurations
    """
    channels_config = os.getenv('CHANNELS_CONFIG')
    if not channels_config:
        raise ValueError("CHANNELS_CONFIG environment variable not set")
    
    return json.loads(channels_config)


def build_command(config: Dict[str, Any], sender_script: str) -> List[str]:
    """
    Build command line arguments for telegram_sender.py
    
    Args:
        config: Channel configuration dictionary
        sender_script: Path to telegram_sender.py
        
    Returns:
        Command as list of strings
    """
    cmd = [sys.executable, sender_script]
    
    # Required parameters
    if 'telegram_bot_token' in config:
        cmd.extend(['--bot-token', config['telegram_bot_token']])
    if 'telegram_channel_id' in config:
        cmd.extend(['--channel-id', config['telegram_channel_id']])
    if 'origin' in config:
        cmd.extend(['--origin', config['origin']])
    if 'language' in config:
        cmd.extend(['--language', config['language']])
    if 'currency' in config:
        cmd.extend(['--currency', config['currency']])
    
    # Optional API credentials
    if 'amadeus_client_id' in config:
        cmd.extend(['--amadeus-client-id', config['amadeus_client_id']])
    if 'amadeus_client_secret' in config:
        cmd.extend(['--amadeus-client-secret', config['amadeus_client_secret']])
    if 'travelpayouts_token' in config:
        cmd.extend(['--travelpayouts-token', config['travelpayouts_token']])
    if 'travelpayouts_marker' in config:
        cmd.extend(['--travelpayouts-marker', config['travelpayouts_marker']])
    if 'openai_key' in config:
        cmd.extend(['--openai-key', config['openai_key']])
    
    return cmd


async def run_channel(config: Dict[str, Any], sender_script: str, index: int, total: int) -> bool:
    """
    Run telegram_sender.py for a single channel configuration.
    
    Args:
        config: Channel configuration
        sender_script: Path to telegram_sender.py
        index: Current channel index (1-based)
        total: Total number of channels
        
    Returns:
        True if successful, False otherwise
    """
    channel_id = config.get('telegram_channel_id', 'unknown')
    origin = config.get('origin', 'unknown')
    language = config.get('language', 'unknown')
    
    print("\n============================================================")
    print(f"Processing channel {index}/{total}")
    print(f"Channel ID: {channel_id}")
    print(f"Origin: {origin}, Language: {language}, Currency: {config.get('currency', 'EUR')}")
    print("============================================================\n")
    
    cmd = build_command(config, sender_script)
    
    try:
        # Run the command
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(f"✓ Successfully processed channel {channel_id}")
            if stdout:
                print(stdout.decode())
            return True
        else:
            print(f"✗ Failed to process channel {channel_id}")
            if stderr:
                print(f"Error: {stderr.decode()}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Exception while processing channel {channel_id}: {e}", file=sys.stderr)
        return False


async def main():
    """Main function to run multi-channel sender."""
    parser = argparse.ArgumentParser(
        description='Run telegram_sender.py for multiple channels',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Load from JSON file
  python run_multi_channel.py --config channels.json
  
  # Load from environment variable
  python run_multi_channel.py --from-env
  
  # Use custom sender script path
  python run_multi_channel.py --config channels.json --sender-script ./custom/path/telegram_sender.py
        """
    )
    
    parser.add_argument(
        '--config',
        help='Path to JSON configuration file'
    )
    parser.add_argument(
        '--from-env',
        action='store_true',
        help='Load configuration from CHANNELS_CONFIG environment variable'
    )
    parser.add_argument(
        '--sender-script',
        default='ev_bot/telegram_sender.py',
        help='Path to telegram_sender.py script (default: ev_bot/telegram_sender.py)'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run channels in parallel (default: sequential)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.config and not args.from_env:
        parser.error("Either --config or --from-env must be specified")
    
    if args.config and args.from_env:
        parser.error("Cannot use both --config and --from-env")
    
    # Load configurations
    try:
        if args.config:
            print(f"Loading configuration from {args.config}")
            configs = load_config_from_file(args.config)
        else:
            print("Loading configuration from CHANNELS_CONFIG environment variable")
            configs = load_config_from_env()
        
        if not configs:
            print("Error: No channel configurations found", file=sys.stderr)
            sys.exit(1)
        
        print(f"Found {len(configs)} channel(s) to process\n")
        
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Verify sender script exists
    sender_script = Path(args.sender_script)
    if not sender_script.exists():
        print(f"Error: Sender script not found: {args.sender_script}", file=sys.stderr)
        sys.exit(1)
    
    # Process channels
    start_time = asyncio.get_event_loop().time()
    
    if args.parallel:
        print("Running channels in parallel...\n")
        tasks = [
            run_channel(config, str(sender_script), i+1, len(configs))
            for i, config in enumerate(configs)
        ]
        results = await asyncio.gather(*tasks)
    else:
        print("Running channels sequentially...\n")
        results = []
        for i, config in enumerate(configs):
            result = await run_channel(config, str(sender_script), i+1, len(configs))
            results.append(result)
    
    # Summary
    elapsed_time = asyncio.get_event_loop().time() - start_time
    successful = sum(results)
    failed = len(results) - successful
    
    print("\n============================================================")
    print("SUMMARY")
    print("{============================================================")
    print(f"Total channels: {len(configs)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Time elapsed: {elapsed_time:.2f} seconds")
    print(f"============================================================\n")
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
