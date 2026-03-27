# mock_data.py
incoming_transactions = [
    # Normal 
    {"txn_id": "T1", "src": "User_A", "dst": "User_B", "amount": 150, "device_id": "DEV_001"},
    {"txn_id": "T2", "src": "User_X", "dst": "User_Y", "amount": 20, "device_id": "DEV_099"},
    
    # Smurfing Loop (A sends to B, B to C, C to A)
    {"txn_id": "T3", "src": "User_B", "dst": "User_C", "amount": 145, "device_id": "DEV_002"},
    {"txn_id": "T4", "src": "User_C", "dst": "User_A", "amount": 140, "device_id": "DEV_003"},
    
    # SYNTHETIC IDENTITY FRAUD (Multiple users, one device)
    {"txn_id": "T5", "src": "User_D", "dst": "User_Z", "amount": 500, "device_id": "DEV_FRAUD_1"},
    {"txn_id": "T6", "src": "User_E", "dst": "User_Z", "amount": 500, "device_id": "DEV_FRAUD_1"},
    {"txn_id": "T7", "src": "User_F", "dst": "User_Z", "amount": 500, "device_id": "DEV_FRAUD_1"},
]