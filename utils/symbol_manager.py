#!/usr/bin/env python3

class SymbolManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.pairs_cache = None
        self.symbol_map = {}
    
    def _load_pairs(self):
        if self.pairs_cache is None:
            self.pairs_cache = self.data_manager.get_tradeable_pairs()
            self._build_symbol_map()
        return self.pairs_cache
    
    def _build_symbol_map(self):
        if not self.pairs_cache:
            return
        
        for pair_name, pair_info in self.pairs_cache.items():
            base = pair_info.get('base', '').upper()
            quote = pair_info.get('quote', '').upper()
            wsname = pair_info.get('wsname', '')
            
            # Normalize base symbol
            if base in ['XXBT', 'XBT']:
                user_symbol = 'BTC'
            elif base.startswith('X') and len(base) > 1:
                user_symbol = base[1:]
            elif base.startswith('Z') and len(base) > 1:
                user_symbol = base[1:]
            else:
                user_symbol = base
            
            # Normalize quote
            if quote in ['ZUSD']:
                quote_symbol = 'USD'
            elif quote in ['ZEUR']:
                quote_symbol = 'EUR'
            elif quote in ['ZGBP']:
                quote_symbol = 'GBP'
            else:
                quote_symbol = quote
            
            pair_key = f"{user_symbol}/{quote_symbol}"
            
            if pair_key not in self.symbol_map:
                self.symbol_map[pair_key] = {
                    'kraken_pair': pair_name,
                    'websocket_pair': wsname.replace('XBT/', 'BTC/') if wsname else None,
                    'base': user_symbol,
                    'quote': quote_symbol,
                    'kraken_base': base,
                    'kraken_quote': quote
                }
    
    def find_pair(self, user_symbol, quote='USD'):
        self._load_pairs()
        user_symbol = user_symbol.upper()
        quote = quote.upper()
        
        # Try exact match first
        pair_key = f"{user_symbol}/{quote}"
        if pair_key in self.symbol_map:
            return self.symbol_map[pair_key]
        
        # Try alternative quotes
        for alt_quote in ['USDT', 'EUR', 'GBP', 'USDC']:
            pair_key = f"{user_symbol}/{alt_quote}"
            if pair_key in self.symbol_map:
                return self.symbol_map[pair_key]
        
        return None
    
    def get_available_symbols(self):
        self._load_pairs()
        symbols = set()
        for pair_key in self.symbol_map.keys():
            symbol = pair_key.split('/')[0]
            symbols.add(symbol)
        return sorted(list(symbols))
    
    def get_available_quotes_for_symbol(self, user_symbol):
        self._load_pairs()
        user_symbol = user_symbol.upper()
        quotes = []
        
        for pair_key, info in self.symbol_map.items():
            if info['base'] == user_symbol:
                quotes.append(info['quote'])
        
        return sorted(quotes)
    
    def validate_symbol(self, user_symbol, quote='USD'):
        return self.find_pair(user_symbol, quote) is not None
    
    def list_all_pairs(self):
        self._load_pairs()
        return list(self.symbol_map.keys())
