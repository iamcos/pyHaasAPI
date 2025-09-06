# Enhanced Authentication System for HaasOnline MCP Server

This enhanced authentication system automatically cycles through multiple credential sets to find the working one for your current server environment. It intelligently manages authentication across different HaasOnline servers and environments.

## 🎯 Key Features

### Smart Credential Management
- **Multiple Credential Sets**: Support for Primary, Local, Backup, and Dev credentials
- **Automatic Discovery**: Cycles through available credentials to find working ones
- **Priority-Based Selection**: Uses success history to prioritize most reliable credentials
- **Session Persistence**: Caches successful authentications for 24 hours
- **Failure Tracking**: Learns from failed attempts to optimize future authentication

### Environment Flexibility
- **Multi-Server Support**: Works with different HaasOnline server instances
- **Development Environments**: Separate credentials for local/dev servers
- **Fallback System**: Graceful degradation to basic authentication if needed
- **Configuration Validation**: Automatic validation of credential completeness

## 🔧 Setup

### 1. Environment Variables
Add your credential sets to your `.env` file:

```env
# Server Configuration
API_HOST=localhost
API_PORT=8090

# Primary Credentials (Production)
API_EMAIL=your-production-email@domain.com
API_PASSWORD=your-production-password

# Local Development Credentials
API_EMAIL_LOCAL=your-local-email@domain.com
API_PASSWORD_LOCAL=your-local-password

# Backup Credentials (Optional)
API_EMAIL_BACKUP=backup-email@domain.com
API_PASSWORD_BACKUP=backup-password

# Development Environment (Optional)
API_EMAIL_DEV=dev-email@domain.com
API_PASSWORD_DEV=dev-password
```

### 2. Quick Setup Script
Run the interactive setup script:

```bash
python setup_enhanced_auth.py
```

This script will:
- Check your current credential configuration
- Help you set up new credential sets interactively
- Test the authentication system
- Verify MCP server integration

## 🚀 How It Works

### Authentication Flow
1. **Priority Calculation**: Ranks credential sets by success rate and recency
2. **Sequential Testing**: Tries credentials in priority order
3. **Success Caching**: Stores successful authentication for reuse
4. **Failure Learning**: Updates failure statistics for future optimization
5. **Session Management**: Maintains active session until expiration

### Priority Factors
- **Recent Success**: Recently successful credentials get highest priority
- **Success Rate**: Historical success/failure ratio
- **Credential Type**: Local credentials prioritized in development environments
- **Last Success Time**: More recent successes ranked higher

### Cache Management
- **Memory Cache**: Fast access to active sessions
- **Disk Cache**: Persistent storage of authentication statistics
- **TTL Management**: Different timeouts for different data types
- **Automatic Cleanup**: Expired entries removed automatically

## 📊 Authentication Statistics

The system tracks detailed statistics for each credential set:

- **Success Count**: Number of successful authentications
- **Failure Count**: Number of failed attempts
- **Success Rate**: Percentage of successful attempts
- **Last Successful**: Timestamp of most recent success
- **Credential Type**: Primary, Local, Backup, or Dev

## 🛠️ MCP Server Integration

### New Tools Added
The enhanced MCP server includes these new tools:

#### `get_auth_status`
Returns detailed authentication status:
```json
{
  "authenticated": true,
  "credential_sets_available": 3,
  "current_session": {
    "credential_set": "local",
    "server_info": {
      "host": "localhost",
      "port": 8090,
      "account_name": "Development Account"
    }
  },
  "credential_sets": [...]
}
```

#### `refresh_authentication`
Forces re-authentication with all available credentials:
```json
{
  "success": true,
  "message": "Authentication refreshed successfully with local credentials",
  "server_info": {...}
}
```

### Server Initialization
The MCP server now automatically:
1. Loads all available credential sets from environment
2. Attempts authentication using priority-based selection
3. Falls back to original authentication if enhanced system unavailable
4. Provides detailed logging of authentication process

## 💻 Code Examples

### Basic Usage
```python
from mcp_server.auth_manager import get_auth_manager

# Get authenticated executor
auth_manager = get_auth_manager()
result = auth_manager.authenticate()

if result.success:
    executor = result.executor
    print(f"Connected with {result.credential_set.name} credentials")
    # Use executor for API calls
else:
    print(f"Authentication failed: {result.error_message}")
```

### Advanced Usage
```python
from mcp_server.auth_manager import get_auth_manager

auth_manager = get_auth_manager()

# Get detailed status
status = auth_manager.get_authentication_status()
print(f"Available credential sets: {status['credential_sets_available']}")

# Force refresh
result = auth_manager.refresh_authentication()
if result.success:
    print("Authentication refreshed successfully")

# Add new credential set dynamically
auth_manager.add_credential_set(
    name="staging",
    email="staging@domain.com", 
    password="staging-password",
    description="Staging server credentials"
)
```

### MCP Server Tools Usage
```python
# Through MCP server tools
import asyncio
from mcp_server.server import HaasMCPServer

async def test_auth():
    server = HaasMCPServer()
    
    # Get authentication status
    status = await server._execute_tool("get_auth_status", {})
    print(status)
    
    # Refresh authentication
    refresh = await server._execute_tool("refresh_authentication", {})
    print(refresh)
```

## 🔍 Troubleshooting

### Common Issues

**No Credentials Found**
- Check your `.env` file exists and contains credential variables
- Verify environment variables are properly formatted
- Use `setup_enhanced_auth.py` to configure credentials interactively

**Authentication Fails for All Credentials**
- Verify server connectivity (check API_HOST and API_PORT)
- Confirm credentials are valid for the target server
- Check server logs for specific error messages
- Test individual credential sets manually

**Cache Issues**
- Delete `.auth_cache.json` to reset authentication statistics
- Check cache directory permissions
- Verify disk space availability

### Debug Mode
Enable debug logging for detailed authentication flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from mcp_server.auth_manager import get_auth_manager
auth_manager = get_auth_manager()
result = auth_manager.authenticate()
```

### Manual Cache Management
```python
from mcp_server.auth_manager import get_auth_manager

auth_manager = get_auth_manager()

# Clear expired cache entries
auth_manager.cache.clear_expired()

# Force refresh (ignores cache)
result = auth_manager.authenticate(force_refresh=True)
```

## 📁 File Structure

```
mcp_server/
├── auth_manager.py              # Core authentication manager
├── server.py                    # Enhanced MCP server
└── .auth_cache.json            # Authentication statistics cache

setup_enhanced_auth.py           # Interactive setup script
ENHANCED_AUTH_GUIDE.md          # This documentation
.env                            # Environment variables
```

## 🔄 Migration from Basic Auth

If you're upgrading from the basic authentication system:

1. **Backup Current Setup**: Save your existing `.env` file
2. **Install Enhanced System**: Copy `auth_manager.py` to `mcp_server/`
3. **Update Server**: The enhanced server.py automatically detects and uses the new system
4. **Test Migration**: Run `python setup_enhanced_auth.py` to verify
5. **Add Additional Credentials**: Set up multiple credential sets as needed

The system maintains backward compatibility - if the enhanced auth manager isn't available, it falls back to the original authentication method.

## 🎯 Best Practices

### Credential Management
- Use descriptive names for different environments
- Regularly rotate credentials across all sets
- Keep backup credentials updated
- Use separate accounts for development/testing

### Environment Configuration
- Set up local credentials for development
- Use production credentials only in production
- Configure appropriate server hosts/ports for each environment
- Test authentication after any credential changes

### Monitoring
- Monitor authentication success rates
- Review authentication logs regularly
- Set up alerts for authentication failures
- Track which credential sets are most reliable

---

**✅ Your enhanced authentication system is now ready to automatically handle multiple credential sets and ensure reliable connections to your HaasOnline servers!**