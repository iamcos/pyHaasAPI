# Miro-HaasOnline Integration

This integration connects Miro collaborative boards with your local HaasOnline server, creating interactive trading dashboards and control panels.

## Features

- **Real-time Dashboard**: Live trading data visualization on Miro boards
- **Interactive Controls**: Click board elements to control trading bots
- **Visual Portfolio Management**: See account balances, P&L, and positions
- **Market Overview**: Real-time market data and sentiment analysis
- **Bot Status Monitoring**: Visual status of all trading bots

## Setup

### 1. Miro App Setup

1. Go to [Miro Developer Portal](https://developers.miro.com/)
2. Create a new app
3. Get your access token
4. Note your team ID

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Integration

```bash
# Start the webhook server
python webhook_server.py

# In another terminal, create a dashboard
python -c "
import asyncio
from miro_haas_bridge import MiroHaasBridge
from pyHaasAPI import SyncExecutor

async def create_dashboard():
    bridge = MiroHaasBridge('your_token', SyncExecutor())
    board_id = await bridge.create_trading_dashboard_board('your_team_id')
    print(f'Dashboard created: {board_id}')

asyncio.run(create_dashboard())
"
```

## Usage Examples

### Create Trading Dashboard

```python
from miro_haas_bridge import MiroHaasBridge
from pyHaasAPI import SyncExecutor

bridge = MiroHaasBridge(miro_token, haas_executor)
board_id = await bridge.create_trading_dashboard_board(team_id)
```

### Update Dashboard Data

```python
# Updates every 30 seconds
while True:
    await bridge.update_dashboard_data(board_id)
    await asyncio.sleep(30)
```

### Handle Board Interactions

The webhook server automatically handles board interactions like:
- Clicking on bot cards to start/stop bots
- Updating parameters through board elements
- Creating new trading strategies visually

## Dashboard Layout

The integration creates boards with these sections:

- **Header**: Dashboard title and timestamp
- **Account Summary**: Balance, P&L, and account status cards
- **Trading Bots**: Status cards for each bot with controls
- **Market Overview**: Real-time price data and market sentiment
- **Performance Metrics**: Charts and KPIs

## Advanced Features

### Custom Widgets

You can extend the integration to create custom Miro widgets:

```python
# Custom risk management widget
risk_widget = {
    "type": "card",
    "data": {
        "title": "Risk Alert",
        "description": f"Portfolio risk: {risk_level}%"
    },
    "style": {"fillColor": "red" if risk_level > 80 else "green"}
}
```

### Interactive Controls

Board elements can trigger actions on your Haas server:

```python
async def handle_bot_control(bot_name: str, action: str):
    if action == "start":
        await lab_manager.start_bot(bot_name)
    elif action == "stop":
        await lab_manager.stop_bot(bot_name)
```

## API Endpoints

- `POST /dashboard/create` - Create new dashboard
- `POST /dashboard/{board_id}/update` - Update dashboard data
- `POST /webhook/miro` - Handle Miro webhooks
- `GET /health` - Health check

## Security Considerations

- Use HTTPS for webhook endpoints
- Verify Miro webhook signatures
- Implement proper authentication for API endpoints
- Limit board access to authorized team members

## Troubleshooting

### Common Issues

1. **Webhook not receiving events**: Check your webhook URL is publicly accessible
2. **Board creation fails**: Verify Miro token and team permissions
3. **Data not updating**: Check HaasOnline server connectivity

### Logs

Check logs for detailed error information:

```bash
tail -f webhook_server.log
```

## Contributing

Feel free to extend this integration with additional features like:
- Advanced charting widgets
- Strategy backtesting visualization
- Risk management controls
- Multi-exchange support