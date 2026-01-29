# AI Usage Tracker

Track AI API usage and costs across multiple providers in a single, local-first tool.

## Features

- **Multi-provider support**: OpenAI, Anthropic, Google Gemini, DeepSeek, and more
- **Cost tracking**: Real-time cost calculation based on provider pricing
- **Budget alerts**: Get notified before exceeding your budget
- **Local storage**: All data stored locally in SQLite, no cloud dependency
- **Easy integration**: Works with Clawdbot sessions or standalone logging
- **CLI interface**: Simple commands for querying and reporting

## Installation

```bash
# Install from source
git clone https://github.com/mverrilli/ai-usage-tracker-cli.git
cd ai-usage-tracker-cli
pip install -e .

# Or install directly (coming soon)
# pip install ai-usage-tracker
```

## Quick Start

1. **Initialize the database**:
   ```bash
   ai-usage-tracker init
   ```

2. **Start monitoring session logs**:
   ```bash
   ai-usage-tracker monitor --path ~/.clawdbot/sessions/
   ```

3. **View usage summary**:
   ```bash
   ai-usage-tracker summary
   ```

4. **Set budget alerts**:
   ```bash
   ai-usage-tracker alert --provider openai --daily 10.00
   ```

## Usage Examples

### Track usage from Clawdbot sessions
```bash
# Parse existing session logs
ai-usage-tracker parse --path ~/.clawdbot/sessions/

# Monitor in real-time
ai-usage-tracker monitor --path ~/.clawdbot/sessions/ --watch
```

### Generate reports
```bash
# Daily usage report
ai-usage-tracker report --period daily

# Provider breakdown
ai-usage-tracker report --by provider

# Export to CSV
ai-usage-tracker export --format csv --output usage.csv
```

### Budget management
```bash
# Set monthly budget
ai-usage-tracker budget --monthly 100.00

# Check current spending
ai-usage-tracker spending

# Get alert when接近 budget
ai-usage-tracker alert --threshold 80
```

## Configuration

Create `~/.config/ai-usage-tracker/config.yaml`:

```yaml
database:
  path: ~/.local/share/ai-usage-tracker/usage.db
  
providers:
  openai:
    enabled: true
    pricing:
      gpt-4o: 0.005
      gpt-4o-mini: 0.0015
      
  anthropic:
    enabled: true
    pricing:
      claude-3-5-sonnet: 0.003
      claude-3-5-haiku: 0.00025
      
  google:
    enabled: true
    pricing:
      gemini-2.0-flash: 0.0001
      gemini-2.0-pro: 0.0025

alerts:
  enabled: true
  daily_limit: 10.00
  monthly_limit: 100.00
  notify_via: console  # console, email, webhook
  
logging:
  level: INFO
  file: ~/.local/share/ai-usage-tracker/logs/tracker.log
```

## Supported Providers

- **OpenAI**: GPT-4, GPT-4o, GPT-4o-mini, o1, o1-mini
- **Anthropic**: Claude 3.5 Sonnet, Claude 3.5 Haiku
- **Google**: Gemini 2.0 Flash, Gemini 2.0 Pro
- **DeepSeek**: DeepSeek Chat, DeepSeek Reasoner
- **Custom providers**: Add your own pricing models

## How It Works

1. **Session Parsing**: Reads Clawdbot session logs to extract usage data
2. **Cost Calculation**: Applies provider-specific pricing to token counts
3. **Database Storage**: Stores all usage data in local SQLite database
4. **Alert Monitoring**: Checks spending against configured budgets
5. **Reporting**: Generates summaries and exports data

## Development

```bash
# Clone repository
git clone https://github.com/mverrilli/ai-usage-tracker-cli.git
cd ai-usage-tracker-cli

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
black ai_usage_tracker/
flake8 ai_usage_tracker/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you find this tool useful, consider supporting its development through GitHub Sponsors. Your support helps fund ongoing development, maintenance, and new features.

### 🏆 Sponsorship Tiers

#### Tier 1: Supporter ($3/month)
- 🎖️ Name listed in README supporters section
- 📝 Early access to new features (beta releases)
- 🐛 Basic support via GitHub Issues
- ❤️ Satisfaction of supporting open source

#### Tier 2: Sponsor ($10/month)
- ⚡ Priority feature requests
- 📧 Direct email support
- 🔧 Custom alert configurations
- 🏆 Name in special sponsors section with link
- 📊 Monthly usage report insights

#### Tier 3: Organization ($50/month)
- 🤝 Custom integrations for your workflow
- 🏢 Enterprise support (SLA)
- 🎯 Private consulting sessions (1 hour/month)
- 🏅 Logo displayed on project page
- 📈 Advanced analytics and reporting

### Current Sponsors

#### 🏆 Gold Sponsors ($50+/month)
*Be the first Gold Sponsor!*

#### 🥈 Silver Sponsors ($10+/month)
*Be the first Silver Sponsor!*

#### 🥉 Supporters ($3+/month)
*Be the first Supporter!*

### Become a Sponsor
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-red?logo=github)](https://github.com/sponsors/mverrilli)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/mverrilli)

### How Sponsor Funds Are Used
- **Development**: New features and improvements
- **Maintenance**: Bug fixes and updates
- **Documentation**: Better guides and tutorials
- **Infrastructure**: Hosting for web dashboard (planned)
- **Community**: Support for users and contributors

## Acknowledgments

- Built as part of the Autonomous Initiatives project
- Inspired by the need for better AI cost management
- Thanks to all contributors and supporters
- Special thanks to future sponsors who will help this project grow
