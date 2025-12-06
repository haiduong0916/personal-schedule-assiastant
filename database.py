import sqlite3

class Database:
    def __init__(self, db_name="schedule.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT,
            start_time TEXT,
            location TEXT,
            reminder_minutes INTEGER
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def add_event(self, data):
        query = "INSERT INTO events (event, start_time, location, reminder_minutes) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (data['event'], data['start_time'], data['location'], data['reminder_minutes']))
        self.conn.commit()

    def update_event(self, event_id, event, start_time, location, reminder):
        query = "UPDATE events SET event=?, start_time=?, location=?, reminder_minutes=? WHERE id=?"
        self.conn.execute(query, (event, start_time, location, reminder, event_id))
        self.conn.commit()

    def get_all_events(self, search_query=None):
        if search_query:
            # Tìm kiếm theo tên sự kiện HOẶC địa điểm
            query = "SELECT * FROM events WHERE event LIKE ? OR location LIKE ? ORDER BY start_time ASC"
            param = f"%{search_query}%"
            cursor = self.conn.execute(query, (param, param))
        else:
            cursor = self.conn.execute("SELECT * FROM events ORDER BY start_time ASC")
        return cursor.fetchall()
        
    def delete_event(self, event_id):
        self.conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self.conn.commit()