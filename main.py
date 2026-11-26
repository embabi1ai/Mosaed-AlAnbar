import json
import os
from datetime import datetime, date
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup

DATA_FILE = "poultry_data.json"

class PoultryAssistant(App):
    def build(self):
        self.title = "مساعد العنبر"
        self.data = self.load_data()
        self.root_box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        self.root_box.add_widget(Label(text="[b]مساعد العنبر[/b]", markup=True, font_size="24sp",
                                       size_hint_y=None, height=dp(48), color=(0.08,0.35,0.20,1)))
        self.body = BoxLayout(orientation="vertical", spacing=dp(7))
        self.root_box.add_widget(self.body)
        self.show_home()
        Clock.schedule_interval(self.check_water, 60)
        return self.root_box

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"birds": 5000, "mortality": [], "feed": [], "treatments": [],
                "tasks": [], "water_minutes": 60, "last_water": datetime.now().isoformat()}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def clear(self):
        self.body.clear_widgets()

    def make_button(self, text, callback):
        b = Button(text=text, size_hint_y=None, height=dp(48), font_size="17sp",
                   background_normal="", background_color=(0.12,0.48,0.29,1))
        b.bind(on_release=lambda *_: callback())
        return b

    def field(self, hint, multiline=False):
        return TextInput(hint_text=hint, multiline=multiline, size_hint_y=None,
                         height=dp(45), font_size="16sp", input_filter=None)

    def page(self, title):
        self.clear()
        self.body.add_widget(Label(text=title, font_size="20sp", size_hint_y=None,
                                   height=dp(40), color=(0.1,0.1,0.1,1)))
        scroll = ScrollView()
        self.content = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None,
                                 padding=(0,0,0,dp(10)))
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        self.body.add_widget(scroll)
        self.body.add_widget(self.make_button("الصفحة الرئيسية", self.show_home))

    def add_label(self, text):
        self.content.add_widget(Label(text=text, size_hint_y=None, height=dp(38),
                                      color=(0.12,0.12,0.12,1), font_size="16sp"))

    def popup(self, title, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        box.add_widget(Label(text=message))
        btn = Button(text="حسناً", size_hint_y=None, height=dp(44))
        box.add_widget(btn)
        pop = Popup(title=title, content=box, size_hint=(.85,.4))
        btn.bind(on_release=pop.dismiss)
        pop.open()

    def show_home(self):
        self.clear()
        total_dead = sum(x["count"] for x in self.data["mortality"])
        remaining = max(0, int(self.data.get("birds",5000)) - total_dead)
        self.body.add_widget(Label(text=f"العدد الأصلي: {self.data.get('birds',5000)}    |    النافق: {total_dead}    |    المتبقي: {remaining}",
                                   size_hint_y=None, height=dp(42), font_size="15sp",
                                   color=(0.1,0.1,0.1,1)))
        for title, fn in [
            ("تسجيل النافق", self.mortality_page),
            ("تسجيل العلف", self.feed_page),
            ("العلاج", self.treatment_page),
            ("متابعة المياه", self.water_page),
            ("مهام العنبر", self.tasks_page),
            ("السجل والإحصائيات", self.report_page),
            ("إعداد عدد الطيور", self.settings_page),
        ]:
            self.body.add_widget(self.make_button(title, fn))

    def mortality_page(self):
        self.page("تسجيل النافق")
        inp = self.field("عدد النافق الآن")
        self.content.add_widget(inp)
        def add():
            try:
                n = int(inp.text)
                if n <= 0: raise ValueError()
                self.data["mortality"].append({"count":n,"date":datetime.now().strftime("%Y-%m-%d %H:%M")})
                self.save_data(); self.popup("تم", "تم تسجيل النافق"); self.mortality_page()
            except ValueError:
                self.popup("تنبيه", "اكتب عدد صحيح أكبر من صفر")
        self.content.add_widget(self.make_button("حفظ النافق", add))
        total = sum(x["count"] for x in self.data["mortality"])
        self.add_label(f"إجمالي النافق: {total}")

    def feed_page(self):
        self.page("تسجيل العلف")
        inp = self.field("كمية العلف بالكيلو")
        self.content.add_widget(inp)
        def add():
            try:
                n = float(inp.text)
                if n <= 0: raise ValueError()
                self.data["feed"].append({"kg":n,"date":datetime.now().strftime("%Y-%m-%d %H:%M")})
                self.save_data(); self.popup("تم", "تم تسجيل كمية العلف"); self.feed_page()
            except ValueError:
                self.popup("تنبيه", "اكتب كمية صحيحة بالكيلو")
        self.content.add_widget(self.make_button("حفظ العلف", add))
        today = date.today().isoformat()
        daily = sum(x["kg"] for x in self.data["feed"] if x["date"].startswith(today))
        total = sum(x["kg"] for x in self.data["feed"])
        self.add_label(f"استهلاك اليوم: {daily:.1f} كجم")
        self.add_label(f"الإجمالي المسجل: {total:.1f} كجم")

    def treatment_page(self):
        self.page("العلاج")
        name = self.field("اسم العلاج")
        hours = self.field("مدة العلاج بالساعات")
        self.content.add_widget(name); self.content.add_widget(hours)
        def add():
            try:
                h = float(hours.text)
                if not name.text.strip() or h <= 0: raise ValueError()
                self.data["treatments"].append({"name":name.text.strip(),"hours":h,
                    "start":datetime.now().strftime("%Y-%m-%d %H:%M"),"end":(datetime.now()).timestamp()+h*3600})
                self.save_data(); self.popup("تم", "تم تسجيل العلاج ومدته"); self.treatment_page()
            except ValueError:
                self.popup("تنبيه", "اكتب اسم العلاج ومدة صحيحة")
        self.content.add_widget(self.make_button("بدء العلاج", add))
        for t in self.data["treatments"][-8:]:
            status = "منتهي" if datetime.now().timestamp() >= t["end"] else "مستمر"
            self.add_label(f'{t["name"]} - {t["hours"]:g} ساعة - {status}')

    def water_page(self):
        self.page("متابعة المياه")
        mins = self.field("التذكير كل كام دقيقة؟",)
        mins.text = str(self.data.get("water_minutes",60))
        self.content.add_widget(mins)
        def set_timer():
            try:
                m = int(mins.text)
                if m < 1: raise ValueError()
                self.data["water_minutes"] = m
                self.data["last_water"] = datetime.now().isoformat()
                self.save_data(); self.popup("تم", f"تم ضبط مراجعة المياه كل {m} دقيقة أثناء تشغيل التطبيق")
            except ValueError:
                self.popup("تنبيه", "اكتب عدد دقائق صحيح")
        self.content.add_widget(self.make_button("حفظ موعد المراجعة", set_timer))
        self.content.add_widget(self.make_button("تمت مراجعة المياه الآن", self.water_done))
        self.add_label("التذكير يعمل أثناء فتح التطبيق فقط.")

    def water_done(self):
        self.data["last_water"] = datetime.now().isoformat()
        self.save_data()
        self.popup("تم", "تم تسجيل مراجعة المياه")

    def check_water(self, _dt):
        try:
            last = datetime.fromisoformat(self.data.get("last_water", datetime.now().isoformat()))
            mins = int(self.data.get("water_minutes",60))
            elapsed = (datetime.now()-last).total_seconds()/60
            if elapsed >= mins:
                self.data["last_water"] = datetime.now().isoformat()
                self.save_data()
                self.popup("تذكير المياه", "راجع المياه والسقايات الآن")
        except Exception:
            pass

    def tasks_page(self):
        self.page("مهام العنبر")
        inp = self.field("اكتب المهمة")
        self.content.add_widget(inp)
        def add():
            if inp.text.strip():
                self.data["tasks"].append({"text":inp.text.strip(),"done":False,
                                           "date":datetime.now().strftime("%Y-%m-%d %H:%M")})
                self.save_data(); self.tasks_page()
        self.content.add_widget(self.make_button("إضافة مهمة", add))
        for i, task in enumerate(self.data["tasks"]):
            status = "✓" if task["done"] else "○"
            self.content.add_widget(self.make_button(f'{status} {task["text"]}', lambda i=i: self.toggle_task(i)))

    def toggle_task(self, i):
        self.data["tasks"][i]["done"] = not self.data["tasks"][i]["done"]
        self.save_data(); self.tasks_page()

    def report_page(self):
        self.page("السجل والإحصائيات")
        dead = sum(x["count"] for x in self.data["mortality"])
        feed = sum(x["kg"] for x in self.data["feed"])
        birds = max(1, int(self.data.get("birds",5000)))
        self.add_label(f"عدد الطيور الأصلي: {birds}")
        self.add_label(f"إجمالي النافق: {dead}")
        self.add_label(f"نسبة النافق: {dead/birds*100:.2f}%")
        self.add_label(f"المتبقي التقديري: {max(0,birds-dead)}")
        self.add_label(f"إجمالي العلف المسجل: {feed:.1f} كجم")
        self.add_label(f"عدد مرات تسجيل العلف: {len(self.data['feed'])}")
        self.add_label(f"عدد مرات تسجيل النافق: {len(self.data['mortality'])}")

    def settings_page(self):
        self.page("إعداد عدد الطيور")
        inp = self.field("العدد الأصلي للطيور")
        inp.text = str(self.data.get("birds",5000))
        self.content.add_widget(inp)
        def save():
            try:
                n = int(inp.text)
                if n < 1: raise ValueError()
                self.data["birds"] = n; self.save_data()
                self.popup("تم", "تم حفظ عدد الطيور"); self.show_home()
            except ValueError:
                self.popup("تنبيه", "اكتب عدد صحيح")
        self.content.add_widget(self.make_button("حفظ", save))

if __name__ == "__main__":
    PoultryAssistant().run()
