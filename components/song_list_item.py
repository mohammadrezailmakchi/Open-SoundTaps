import flet as ft

class SongListItem(ft.Container):
    def __init__(self, song_id, title, artist, album, genre, duration, on_play_song):
        super().__init__(
            on_click=lambda e: on_play_song(song_id),
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(vertical=8, horizontal=15),
            ink=True, # Shows a ripple effect on click
        )
        
        # Helper function to create consistently styled text for each column
        def text_column(value, expand_val=1):
            return ft.Container(
                content=ft.Text(value, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                expand=expand_val
            )

        # The content of the component is a Row with Text columns
        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                text_column(title, expand_val=3),
                text_column(artist, expand_val=2),
                text_column(album, expand_val=3),
                text_column(genre, expand_val=2),
                ft.Container(
                    content=ft.Text(duration, text_align=ft.TextAlign.RIGHT),
                    width=50 # Fixed width for duration
                ),
            ]
        )