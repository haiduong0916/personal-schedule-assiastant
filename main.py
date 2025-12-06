import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import time
import datetime
from datetime import timedelta 
import calendar
import dateparser
import json 
import winsound

# IMPORT CÁC MODULE KHÁC
from database import Database
from nlp_engine import NLPEngine

# DIALOG SỬA SỰ KIỆN
class EditEventDialog(tk.Toplevel):
    def __init__(self, parent, event_data):
        super().__init__(parent)
        self.title("Sửa Sự Kiện")
        
        window_width = 450
        window_height = 350
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x_cordinate = int((screen_width/2) - (window_width/2))
        y_cordinate = int((screen_height/2) - (window_height/2))
        
        self.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

        self.result = None
        self.event_data = event_data 

        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        # Style 
        self.font_label = ("Segoe UI", 10)
        self.font_entry = ("Segoe UI", 10)

        tk.Label(self, text="Tên sự kiện:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(15, 0))
        self.entry_event = tk.Entry(self, width=50, font=self.font_entry)
        self.entry_event.insert(0, event_data[1])
        self.entry_event.pack(padx=20, pady=5)

        tk.Label(self, text="Thời gian (VD: 14h30 20/10, sáng mai...):", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20)
        self.entry_time = tk.Entry(self, width=50, font=self.font_entry)
        try: display_time = datetime.datetime.fromisoformat(event_data[2]).strftime("%H:%M %d/%m/%Y")
        except: display_time = event_data[2]
        self.entry_time.insert(0, display_time)
        self.entry_time.pack(padx=20, pady=5)

        tk.Label(self, text="Địa điểm:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20)
        self.entry_loc = tk.Entry(self, width=50, font=self.font_entry)
        self.entry_loc.insert(0, event_data[3])
        self.entry_loc.pack(padx=20, pady=5)

        tk.Label(self, text="Nhắc trước (phút):", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20)
        self.entry_remind = tk.Entry(self, width=50, font=self.font_entry)
        self.entry_remind.insert(0, str(event_data[4]))
        self.entry_remind.pack(padx=20, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Lưu Thay Đổi", command=self.on_save, bg="#4CAF50", fg="white", width=15, relief="flat", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Hủy Bỏ", command=self.destroy, bg="#f44336", fg="white", width=10, relief="flat", font=("Segoe UI", 9)).pack(side="left", padx=5)

    def on_save(self):
        raw_time = self.entry_time.get()
        parsed_date = None
        try:
            settings = {'DATE_ORDER': 'DMY', 'PREFER_DATES_FROM': 'future'}
            parsed_date = dateparser.parse(raw_time, settings=settings, languages=['vi'])
        except: pass

        if not parsed_date:
            messagebox.showerror("Lỗi", "Định dạng thời gian không hợp lệ!")
            return

        now = datetime.datetime.now()
        if parsed_date.year > now.year:
            messagebox.showerror("Lỗi Năm", f"Năm {parsed_date.year} vượt quá năm hiện tại. Vui lòng chọn trong năm nay.")
            return
        if parsed_date < now - timedelta(minutes=1):
            messagebox.showerror("Lỗi Thời Gian", f"Thời gian {parsed_date.strftime('%H:%M %d/%m/%Y')} đã trôi qua.")
            return

        self.result = {
            'id': self.event_data[0],
            'event': self.entry_event.get(),
            'start_time': parsed_date.isoformat(),
            'location': self.entry_loc.get(),
            'reminder_minutes': int(self.entry_remind.get())
        }
        self.destroy()

class ScheduleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trợ Lý Lịch Trình Cá Nhân (NLP)")
        self.root.geometry("1000x750")
        self.root.configure(bg="#F3F4F6") 
        
        self.nlp = NLPEngine()
        self.db = Database()
        
        self.current_date = datetime.datetime.now()
        self.cal_month = self.current_date.month
        self.cal_year = self.current_date.year
        self.view_mode = "list"

        self.style_font = ("Segoe UI", 11)
        self.btn_font = ("Segoe UI", 10, "bold")

        input_container = tk.Frame(root, bg="#F3F4F6", padx=10, pady=10)
        input_container.pack(fill="x")
        
        input_frame = tk.LabelFrame(input_container, text="💬 Nhập yêu cầu của bạn", font=("Segoe UI", 12, "bold"), bg="white", fg="#333", padx=15, pady=15, relief="flat")
        input_frame.pack(fill="x")
        
        self.txt_input = tk.Entry(input_frame, width=50, font=("Segoe UI", 12), relief="solid", bd=1)
        self.txt_input.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)
        self.txt_input.bind("<Return>", lambda event: self.process_input()) 
        
        tk.Button(input_frame, text="➕ Thêm Sự Kiện", command=self.process_input, bg="#10B981", fg="white", font=self.btn_font, relief="flat", padx=15, pady=5).pack(side="right")

        toolbar_frame = tk.Frame(root, bg="#F3F4F6", padx=10, pady=5)
        toolbar_frame.pack(fill="x")
        
        search_frame = tk.Frame(toolbar_frame, bg="#F3F4F6")
        search_frame.pack(side="left")
        tk.Label(search_frame, text="🔍", bg="#F3F4F6", font=("Segoe UI", 12)).pack(side="left")
        self.txt_search = tk.Entry(search_frame, width=25, font=("Segoe UI", 10))
        self.txt_search.pack(side="left", padx=5)
        self.txt_search.bind("<KeyRelease>", self.on_search) 
        
        tk.Frame(toolbar_frame, width=30, bg="#F3F4F6").pack(side="left")

        tk.Button(toolbar_frame, text="📋 Danh Sách", command=self.show_list_view, bg="white", fg="#333", font=("Segoe UI", 9), relief="groove").pack(side="left", padx=2)
        tk.Button(toolbar_frame, text="📅 Lịch Tháng", command=self.show_calendar_view, bg="white", fg="#333", font=("Segoe UI", 9), relief="groove").pack(side="left", padx=2)
        
        tk.Button(toolbar_frame, text="📤 Xuất Dữ Liệu", command=self.export_data, bg="#8B5CF6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat").pack(side="left", padx=10)

        self.btn_del = tk.Button(toolbar_frame, text="🗑 Xóa", command=self.delete_selected, bg="#EF4444", fg="white", font=("Segoe UI", 9, "bold"), relief="flat")
        self.btn_del.pack(side="right", padx=2)
        self.btn_edit = tk.Button(toolbar_frame, text="✏️ Sửa", command=self.edit_selected, bg="#3B82F6", fg="white", font=("Segoe UI", 9, "bold"), relief="flat")
        self.btn_edit.pack(side="right", padx=2)

        self.content_frame = tk.Frame(root, bg="#F3F4F6", padx=10, pady=5)
        self.content_frame.pack(fill="both", expand=True)

        self.init_list_view()
        self.init_calendar_view()
        self.show_list_view()

        self.running = True
        self.reminder_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.reminder_thread.start()

    def init_list_view(self):
        self.list_container = tk.Frame(self.content_frame, bg="white")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", fieldbackground="white", foreground="black", rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#E5E7EB", foreground="#374151")
        
        columns = ("ID", "Sự kiện", "Thời gian", "Địa điểm", "Nhắc trước")
        self.tree = ttk.Treeview(self.list_container, columns=columns, show="headings")
        
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=0, stretch=False) # Ẩn ID
        self.tree.heading("Sự kiện", text="Nội dung sự kiện"); self.tree.column("Sự kiện", width=300)
        self.tree.heading("Thời gian", text="Thời gian"); self.tree.column("Thời gian", width=150, anchor="center")
        self.tree.heading("Địa điểm", text="Địa điểm"); self.tree.column("Địa điểm", width=150, anchor="center")
        self.tree.heading("Nhắc trước", text="Nhắc trước"); self.tree.column("Nhắc trước", width=100, anchor="center")
        
        sb = ttk.Scrollbar(self.list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def init_calendar_view(self):
        self.calendar_container = tk.Frame(self.content_frame, bg="white", relief="flat", bd=1)
        
        nav_frame = tk.Frame(self.calendar_container, bg="white", pady=10)
        nav_frame.pack(fill="x")
        
        tk.Button(nav_frame, text="❮ Tháng Trước", command=self.prev_month, relief="flat", bg="#E5E7EB", font=("Segoe UI", 9)).pack(side="left", padx=10)
        self.lbl_month_year = tk.Label(nav_frame, text="", font=("Segoe UI", 16, "bold"), bg="white", fg="#111827")
        self.lbl_month_year.pack(side="left", expand=True)
        tk.Button(nav_frame, text="Tháng Sau ❯", command=self.next_month, relief="flat", bg="#E5E7EB", font=("Segoe UI", 9)).pack(side="right", padx=10)
        
        self.grid_frame = tk.Frame(self.calendar_container, bg="#E5E7EB") # Màu nền của lưới (tạo đường kẻ)
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def show_list_view(self):
        self.view_mode = "list"
        self.calendar_container.pack_forget()
        self.list_container.pack(fill="both", expand=True)
        self.btn_del.config(state="normal")
        self.btn_edit.config(state="normal") 
        self.refresh_data()

    def show_calendar_view(self):
        self.view_mode = "grid"
        self.list_container.pack_forget()
        self.calendar_container.pack(fill="both", expand=True)
        self.btn_del.config(state="disabled")
        self.btn_edit.config(state="disabled")
        self.draw_calendar()

    def draw_calendar(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        
        month_name = f"Tháng {self.cal_month} - {self.cal_year}"
        self.lbl_month_year.config(text=month_name)
        
        days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        for i, d in enumerate(days):
            header = tk.Label(self.grid_frame, text=d, bg="#F9FAFB", fg="#6B7280", font=("Segoe UI", 9, "bold"), pady=8)
            header.grid(row=0, column=i, sticky="nsew", padx=1, pady=1) # padx/pady tạo đường kẻ grid

        for i in range(7): self.grid_frame.columnconfigure(i, weight=1)
        for i in range(7): self.grid_frame.rowconfigure(i, weight=1)
        
        cal = calendar.monthcalendar(self.cal_year, self.cal_month)
        keyword = self.txt_search.get()
        events = self.db.get_all_events(keyword if keyword else None)

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0: 
                    tk.Label(self.grid_frame, bg="#F3F4F6").grid(row=r+1, column=c, sticky="nsew", padx=1, pady=1)
                    continue
                
                cell_bg = "white"
                fg_color = "#1F2937"
                
                is_today = (day == self.current_date.day and 
                            self.cal_month == self.current_date.month and 
                            self.cal_year == self.current_date.year)
                
                if is_today:
                    cell_bg = "#EFF6FF" # Xanh nhạt
                    fg_color = "#2563EB" # Xanh đậm

                cell = tk.Frame(self.grid_frame, bg=cell_bg)
                cell.grid(row=r+1, column=c, sticky="nsew", padx=1, pady=1)
                
                lbl_day = tk.Label(cell, text=str(day), font=("Segoe UI", 10, "bold"), bg=cell_bg, fg=fg_color)
                lbl_day.pack(anchor="ne", padx=5, pady=2)

                count_event = 0
                for e in events:
                    try:
                        edt = datetime.datetime.fromisoformat(e[2])
                        if edt.day == day and edt.month == self.cal_month and edt.year == self.cal_year:
                            event_text = f"● {edt.strftime('%H:%M')} {e[1]}"
                            lbl_evt = tk.Label(cell, text=event_text, font=("Segoe UI", 8), 
                                               bg=cell_bg if not is_today else "#DBEAFE", 
                                               fg="#374151", anchor="w", cursor="hand2")
                            lbl_evt.pack(fill="x", padx=2, pady=1)
                            count_event += 1
                            if count_event >= 3: # Chỉ hiện tối đa 3 sự kiện để không vỡ layout
                                tk.Label(cell, text="...", font=("Segoe UI", 7), bg=cell_bg, fg="#9CA3AF").pack(anchor="center")
                                break
                    except: pass

    def process_input(self):
        text = self.txt_input.get()
        if not text: return
        try:
            data = self.nlp.process(text)
            if not data['start_time']:
                messagebox.showerror("Lỗi", "Không rõ thời gian")
                return
            self.db.add_event(data)
            self.txt_input.delete(0, tk.END)
            self.refresh_data()
            messagebox.showinfo("Thành công", f"Đã thêm: {data['event']}")
        except ValueError as ve:
            messagebox.showerror("Lỗi Dữ Liệu", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def on_search(self, event): self.refresh_data()

    def refresh_data(self):
        keyword = self.txt_search.get()
        events = self.db.get_all_events(keyword if keyword else None)
        
        for row in self.tree.get_children(): self.tree.delete(row)
        
        self.tree.tag_configure('odd', background='#F9FAFB')
        self.tree.tag_configure('even', background='white')

        for i, e in enumerate(events):
            d_time = e[2]
            try: d_time = datetime.datetime.fromisoformat(e[2]).strftime("%H:%M %d/%m/%Y")
            except: pass
            
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert("", tk.END, values=(e[0], e[1], d_time, e[3], e[4]), tags=(tag,))
            
        if self.view_mode == "grid": self.draw_calendar()

    def delete_selected(self):
        sel = self.tree.selection()
        if sel:
            if messagebox.askyesno("Xóa", "Bạn chắc chắn xóa?"):
                self.db.delete_event(self.tree.item(sel[0])['values'][0])
                self.refresh_data()

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel: return
        event_id = self.tree.item(sel[0])['values'][0]
        events = self.db.get_all_events()
        event_data = next((e for e in events if e[0] == event_id), None)
        if event_data:
            dialog = EditEventDialog(self.root, event_data)
            self.root.wait_window(dialog)
            if dialog.result:
                self.db.update_event(dialog.result['id'], dialog.result['event'], dialog.result['start_time'], dialog.result['location'], dialog.result['reminder_minutes'])
                self.refresh_data()
                messagebox.showinfo("Thành công", "Đã cập nhật!")

    def check_reminders(self):
        while self.running:
            try:
                events = self.db.get_all_events()
                now = datetime.datetime.now()
                for e in events:
                    if not e[2]: continue
                    try:
                        et = datetime.datetime.fromisoformat(e[2])
                        rem = et - timedelta(minutes=int(e[4]))
                        if rem <= now <= rem + timedelta(seconds=60):
                            if winsound: 
                                try: winsound.Beep(1000, 500)
                                except: pass
                            self.root.after(0, lambda ev=e: messagebox.showwarning("NHẮC NHỞ", f"{ev[1]}\n{ev[3]}"))
                    except: pass
            except: pass
            time.sleep(60)
            
    def prev_month(self):
        if self.cal_month == 1: self.cal_month=12; self.cal_year-=1
        else: self.cal_month-=1
        self.draw_calendar()
        
    def next_month(self):
        if self.cal_month == 12: self.cal_month=1; self.cal_year+=1
        else: self.cal_month+=1
        self.draw_calendar()

    def export_data(self):
        events = self.db.get_all_events()
        if not events:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xuất!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON file", "*.json"), ("iCalendar file", "*.ics")]
        )
        
        if not file_path: return

        try:
            if file_path.endswith('.json'):
                data_list = []
                for e in events:
                    data_list.append({
                        "id": e[0],
                        "event": e[1],
                        "start_time": e[2],
                        "location": e[3],
                        "reminder_minutes": e[4]
                    })
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data_list, f, ensure_ascii=False, indent=4)
            
            elif file_path.endswith('.ics'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//My Schedule App//EN\n")
                    for e in events:
                        try:
                            dt = datetime.datetime.fromisoformat(e[2])
                            ics_time = dt.strftime("%Y%m%dT%H%M%S")
                            f.write("BEGIN:VEVENT\n")
                            f.write(f"SUMMARY:{e[1]}\n")
                            f.write(f"DTSTART:{ics_time}\n")
                            f.write(f"LOCATION:{e[3]}\n")
                            f.write("END:VEVENT\n")
                        except: pass
                    f.write("END:VCALENDAR")
            
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra {file_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScheduleApp(root)
    root.mainloop()