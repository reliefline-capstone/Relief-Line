"""Plain-language Movement History labels for the expired/damaged food-pack
moves, shared by every tier (PSWDO, CSWDO, barangay) and their exports so
the same move always reads the same way.

Each expiry or damage step is logged as a pair of rows - one on usable
"Food Packs" and one on the separate "Expired Food Packs" / "Damaged Food
Packs" bucket - so every label says which bucket went up or down."""

EXPIRED = "Expired Food Packs"
DAMAGED = "Damaged Food Packs"


def stock_log_label(item_type, delta, source_type, reason=""):
    """Label for an expired/damaged stock log, or None for anything else
    (the caller keeps its own Received / Released / ... wording)."""
    reason = (reason or "").lower()
    disposed = "disposed" in reason

    if source_type == "expired":
        if item_type == "food_pack_expired":
            if delta > 0:
                return f"Expired - Added to {EXPIRED}"
            return "Expired - Disposed" if disposed else f"Expired - Removed from {EXPIRED}"
        # usable Food Packs side
        return "Expired - Removed from Food Packs" if delta < 0 else "Expired - Returned to Food Packs"

    if item_type == "food_pack_damaged":
        if delta > 0:
            return f"Damaged - Added to {DAMAGED}"
        return "Damaged - Disposed" if disposed else f"Damaged - Removed from {DAMAGED}"

    if source_type == "damaged_return":
        # Barangay's own 0-qty marker row - the packs went back to the warehouse.
        return "Damaged - Returned to Warehouse"

    if item_type == "food_pack" and delta > 0 and "previously-damaged" in reason:
        return "Damaged - Returned to Food Packs"

    return None
