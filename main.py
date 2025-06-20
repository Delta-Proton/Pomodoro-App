from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

import soundfile as sf
import sounddevice as sd

Window.title


class PomodoroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Параметры таймера
        self.focus_duration = 25
        self.short_break = 5
        self.long_break = 15
        self.cycles_before_long = 4

        self.is_running = False
        self.time_count = 6
        self.remaining = self.focus_duration * 60

        # Звуки
        self.start_sound, self.start_sr = sf.read("audio/Time_start.wav")
        self.end_sound, self.end_sr = sf.read("audio/Time_end.wav")

        # Построение интерфейса
        self.layout = BoxLayout(orientation="vertical")

        # Settings
        top_anchor = AnchorLayout(
            anchor_x="left", anchor_y="top", size_hint=(1, None), height=50
        )
        settings_btn = Button(
            text="Settings",
            size_hint=(None, None),
            size=(120, 40),
            on_press=self.go_to_settings,
        )
        top_anchor.add_widget(settings_btn)
        self.layout.add_widget(top_anchor)

        # Таймер
        timer_anchor = AnchorLayout(
            anchor_x="center", anchor_y="center", size_hint=(1, 0.4)
        )
        self.timer_label = Label(text=self.MM_SS(self.remaining), font_size=72)
        timer_anchor.add_widget(self.timer_label)
        self.layout.add_widget(timer_anchor)

        # Кнопки Start и Stop
        btn_column = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=340,  # ширина под кнопки
            spacing=20,
            padding=20,
        )
        self.start_btn = Button(
            text="Start", size_hint=(1, None), height=100, on_press=self.start_time
        )
        btn_column.add_widget(self.start_btn)

        stop_btn = Button(
            text="Stop", size_hint=(1, None), height=100, on_press=self.stop_time
        )
        btn_column.add_widget(stop_btn)

        btn_anchor = AnchorLayout(
            anchor_x="center", anchor_y="center", size_hint=(1, 0.3)
        )
        btn_anchor.add_widget(btn_column)
        self.layout.add_widget(btn_anchor)

        self.add_widget(self.layout)

        # Планировщик тика, пока не запущен
        self.event = None

    def MM_SS(self, sec):
        m, s = divmod(sec, 60)
        return f"{m:02}:{s:02}"

    def update(self, dt):
        if not self.is_running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self.timer_label.text = self.MM_SS(self.remaining)
        else:
            sd.play(self.end_sound, self.end_sr)
            self.is_running = False

            if self.time_count == 7:
                self.time_count = 0
            else:
                self.time_count += 1

            if self.time_count == 7:

                self.remaining = self.long_break * 60
            elif self.time_count % 2 == 1:
                self.remaining = self.short_break * 60
            else:
                self.remaining = self.focus_duration * 60

            self.start_btn.text = "Start"
            self.timer_label.text = self.MM_SS(self.remaining)

            if self.event:
                self.event.cancel()
                self.event = None

    def start_time(self, inst):
        if not self.is_running:
            sd.play(self.start_sound, self.start_sr)
            self.is_running = True
            self.start_btn.text = "Pause"
            if not self.event:
                self.event = Clock.schedule_interval(self.update, 1)
        else:
            self.is_running = False
            self.start_btn.text = "Resume"

    def stop_time(self, inst):
        if self.event:
            self.event.cancel()
            self.event = None
        self.is_running = False
        self.time_count = 0
        self.remaining = self.focus_duration * 60
        self.timer_label.text = self.MM_SS(self.remaining)
        self.start_btn.text = "Start"

    def go_to_settings(self, inst):
        s = self.manager.get_screen("settings")
        s.focus_input.text = str(self.focus_duration)
        s.short_input.text = str(self.short_break)
        s.long_input.text = str(self.long_break)
        self.manager.current = "settings"


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        container = BoxLayout(
            orientation="vertical",
            spacing=15,
            padding=20,
            size_hint=(None, None),
            size=(320, 260),
        )

        def make_row(caption, default):
            row = BoxLayout(size_hint_y=None, height=40, spacing=10)
            lbl = Label(text=caption, size_hint_x=0.5)
            inp = TextInput(
                text=str(default), multiline=False, input_filter="int", size_hint_x=0.5
            )
            row.add_widget(lbl)
            row.add_widget(inp)
            return row, inp

        r1, self.focus_input = make_row("Work (min):", 25)
        r2, self.short_input = make_row("Short break:", 5)
        r3, self.long_input = make_row("Long break:", 15)

        container.add_widget(r1)
        container.add_widget(r2)
        container.add_widget(r3)

        btns = BoxLayout(size_hint_y=None, height=60, spacing=20)
        btns.add_widget(Button(text="Save", size_hint=(1, 1), on_press=self.save))
        btns.add_widget(Button(text="Back", size_hint=(1, 1), on_press=self.back))
        container.add_widget(btns)

        anchor = AnchorLayout(anchor_x="center", anchor_y="center")
        anchor.add_widget(container)
        self.add_widget(anchor)

    def save(self, inst):
        main = self.manager.get_screen("main")
        try:
            main.focus_duration = int(self.focus_input.text)
            main.short_break = int(self.short_input.text)
            main.long_break = int(self.long_input.text)
            main.remaining = main.focus_duration * 60
            main.timer_label.text = main.MM_SS(main.remaining)
        except ValueError:
            pass
        self.manager.current = "main"

    def back(self, inst):
        self.manager.current = "main"


class PomodApp(App):
    def build(self):

        Window.size = (400, 600)
        sm = ScreenManager()
        sm.add_widget(PomodoroScreen(name="main"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm


if __name__ == "__main__":
    PomodApp().run()
