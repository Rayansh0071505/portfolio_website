# ElastiCache Redis for Semantic Caching
# Uses RedisJSON + RediSearch for LangChain RedisSemanticCache

# Subnet group for ElastiCache (uses private subnet)
resource "aws_elasticache_subnet_group" "redis" {
  count = var.redis_enabled ? 1 : 0

  name       = "${replace(var.project_name, "_", "-")}-redis-subnet-group"
  subnet_ids = [aws_subnet.private.id]

  tags = {
    Name = "${var.project_name}-redis-subnet-group"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "semantic_cache" {
  count = var.redis_enabled ? 1 : 0
  cluster_id           = "${replace(var.project_name, "_", "-")}-cache"
  engine               = "redis"
  engine_version       = "7.1"  # Latest stable with RedisJSON + RediSearch support
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  parameter_group_name = aws_elasticache_parameter_group.redis[0].name
  subnet_group_name    = aws_elasticache_subnet_group.redis[0].name
  security_group_ids   = [aws_security_group.redis.id]

  # Free tier compatible settings
  port                 = 6379

  # Backup and maintenance
  snapshot_retention_limit = 0  # Set to 0 for free tier (no backups)
  maintenance_window       = "sun:05:00-sun:06:00"

  # Auto-upgrade minor versions
  auto_minor_version_upgrade = true

  # Enable Multi-AZ only if needed (costs more)
  az_mode = "single-az"

  tags = {
    Name        = "${var.project_name}-semantic-cache"
    Purpose     = "LangChain semantic caching with vector similarity"
    CacheType   = "RedisSemanticCache"
  }
}

# Parameter Group for Redis
resource "aws_elasticache_parameter_group" "redis" {
  count = var.redis_enabled ? 1 : 0

  name   = "${replace(var.project_name, "_", "-")}-redis-params"
  family = "redis7"

  # Enable persistence (if needed, but adds cost)
  # For semantic cache, we can disable persistence (cache can rebuild)
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict least recently used keys when memory full
  }

  tags = {
    Name = "${var.project_name}-redis-params"
  }
}
