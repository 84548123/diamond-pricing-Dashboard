class PricingEngine:
    def analyze(self, vdb_price: float, diamax_price: float, vdb_ppc: float, diamax_ppc: float, 
                shape: str, color: str, clarity: str, cut: str, polish: str, symmetry: str,
                fluorescence: str, lab: str, carat: float, data_age_minutes: float = 0,
                price_history: list = None) -> dict:
        
        spread = vdb_price - diamax_price
        profit_margin_pct = (spread / vdb_price * 100) if vdb_price > 0 else 0
        
        # Price Ladder
        buy_price = diamax_price
        max_buy_price = diamax_price + (spread * 0.25)
        min_sell_price = diamax_price + (spread * 0.50)
        recommended_sell_price = diamax_price + (spread * 0.75)
        premium_sell_price = vdb_price
        
        # Recommendation
        if profit_margin_pct >= 10:
            recommendation = 'STRONG_BUY'
            stars = 5
        elif profit_margin_pct >= 5:
            recommendation = 'BUY'
            stars = 4
        elif profit_margin_pct >= 3:
            recommendation = 'HOLD'
            stars = 3
        elif profit_margin_pct > 0:
            recommendation = 'WAIT'
            stars = 2
        else:
            recommendation = 'AVOID'
            stars = 1
        
        # Confidence Score (weighted 4 factors)
        margin_score = min(100, profit_margin_pct * 10) if profit_margin_pct > 0 else 0
        freshness_score = max(0, 100 - (data_age_minutes * 2))  # loses 2pts per minute
        stability_score = self._calc_stability(price_history or [])
        spec_score = self._calc_spec_premium(cut, polish, symmetry, lab, fluorescence)
        
        confidence = (0.40 * margin_score + 0.25 * freshness_score + 
                     0.20 * stability_score + 0.15 * spec_score)
        confidence = round(min(100, max(0, confidence)), 1)
        
        # Risk-adjusted profit
        risk_adjusted_profit = round(spread * (confidence / 100), 2)
        
        # Holding period
        holding_days = self._estimate_holding_period(shape, color, clarity, cut, lab, carat)
        
        # Composite buy score
        margin_component = min(100, profit_margin_pct * 10) * 0.35
        confidence_component = confidence * 0.25
        turnover_component = max(0, 100 - holding_days * 3) * 0.20
        size_component = min(100, carat * 40) * 0.20
        composite_buy_score = round(margin_component + confidence_component + turnover_component + size_component, 1)
        
        return {
            'buy_price': round(buy_price, 2),
            'max_buy_price': round(max_buy_price, 2),
            'min_sell_price': round(min_sell_price, 2),
            'recommended_sell_price': round(recommended_sell_price, 2),
            'premium_sell_price': round(premium_sell_price, 2),
            'expected_profit': round(spread, 2),
            'profit_margin_pct': round(profit_margin_pct, 2),
            'confidence_score': confidence,
            'risk_adjusted_profit': risk_adjusted_profit,
            'composite_buy_score': composite_buy_score,
            'holding_period_days': holding_days,
            'recommendation': recommendation,
            'stars': stars,
            'negotiation_range_low': round(min_sell_price, 2),
            'negotiation_range_high': round(premium_sell_price, 2),
        }
    
    def _calc_stability(self, history: list) -> float:
        if len(history) < 2: return 70.0  # default medium
        margins = [h.get('profit_margin_pct', 0) for h in history[-10:]]
        if not margins: return 70.0
        avg = sum(margins) / len(margins)
        variance = sum((m - avg) ** 2 for m in margins) / len(margins)
        return max(0, min(100, 100 - variance * 5))
    
    def _calc_spec_premium(self, cut, polish, symmetry, lab, fluorescence) -> float:
        score = 50.0
        if cut == 'EX': score += 15
        elif cut == 'VG': score += 8
        if polish == 'EX': score += 10
        elif polish == 'VG': score += 5
        if symmetry == 'EX': score += 10
        elif symmetry == 'VG': score += 5
        if lab == 'GIA': score += 10
        elif lab == 'IGI': score += 5
        if fluorescence in ('NON', 'NONE', 'FNT'): score += 5
        elif fluorescence in ('STG', 'VST'): score -= 10
        return min(100, max(0, score))
    
    def _estimate_holding_period(self, shape, color, clarity, cut, lab, carat) -> int:
        base = 7
        if shape == 'ROUND': base = 5
        elif shape in ('OVAL', 'CUSHION'): base = 8
        else: base = 12
        
        color_factor = 1.0
        if color in ('D', 'E', 'F'): color_factor = 0.7
        elif color in ('G', 'H'): color_factor = 0.85
        elif color in ('I', 'J'): color_factor = 1.0
        else: color_factor = 1.4
        
        clarity_factor = 1.0
        if clarity in ('FL', 'IF', 'VVS1', 'VVS2'): clarity_factor = 0.8
        elif clarity in ('VS1', 'VS2'): clarity_factor = 0.9
        elif clarity in ('SI1', 'SI2'): clarity_factor = 1.1
        else: clarity_factor = 1.5
        
        lab_factor = 0.9 if lab == 'GIA' else 1.1
        
        return max(2, min(30, int(base * color_factor * clarity_factor * lab_factor)))
