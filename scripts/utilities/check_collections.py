from arango import ArangoClient
import os

client = ArangoClient(hosts='http://localhost:8529')
db = client.db(
    os.getenv('ARANGO_DB_NAME', 'memory_bank'),
    username=os.getenv('ARANGO_USER', 'root'),
    password=os.getenv('ARANGO_PASSWORD', 'openSesame')
)

print('Collections in memory_bank database:')
collections = []
for collection in db.collections():
    if not collection['name'].startswith('_'):  # Skip system collections
        collections.append((collection['name'], collection['type']))
        
# Sort and display
collections.sort()
for name, ctype in collections:
    print(f'  - {name} (type: {"edge" if ctype == 3 else "document"})')