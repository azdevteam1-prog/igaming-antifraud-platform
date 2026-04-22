import redis
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class RealTimeFeatureStore:
    """Redis-based real-time feature store for streaming fraud detection.
    
    Features:
    - Sub-second feature retrieval
    - Time-windowed aggregations (1h, 24h, 7d)
    - Automatic expiration
    - Streaming updates
    - Distributed caching
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            self.redis.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
    
    def _get_key(self, entity_type: str, entity_id: str, feature_name: str) -> str:
        """Generate Redis key."""
        return f"features:{entity_type}:{entity_id}:{feature_name}"
    
    def _get_timeseries_key(self, entity_type: str, entity_id: str, metric: str) -> str:
        """Generate time-series key for aggregations."""
        return f"ts:{entity_type}:{entity_id}:{metric}"
    
    # ===== Player Features =====
    
    def update_player_transaction(self, player_id: str, transaction: Dict[str, Any]):
        """Update player features when new transaction occurs (streaming)."""
        if not self.redis:
            return
        
        try:
            amount = float(transaction.get('amount', 0))
            tx_type = transaction.get('tx_type', 'unknown')
            status = transaction.get('status', 'unknown')
            timestamp = datetime.utcnow().timestamp()
            
            # Store transaction in time-series (sorted set by timestamp)
            ts_key = self._get_timeseries_key('player', player_id, 'transactions')
            self.redis.zadd(ts_key, {json.dumps(transaction): timestamp})
            self.redis.expire(ts_key, 7 * 86400)  # Keep 7 days
            
            # Update real-time counters
            self._increment_counter(f"player:{player_id}:tx_count_total", 1)
            self._increment_counter(f"player:{player_id}:tx_count_{tx_type}", 1)
            
            if status == 'failed':
                self._increment_counter(f"player:{player_id}:failed_count", 1)
            elif status == 'chargeback':
                self._increment_counter(f"player:{player_id}:chargeback_count", 1)
            
            # Update amount aggregations
            self._update_amount_stats(player_id, amount, tx_type)
            
            # Update velocity features
            self._update_velocity_features(player_id, timestamp)
            
        except Exception as e:
            logger.error(f"Failed to update player features: {e}")
    
    def _increment_counter(self, key: str, value: int = 1, ttl: int = 7 * 86400):
        """Increment counter with expiration."""
        self.redis.incr(key, value)
        self.redis.expire(key, ttl)
    
    def _update_amount_stats(self, player_id: str, amount: float, tx_type: str):
        """Update amount statistics (running average, max, etc.)."""
        # Store amounts in sorted set for percentile calculations
        amounts_key = f"amounts:{player_id}:{tx_type}"
        self.redis.zadd(amounts_key, {str(amount): datetime.utcnow().timestamp()})
        self.redis.expire(amounts_key, 7 * 86400)
        
        # Update max amount
        max_key = f"max_amount:{player_id}:{tx_type}"
        current_max = self.redis.get(max_key)
        if not current_max or float(current_max) < amount:
            self.redis.setex(max_key, 7 * 86400, amount)
    
    def _update_velocity_features(self, player_id: str, timestamp: float):
        """Update transaction velocity features."""
        # Store timestamps for velocity calculations
        velocity_key = f"velocity:{player_id}"
        self.redis.zadd(velocity_key, {str(timestamp): timestamp})
        self.redis.expire(velocity_key, 86400)  # Keep 24 hours
    
    def get_player_features(self, player_id: str) -> Dict[str, Any]:
        """Get all real-time features for a player."""
        if not self.redis:
            return {}
        
        now = datetime.utcnow().timestamp()
        features = {}
        
        try:
            # Time-windowed transaction counts
            ts_key = self._get_timeseries_key('player', player_id, 'transactions')
            
            # Last 1 hour
            one_hour_ago = now - 3600
            tx_1h = self.redis.zrangebyscore(ts_key, one_hour_ago, now)
            features['tx_count_1h'] = len(tx_1h)
            
            # Last 24 hours
            one_day_ago = now - 86400
            tx_24h = self.redis.zrangebyscore(ts_key, one_day_ago, now)
            features['tx_count_24h'] = len(tx_24h)
            
            # Last 7 days
            seven_days_ago = now - (7 * 86400)
            tx_7d = self.redis.zrangebyscore(ts_key, seven_days_ago, now)
            features['tx_count_7d'] = len(tx_7d)
            
            # Amount statistics
            amounts_24h = []
            for tx_json in tx_24h:
                try:
                    tx = json.loads(tx_json)
                    amounts_24h.append(float(tx.get('amount', 0)))
                except:
                    pass
            
            if amounts_24h:
                features['avg_amount_24h'] = sum(amounts_24h) / len(amounts_24h)
                features['max_amount_24h'] = max(amounts_24h)
                features['min_amount_24h'] = min(amounts_24h)
            else:
                features['avg_amount_24h'] = 0
                features['max_amount_24h'] = 0
                features['min_amount_24h'] = 0
            
            # Counters
            features['failed_count'] = int(self.redis.get(f"player:{player_id}:failed_count") or 0)
            features['chargeback_count'] = int(self.redis.get(f"player:{player_id}:chargeback_count") or 0)
            
            # Velocity (transactions per hour)
            velocity_key = f"velocity:{player_id}"
            timestamps = self.redis.zrangebyscore(velocity_key, one_hour_ago, now)
            features['velocity_1h'] = len(timestamps)
            
            # Unique entities (simplified - would track in separate sets)
            unique_ips = set()
            unique_devices = set()
            for tx_json in tx_24h:
                try:
                    tx = json.loads(tx_json)
                    if tx.get('ip_address'):
                        unique_ips.add(tx['ip_address'])
                    if tx.get('device_id'):
                        unique_devices.add(tx['device_id'])
                except:
                    pass
            
            features['unique_ips_24h'] = len(unique_ips)
            features['unique_devices_24h'] = len(unique_devices)
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to get player features: {e}")
            return {}
    
    # ===== Device Features =====
    
    def update_device_fingerprint(self, device_id: str, player_id: str, fingerprint: Dict[str, Any]):
        """Track device fingerprint and associated players."""
        if not self.redis:
            return
        
        try:
            # Store device -> players mapping
            device_players_key = f"device:{device_id}:players"
            self.redis.sadd(device_players_key, player_id)
            self.redis.expire(device_players_key, 30 * 86400)  # 30 days
            
            # Store fingerprint
            fp_key = f"device:{device_id}:fingerprint"
            self.redis.setex(fp_key, 30 * 86400, json.dumps(fingerprint))
            
            # Track first/last seen
            if not self.redis.exists(f"device:{device_id}:first_seen"):
                self.redis.setex(f"device:{device_id}:first_seen", 365 * 86400, datetime.utcnow().isoformat())
            self.redis.setex(f"device:{device_id}:last_seen", 30 * 86400, datetime.utcnow().isoformat())
            
        except Exception as e:
            logger.error(f"Failed to update device fingerprint: {e}")
    
    def get_device_shared_players(self, device_id: str) -> List[str]:
        """Get all players who used this device."""
        if not self.redis:
            return []
        
        try:
            device_players_key = f"device:{device_id}:players"
            return list(self.redis.smembers(device_players_key))
        except Exception as e:
            logger.error(f"Failed to get device shared players: {e}")
            return []
    
    # ===== IP Features =====
    
    def update_ip_activity(self, ip_address: str, player_id: str, action: str):
        """Track IP address activity."""
        if not self.redis:
            return
        
        try:
            # Store IP -> players mapping
            ip_players_key = f"ip:{ip_address}:players"
            self.redis.sadd(ip_players_key, player_id)
            self.redis.expire(ip_players_key, 7 * 86400)
            
            # Store activity timeline
            activity_key = f"ip:{ip_address}:activity"
            activity = {
                'player_id': player_id,
                'action': action,
                'timestamp': datetime.utcnow().isoformat()
            }
            self.redis.zadd(activity_key, {json.dumps(activity): datetime.utcnow().timestamp()})
            self.redis.expire(activity_key, 7 * 86400)
            
        except Exception as e:
            logger.error(f"Failed to update IP activity: {e}")
    
    def get_ip_shared_players(self, ip_address: str) -> List[str]:
        """Get all players who used this IP."""
        if not self.redis:
            return []
        
        try:
            ip_players_key = f"ip:{ip_address}:players"
            return list(self.redis.smembers(ip_players_key))
        except Exception as e:
            logger.error(f"Failed to get IP shared players: {e}")
            return []
    
    # ===== Batch Operations =====
    
    def batch_get_features(self, player_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get features for multiple players efficiently."""
        if not self.redis:
            return {}
        
        results = {}
        for player_id in player_ids:
            results[player_id] = self.get_player_features(player_id)
        
        return results
    
    def clear_player_features(self, player_id: str):
        """Clear all features for a player (for testing/debugging)."""
        if not self.redis:
            return
        
        pattern = f"*{player_id}*"
        for key in self.redis.scan_iter(match=pattern):
            self.redis.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feature store statistics."""
        if not self.redis:
            return {}
        
        try:
            info = self.redis.info()
            return {
                'total_keys': info.get('db0', {}).get('keys', 0),
                'used_memory_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_hours': round(info.get('uptime_in_seconds', 0) / 3600, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
