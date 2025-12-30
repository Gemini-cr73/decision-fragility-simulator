# app/main.py

import argparse

from app.analytics.report import build_report, list_report_history


def safe_float(value):
    """Convert to float if possible, otherwise return None."""
    try:
        return float(value)
    except Exception:
        return None


def cmd_run(_args: argparse.Namespace) -> None:
    report_text = build_report()
    print(report_text)


def cmd_history(args: argparse.Namespace) -> None:
    rows = list_report_history(limit=args.limit)

    if not rows:
        print("No past runs found in analytics.reports.")
        return

    print(
        f"{'ID':>4}  {'Timestamp':<20} {'Events':>8} {'Score':>10}  Label"
    )
    print("-" * 60)

    for row in rows:
        id_, created_at, total_events, score, label = row

        # created_at may be str or datetime
        if hasattr(created_at, "strftime"):
            ts = created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts = str(created_at)

        # score may be bad text, so guard it
        score_val = safe_float(score)
        score_str = f"{score_val:.4f}" if score_val is not None else "N/A"

        print(
            f"{id_:>4}  {ts:<20} {total_events:>8} {score_str:>10}  {label}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decision-Fragility Simulator - CLI"
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="sub-command to run"
    )

    run_parser = subparsers.add_parser(
        "run", help="compute fragility and store a new report"
    )
    run_parser.set_defaults(func=cmd_run)

    hist_parser = subparsers.add_parser(
        "history", help="list past fragility runs from analytics.reports"
    )
    hist_parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="number of recent runs to display (default: 20)",
    )
    hist_parser.set_defaults(func=cmd_history)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
