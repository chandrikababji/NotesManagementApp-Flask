from itsdangerous import URLSafeTimedSerializer
secret_key=b'\x9e\x9f\xb8N\xb7'  #generated secret key in idle
def endata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data)
def dndata(data):
    serializer=URLSafeTimedSerializer(secret_key)
    return serializer.loads(data)