import flet as ft
import math

# I've assumed some of your constants. You can move them to a config file later.
TEXT_COLOR = ft.colors.WHITE
LIGHT_BLUE = ft.colors.LIGHT_BLUE_ACCENT
PRIMARY_COLOR = ft.colors.with_opacity(0.9, "#212121")
BORDER_RADIUS = ft.border_radius.all(8)

def format_duration(seconds):
    """Helper function to format time from seconds to MM:SS."""
    if seconds is None or not isinstance(seconds, (int, float)):
        return "0:00"
    seconds = max(0, seconds)
    minutes, seconds = divmod(math.floor(seconds), 60)
    return f"{minutes}:{seconds:02d}"

class PlayerBar(ft.Container):
    def __init__(self, on_play_pause_clicked, on_next_clicked, on_previous_clicked, on_seek_position, on_volume_changed, on_shuffle_clicked, on_repeat_clicked):
        super().__init__(
            height=150,
            bgcolor=PRIMARY_COLOR,
            border_radius=BORDER_RADIUS,
            padding=ft.padding.only(15, 10, 15, 10),
        )

        # Store callbacks
        self._on_play_pause_clicked = on_play_pause_clicked
        self._on_next_clicked = on_next_clicked
        self._on_previous_clicked = on_previous_clicked
        self._on_seek_position = on_seek_position
        self._on_volume_changed = on_volume_changed
        self._on_shuffle_clicked = on_shuffle_clicked
        self._on_repeat_clicked = on_repeat_clicked

        # -- Define all internal widgets --
        self.thumbnail = ft.Image(src="default_thumbnail.jpg", width=80, height=80, fit=ft.ImageFit.COVER, border_radius=BORDER_RADIUS)
        self.song_title = ft.Text("Unknown Title", size=22, weight=ft.FontWeight.W_500)
        self.song_artist = ft.Text("Unknown Artist", size=16, weight=ft.FontWeight.W_300)

        self.play_button = ft.IconButton(icon=ft.icons.PLAY_ARROW_ROUNDED, icon_color=TEXT_COLOR, on_click=self._play_pause_handler, icon_size=28)
        self.next_button = ft.IconButton(icon=ft.icons.SKIP_NEXT_ROUNDED, icon_color=TEXT_COLOR, on_click=self._next_handler, icon_size=18)
        self.prev_button = ft.IconButton(icon=ft.icons.SKIP_PREVIOUS_ROUNDED, icon_color=TEXT_COLOR, on_click=self._prev_handler, icon_size=18)
        self.shuffle_button = ft.IconButton(icon=ft.icons.SHUFFLE, icon_color=TEXT_COLOR, on_click=self._shuffle_handler, icon_size=18)
        self.repeat_button = ft.IconButton(icon=ft.icons.REPEAT, icon_color=TEXT_COLOR, on_click=self._repeat_handler, icon_size=18)

        self.duration_passed = ft.Text(format_duration(0), size=13)
        self.duration_total = ft.Text(format_duration(0), size=13) # Renamed from 'duration_left' for clarity
        self.progress_slider = ft.Slider(expand=True, min=0, max=100, value=0, on_change_end=self._seek_handler, active_color=LIGHT_BLUE)

        self.volume_slider = ft.Slider(width=100, min=0, max=1, value=0.5, on_change=self._volume_handler, active_color=LIGHT_BLUE)
        self.volume_button = ft.IconButton(icon=ft.icons.VOLUME_UP, on_click=self.toggle_volume_slider, icon_size=18)
        self.volume_container = ft.Container(
            visible=False,
            content=self.volume_slider,
            margin=ft.margin.only(right=35)
        )

        # -- Arrange widgets according to your layout --
        self.content = ft.Column(
            spacing=5,
            controls=[
                # Top Row: Progress Slider
                ft.Row(
                    controls=[
                        self.duration_passed,
                        self.progress_slider,
                        self.duration_total,
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                # Bottom Row: Song Info, Controls, Volume
                ft.Row(
                    controls=[
                        # Left: Song Info
                        ft.Row(
                            expand=1,
                            controls=[
                                self.thumbnail,
                                ft.Column(
                                    controls=[self.song_title, self.song_artist],
                                    spacing=5,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        # Center: Playback Controls
                        ft.Row(
                            expand=1,
                            controls=[
                                self.shuffle_button,
                                self.prev_button,
                                ft.Container(content=self.play_button, width=60, height=60), # Center play button
                                self.next_button,
                                self.repeat_button,
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        # Right: Volume Control
                        ft.Row(
                            expand=1,
                            controls=[
                                ft.Stack(controls=[self.volume_container, self.volume_button])
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
            ],
        )

    # -- Internal handlers --
    def _play_pause_handler(self, e): self._on_play_pause_clicked()
    def _next_handler(self, e): self._on_next_clicked()
    def _prev_handler(self, e): self._on_previous_clicked()
    def _seek_handler(self, e): self._on_seek_position(e.control.value)
    def _shuffle_handler(self, e): self._on_shuffle_clicked()
    def _repeat_handler(self, e): self._on_repeat_clicked()
    
    def _volume_handler(self, e):
        self._on_volume_changed(e.control.value)
        vol = e.control.value
        if vol == 0: self.volume_button.icon = ft.icons.VOLUME_OFF
        elif vol < 0.5: self.volume_button.icon = ft.icons.VOLUME_DOWN
        else: self.volume_button.icon = ft.icons.VOLUME_UP
        self.update()

    def toggle_volume_slider(self, e):
        self.volume_container.visible = not self.volume_container.visible
        self.update()

    # -- Public methods to update UI --
    def set_playing_state(self, is_playing: bool):
        self.play_button.icon = ft.icons.PAUSE_ROUNDED if is_playing else ft.icons.PLAY_ARROW_ROUNDED
        self.update()

    def update_song_details(self, title: str, artist: str, thumbnail_path: str):
        self.song_title.value = title
        self.song_artist.value = artist
        self.thumbnail.src = thumbnail_path
        self.update()

    def update_progress(self, total_seconds: float, current_seconds: float):
        self.progress_slider.max = total_seconds
        self.progress_slider.value = current_seconds
        self.duration_total.value = format_duration(total_seconds)
        self.duration_passed.value = format_duration(current_seconds)
        self.update()