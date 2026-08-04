from app.models.alert import Alert

class AlertEngine:
    def compare_and_generate_alerts(self, old_matches: list, new_matches: list) -> list[Alert]:
        alerts = []
        old_map = {m.id: m for m in old_matches}
        
        for new_match in new_matches:
            if new_match.id in old_map:
                old_match = old_map[new_match.id]
                if abs(new_match.diamax_price - old_match.diamax_price) / (old_match.diamax_price or 1) > 0.01:
                    alerts.append(Alert(
                        alert_type="PRICE_CHANGE",
                        title="Price Changed",
                        message=f"Price for stone changed.",
                        stone_match_id=new_match.id,
                        vdb_stone_id=new_match.vdb_stone_id,
                        diamax_stone_id=new_match.diamax_stone_id,
                        old_value=old_match.diamax_price,
                        new_value=new_match.diamax_price
                    ))
                if new_match.recommendation != old_match.recommendation:
                    alerts.append(Alert(
                        alert_type=f"{new_match.recommendation}_ALERT",
                        title=f"Recommendation changed to {new_match.recommendation}",
                        message=f"Stone recommendation is now {new_match.recommendation}.",
                        stone_match_id=new_match.id,
                        vdb_stone_id=new_match.vdb_stone_id,
                        diamax_stone_id=new_match.diamax_stone_id
                    ))
            else:
                alerts.append(Alert(
                    alert_type="NEW_MATCH",
                    title="New Match Found",
                    message="A new match was found.",
                    stone_match_id=new_match.id,
                    vdb_stone_id=new_match.vdb_stone_id,
                    diamax_stone_id=new_match.diamax_stone_id
                ))
        return alerts
