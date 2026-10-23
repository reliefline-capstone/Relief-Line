# Readable labels for stock movements.

EXPIRED = "Expired Food Packs"
DAMAGED = "Damaged Food Packs"


# Writes the readable name of a stock movement shown in stock history tables
# (e.g. 'Expired - Disposed', 'Damaged - Returned to Food Packs').
def stock_log_label(item_type, delta, source_type, reason=""):
    reason = (reason or "").lower()
    disposed = "disposed" in reason

    if source_type == "expired":
        if item_type == "food_pack_expired":
            if delta > 0:
                return f"Expired - Added to {EXPIRED}"
            return "Expired - Disposed" if disposed else f"Expired - Removed from {EXPIRED}"
        return "Expired - Removed from Food Packs" if delta < 0 else "Expired - Returned to Food Packs"

    if item_type == "food_pack_damaged":
        if delta > 0:
            return f"Damaged - Added to {DAMAGED}"
        return "Damaged - Disposed" if disposed else f"Damaged - Removed from {DAMAGED}"

    if source_type == "damaged_return":
        return "Damaged - Returned to Warehouse"

    if item_type == "food_pack" and delta > 0 and "previously-damaged" in reason:
        return "Damaged - Returned to Food Packs"

    return None
