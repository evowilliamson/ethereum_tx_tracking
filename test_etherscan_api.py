"""
Quick test script to verify Etherscan API connection
"""

import requests
import json
from blockchain_settings import ETHERSCAN_API_KEY, WALLET_ADDRESS
from ethereum_config import ETHERSCAN_API_BASE, ETHEREUM_CHAIN_ID

def test_api():
    """Test the Etherscan API connection"""
    print("Testing Etherscan API connection...")
    print(f"API Key: {ETHERSCAN_API_KEY[:10]}...")
    print(f"Address: {WALLET_ADDRESS}")
    print("=" * 60)
    
    # Test 1: Get normal transactions using V2 API
    print("\nTest 1: Fetching normal transactions (V2 API)...")
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': WALLET_ADDRESS,
        'startblock': 0,
        'endblock': 99999999,
        'page': 1,
        'offset': 10,
        'sort': 'desc',
        'apikey': ETHERSCAN_API_KEY,
        'chainid': ETHEREUM_CHAIN_ID  # Required for V2
    }
    
    response = requests.get(ETHERSCAN_API_BASE, params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"Message: {data.get('message', 'N/A')}")
        
        if data.get('status') == '1':
            result = data.get('result', [])
            print(f"Found {len(result)} transactions")
            if result:
                print(f"Latest transaction hash: {result[0].get('hash', 'N/A')}")
        else:
            print(f"Error: {data.get('message', 'Unknown error')}")
            print(f"Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"HTTP Error: {response.text}")
    
    # Test 2: Get ERC-20 transfers using V2 API
    print("\nTest 2: Fetching ERC-20 transfers (V2 API)...")
    params['action'] = 'tokentx'
    params['chainid'] = ETHEREUM_CHAIN_ID  # Ensure chainid is set
    response = requests.get(ETHERSCAN_API_BASE, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        print(f"API Status: {data.get('status')}")
        print(f"Message: {data.get('message', 'N/A')}")
        
        if data.get('status') == '1':
            result = data.get('result', [])
            print(f"Found {len(result)} ERC-20 transfers")
            if result:
                print(f"Latest transfer hash: {result[0].get('hash', 'N/A')}")
        else:
            print(f"Error: {data.get('message', 'Unknown error')}")
    else:
        print(f"HTTP Error: {response.text}")
    
    print("\n" + "=" * 60)
    print("Test complete!")

if __name__ == "__main__":
    test_api()

