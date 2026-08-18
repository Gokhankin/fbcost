import sys
sys.path.insert(0, '/home/society/Masaüstü/fbcost')
from app import app, index

with app.test_request_context('/'):
    res = index()
    print("Rendered Output Length:", len(res))
    print("Rendered Output First 200 chars:")
    print(res[:200])
