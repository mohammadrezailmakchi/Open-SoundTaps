import flet as ft

# Import your new, clean modules
from core.song_manager import SongManager
from views.library_view import LibraryView
from components.nav_rail import NavRail
from components.player_bar import PlayerBar

def main(page: ft.Page):
    page.title = "My Music App"
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    page.padding = 0

    # --- 1. Initialize Core Logic ---
    # This loads all songs, albums, and artists into one object.
    song_manager = SongManager()

    # --- 2. Define Handler Functions ---
    # These functions will contain your actual player logic (from core/audio_player.py).
    # For now, they can just print messages.

    def add_folder():
        print("Add Folder clicked. Logic to open file dialog goes here.")
        # After adding, you would re-initialize the manager and update the view:
        # song_manager = SongManager()
        # library_view.populate_lists(song_manager.songs, song_manager.albums, song_manager.artists)
        # page.update()

    def change_route(selected_index):
        print(f"Route changed to index {selected_index}")
        # In a real app, you would swap out library_view for other views.
        # For example:
        # if selected_index == 0:
        #     main_content.content = home_view
        # elif selected_index == 1:
        #     main_content.content = library_view

    # --- PlayerBar Handlers ---
    def play_pause(): print("Play/Pause clicked!")
    def next_song(): print("Next clicked!")
    def prev_song(): print("Previous clicked!")
    def seek_position(value): print(f"Seek to {value}")
    def volume_change(value): print(f"Volume changed to {value}")
    def shuffle_toggle(): print("Shuffle toggled!")
    def repeat_toggle(): print("Repeat toggled!")


    # --- 3. Initialize UI Components ---
    nav_rail = NavRail(on_change_route=change_route)
    library_view = LibraryView(on_add_folder_clicked=add_folder)
    player_bar = PlayerBar(
        on_play_pause_clicked=play_pause,
        on_next_clicked=next_song,
        on_previous_clicked=prev_song,
        on_seek_position=seek_position,
        on_volume_changed=volume_change,
        on_shuffle_clicked=shuffle_toggle,
        on_repeat_clicked=repeat_toggle,
    )

    # --- 4. Assemble Final Layout ---
    # Main content area that can be swapped out
    main_content = ft.Container(
        content=library_view,
        expand=True,
        padding=ft.padding.all(15)
    )

    # The top-level layout is a Column containing the main Row and the PlayerBar
    page.add(
        ft.Column(
            expand=True,
            controls=[
                # An inner Row for the main content area
                ft.Row(
                    expand=True,
                    controls=[
                        nav_rail,
                        ft.VerticalDivider(width=1, color="#444444"),
                        main_content,
                    ]
                ),
                player_bar, # The player bar sits at the bottom of the column
            ]
        )
    )
    
    
        # --- 5. Connect Logic to UI ---
    # Give the library view the data it needs to display.
    library_view.populate_lists(
        songs=song_manager.songs,
        albums=song_manager.albums,
        artists=song_manager.artists
    )
    
    page.update()

ft.app(target=main)