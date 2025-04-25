import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True  
)

# redis_client.set("test_key", "hello")
# print(redis_client.get("test_key")) 