class NegotiationEngine:
    def get_advice(self, pricing_analysis: dict) -> dict:
        return {
            'do_not_buy_above': pricing_analysis['max_buy_price'],
            'do_not_sell_below': pricing_analysis['min_sell_price'],
            'ideal_sell_price': pricing_analysis['recommended_sell_price'],
            'premium_sell_price': pricing_analysis['premium_sell_price'],
            'negotiation_range': [pricing_analysis['min_sell_price'], pricing_analysis['premium_sell_price']]
        }
