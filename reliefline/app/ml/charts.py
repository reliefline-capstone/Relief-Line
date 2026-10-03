"""
Geometry for the two forecast line charts on the Predictive Analytics page.
Pure functions (no Flask, no DB): they turn forecast numbers into SVG
coordinates so the template only has to draw them.

  cover_chart    - "Will the stock last?": cumulative expected demand and the
                   cumulative P90 scenario against the warehouse's stock on
                   hand, with the month each one crosses the stock.
  backtest_chart - "How did the model do?": actual vs forecast (expected and
                   P90) for the latest backtest year, months that broke the
                   P90 line marked.
"""
from app.ml.train import MONTH_LABELS

W, H = 1000, 300
LEFT, RIGHT, TOP, BOTTOM = 66, 26, 22, 44
PLOT_W = W - LEFT - RIGHT
PLOT_H = H - TOP - BOTTOM


def _nice_ticks(vmax, target=4):
    """(ceiling, [tick values]) with a 1/2/2.5/5 x 10^k step."""
    vmax = max(float(vmax), 1.0)
    raw = vmax / target
    mag = 10 ** (len(str(int(raw))) - 1) if raw >= 1 else 1
    step = mag
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw:
            break
    top = step * (int(vmax / step) + (0 if vmax % step == 0 else 1))
    ticks = [step * i for i in range(int(top / step) + 1)]
    return top, ticks


def _fmt(v):
    return f"{int(round(v)):,}"


def _month_label(iso, first_year=None):
    y, m = int(iso[:4]), int(iso[5:7])
    label = MONTH_LABELS[m - 1]
    return f"{label} '{y % 100:02d}" if first_year is not None and y != first_year else label


def _crossing(cum, stock):
    """Position (in months from the start, fractional) where the running total
    `cum` (cum[0] == 0, one entry per month end) first exceeds `stock`, or
    None if it never does."""
    for i in range(1, len(cum)):
        if cum[i] > stock:
            span = cum[i] - cum[i - 1]
            frac = (stock - cum[i - 1]) / span if span > 0 else 0
            return (i - 1) + max(min(frac, 1.0), 0.0)
    return None


def cover_chart(months, stock):
    """months: forecast_lgu(...)["months"] (needs cum_expected / cum_p90).
    stock: food packs on hand. Returns a dict for the template."""
    n = len(months)
    first_year = months[0]["year"]
    cum_e = [0] + [m["cum_expected"] for m in months]
    cum_p = [0] + [m["cum_p90"] for m in months]
    top, ticks = _nice_ticks(max(cum_p[-1], stock) * 1.05)
    step_x = PLOT_W / n

    def x(i):
        return LEFT + i * step_x

    def y(v):
        return TOP + PLOT_H - (v / top) * PLOT_H

    def month_name(pos):
        idx = min(int(pos), n - 1)  # pos is months elapsed; the run-out month is idx
        m = months[idx]
        return f"{m['label']}" + (f" '{m['year'] % 100:02d}" if m["year"] != first_year else "")

    cross_e, cross_p = _crossing(cum_e, stock), _crossing(cum_p, stock)

    def full_month_name(pos):
        m = months[min(int(pos), n - 1)]
        return f"{m['label']} {m['year']}"

    def marker(pos):
        return None if pos is None else {"x": round(x(pos), 1), "y": round(y(stock), 1), "label": month_name(pos)}

    def runout(pos):
        """Plain-language summary for the tiles above the chart: None when
        the stock lasts the whole period."""
        return None if pos is None else {"month": full_month_name(pos), "months": round(pos, 1)}

    def shortfall(cum, pos):
        """SVG polygon of the area where demand is above the stock line
        (from the run-out point to the end of the period), or None."""
        if pos is None:
            return None
        pts = [(x(pos), y(stock))] + [(x(i), y(cum[i])) for i in range(1, n + 1) if i > pos] + [(x(n), y(stock))]
        return " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)

    # End-of-period totals at the right end of each line, nudged apart when
    # the two lines finish close together so the labels don't overlap.
    end_e_y, end_p_y = y(cum_e[-1]) - 8, y(cum_p[-1]) - 8
    if abs(end_p_y - end_e_y) < 16:
        end_p_y = end_e_y - 16

    def sentence(pos, what):
        if pos is None:
            return f"{what} the stock lasts the whole {n}-month period."
        return f"{what} the stock runs out in {month_name(pos)} (about {pos:.1f} months in)."

    return {
        "w": W, "h": H, "left": LEFT, "right": W - RIGHT, "top": TOP, "bottom": TOP + PLOT_H,
        "y_ticks": [{"y": round(y(t), 1), "label": _fmt(t)} for t in ticks],
        # Month labels sit at the MIDDLE of each month (month i spans x(i) to
        # x(i+1)), so a run-out dot inside a month sits right above that
        # month's label - at month ends, a July dot sat over "Jun".
        "x_labels": [{"x": round(x(i + 0.5), 1), "label": _month_label(f"{m['year']}-{m['month']:02d}", first_year)}
                     for i, m in enumerate(months)],
        "expected_pts": " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(cum_e)),
        "p90_pts": " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(cum_p)),
        "short_expected_pts": shortfall(cum_e, cross_e),
        "short_p90_pts": shortfall(cum_p, cross_p),
        "end_x": round(x(n), 1),
        "end_expected_y": round(end_e_y, 1), "end_p90_y": round(end_p_y, 1),
        "stock_y": round(y(stock), 1),
        "stock": int(stock),
        "cross_expected": marker(cross_e), "cross_p90": marker(cross_p),
        "runout_expected": runout(cross_e), "runout_p90": runout(cross_p),
        "n_months": n,
        "sentences": [sentence(cross_e, "At expected demand,"), sentence(cross_p, "In a bad-season (P90) scenario,")],
        # green: lasts the whole period even in the P90 scenario; red: runs out
        # within 3 months at EXPECTED demand; amber: anything in between (runs
        # out later in the period, or only in the bad-season scenario).
        "status": ("healthy" if cross_p is None else
                   "critical" if (cross_e is not None and cross_e < 3) else "warning"),
        "end_expected": cum_e[-1], "end_p90": cum_p[-1],
    }


def backtest_chart(series):
    """series: {"origin": "leave-one-typhoon-out", "points": [{month, actual,
    expected, p90}]} - one point per real relief event on record, sorted
    chronologically (app.ml.train._backtest_points), NOT one calendar year of
    monthly points like the old rolling-origin chart. `expected`/`p90` for
    each point come from a fit that excluded that point's own event, so this
    is an honest out-of-sample comparison even though there's no single
    "trained through" date - see app.ml.predict.backtest_series."""
    pts = series["points"]
    n = len(pts)
    first_year = int(pts[0]["month"][:4])
    last_year = int(pts[-1]["month"][:4])
    top, ticks = _nice_ticks(max(max(p["actual"], p["p90"]) for p in pts) * 1.05)
    step_x = PLOT_W / n

    def x(i):
        return LEFT + (i + 0.5) * step_x

    def y(v):
        return TOP + PLOT_H - (v / top) * PLOT_H

    over = [i for i, p in enumerate(pts) if p["actual"] > p["p90"]]
    return {
        "w": W, "h": H, "left": LEFT, "right": W - RIGHT, "top": TOP, "bottom": TOP + PLOT_H,
        "y_ticks": [{"y": round(y(t), 1), "label": _fmt(t)} for t in ticks],
        "x_labels": [{"x": round(x(i), 1), "label": _month_label(p["month"], first_year)} for i, p in enumerate(pts)],
        "actual_pts": " ".join(f"{x(i):.1f},{y(p['actual']):.1f}" for i, p in enumerate(pts)),
        "expected_pts": " ".join(f"{x(i):.1f},{y(p['expected']):.1f}" for i, p in enumerate(pts)),
        "p90_pts": " ".join(f"{x(i):.1f},{y(p['p90']):.1f}" for i, p in enumerate(pts)),
        "dots": [{"x": round(x(i), 1), "y": round(y(p["actual"]), 1), "over": i in over,
                  "tip": f"{_month_label(p['month'], first_year)}: actual {_fmt(p['actual'])}, "
                         f"forecast {_fmt(p['expected'])}, P90 {_fmt(p['p90'])}"}
                 for i, p in enumerate(pts)],
        "date_range": f"{first_year}" if first_year == last_year else f"{first_year}-{last_year}",
        "total_actual": int(sum(p["actual"] for p in pts)),
        "total_expected": int(sum(p["expected"] for p in pts)),
        "months_over": len(over), "n": n,
    }
