"""
Database configuration for results storage and history management.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from urllib.parse import urlparse


@dataclass
class PostgreSQLConfig:
    """PostgreSQL database configuration for results storage."""
    host: str = "localhost"
    port: int = 5432
    database: str = "haasscript_backtesting"
    username: str = "postgres"
    password: str = ""
    
    # Connection pool settings
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    
    # Performance settings
    statement_timeout: int = 300  # 5 minutes
    idle_in_transaction_timeout: int = 60
    
    def get_connection_string(self, include_password: bool = True) -> str:
        """Generate PostgreSQL connection string."""
        password_part = f":{self.password}" if include_password and self.password else ""
        return f"postgresql://{self.username}{password_part}@{self.host}:{self.port}/{self.database}"
    
    def validate(self) -> None:
        """Validate PostgreSQL configuration."""
        if not self.host:
            raise ValueError("PostgreSQL host is required")
        if not self.database:
            raise ValueError("PostgreSQL database name is required")
        if not self.username:
            raise ValueError("PostgreSQL username is required")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("PostgreSQL port must be between 1 and 65535")


@dataclass
class MongoDBConfig:
    """MongoDB configuration for RAG knowledge base."""
    host: str = "localhost"
    port: int = 27017
    database: str = "haasscript_knowledge"
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Connection settings
    connection_timeout_ms: int = 30000
    server_selection_timeout_ms: int = 30000
    max_pool_size: int = 100
    
    # Authentication
    auth_source: str = "admin"
    auth_mechanism: Optional[str] = None
    
    def get_connection_string(self, include_password: bool = True) -> str:
        """Generate MongoDB connection string."""
        if self.username and self.password and include_password:
            auth_part = f"{self.username}:{self.password}@"
        elif self.username:
            auth_part = f"{self.username}@"
        else:
            auth_part = ""
        
        return f"mongodb://{auth_part}{self.host}:{self.port}/{self.database}"
    
    def validate(self) -> None:
        """Validate MongoDB configuration."""
        if not self.host:
            raise ValueError("MongoDB host is required")
        if not self.database:
            raise ValueError("MongoDB database name is required")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("MongoDB port must be between 1 and 65535")


@dataclass
class RedisConfig:
    """Redis configuration for caching."""
    host: str = "localhost"
    port: int = 6379
    database: int = 0
    password: Optional[str] = None
    
    # Connection settings
    connection_timeout: int = 30
    socket_timeout: int = 30
    max_connections: int = 50
    
    # Performance settings
    decode_responses: bool = True
    health_check_interval: int = 30
    
    def get_connection_string(self, include_password: bool = True) -> str:
        """Generate Redis connection string."""
        password_part = f":{self.password}@" if include_password and self.password else ""
        return f"redis://{password_part}{self.host}:{self.port}/{self.database}"
    
    def validate(self) -> None:
        """Validate Redis configuration."""
        if not self.host:
            raise ValueError("Redis host is required")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("Redis port must be between 1 and 65535")
        if self.database < 0:
            raise ValueError("Redis database must be non-negative")


@dataclass
class DatabaseConfig:
    """Complete database configuration container."""
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)
    mongodb: MongoDBConfig = field(default_factory=MongoDBConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    
    # Feature flags
    enable_postgresql: bool = True
    enable_mongodb: bool = True
    enable_redis: bool = True
    
    def __post_init__(self):
        """Validate all database configurations."""
        if self.enable_postgresql:
            self.postgresql.validate()
        if self.enable_mongodb:
            self.mongodb.validate()
        if self.enable_redis:
            self.redis.validate()
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database configuration from environment variables."""
        config = cls()
        
        # PostgreSQL configuration
        if pg_host := os.getenv('POSTGRES_HOST'):
            config.postgresql.host = pg_host
        if pg_port := os.getenv('POSTGRES_PORT'):
            config.postgresql.port = int(pg_port)
        if pg_db := os.getenv('POSTGRES_DB'):
            config.postgresql.database = pg_db
        if pg_user := os.getenv('POSTGRES_USER'):
            config.postgresql.username = pg_user
        if pg_pass := os.getenv('POSTGRES_PASSWORD'):
            config.postgresql.password = pg_pass
        
        # MongoDB configuration
        if mongo_host := os.getenv('MONGO_HOST'):
            config.mongodb.host = mongo_host
        if mongo_port := os.getenv('MONGO_PORT'):
            config.mongodb.port = int(mongo_port)
        if mongo_db := os.getenv('MONGO_DB'):
            config.mongodb.database = mongo_db
        if mongo_user := os.getenv('MONGO_USER'):
            config.mongodb.username = mongo_user
        if mongo_pass := os.getenv('MONGO_PASSWORD'):
            config.mongodb.password = mongo_pass
        
        # Redis configuration
        if redis_host := os.getenv('REDIS_HOST'):
            config.redis.host = redis_host
        if redis_port := os.getenv('REDIS_PORT'):
            config.redis.port = int(redis_port)
        if redis_db := os.getenv('REDIS_DB'):
            config.redis.database = int(redis_db)
        if redis_pass := os.getenv('REDIS_PASSWORD'):
            config.redis.password = redis_pass
        
        # Feature flags
        config.enable_postgresql = os.getenv('ENABLE_POSTGRESQL', 'true').lower() == 'true'
        config.enable_mongodb = os.getenv('ENABLE_MONGODB', 'true').lower() == 'true'
        config.enable_redis = os.getenv('ENABLE_REDIS', 'true').lower() == 'true'
        
        return config
    
    @classmethod
    def from_url(cls, database_url: str) -> 'DatabaseConfig':
        """Create configuration from database URL."""
        parsed = urlparse(database_url)
        config = cls()
        
        if parsed.scheme == 'postgresql':
            config.postgresql.host = parsed.hostname or 'localhost'
            config.postgresql.port = parsed.port or 5432
            config.postgresql.database = parsed.path.lstrip('/')
            config.postgresql.username = parsed.username or 'postgres'
            config.postgresql.password = parsed.password or ''
        elif parsed.scheme == 'mongodb':
            config.mongodb.host = parsed.hostname or 'localhost'
            config.mongodb.port = parsed.port or 27017
            config.mongodb.database = parsed.path.lstrip('/')
            config.mongodb.username = parsed.username
            config.mongodb.password = parsed.password
        elif parsed.scheme == 'redis':
            config.redis.host = parsed.hostname or 'localhost'
            config.redis.port = parsed.port or 6379
            config.redis.database = int(parsed.path.lstrip('/')) if parsed.path else 0
            config.redis.password = parsed.password
        
        return config
    
    def to_dict(self, include_passwords: bool = False) -> Dict[str, Any]:
        """Convert database configuration to dictionary."""
        return {
            'postgresql': {
                'host': self.postgresql.host,
                'port': self.postgresql.port,
                'database': self.postgresql.database,
                'username': self.postgresql.username,
                'password': self.postgresql.password if include_passwords else '***',
                'min_connections': self.postgresql.min_connections,
                'max_connections': self.postgresql.max_connections,
                'connection_timeout': self.postgresql.connection_timeout,
            },
            'mongodb': {
                'host': self.mongodb.host,
                'port': self.mongodb.port,
                'database': self.mongodb.database,
                'username': self.mongodb.username,
                'password': self.mongodb.password if include_passwords else '***',
                'connection_timeout_ms': self.mongodb.connection_timeout_ms,
                'max_pool_size': self.mongodb.max_pool_size,
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'database': self.redis.database,
                'password': self.redis.password if include_passwords else '***',
                'connection_timeout': self.redis.connection_timeout,
                'max_connections': self.redis.max_connections,
            },
            'features': {
                'postgresql_enabled': self.enable_postgresql,
                'mongodb_enabled': self.enable_mongodb,
                'redis_enabled': self.enable_redis,
            }
        }