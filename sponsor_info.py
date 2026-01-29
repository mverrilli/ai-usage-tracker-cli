#!/usr/bin/env python3
"""
Sponsor information for AI Usage Tracker CLI
This script can be integrated into the CLI to show sponsor information.
"""

import sys

SPONSOR_INFO = """
╔══════════════════════════════════════════════════════════════╗
║                    Support AI Usage Tracker                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  This tool is developed as open source software.            ║
║  Your sponsorship helps fund development and maintenance.    ║
║                                                              ║
║  🏆 Sponsor Tiers:                                           ║
║    • Supporter: $3/month - Name in README, early access     ║
║    • Sponsor: $10/month - Priority support, custom configs  ║
║    • Organization: $50/month - Custom integrations, logo    ║
║                                                              ║
║  📍 Sponsor now: https://github.com/sponsors/mverrilli      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

def show_sponsor_info():
    """Display sponsor information"""
    print(SPONSOR_INFO)

def get_sponsor_command_suggestion():
    """Return a suggestion for adding sponsor command to CLI"""
    return """
To add sponsor information to your CLI:

1. Add this import to cli.py:
   from .sponsor_info import show_sponsor_info

2. Add sponsor command parser:
   sponsor_parser = subparsers.add_parser("sponsor", help="Show sponsor information")
   sponsor_parser.set_defaults(func=lambda args: show_sponsor_info())

3. Or add to epilog/help text:
   epilog=f\"\"\"{standard_epilog}\\n\\n{SPONSOR_INFO}\"\"\"
"""

if __name__ == "__main__":
    show_sponsor_info()
    
    # Optional: Show how to integrate
    if len(sys.argv) > 1 and sys.argv[1] == "--integration":
        print("\n" + "="*60)
        print("Integration Instructions:")
        print("="*60)
        print(get_sponsor_command_suggestion())