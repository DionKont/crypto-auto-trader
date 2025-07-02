#!/usr/bin/env python3

import sys
sys.path.append('/Users/dionysioskontopodias/projects/crypto-auto-trader')

from modules.data_ingestion.data_manager import DataIngestionManager
from utils.symbol_manager import SymbolManager

def test_symbol_manager():
    print("Testing SymbolManager...")
    
    data_manager = DataIngestionManager()
    symbol_manager = SymbolManager(data_manager)
    
    print("1. Testing BTC lookup:")
    btc_info = symbol_manager.find_pair('BTC')
    if btc_info:
        print(f"   BTC: {btc_info}")
    else:
        print("   BTC not found")
    
    print("\n2. Testing ETH lookup:")
    eth_info = symbol_manager.find_pair('ETH')
    if eth_info:
        print(f"   ETH: {eth_info}")
    else:
        print("   ETH not found")
    
    print("\n3. Testing available symbols (first 10):")
    symbols = symbol_manager.get_available_symbols()[:10]
    print(f"   {', '.join(symbols)}")
    
    print("\n4. Testing quotes for BTC:")
    btc_quotes = symbol_manager.get_available_quotes_for_symbol('BTC')
    print(f"   BTC quotes: {btc_quotes}")
    
    print("\n5. Testing validation:")
    print(f"   BTC/USD valid: {symbol_manager.validate_symbol('BTC', 'USD')}")
    print(f"   NOTEXIST/USD valid: {symbol_manager.validate_symbol('NOTEXIST', 'USD')}")
    
    print("\n6. Testing total pairs:")
    all_pairs = symbol_manager.list_all_pairs()
    print(f"   Total pairs available: {len(all_pairs)}")
    print(f"   Sample pairs: {', '.join(all_pairs[:5])}...")

if __name__ == "__main__":
    test_symbol_manager()
