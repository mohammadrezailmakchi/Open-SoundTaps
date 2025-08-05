import flet as ft

class LibraryView(ft.Column):
    """The main view for the Music Library, containing tabs for songs, albums, and artists."""
    def __init__(self, on_add_folder_clicked):
        super().__init__(expand=6) # Takes up most of the space

        self._on_add_folder_clicked = on_add_folder_clicked

        # Define UI elements
        self.song_list_view = ft.ListView(expand=True, spacing=10, auto_scroll=False)
        self.album_list_view = ft.ListView(expand=True, spacing=10, auto_scroll=False)
        self.artist_list_view = ft.ListView(expand=True, spacing=10, auto_scroll=False)

        add_folder_button = ft.ElevatedButton(
            "Add Folder",
            icon=ft.icons.FOLDER,
            on_click=lambda e: self._on_add_folder_clicked(),
        )

        self.controls = [
            ft.Row(controls=[ft.Text("Music", size=32, weight=ft.FontWeight.BOLD), ft.Container(expand=True), add_folder_button]),
            ft.Tabs(
                expand=True,
                selected_index=0,
                tabs=[
                    ft.Tab(text="Songs", content=self.song_list_view),
                    ft.Tab(text="Albums", content=self.album_list_view),
                    ft.Tab(text="Artists", content=self.artist_list_view),
                ],
            ),
        ]

    def populate_lists(self, songs, albums, artists):
        """Clears and populates all list views with data from the SongManager."""
        self.song_list_view.controls.clear()
        for song_id, song_data in songs.items():
            # This is where you'd build your fancy song row component
            self.song_list_view.controls.append(
                ft.ListTile(title=ft.Text(song_data["title"]), subtitle=ft.Text(song_data["artist"]))
            )

        self.album_list_view.controls.clear()
        for album_id, album_data in albums.items():
            self.album_list_view.controls.append(
                ft.ListTile(title=ft.Text(album_data["title"]), subtitle=ft.Text(album_data["artist"]))
            )

        self.artist_list_view.controls.clear()
        for artist_id, artist_data in artists.items():
            self.artist_list_view.controls.append(
                ft.ListTile(title=ft.Text(artist_data["title"]))
            )
        
        self.update()
        print("Library view populated with data.")