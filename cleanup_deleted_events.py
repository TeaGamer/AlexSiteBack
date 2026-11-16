"""Permanently remove calendar events past their 12-hour recovery window."""

from Backend import app, Event, ensure_calendar_schema


def main():
    with app.app_context():
        ensure_calendar_schema()
        removed = Event.purge_expired()
        print(f"Removed {removed} expired calendar event(s).")


if __name__ == "__main__":
    main()
