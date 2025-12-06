import re
import datetime
from datetime import timedelta
import unicodedata
import dateparser
import calendar

class NLPEngine:
    def __init__(self):
        # 1. Từ điển PM
        self.pm_keywords = [
            "đi chơi", "di choi", "xem phim", "coi phim", "ăn tối", "an toi", 
            "nhậu", "party", "tiệc", "hẹn hò", 
            "tối", "toi", "đêm", "dem",
            "chiều", "chieu", "trưa", "trua"
        ]
        
        # 2. Từ khóa địa điểm
        self.loc_markers = [
            "tại", "ở", "đến", "về", "ra", "qua", "địa điểm", "khu vực",
            "phòng", "sảnh", "lầu", "tầng",
            "nhà hàng", "quán", "coffee", "rạp", "cinema",
            "hồ bơi", "sân", "trường", "lớp", "tòa nhà",
            "tai", "o", "dia diem",
            "phong", "sanh", "lau", "tang",
            "nha hang", "quan", "rap",
            "ho boi", "san", "truong", "lop", 
        ]
        
        # 3. Từ điển hành động
        self.action_verbs = [
            "đi", "di", "làm", "lam", "học", "hoc", "họp", "hop", 
            "mua", "bán", "ban", "gửi", "gui", "nộp", "nop", 
            "check", "xem", "coi", "ăn", "an", "uống", "uong", 
            "gặp", "gap", "đón", "don", "tập", "tap", "chạy", "chay", 
            "ngủ", "ngu", "báo cáo", "bao cao", "viết", "viet", 
            "dọn", "don", "sửa", "sua", "thi", "kiểm tra", "kiem tra",
            "đá", "da", "chơi", "choi", "gọi", "goi", "về", "ve",
            "tham gia", "du", "dự", "sinh nhật", "sinh nhat" 
        ]

        # 4. Từ dừng
        self.stop_words = [
            "lúc", "vào", "ngày", "báo", "nhắc", "trong", "để", "cùng", "với", 
            "hôm", "sáng", "chiều", "tối", "mai", "mốt", "tuần", "thứ",
            "luc", "vao", "ngay", "bao", "nhac", "hom", "sang", "chieu", "toi", "tuan", "thu",
            "de", "cung", "voi", "trong"
        ]
        
        self.invalid_locations = [
            "me", "ba", "bo", "ma", "anh", "em", "chi", "ban", "nguoi yeu", "crush", "moi nguoi",
            "dau", "do", "day", "kia", "viec", "hoc", "lam",
            "mẹ", "bố", "bà", "anh", "chị", "em", "bạn", "mình"
        ]

    def no_accent(self, s):
        return unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8').lower()

    def get_weekday_index(self, text):
        text = self.no_accent(text)
        if "thu 2" in text: return 0
        if "thu 3" in text: return 1
        if "thu 4" in text: return 2
        if "thu 5" in text: return 3
        if "thu 6" in text: return 4
        if "thu 7" in text: return 5
        if "chu nhat" in text: return 6
        return None

    #  HÀM KIỂM TRA HỢP LỆ 
    def validate_datetime_detailed(self, d, m, y, h=0, mi=0):
        now = datetime.datetime.now()

        # 1. Kiểm tra Lịch (Calendar check)
        if not (1 <= m <= 12):
            raise ValueError(f"Tháng {m} không hợp lệ (Phải từ 1-12).")
        
        try:
            max_day = calendar.monthrange(y, m)[1]
            if not (1 <= d <= max_day):
                raise ValueError(f"Tháng {m}/{y} chỉ có tối đa {max_day} ngày (Bạn nhập ngày {d}).")
            
            dt_obj = datetime.datetime(y, m, d, h, mi)
        except ValueError:
            raise ValueError("Ngày giờ không hợp lệ (Ví dụ: Giờ > 23 hoặc Phút > 59).")

        # 2. Kiểm tra Năm 
        if y > now.year:
            raise ValueError(f"Năm {y} vượt quá năm hiện tại {now.year}. Vui lòng chỉ đặt lịch trong năm nay.")

        # 3. Kiểm tra Quá khứ
        if dt_obj < now - timedelta(minutes=1):
            raise ValueError(f"Thời gian {dt_obj.strftime('%H:%M %d/%m/%Y')} đã trôi qua. Vui lòng nhập thời gian tương lai.")

        return dt_obj

    def extract_explicit_date(self, text):
        # Regex bắt: DD/MM hoặc DD-MM
        match = re.search(r'\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?\b', text)
        if match:
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3)) if match.group(3) else datetime.datetime.now().year
            
            # Kiểm tra sơ bộ ngày tháng nếu sai ngày/tháng/năm sẽ báo lỗi ngay lập tức
            try:
                self.validate_datetime_detailed(d, m, y, 0, 0)
            except ValueError as e:
                if "trôi qua" not in str(e):
                    raise e
            
            return datetime.datetime(y, m, d)
        return None

    def parse_special_dates(self, text, now):
        clean_text = self.no_accent(text)
        if "mai" in clean_text and "phomai" not in clean_text and "khuyen mai" not in clean_text:
            return now + timedelta(days=1)
        if "mot" in clean_text or "ngay kia" in clean_text:
            return now + timedelta(days=2)
        if "hom nay" in clean_text or "toi nay" in clean_text or "sang nay" in clean_text:
            return now
        if "cuoi tuan" in clean_text:
            days_ahead = (6 - now.weekday()) % 7 
            if days_ahead == 0 and now.weekday() == 6: days_ahead = 7
            return now + timedelta(days=days_ahead)

        match = re.search(r'(thu\s*\d|chu nhat)\s*(toi|tuan sau|sau)', clean_text)
        if match:
            wd_idx = self.get_weekday_index(match.group(1))
            if wd_idx is not None:
                days_ahead = wd_idx - now.weekday()
                if "tuan sau" in match.group(2): 
                    days_until_next_mon = 7 - now.weekday()
                    return now + timedelta(days=days_until_next_mon + wd_idx)
                else: 
                    if days_ahead <= 0: days_ahead += 7
                    return now + timedelta(days=days_ahead)

        match_simple = re.search(r'(thu\s*\d|chu nhat)', clean_text)
        if match_simple and "tuan truoc" not in clean_text:
            wd_idx = self.get_weekday_index(match_simple.group(1))
            if wd_idx is not None:
                days_ahead = wd_idx - now.weekday()
                if days_ahead <= 0: days_ahead += 7
                return now + timedelta(days=days_ahead)
        return None

    def extract_time_from_string(self, text):
        pattern = r'(\d{1,2})\s*(h|:|g|giờ|gio)\s*(\d{0,2})'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        valid_time = None
        for match in matches:
            try:
                h = int(match.group(1))
                m = int(match.group(3)) if match.group(3) else 0
                if 0 <= h <= 23 and 0 <= m <= 59: valid_time = (h, m) 
            except: continue
        return valid_time if valid_time else (None, None)

    def extract_location(self, text):
        sorted_markers = sorted(self.loc_markers, key=len, reverse=True)
        marker_pattern = r'\b(?:' + '|'.join(map(re.escape, sorted_markers)) + r')\b\s+'
        matches = list(re.finditer(marker_pattern, text, re.IGNORECASE))
        if not matches: return "Chưa xác định"

        best_match = matches[0]
        for m in matches:
            w = m.group(0).strip().lower()
            if w in ["tại", "ở", "tai", "o", "đến", "den", "về", "ve"]:
                best_match = m
                break

        start_index = best_match.end()
        candidate_str = text[start_index:]
        min_cut_index = len(candidate_str)
        
        time_pattern_idx = re.search(r'\d{1,2}(h|:|g)', candidate_str)
        if time_pattern_idx: min_cut_index = min(min_cut_index, time_pattern_idx.start())

        for sw in self.stop_words:
            sw_match = re.search(r'\s+' + sw + r'\b', candidate_str, re.IGNORECASE)
            if sw_match: min_cut_index = min(min_cut_index, sw_match.start())

        final_location = candidate_str[:min_cut_index].strip()
        final_location = final_location.strip(" ,.")
        
        if final_location.lower() in self.invalid_locations: return "Chưa xác định"
        if len(final_location) < 1: return "Chưa xác định"

        marker_word = best_match.group(0).strip()
        prepositions = ["tại", "ở", "đến", "về", "ra", "qua", "địa điểm", "khu vực", "tai", "o", "den", "ve", "dia diem"]
        if marker_word.lower() not in prepositions:
             final_location = f"{marker_word} {final_location}"

        return final_location.capitalize()

    def extract_time(self, text):
        now = datetime.datetime.now()
        
        # Bắt ngày cụ thể (Nếu ngày sai như 30/2 sẽ văng lỗi ngay tại đây)
        extracted_date = self.extract_explicit_date(text)
        
        if not extracted_date: extracted_date = self.parse_special_dates(text, now)
        if not extracted_date:
            settings = {'PREFER_DATES_FROM': 'future', 'DATE_ORDER': 'DMY', 'RELATIVE_BASE': now}
            extracted_date = dateparser.parse(text, languages=['vi'], settings=settings)

        hour, minute = self.extract_time_from_string(text)
        
        # Logic ghép giờ
        if extracted_date and hour is not None: extracted_date = extracted_date.replace(hour=hour, minute=minute, second=0)
        if not extracted_date and hour is not None: extracted_date = now.replace(hour=hour, minute=minute, second=0)
        if extracted_date and hour is None:
            clean = self.no_accent(text)
            if "sang" in clean: hour, minute = 8, 0
            elif "chieu" in clean: hour, minute = 14, 0
            elif "toi" in clean: hour, minute = 19, 0
            else: hour, minute = 8, 0 # Mặc định 8h sáng
            extracted_date = extracted_date.replace(hour=hour, minute=minute, second=0)
        
        if extracted_date:
            is_pm = any(kw in self.no_accent(text) for kw in self.pm_keywords)
            if extracted_date.hour < 12 and is_pm and "sang" not in self.no_accent(text): extracted_date += timedelta(hours=12)
            
            # --- KIỂM TRA HỢP LỆ CUỐI CÙNG (BAO GỒM CHECK QUÁ KHỨ) ---
            self.validate_datetime_detailed(
                extracted_date.day, extracted_date.month, extracted_date.year,
                extracted_date.hour, extracted_date.minute
            )

        return extracted_date

    def identify_event_action(self, text):
        sorted_actions = sorted(self.action_verbs, key=lambda x: len(x), reverse=True)
        pattern = r'\b(' + '|'.join(map(re.escape, sorted_actions)) + r')\b'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return text[match.start():]
        return text

    def normalize_text_pre(self, text):
        text = text.lower()
        text = re.sub(r'\bt2\b', 'thứ 2', text)
        text = re.sub(r'\bt3\b', 'thứ 3', text)
        text = re.sub(r'\bt4\b', 'thứ 4', text)
        text = re.sub(r'\bt5\b', 'thứ 5', text)
        text = re.sub(r'\bt6\b', 'thứ 6', text)
        text = re.sub(r'\bt7\b', 'thứ 7', text)
        text = re.sub(r'\bcn\b', 'chủ nhật', text)
        
        text = text.replace("p.", "phòng ").replace("tầng ", "lầu ")
        text = re.sub(r'\btrc\b', 'trước', text) 
        text = text.replace("truoc", "trước")
        text = text.replace("báo trước", "nhắc trước").replace("bao trước", "nhắc trước")
        text = text.replace("hẹn trước", "nhắc trước").replace("hen trước", "nhắc trước")
        text = text.replace("nhac trước", "nhắc trước")
        text = re.sub(r'(\d+)\s*(p|phut)\b', r'\1 phút', text)
        
        return text

    def process(self, text):
        text_origin = text 
        text = self.normalize_text_pre(text)
        
        reminder_minutes = 15
        match_remind = re.search(r'nhắc trước\s*(\d+)\s*(phút|giờ)', text)
        remind_str = ""
        if match_remind:
            val = int(match_remind.group(1))
            if "giờ" in match_remind.group(2): val *= 60
            reminder_minutes = val
            remind_str = match_remind.group(0)

        start_time = self.extract_time(text) 
        
        loc = self.extract_location(text_origin)
        event = self.identify_event_action(text).replace(remind_str, "")
        
        if loc != "Chưa xác định":
             loc_lower = loc.lower()
             event = re.sub(re.escape(loc_lower), '', event, flags=re.IGNORECASE)
             all_markers_pattern = r'\b(?:' + '|'.join(map(re.escape, self.loc_markers)) + r')\b'
             event = re.sub(all_markers_pattern, '', event, flags=re.IGNORECASE)

        event = re.sub(r'\b\d{1,2}\s*(h|:|g|giờ|gio)\s*\d{0,2}\b', '', event)
        event = re.sub(r'\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?\b', '', event)

        remove_list = [
            "vào lúc", "vao luc", "vào", "lúc", "tại", "ở", "trong", "để",
            "vao", "luc", "tai", "o", "trong", "de", 
            "cuối tuần", "tuần tới", "tuần sau", "tuan toi", "tuan sau", "cuoi tuan",
            "thứ 2", "thứ 3", "thứ 4", "thứ 5", "thứ 6", "thứ 7", "chủ nhật", 
            "thu 2", "thu 3", "thu 4", "thu 5", "thu 6", "thu 7", "chu nhat",
            "ngày mai", "hôm nay", "tới", "ngay mai", "hom nay", "toi",
            "sáng nay", "chiều nay", "tối nay", "sang nay", "chieu nay", "toi nay",
            "sáng mai", "chiều mai", "tối mai", "sang mai", "chieu mai", "toi mai",
            "mai", "mốt", "mot", "nay",
            "sáng", "trưa", "chiều", "tối", "đêm",
            "sang", "trua", "chieu", "toi", "dem"
        ]
        
        for w in remove_list:
             event = re.sub(r'\b' + re.escape(w) + r'\b', ' ', event, flags=re.IGNORECASE)
        
        event = re.sub(r'\s+', ' ', event).strip()
        if len(event) < 2: event = "Sự kiện mới"

        return {
            "event": event.capitalize(),
            "start_time": start_time.replace(microsecond=0).isoformat() if start_time else None,
            "end_time": None,
            "location": loc,
            "reminder_minutes": reminder_minutes
        }