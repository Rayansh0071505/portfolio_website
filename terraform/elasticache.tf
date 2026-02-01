# ElastiCache Valkey for Semantic Caching with Vector Search
# Uses Replication Group API (required for Valkey)

# Subnet group for ElastiCache (uses private subnet)
resource "aws_elasticache_subnet_group" "redis" {
  count = var.redis_enabled ? 1 : 0

  name       = "${replace(var.project_name, "_", "-")}-valkey-subnet-group"
  subnet_ids = [aws_subnet.private.id]

  tags = {
    Name = "${var.project_name}-valkey-subnet-group"
  }
}

# ElastiCache Valkey Replication Group with Vector Search
resource "aws_elasticache_replication_group" "semantic_cache" {
  count = var.redis_enabled ? 1 : 0

  replication_group_id       = "${replace(var.project_name, "_", "-")}-cache"
  description                = "Valkey cluster for semantic caching with vector search"
  engine                     = "valkey"
  engine_version             = "8.2"
  node_type                  = var.redis_node_type
  num_cache_clusters         = 1
  parameter_group_name       = aws_elasticache_parameter_group.redis[0].name
  subnet_group_name          = aws_elasticache_subnet_group.redis[0].name
  security_group_ids         = [aws_security_group.redis.id]
  port                       = 6379

  # Single node configuration (free tier compatible)
  automatic_failover_enabled = false
  multi_az_enabled          = false

  # Backup and maintenance
  snapshot_retention_limit = 0  # No backups for free tier
  maintenance_window       = "sun:05:00-sun:06:00"

  # Auto-upgrade minor versions
  auto_minor_version_upgrade = true

  # At-rest encryption (optional, adds cost)
  at_rest_encryption_enabled = false
  transit_encryption_enabled = false

  tags = {
    Name        = "${var.project_name}-semantic-cache"
    Purpose     = "LangChain semantic caching with vector similarity"
    CacheType   = "ValkeySemanticCache"
  }

  lifecycle {
    create_before_destroy = false
  }
}

# Parameter Group for Valkey
resource "aws_elasticache_parameter_group" "redis" {
  count = var.redis_enabled ? 1 : 0

  name   = "${replace(var.project_name, "_", "-")}-valkey-params"
  family = "valkey8"

  # Enable persistence (if needed, but adds cost)
  # For semantic cache, we can disable persistence (cache can rebuild)
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"  # Evict least recently used keys when memory full
  }

  tags = {
    Name = "${var.project_name}-valkey-params"
  }
}
