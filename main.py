import flet as ft
import os
import base64
import uuid
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC
import threading
import random
from pynput import keyboard
import time
import requests
from bs4 import BeautifulSoup
from hashlib import md5
import json


# Removed unused import
# from PyQt5.QtWidgets import QMessageBox

def main(page: ft.Page):
    page.window.maximized = True
    page.bgcolor = ft.colors.BLACK
    main_frame_height = 610

    # Main colors
    PRIMARY_COLOR = "#1D1D1D"
    TEXT_COLOR = ft.colors.WHITE
    TRANSPARENT = ft.colors.TRANSPARENT
    DARK_BLUE = ft.colors.BLUE
    LIGHT_BLUE = ft.colors.BLUE
    BLACK = ft.colors.BLACK

    # Controls
    BORDER_RADIUS = 8
    PADDING = ft.padding.all(10)
    
    # Variables
        # Playback Variables
    duration_passed = 0.0
    duration_left = 0.0
    slider_value = 0.0
    is_playing = False
    is_repeat = False
    is_shuffle = False
    current_volume = 1.0
    played_songs = []
    timer = None
    press_times = []
    
    current_song_title = ""
    current_song_artist = ""
    
    shuffle_icon = ft.icons.SHUFFLE_ROUNDED
    previous_song = ft.icons.SKIP_PREVIOUS_ROUNDED
    play_song = ft.icons.PLAY_ARROW_ROUNDED
    paused_song = ft.icons.PAUSE_ROUNDED
    next_song = ft.icons.SKIP_NEXT_ROUNDED
    repeat_song = ft.icons.REPEAT_ROUNDED
    volume_control_icon = ft.icons.VOLUME_UP_ROUNDED
    
    thumbnail_path_global = ""
    song_title_global = ""
    artist_name_global = ""
    album_name_global = ""
    year_released_global = ""
    song_genre_global = ""
    song_duration_global = 0.0
    audio_file_path = ""
    
    current_volume = 1.0
    
    # Variable to track the selected song container
    selected_song_box = None
    selected_album_box = None
    selected_artist_box = None
    
    sorted_songs = None
    
    
    
    album_isActive = False
    
    is_double_tap_handled = None

    foreground_container_y_position = 610  # Start near the bottom
    album_is_visible = False  # Tracks if the layer is fully visible
    first_drag = False
    albums_sorted = {}
    
    SERVER_URL = "https://soundtaps-server.onrender.com"
    CACHE_FOLDER = "cache"
    CACHE_EXPIRY = 3 * 24 * 60 * 60  # Cache duration: 3 days in seconds
    CONFIG_FILE = os.path.join(CACHE_FOLDER, "artists_config.json")
    
    

    def format_duration(minutes: float) -> str:
        mins = int(minutes) // 60
        secs = int(minutes) % 60
        return f"{mins}:{secs:02}"
    
    audio = ft.Audio(autoplay=True,)
    audio.visible = False
    
    user_interacting_with_slider = False

    
    # Widgets
    Song_List = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=False,  # Changed from True to False
    )

    Album_List = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=False,
    )
    
    Album_List_browser = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=False,
    )
    
    Artist_song_list_browser = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=False,
    )
    
    Artist_album_list_browser = ft.ListView(
        expand=True,
        spacing=10,
        auto_scroll=False,
    )

    Artist_List = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=False,
    )
    
    current_thumbnail_widget = ft.Image(
        src=thumbnail_path_global if thumbnail_path_global else "default_thumbnail.jpg",
        width=80,
        height=80,
        fit=ft.ImageFit.COVER,
        repeat=ft.ImageRepeat.NO_REPEAT,
        border_radius=BORDER_RADIUS,
    )
    
    current_song_title_widget = ft.Text(
        current_song_title,
        size=22,
        weight=ft.FontWeight.W_500,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.CENTER,
        max_lines=1,
    )
    
    current_song_artist_widget = ft.Text(
        current_song_artist,
        size=16,
        weight=ft.FontWeight.W_300,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.CENTER,
        max_lines=1,
    )
    
    play_song_button = ft.IconButton(icon=play_song, icon_color=TEXT_COLOR, icon_size=28)
    repeat_song_button = ft.IconButton(icon=repeat_song, icon_color=TEXT_COLOR, icon_size=18)
    shuffle_song_button = ft.IconButton(icon=shuffle_icon, icon_color=TEXT_COLOR, icon_size=18)
    
    duration_passed_widget = ft.Text(
        format_duration(duration_passed),
        size=13,
        weight=ft.FontWeight.W_300,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.CENTER
    )
    
    duration_left_widget = ft.Text(
        format_duration(duration_left),
        size=13,
        weight=ft.FontWeight.W_300,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.CENTER
    )
    
    time_line_slider = ft.Slider(
        value=slider_value,
        expand=True,
        thumb_color=LIGHT_BLUE,
        inactive_color=TEXT_COLOR,
        active_color=LIGHT_BLUE,
        
    )
    
    def initialize_config():
        """
        Initializes the configuration JSON file if it does not exist.
        """
        

    def load_artist_data():
        """
        Loads artist data from the configuration file.

        Returns:
            dict: Dictionary of artist data.
        """
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

    def save_artist_data(artist_data):
        """
        Saves artist data to the configuration file.

        Args:
            artist_data (dict): Dictionary of artist data.
        """
        with open(CONFIG_FILE, 'w') as f:
            json.dump(artist_data, f, indent=4)

    def clear_expired_cache():
        """
        Removes cached files and updates configuration data for expired entries.
        """
        os.makedirs(CACHE_FOLDER, exist_ok=True)
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(CACHE_FOLDER):
            return

        current_time = time.time()
        artist_data = load_artist_data()
        updated_data = {}

        for artist_name, data in artist_data.items():
            file_path = data.get("thumbnail_path")
            if file_path and os.path.exists(file_path):
                last_modified_time = os.path.getmtime(file_path)
                if current_time - last_modified_time > CACHE_EXPIRY:
                    os.remove(file_path)
                    print(f"Removed expired cache file for artist: {artist_name}")
                else:
                    updated_data[artist_name] = data

        save_artist_data(updated_data)

    def fetch_and_save_artist_info(artist_name):
        """
        Fetches artist info, caches the thumbnail, and updates the configuration file.

        Args:
            artist_name (str): The name of the artist.

        Returns:
            dict: A dictionary containing artist info, including the thumbnail path and Spotify URL.
        """
        artist_data = load_artist_data()

        if artist_name in artist_data:
            print(f"Artist {artist_name} found in cache.")
            return artist_data[artist_name]

        # Fetch artist info from the server
        params = {"artist": artist_name}
        response = requests.get(f"{SERVER_URL}/artist-info", params=params)

        if response.status_code == 200:
            data = response.json()

            # Extract the smallest thumbnail URL from the images list
            if data.get("images"):
                thumbnail_url = data["images"][0]["url"]  # Assuming the smallest image is last
            else:
                thumbnail_url = None

            # Ensure Spotify URL is present
            spotify_url = data.get("spotify_url")

            if not thumbnail_url or not spotify_url:
                raise Exception("Incomplete artist data received.")

            # Save thumbnail to cache folder
            os.makedirs(CACHE_FOLDER, exist_ok=True)

            filename = f"{artist_name.replace(' ', '_').lower()}.jpg"
            file_path = os.path.join(CACHE_FOLDER, filename)

            if not os.path.exists(file_path):
                thumbnail_response = requests.get(thumbnail_url)
                if thumbnail_response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(thumbnail_response.content)
                else:
                    raise Exception("Failed to download the thumbnail image.")

            # Update artist data
            artist_info = {
                "thumbnail_path": file_path,
                "spotify_url": spotify_url
            }
            artist_data[artist_name] = artist_info
            save_artist_data(artist_data)

            return artist_info
        else:
            raise Exception(f"Failed to fetch artist info: {response.status_code} {response.json()}")


    def on_drag(e: ft.DragUpdateEvent):
        nonlocal foreground_container_y_position, album_is_visible, first_drag

        if not album_isActive:
            return

        # Ensure the drag started from the foreground container or first drag flag is True
        if not first_drag:
            if foreground_container_y_position <= e.global_y <= foreground_container_y_position + 100:
                first_drag = True
            else:
                return

        # Calculate new position based on drag
        new_y = e.global_y  # Use global_y for direct position comparison

        # Check if the drag exceeds 200px beyond the container's current position
        if album_is_visible and new_y <= 50:
            # Stick to the top
            foreground_container_y_position = 0
            album_is_visible = True
        elif not album_is_visible and new_y >= main_frame_height - 50:
            # Stick to the bottom
            foreground_container_y_position = main_frame_height - 50
            album_is_visible = False
        else:
            # Update position within bounds during drag
            foreground_container_y_position = min(max(new_y, 0), main_frame_height - 50)

        # Update the container's offset to reflect its position
        slide_browsing_container.offset = ft.Offset(0, foreground_container_y_position / main_frame_height)
        slide_browsing_container.update()

    def on_drag_end(e: ft.DragEndEvent):
        nonlocal foreground_container_y_position, album_is_visible, first_drag

        if not album_isActive:
            return

        # Ensure the drag started from the foreground container or first drag flag is True
        if not first_drag:
            return

        # Snap to final position based on release point
        if foreground_container_y_position < main_frame_height / 2:
            # Snap to fully visible (top)
            foreground_container_y_position = 10
            album_is_visible = True
        else:
            # Snap to hidden (bottom)
            foreground_container_y_position = main_frame_height - 50
            album_is_visible = False

        # Animate to the final position
        slide_browsing_container.offset = ft.Offset(0, foreground_container_y_position / main_frame_height)
        slide_browsing_container.update()

        # Reset the first drag flag
        first_drag = False

    
    primary_widget_text_container = ft.Text(
        value="Music",
        size=32,
        weight=ft.FontWeight.W_600,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.LEFT,
        max_lines=1,
        )
    
    secondary_widget_text_container = ft.Text(
        value="Music",
        size=18,
        weight=ft.FontWeight.W_400,
        color=TEXT_COLOR,
        text_align=ft.TextAlign.LEFT,
        max_lines=1,
        )
    
    song_browsing_container = ft.Column(
        controls=[
            ft.Column(
                controls=[
                    ft.Container(
                        bgcolor=TRANSPARENT,
                        height=40,
                        expand=1,
                        border_radius=BORDER_RADIUS
                        ),
                    
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(width=15),
                                ft.Text(
                                    "Music",
                                    size=32,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_COLOR,
                                    text_align=ft.TextAlign.LEFT
                                    ),
                                
                                
                                
                                ft.Container(expand=1),
                                ft.Container(
                                    content=ft.ElevatedButton(
                                        icon=ft.icons.FOLDER,
                                        icon_color=TEXT_COLOR,
                                        text="Add Folder",
                                        color=TEXT_COLOR,
                                        bgcolor=TRANSPARENT,
                                        height=40,
                                        ),
                                    padding=ft.padding.only(0,0,0,0)
                                    ),
                                ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=2,
                            ),
                        bgcolor=TRANSPARENT,
                        height=40,
                        expand=1,
                        padding=ft.padding.all(0)
                        ),
                    
                    ft.Container(
                        content=#----------- Tabs -------------
                    
                    ft.Tabs(
                        selected_index=0,
                        clip_behavior=False,
                        animation_duration=200,
                        tabs=[
                            ft.Tab(
                                tab_content=ft.Text(
                                    "Songs",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_COLOR,
                                    text_align=ft.TextAlign.LEFT
                                    ),
                                content=ft.Container(
                                    content=Song_List,
                                    padding=ft.padding.all(10)
                                ),
                                
                            ),
                            ft.Tab(
                                tab_content=ft.Text(
                                    "Albums",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_COLOR,
                                    text_align=ft.TextAlign.LEFT
                                    ),
                                content=ft.Container(
                                    content=Album_List,
                                    padding=ft.padding.all(10)
                                ),
                            ),
                            ft.Tab(
                                tab_content=ft.Text(
                                    "Artists",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_COLOR,
                                    text_align=ft.TextAlign.LEFT
                                    ),
                                icon=ft.icons.SETTINGS,
                                content=ft.Container(
                                    content=Artist_List,
                                    padding=ft.padding.all(10)
                                ),
                            ),
                            
                        ],
                        expand=1,
                        divider_color=TRANSPARENT,
                        label_color=TEXT_COLOR,
                        indicator_color=TEXT_COLOR,
                        overlay_color={
                            ft.ControlState.HOVERED: TRANSPARENT,
                        },
                        ),
                    
                    #-------------- Tabs End ----------------,
                    
                        bgcolor=TRANSPARENT,
                        width="expand",
                        height=490,
                        margin=ft.margin.all(0)
                    )
                    
                ],
            ),
            
            ],
        )
    
    
    
    thumbnail_open_container = ft.Image(
        width=200,
        height=200,
        fit=ft.ImageFit.COVER,
        repeat=ft.ImageRepeat.NO_REPEAT,
        border_radius=BORDER_RADIUS,
        )
    
    
    album_browsing_container = ft.Column(
                controls=[
                    ft.Container(
                        bgcolor=TRANSPARENT,
                        height=40,
                        border_radius=BORDER_RADIUS
                        ),

                    ft.Container(
                        content=ft.Row(
                            controls=[
                                thumbnail_open_container,
                                ft.Column(
                                    controls=[
                                        ft.Column(
                                            controls=[
                                                primary_widget_text_container,
                                                secondary_widget_text_container,
                                                ],
                                            alignment=ft.MainAxisAlignment.START,
                                            spacing=2,
                                            ),
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Row(
                                                        controls=[
                                                            ft.ElevatedButton(
                                                                icon=ft.icons.PLAY_ARROW_ROUNDED,
                                                                icon_color=TEXT_COLOR,
                                                                text="Play",
                                                                color=TEXT_COLOR,
                                                                bgcolor=TRANSPARENT,
                                                                height=40,
                                                                ),
                                                            ft.ElevatedButton(
                                                                icon=ft.icons.OPEN_IN_NEW_ROUNDED,
                                                                icon_color=TEXT_COLOR,
                                                                text="Open in Spotify",
                                                                color=TEXT_COLOR,
                                                                bgcolor=TRANSPARENT,
                                                                height=40,
                                                                ),
                                                            
                                                            ]
                                                        ),
                                                    bgcolor=TRANSPARENT,
                                                    padding=ft.padding.all(0)
                                                    
                                                    
                                                    ),
                                                
                                                ],
                                            alignment=ft.VerticalAlignment.CENTER,
                                            spacing=10,
                                            ),
                                        ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ]
                                ),
                        bgcolor=TRANSPARENT,
                        height=200,

                        padding=ft.padding.all(0)
                        ),
                    
                    ft.Container(
                        content=Album_List_browser,                            
                        bgcolor=TRANSPARENT,
                        width="expand",
                        height=330,
                        margin=ft.margin.only(0,0,0,0)
                        )
                    ],
                )
    
    artist_browsing_container = ft.Column(
                controls=[
                    ft.Container(
                        bgcolor=TRANSPARENT,
                        height=40,
                        border_radius=BORDER_RADIUS
                        ),

                    ft.Container(
                        content=ft.Row(
                            controls=[
                                thumbnail_open_container,
                                ft.Column(
                                    controls=[
                                        ft.Column(
                                            controls=[
                                                primary_widget_text_container,
                                                ],
                                            alignment=ft.MainAxisAlignment.START,
                                            spacing=2,
                                            ),
                                        ft.Row(
                                            controls=[
                                                ft.Container(
                                                    content=ft.Row(
                                                        controls=[
                                                            ft.ElevatedButton(
                                                                icon=ft.icons.PLAY_ARROW_ROUNDED,
                                                                icon_color=TEXT_COLOR,
                                                                text="Play",
                                                                color=TEXT_COLOR,
                                                                bgcolor=TRANSPARENT,
                                                                height=40,
                                                                ),
                                                            ft.ElevatedButton(
                                                                icon=ft.icons.OPEN_IN_NEW_ROUNDED,
                                                                icon_color=TEXT_COLOR,
                                                                text="Open in Spotify",
                                                                color=TEXT_COLOR,
                                                                bgcolor=TRANSPARENT,
                                                                height=40,
                                                                ),
                                                            
                                                            ]
                                                        ),
                                                    bgcolor=TRANSPARENT,
                                                    padding=ft.padding.all(0)
                                                    
                                                    
                                                    ),
                                                
                                                ],
                                            alignment=ft.VerticalAlignment.CENTER,
                                            spacing=10,
                                            ),
                                        ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                    ),
                                    ]
                                ),
                        bgcolor=TRANSPARENT,
                        height=200,

                        padding=ft.padding.all(0)
                        ),
                    
                    ft.Container(
                        content=ft.Tabs(
                        selected_index=0,
                        clip_behavior=False,
                        animation_duration=200,
                        tabs=[
                            ft.Tab(
                                tab_content=ft.Text(
                                    "Songs",
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_COLOR,
                                    text_align=ft.TextAlign.LEFT
                                    ),
                                content=ft.Container(
                                    content=Artist_song_list_browser,
                                    padding=ft.padding.all(10)
                                ),
                                
                                ),
                            ft.Tab(
                                    tab_content=ft.Text(
                                        "Albums",
                                        size=16,
                                        weight=ft.FontWeight.W_600,
                                        color=TEXT_COLOR,
                                        text_align=ft.TextAlign.LEFT
                                        ),
                                    content=ft.Container(
                                        content=Artist_album_list_browser,
                                        padding=ft.padding.all(10)
                                    ),
                                ),
                            ],
                            expand=1,
                            divider_color=TRANSPARENT,
                            label_color=TEXT_COLOR,
                            indicator_color=TEXT_COLOR,
                            overlay_color={
                                ft.ControlState.HOVERED: TRANSPARENT,
                                },
                            ),                            
                        bgcolor=TRANSPARENT,
                        width="expand",
                        height=330,
                        margin=ft.margin.only(0,0,0,0)
                        )
                    ],
                )
            
    
    
    slide_browsing_container = ft.Container(
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,  # Ensure rounded corners work with BackdropFilter
            bgcolor=ft.colors.with_opacity(0.85,BLACK),
            blur=ft.Blur(10,10),
            padding=ft.padding.only(17,0,0,0),
            height=790,
            alignment=ft.alignment.center,
            offset=ft.Offset(0, foreground_container_y_position / main_frame_height),
            animate_offset=ft.Animation(400, "easeOutCubic"),  # Smooth easing curve
        )
    
    gesture_detector = ft.GestureDetector(
        content=ft.Stack([song_browsing_container, slide_browsing_container]),
        on_pan_update=on_drag,
        on_pan_end=on_drag_end,
        
    )
    
    right_main_stack = ft.Stack(
        controls=[gesture_detector],
        height=main_frame_height,
        alignment=ft.alignment.center,
        clip_behavior=ft.ClipBehavior.HARD_EDGE
        )
    
    right_main_container = ft.Container(
        content=right_main_stack,
        expand=6,
        alignment=ft.alignment.center,
        clip_behavior=ft.ClipBehavior.HARD_EDGE
    )
    def volume_slider_on_change(e):
        nonlocal current_volume,audio
        current_volume = e.control.value
        audio.volume = current_volume
        
    def toggle_dropdown(e):
        # Toggle dropdown visibility
        volume_dropdown.visible = not volume_dropdown.visible
        page.update()
        
    def toggle_dropdown_hide(e):
        # Toggle dropdown visibility
        volume_dropdown.visible = False
        page.update()
    
    volume_slider = ft.Slider(
        value=current_volume,
        thumb_color=LIGHT_BLUE,
        inactive_color=TEXT_COLOR,
        active_color=LIGHT_BLUE,
        scale=0.75,
        on_change_end= lambda e: volume_slider_on_change(e),
        on_blur= lambda e: toggle_dropdown_hide(e),
        
    )
    
    volume_dropdown = ft.Container(
        visible=False,
        content=ft.Container(
            content=ft.Column([
            volume_slider
            ]),
        ),
        margin=ft.margin.only(10,0,10,0)
    )
    
    is_playing = False  # To track if audio is playing
    timer = None  # Timer object
    
    def filter_and_transform_dict(input_dict, keys_list):
        """
        Takes a dictionary and a list, filters the dictionary by keys from the list,
        and creates a new dictionary with the same keys but modifies the values.

        Args:
            input_dict (dict): The input dictionary to filter and transform.
            keys_list (list): The list of keys to filter by.

        Returns:
            dict: A new dictionary with keys from the list and their corresponding values.
        """
        # Initialize the result dictionary
        result_dict = {}

        for key in keys_list:
            if key in input_dict:
                # Use the key from the input_dict
                result_dict[key] = input_dict[key]

        return result_dict


    def is_song_widget(widget):
        # Check if the widget is a song widget by verifying its structure
        return (
            hasattr(widget.content, 'controls') and
            len(widget.content.controls) > 1 and
            isinstance(widget.content.controls[0], ft.Image)
        )
        
    def next_song_action(e=None):
        """Handles manual navigation to the next song."""
        nonlocal selected_song_box, Song_List, songs, album_isActive, Album_List_browser
        nonlocal is_repeat, is_shuffle, played_songs

        next_song_box = None

        while not next_song_box:
            try:
                if is_repeat:
                    # Repeat the same song
                    next_song_box = selected_song_box
                elif is_shuffle:
                    # Shuffle mode: select a random song that hasn't been played yet
                    available_songs = [
                        song for song in Song_List.controls
                        if song != selected_song_box and song not in played_songs
                    ]
                    if not available_songs:
                        # All songs have been played; reset the played_songs list
                        played_songs = []
                        available_songs = [song for song in Song_List.controls if song != selected_song_box]

                    next_song_box = random.choice(available_songs)
                    played_songs.append(next_song_box)
                else:
                    # Determine if the selected song is in the Song_List or Album_List_browser
                    if selected_song_box in Song_List.controls:
                        # Normal mode: play the next song in the Song_List
                        current_index = Song_List.controls.index(selected_song_box)
                        next_index = current_index + 1

                        total_controls = len(Song_List.controls)
                        for i in range(next_index, total_controls):
                            potential_next = Song_List.controls[i]
                            if is_song_widget(potential_next):
                                next_song_box = potential_next
                                break
                        else:
                            # Loop back to the beginning
                            for i in range(total_controls):
                                potential_next = Song_List.controls[i]
                                if is_song_widget(potential_next):
                                    next_song_box = potential_next
                                    break
                    else:
                        # Normal mode: play the next song in the Album_List_browser
                        current_index = Album_List_browser.controls.index(selected_song_box)
                        next_index = current_index + 1

                        total_controls = len(Album_List_browser.controls)
                        for i in range(next_index, total_controls):
                            potential_next = Album_List_browser.controls[i]
                            if is_song_widget(potential_next):
                                next_song_box = potential_next
                                break
                        else:
                            # Loop back to the beginning
                            for i in range(total_controls):
                                potential_next = Album_List_browser.controls[i]
                                if is_song_widget(potential_next):
                                    next_song_box = potential_next
                                    break

                if not next_song_box:
                    # If no next song is found, retry
                    continue

                set_current_song(
                    next_song_box,
                    next_song_box.content.controls[0].src,  # thumbnail_path
                    next_song_box.content.controls[1].value,  # song_title
                    next_song_box.content.controls[2].value,  # artist_name
                    int(songs[next_song_box.content.controls[1].value]["duration"]),  # song_duration
                    songs[next_song_box.content.controls[1].value]["file_path"]  # audio_path
                )
            except Exception as error:
                # Log the error and retry
                print(f"Error while selecting next song: {error}")

        page.update()

    def previous_song_action(e=None):
        """Handles manual navigation to the previous song."""
        nonlocal selected_song_box, Song_List, songs, album_isActive, Album_List_browser
        nonlocal is_repeat, is_shuffle, played_songs

        next_song_box = None

        while not next_song_box:
            try:
                if is_repeat:
                    # Repeat the same song
                    next_song_box = selected_song_box
                elif is_shuffle:
                    # Shuffle mode: select a random song that hasn't been played yet
                    available_songs = [
                        song for song in Song_List.controls
                        if song != selected_song_box and song not in played_songs
                    ]
                    if not available_songs:
                        # All songs have been played; reset the played_songs list
                        played_songs = []
                        available_songs = [song for song in Song_List.controls if song != selected_song_box]

                    next_song_box = random.choice(available_songs)
                    played_songs.append(next_song_box)
                else:
                    # Determine if the selected song is in the Song_List or Album_List_browser
                    if selected_song_box in Song_List.controls:
                        # Normal mode: play the previous song in the Song_List
                        current_index = Song_List.controls.index(selected_song_box)
                        next_index = current_index - 1

                        total_controls = len(Song_List.controls)
                        for i in range(next_index, -1, -1):
                            potential_next = Song_List.controls[i]
                            if is_song_widget(potential_next):
                                next_song_box = potential_next
                                break
                        else:
                            # Loop back to the end
                            for i in range(total_controls - 1, -1, -1):
                                potential_next = Song_List.controls[i]
                                if is_song_widget(potential_next):
                                    next_song_box = potential_next
                                    break
                    else:
                        # Normal mode: play the previous song in the Album_List_browser
                        current_index = Album_List_browser.controls.index(selected_song_box)
                        next_index = current_index - 1

                        total_controls = len(Album_List_browser.controls)
                        for i in range(next_index, -1, -1):
                            potential_next = Album_List_browser.controls[i]
                            if is_song_widget(potential_next):
                                next_song_box = potential_next
                                break
                        else:
                            # Loop back to the end
                            for i in range(total_controls - 1, -1, -1):
                                potential_next = Album_List_browser.controls[i]
                                if is_song_widget(potential_next):
                                    next_song_box = potential_next
                                    break

                if not next_song_box:
                    # If no previous song is found, retry
                    continue

                set_current_song(
                    next_song_box,
                    next_song_box.content.controls[0].src,  # thumbnail_path
                    next_song_box.content.controls[1].value,  # song_title
                    next_song_box.content.controls[2].value,  # artist_name
                    int(songs[next_song_box.content.controls[1].value]["duration"]),  # song_duration
                    songs[next_song_box.content.controls[1].value]["file_path"]  # audio_path
                )
            except Exception as error:
                # Log the error and retry
                print(f"Error while selecting previous song: {error}")

        page.update()

        
    def toggle_repeat(e):
        nonlocal is_repeat
        is_repeat = not is_repeat
        if is_repeat:
            repeat_song_button.icon = ft.icons.REPEAT_ONE_ROUNDED  # Indicate repeat mode
        else:
            repeat_song_button.icon = ft.icons.REPEAT_ROUNDED  # Default repeat icon
        page.update()

    def toggle_shuffle(e):
        nonlocal is_shuffle, played_songs
        is_shuffle = not is_shuffle
        if is_shuffle:
            shuffle_song_button.icon = ft.icons.SHUFFLE_ON_ROUNDED  # Indicate shuffle mode
            played_songs = []  # Reset played songs when shuffle is activated
        else:
            shuffle_song_button.icon = ft.icons.SHUFFLE_ROUNDED  # Default shuffle icon
        page.update()
                
    def handle_song_end(e=None):
        nonlocal is_playing, duration_passed, slider_value, timer, play_song_button, selected_song_box
        nonlocal is_repeat, is_shuffle, played_songs, Song_List, Album_List_browser, songs, album_isActive

        is_playing = False
        duration_passed = 0
        slider_value = 0
        time_line_slider.value = 0
        duration_passed_widget.value = format_duration(duration_passed)
        duration_left_widget.value = format_duration(song_duration_global)
        play_song_button.icon = play_song  # Reset to play icon
        stop_timer()  # Ensure the timer is stopped

        next_song_box = None

        if is_repeat:
            # Repeat the same song
            next_song_box = selected_song_box
        elif is_shuffle:
            # Shuffle mode: select a random song that hasn't been played yet
            available_songs = [
                song for song in Song_List.controls
                if song != selected_song_box and song not in played_songs
            ]
            if not available_songs:
                # All songs have been played; reset the played_songs list
                played_songs = []
                available_songs = [song for song in Song_List.controls if song != selected_song_box]

            next_song_box = random.choice(available_songs)
            played_songs.append(next_song_box)
        else:
            # Determine if the selected song is in the Song_List or Album_List_browser
            if selected_song_box in Song_List.controls:
                # Normal mode: play the next song in the Song_List
                current_index = Song_List.controls.index(selected_song_box)
                next_index = current_index + 1

                total_controls = len(Song_List.controls)
                for i in range(next_index, total_controls):
                    potential_next = Song_List.controls[i]
                    if is_song_widget(potential_next):
                        next_song_box = potential_next
                        break
                else:
                    # Loop back to the beginning
                    for i in range(total_controls):
                        potential_next = Song_List.controls[i]
                        if is_song_widget(potential_next):
                            next_song_box = potential_next
                            break
            else:
                # Normal mode: play the next song in the Album_List_browser
                current_index = Album_List_browser.controls.index(selected_song_box)
                next_index = current_index + 1

                total_controls = len(Album_List_browser.controls)
                for i in range(next_index, total_controls):
                    potential_next = Album_List_browser.controls[i]
                    if is_song_widget(potential_next):
                        next_song_box = potential_next
                        break
                else:
                    # Loop back to the beginning
                    for i in range(total_controls):
                        potential_next = Album_List_browser.controls[i]
                        if is_song_widget(potential_next):
                            next_song_box = potential_next
                            break

        if next_song_box:
            set_current_song(
                next_song_box,
                next_song_box.content.controls[0].src,  # thumbnail_path
                next_song_box.content.controls[1].value,  # song_title
                next_song_box.content.controls[2].value,  # artist_name
                int(songs[next_song_box.content.controls[1].value]["duration"]),  # song_duration
                songs[next_song_box.content.controls[1].value]["file_path"]  # audio_path
            )
        else:
            # No next song to play; optionally, reset the UI or stop playback
            pass

        page.update()

        

    
    # Update slider value every second
    def update_slider(order_from_slider=False):
        nonlocal slider_value, duration_passed, timer, is_playing, time_line_slider

        # If playing or triggered by manual slider movement:
        if (is_playing and audio_file_path) or order_from_slider:
            # If we are not in manual interaction mode and not triggered by the user, get current position
            if is_playing and not order_from_slider and not user_interacting_with_slider:
                try:
                    duration_passed = audio.get_current_position() / 1000
                except Exception as e:
                    print(e)

            # Update text fields regardless
            time_line_slider.min = 0
            time_line_slider.max = 100
            duration_passed_widget.value = format_duration(duration_passed)
            duration_left_widget.value = format_duration(song_duration_global - duration_passed)

            # Update slider only if not user_interacting or triggered by user’s own final action
            if not user_interacting_with_slider or order_from_slider:
                slider_value = (duration_passed / song_duration_global) * 100
                time_line_slider.value = min(slider_value, 100)

            page.update()

            # Check if song ended
            if duration_passed >= song_duration_global:
                duration_passed = 0
                time_line_slider.value = 0
                is_playing = False
                stop_timer()
                page.update()
        else:
            # Not playing and not slider order means no reason to update
            stop_timer()

    # Start the timer
    def start_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = threading.Timer(0.25, lambda: [update_slider(), start_timer()])
        timer.start()

    # Stop the timer
    def stop_timer():
        nonlocal timer
        if timer:
            timer.cancel()
        timer = None

    # Hook the play button to start the timer
    def play_song_slider_action():
        nonlocal is_playing
        if audio_file_path:
            is_playing = True
            audio.play()
            start_timer()

    # Ensure the slider doesn't conflict with manual changes
    def slider_on_change(e):
        nonlocal user_interacting_with_slider, duration_passed
        user_interacting_with_slider = False

        # User finished dragging; set the audio position based on the final slider value.
        duration_passed = (e.control.value * song_duration_global) / 100
        audio.seek(int(duration_passed * 1000))
        # Update the UI to reflect this final position
        update_slider(order_from_slider=True)
        
    def slider_on_change_start(e):
        nonlocal user_interacting_with_slider
        user_interacting_with_slider = True
        # User started dragging; stop updating slider position from timer updates
        # but we can still let durations update if needed.
        
    def pause_resume_action(e=None):
        nonlocal is_playing
        if is_playing:
            play_song_button.icon = play_song
            is_playing = False
            audio.pause()
        else:
            play_song_button.icon = paused_song
            is_playing = True
            start_timer()
            audio.resume()
        page.update()
    
    # Function to load songs
    def load_songs_to_dict(folder="songs"):
        if not os.path.exists(folder):
            os.makedirs(folder)
            return {}

        songs_dict = {}

        for file in os.listdir(folder):
            if file.endswith(".mp3"):
                file_path = os.path.join(folder, file)
                song_metadata = extract_metadata_with_id(file_path)
                if song_metadata:
                    title = song_metadata["title"]
                    songs_dict[title] = song_metadata

        if not songs_dict:
            print(f"No MP3 files found in the '{folder}' folder.")
        
        return songs_dict

    def extract_metadata_with_id(file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            song_id = str(uuid.uuid4())
            metadata = {
                "id": song_id,
                "artist": audio.get("TPE1", "Unknown Artist").text[0] if "TPE1" in audio else "Unknown Artist",
                "album": audio.get("TALB", "Unknown Album").text[0] if "TALB" in audio else "Unknown Album",
                "genre": audio.get("TCON", "Unknown Genre").text[0] if "TCON" in audio else "Unknown Genre",
                "year": audio.get("TDRC", "Unknown Year").text[0] if "TDRC" in audio else "Unknown Year",
                "bitrate": int(audio.info.bitrate / 1000),
                "duration": int(audio.info.length),
                "file_path": file_path,
                "thumbnail_path": None
            }
            title = audio.get("TIT2", "Unknown Title").text[0] if "TIT2" in audio else "Unknown Title"
            metadata["title"] = title

            try:
                album_art = audio.tags.getall("APIC")[0].data
                thumbnail_path = save_thumbnail(file_path, album_art)
                metadata["thumbnail_path"] = thumbnail_path
            except IndexError:
                print(f"No album art found for {file_path}. Using default thumbnail.")
                metadata["thumbnail_path"] = "default_thumbnail.jpg"

            return metadata
        except Exception as e:
            print(f"Error loading metadata for {file_path}: {e}")
            return None

    def save_thumbnail(file_path, image_data):
        try:
            thumbnail_folder = "thumbnails"
            os.makedirs(thumbnail_folder, exist_ok=True)
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            thumbnail_path = os.path.join(thumbnail_folder, f"{base_name}.jpg")
            
            with open(thumbnail_path, "wb") as img_file:
                img_file.write(image_data)
            
            return thumbnail_path
        except Exception as e:
            print(f"Error saving thumbnail for {file_path}: {e}")
            return None

    def sort_songs_a_to_z(songs_dict):
        def custom_key(item):
            song_title = item[0]
            first_char = song_title[0].lower()

            if not first_char.isalnum():
                # Group all symbols together under "&"
                return "&"
            elif first_char.isdigit():
                # Group all numbers together under "#"
                return "#"
            return first_char

        return dict(sorted(songs_dict.items(), key=custom_key))

    def search_songs(songs_dict, search_query):
        search_query = search_query.lower()
        matches = (
            {
                "title": title,
                "artist": metadata["artist"],
                "album": metadata["album"],
                "genre": metadata["genre"],
                "year": metadata["year"],
                "file_path": metadata["file_path"]
            }
            for title, metadata in songs_dict.items()
            if (
                search_query in title.lower()
                or search_query in metadata["artist"].lower()
                or search_query in metadata["album"].lower()
                or search_query in metadata["genre"].lower()
            )
        )
        return list(matches)
    
    def truncate_string(input_string, index):
        index = int(index)
        if len(input_string) <= index:
            return input_string
        else:
            return input_string[:index] + "..."
    
    def songs_letter_widget(letter):
        
        # Create a new container for the song
        letter_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        letter,
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=LIGHT_BLUE,
                        text_align=ft.TextAlign.LEFT,
                        expand=3,
                    ),
                    
                ],
                spacing=10,
            ),
            padding=ft.padding.only(5,5,5,5),
            bgcolor=TRANSPARENT,
            border_radius=BORDER_RADIUS,
            expand=True,
            margin=ft.margin.only(10,0,10,0),
            
            
        )
        
        return letter_box
    
    def song_widget(thumbnail_path, song_title, artist_name, album_name, year_released, song_genre, song_duration, audio_path):

        # Create a new container for the song
        song_box = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Image(
                        src=thumbnail_path if thumbnail_path else "default_thumbnail.jpg",
                        width=40,
                        height=40,
                        fit=ft.ImageFit.COVER,
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        border_radius=BORDER_RADIUS,
                    ),
                    ft.Text(
                        song_title,
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.LEFT,
                        expand=3,
                        max_lines=1,
                    ),
                    ft.Text(
                        artist_name,
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                        expand=3,
                        max_lines=1,
                    ),
                    ft.Text(
                        album_name,
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                        expand=2,
                        max_lines=1,
                    ),
                    ft.Text(
                        str(year_released)[:str(year_released).find("-")],
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.RIGHT,
                        expand=1,
                    ),
                    ft.Text(
                        song_genre,
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.LEFT,
                        expand=1,
                    ),
                    ft.Text(
                        format_duration(song_duration),
                        size=14,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                    ft.Container(
                        width=15,
                    )
                ],
                spacing=10,
            ),
            padding=ft.padding.only(5,5,5,5),
            bgcolor=PRIMARY_COLOR,
            border_radius=BORDER_RADIUS,
            expand=True,
            margin=ft.margin.only(10,0,10,0),
            on_click=lambda e: set_current_song(
                song_box,  # Pass the current song_box
                thumbnail_path,
                song_title,
                artist_name,
                song_duration,
                audio_path
            ),
            
        )
        
        return song_box
    
    
    def set_current_song(song_box_clicked, thumbnail_path, song_title, artist_name, song_duration, audio_path):
        nonlocal selected_song_box, thumbnail_path_global, song_title_global, artist_name_global, song_duration_global, audio_file_path
        nonlocal duration_passed, slider_value, is_playing

        # If there's a previously selected song, reset its background color
        if selected_song_box and selected_song_box != song_box_clicked:
            selected_song_box.bgcolor = PRIMARY_COLOR
            # Stop the timer and reset playback variables
            
        stop_timer()
        is_playing = False
        duration_passed = 0
        slider_value = 0

        # Set the new song as selected
        selected_song_box = song_box_clicked
        selected_song_box.bgcolor = DARK_BLUE

        # Update global song info variables
        thumbnail_path_global = thumbnail_path
        song_title_global = song_title
        artist_name_global = artist_name
        song_duration_global = song_duration
        audio_file_path = audio_path
        
        # Update the UI elements
        current_thumbnail_widget.src = thumbnail_path_global if thumbnail_path_global else "default_thumbnail.jpg"
        current_song_title_widget.value = truncate_string(song_title_global,40)
        current_song_artist_widget.value = truncate_string(artist_name_global,35)
        duration_passed_widget.value = format_duration(duration_passed)  # Reset to 0
        duration_left_widget.value = format_duration(song_duration_global)

        # Load the new audio and prepare for playback
        audio.src = audio_file_path
        audio.volume = current_volume
        audio.visible = True
        play_song_button.icon = paused_song
        audio.on_state_changed = lambda e: handle_song_end() if e.data == "completed" else None

        # Automatically start playback of the new song
        time_line_slider.on_change_end = lambda e: slider_on_change(e)
        time_line_slider.on_change_start = lambda e: slider_on_change_start(e)
        play_song_slider_action()

        # Refresh the page to reflect changes
        page.update()
        

    def populate_song_list(sorted_songs:dict):
        """Populates the song list with categorized songs by their starting letter."""
        nonlocal Song_List

        letter = "#"  # Initial category for non-alphabetic entries

        for title, metadata in sorted_songs.items():
            # Determine the current song's starting letter
            current_letter = str(title)[0].upper()
            if not current_letter.isalpha():
                current_letter = "#"
                Song_List.controls.append(songs_letter_widget(current_letter))

            # Add a new letter widget if the starting letter changes
            if current_letter != letter:
                letter = current_letter
                Song_List.controls.append(songs_letter_widget(letter))

            # Add the song widget
            Song_List.controls.append(
                song_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    song_title=title,
                    artist_name=metadata["artist"],
                    album_name=metadata["album"],
                    year_released=metadata["year"],
                    song_genre=metadata["genre"],
                    song_duration=metadata["duration"],
                    audio_path=metadata["file_path"],
                )
            )

        page.update()
        
        
    def populate_song_list_inside_album(sorted_songs:dict):
        """Populates the song list with categorized songs by their starting letter."""
        nonlocal Album_List_browser

        letter = "#"  # Initial category for non-alphabetic entries
        Album_List_browser.controls.clear()

        for title, metadata in sorted_songs.items():
            # Determine the current song's starting letter
            current_letter = str(title)[0].upper()
            if not current_letter.isalpha():
                current_letter = "#"
                Album_List_browser.controls.append(songs_letter_widget(current_letter))

            # Add a new letter widget if the starting letter changes
            if current_letter != letter:
                letter = current_letter
                Album_List_browser.controls.append(songs_letter_widget(letter))

            # Add the song widget
            Album_List_browser.controls.append(
                song_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    song_title=title,
                    artist_name=metadata["artist"],
                    album_name=metadata["album"],
                    year_released=metadata["year"],
                    song_genre=metadata["genre"],
                    song_duration=metadata["duration"],
                    audio_path=metadata["file_path"],
                )
            )

        page.update()
        
    def populate_song_list_inside_artist(sorted_songs:dict):
        """Populates the song list with categorized songs by their starting letter."""
        nonlocal Artist_song_list_browser

        letter = "#"  # Initial category for non-alphabetic entries
        Artist_song_list_browser.controls.clear()

        for title, metadata in sorted_songs.items():
            # Determine the current song's starting letter
            current_letter = str(title)[0].upper()
            if not current_letter.isalpha():
                current_letter = "#"
                Artist_song_list_browser.controls.append(songs_letter_widget(current_letter))

            # Add a new letter widget if the starting letter changes
            if current_letter != letter:
                letter = current_letter
                Artist_song_list_browser.controls.append(songs_letter_widget(letter))

            # Add the song widget
            Artist_song_list_browser.controls.append(
                song_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    song_title=title,
                    artist_name=metadata["artist"],
                    album_name=metadata["album"],
                    year_released=metadata["year"],
                    song_genre=metadata["genre"],
                    song_duration=metadata["duration"],
                    audio_path=metadata["file_path"],
                )
            )

        page.update()
        
        
    def album_widget(thumbnail_path, artist_name, album_name,songs):
        nonlocal selected_album_box,sorted_songs  # To modify the selected_song_box variable
        thumbnail_path = thumbnail_path
        # Create a new container for the song
        album_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[ft.Image(
                        src=thumbnail_path if thumbnail_path else "default_thumbnail.jpg",
                        width=160,
                        height=160,
                        fit=ft.ImageFit.COVER,
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        border_radius=BORDER_RADIUS,
                                            )
                                     ],
                           alignment=ft.MainAxisAlignment.CENTER
                           ),
                    ft.Row(controls=[ft.Text(
                        album_name,
                        size=16,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                                            )
                                     ],
                           alignment=ft.MainAxisAlignment.CENTER
                           ),
                    ft.Row(controls=[ft.Text(
                        artist_name,
                        size=13,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                                            )
                                     ],
                           alignment=ft.MainAxisAlignment.CENTER
                           )
                    ,
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.padding.all(5),
            bgcolor=TRANSPARENT,
            border_radius=BORDER_RADIUS,
            width=200,
            height=220,
            margin=ft.margin.all(0),
            on_click=lambda e: go_to_album(album_name,artist_name,thumbnail_path,song_dict=sorted_songs,song_list=songs),
            expand=False

        )
        
        return album_box
    
    def artist_widget(thumbnail_path, artist_name,songs,albums):
        nonlocal selected_artist_box,sorted_songs  # To modify the selected_song_box variable
        thumbnail_path = thumbnail_path
        # Create a new container for the song
        artist_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[ft.Image(
                        src=thumbnail_path if thumbnail_path else "default_thumbnail.jpg",
                        width=160,
                        height=160,
                        fit=ft.ImageFit.COVER,
                        repeat=ft.ImageRepeat.NO_REPEAT,
                        border_radius=80,
                                            )
                                     ],
                           alignment=ft.MainAxisAlignment.CENTER
                           ),
                    ft.Row(controls=[ft.Text(
                        artist_name,
                        size=16,
                        weight=ft.FontWeight.W_300,
                        color=TEXT_COLOR,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=1,
                                            )
                                     ],
                           alignment=ft.MainAxisAlignment.CENTER
                           ),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            padding=ft.padding.all(0),
            bgcolor=TRANSPARENT,
            border_radius=BORDER_RADIUS,
            width=200,
            height=200,
            margin=ft.margin.all(0),
            on_click=lambda e: go_to_artist(artist_name=artist_name,thumbnail=thumbnail_path,song_dict=sorted_songs,song_list=songs,album_list=albums),
            expand=False

        )
        
        return artist_box
    
    def go_to_album(album_name,artist_name,thumbnail,song_dict,song_list):
        nonlocal album_isActive,primary_widget_text_container,secondary_widget_text_container,gesture_detector,album_is_visible,foreground_container_y_position
        slide_browsing_container.content = album_browsing_container
        primary_widget_text_container.value = album_name
        secondary_widget_text_container.value = artist_name
        if thumbnail:
            thumbnail_open_container.src = thumbnail
        else:
            thumbnail_open_container.src = "placeholder.png"
        foreground_container_y_position = 10
        slide_browsing_container.offset = ft.Offset(0,foreground_container_y_position / main_frame_height)
        album_isActive = True
        album_is_visible = True
        album_songs = filter_and_transform_dict(song_dict,song_list)
        sorted_songs_album = sort_songs_a_to_z(album_songs)
        populate_song_list_inside_album(sorted_songs_album)

    def go_to_artist(artist_name,thumbnail,song_dict,song_list,album_list):
        nonlocal album_isActive,primary_widget_text_container,secondary_widget_text_container,gesture_detector,album_is_visible,foreground_container_y_position,albums_sorted
        slide_browsing_container.content = artist_browsing_container
        primary_widget_text_container.value = artist_name
        if thumbnail:
            thumbnail_open_container.src = thumbnail
        else:
            thumbnail_open_container.src = "placeholder.png"
        foreground_container_y_position = 10
        slide_browsing_container.offset = ft.Offset(0,foreground_container_y_position / main_frame_height)
        album_isActive = True
        album_is_visible = True
        album_songs = filter_and_transform_dict(song_dict,song_list)
        sorted_songs_album = sort_songs_a_to_z(album_songs)
        populate_song_list_inside_artist(sorted_songs_album)
        albums_sorted_artist = {}
        for album, metadata in albums_sorted.items():
            if metadata["artist"] == artist_name:
                albums_sorted_artist[album] = metadata
                
        populate_album_list_in_artist_albums(albums_sorted_artist)


    def populate_album_list(sorted_albums: dict):
        """Populates the album list with categorized albums by their starting letter, organizing them into rows with a maximum of 6 albums per row."""
        nonlocal Album_List

        letter = "#"  # Initial category for numbers and symbols
        current_column = None
        current_row = None

        for album_name, metadata in sorted_albums.items():
            # Determine the current album's starting letter
            if album_name is None or not album_name.strip():
                album_name = "Unknown Album"
            current_letter = str(album_name)[0].upper()
            if not current_letter.isalpha():
                if current_letter.isnumeric():
                    current_letter = "#"
                else:
                    current_letter = "&"

            # Add a new letter widget and start a new column if the starting letter changes
            if current_letter != letter:
                # Check if there were albums under the previous letter
                if current_column and len(current_column.controls) > 0:
                    Album_List.controls.append(songs_letter_widget(letter))
                    Album_List.controls.append(current_column)

                # Reset for the new letter
                letter = current_letter
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_row = None  # Reset current row for the new letter

            # Ensure current_column is initialized
            if not current_column:
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)

            # Start a new row if none exists or the current row is full
            if not current_row or len(current_row.controls) >= 6:
                current_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_column.controls.append(current_row)

            # Add the album widget to the current row
            current_row.controls.append(
                album_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    artist_name=metadata["artist"],
                    album_name=album_name,
                    songs=metadata["songs"],
                )
            )

        # Append the final column if it has content
        if current_column and len(current_column.controls) > 0:
            Album_List.controls.append(songs_letter_widget(letter))
            Album_List.controls.append(current_column)

        page.update()
        
    def populate_album_list_in_artist_albums(sorted_albums: dict):
        """Populates the album list with categorized albums by their starting letter, organizing them into rows with a maximum of 6 albums per row."""
        nonlocal Artist_album_list_browser

        Artist_album_list_browser.controls.clear()
        
        letter = "#"  # Initial category for numbers and symbols
        current_column = None
        current_row = None

        for album_name, metadata in sorted_albums.items():
            # Determine the current album's starting letter
            if album_name is None or not album_name.strip():
                album_name = "Unknown Album"
            current_letter = str(album_name)[0].upper()
            if not current_letter.isalpha():
                if current_letter.isnumeric():
                    current_letter = "#"
                else:
                    current_letter = "&"

            # Add a new letter widget and start a new column if the starting letter changes
            if current_letter != letter:
                # Check if there were albums under the previous letter
                if current_column and len(current_column.controls) > 0:
                    Artist_album_list_browser.controls.append(songs_letter_widget(letter))
                    Artist_album_list_browser.controls.append(current_column)

                # Reset for the new letter
                letter = current_letter
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_row = None  # Reset current row for the new letter

            # Ensure current_column is initialized
            if not current_column:
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)

            # Start a new row if none exists or the current row is full
            if not current_row or len(current_row.controls) >= 6:
                current_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_column.controls.append(current_row)

            # Add the album widget to the current row
            current_row.controls.append(
                album_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    artist_name=metadata["artist"],
                    album_name=album_name,
                    songs=metadata["songs"],
                )
            )

        # Append the final column if it has content
        if current_column and len(current_column.controls) > 0:
            Artist_album_list_browser.controls.append(songs_letter_widget(letter))
            Artist_album_list_browser.controls.append(current_column)

        page.update()
        
        
        
    def populate_artist_list(sorted_artist: dict):
        """Populates the album list with categorized albums by their starting letter, organizing them into rows with a maximum of 6 albums per row."""
        nonlocal Artist_List

        letter = "#"  # Initial category for numbers and symbols
        current_column = None
        current_row = None

        for artist_name, metadata in sorted_artist.items():
            # Determine the current album's starting letter
            if artist_name is None or not artist_name.strip():
                artist_name = "Unknown Album"
            current_letter = str(artist_name)[0].upper()
            if not current_letter.isalpha():
                if current_letter.isnumeric():
                    current_letter = "#"
                else:
                    current_letter = "&"

            # Add a new letter widget and start a new column if the starting letter changes
            if current_letter != letter:
                # Check if there were albums under the previous letter
                if current_column and len(current_column.controls) > 0:
                    Artist_List.controls.append(songs_letter_widget(letter))
                    Artist_List.controls.append(current_column)

                # Reset for the new letter
                letter = current_letter
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_row = None  # Reset current row for the new letter

            # Ensure current_column is initialized
            if not current_column:
                current_column = ft.Column(spacing=10, alignment=ft.MainAxisAlignment.START)

            # Start a new row if none exists or the current row is full
            if not current_row or len(current_row.controls) >= 6:
                current_row = ft.Row(spacing=10, alignment=ft.MainAxisAlignment.START)
                current_column.controls.append(current_row)
                
            try:
                artist_data = fetch_and_save_artist_info(artist_name)
                thumbnail_path = artist_data["thumbnail_path"]
                spotify_url = artist_data["spotify_url"]

                print(f"Spotify URL: {spotify_url}")
                print(f"Thumbnail saved at: {thumbnail_path}")
            except Exception as e:
                print(f"Error: {str(e)}")

            # Add the album widget to the current row
            current_row.controls.append(
                artist_widget(
                    thumbnail_path=metadata["thumbnail_path"],
                    artist_name=artist_name,
                    songs=metadata["songs"],
                    albums=metadata["albums"],
                )
            )

        # Append the final column if it has content
        if current_column and len(current_column.controls) > 0:
            Artist_List.controls.append(songs_letter_widget(letter))
            Artist_List.controls.append(current_column)

        page.update()

    def get_albums_sorted_from_songs(sorted_songs: dict):
        """Generates a dictionary of albums from the sorted songs dictionary.

        Args:
            sorted_songs (dict): A dictionary where keys are song titles and values are metadata dictionaries.

        Returns:
            dict: A dictionary where keys are album names, and values are dictionaries containing album details and a list of song titles.
        """
        albums_sorted = {}

        for song_title, metadata in sorted_songs.items():
            album_name = metadata.get("album", "Unknown Album")
            artist_name = metadata.get("artist", "Unknown Artist")
            thumbnail_path = metadata.get("thumbnail_path", "default_thumbnail.jpg")
            
            

            # Initialize the album entry if it doesn't exist
            if album_name not in albums_sorted:
                albums_sorted[album_name] = {
                    "artist": artist_name,
                    "thumbnail_path": thumbnail_path,
                    "songs": []
                }

            # Append the song title to the album
            albums_sorted[album_name]["songs"].append(song_title)

        return albums_sorted
    
    def fetch_and_save_artist_info_threaded(artist_name, callback):
        """
        Fetches artist info, caches the thumbnail, and updates the configuration file in a separate thread.

        Args:
            artist_name (str): The name of the artist.
            callback (function): A callback function to process the artist info once fetched.
        """
        def fetch_task():
            try:
                artist_data = fetch_and_save_artist_info(artist_name)
                callback(artist_name, artist_data)
                page.update()
            except Exception as e:
                print(f"Error fetching artist info for {artist_name}: {str(e)}")

        thread = threading.Thread(target=fetch_task)
        thread.start()

    
    def get_artists_sorted_from_songs(sorted_songs: dict):
        """
        Generates a dictionary of artists from the sorted songs dictionary.

        Args:
            sorted_songs (dict): A dictionary where keys are song titles and values are metadata dictionaries.

        Returns:
            dict: A dictionary where keys are artist names, and values are dictionaries containing artist details and a list of song titles.
        """
        artists_sorted = {}

        def on_artist_info_fetched(artist_name, artist_data):
            """
            Callback function to handle artist data fetched in a thread.

            Args:
                artist_name (str): The name of the artist.
                artist_data (dict): The artist data fetched.
            """
            if artist_name not in artists_sorted:
                artists_sorted[artist_name] = {
                    "albums": {},
                    "thumbnail_path": artist_data["thumbnail_path"],
                    "songs": [],
                    "spotify": artist_data["spotify_url"],
                }

            # Populate the sorted songs and albums
            for song_title, metadata in sorted_songs.items():
                if metadata.get("artist") == artist_name:
                    album_name = metadata.get("album", "Unknown Album")

                    # Initialize the album entry under the artist if it doesn't exist
                    if album_name not in artists_sorted[artist_name]["albums"]:
                        artists_sorted[artist_name]["albums"][album_name] = []

                    # Append the song title to the album under the artist
                    artists_sorted[artist_name]["albums"][album_name].append(song_title)
                    artists_sorted[artist_name]["songs"].append(song_title)

        for song_title, metadata in sorted_songs.items():
            artist_name = metadata.get("artist", "Unknown Artist")

            # Fetch artist info in a thread
            fetch_and_save_artist_info_threaded(artist_name, on_artist_info_fetched)

        return artists_sorted


    
    
    #------------------ event handler ----------------------

    repeat_song_button.on_click = lambda e: toggle_repeat(e)
    shuffle_song_button.on_click = lambda e: toggle_shuffle(e)
    play_song_button.on_click = lambda e: pause_resume_action(e)
    
    initialize_config()
    
    # Clear expired cache at the start
    clear_expired_cache()
    
    
    # Load and sort songs
    songs = load_songs_to_dict()
    sorted_songs = sort_songs_a_to_z(songs)
    
    populate_song_list(sorted_songs)
    
    albums = get_albums_sorted_from_songs(sorted_songs)
    albums_sorted = sort_songs_a_to_z(albums)
    
    populate_album_list(albums_sorted)
    
    artists = get_artists_sorted_from_songs(sorted_songs)
    artists_sorted = sort_songs_a_to_z(artists)
    
    populate_artist_list(artists_sorted)
    
    
    
    # Layout
    layout = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Container(
                                                bgcolor=TRANSPARENT,
                                                height=40,
                                                expand=1,
                                                border_radius=BORDER_RADIUS
                                                ),

                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[ft.Container(width=15),
                                                        ft.Icon(name=ft.icons.HOME_FILLED, color=TEXT_COLOR, size=16,),
                                                        ft.Text("Home", size=16,weight=ft.FontWeight.W_600, color=TEXT_COLOR,text_align=ft.TextAlign.LEFT),
                                                        ],
                                                    alignment=ft.MainAxisAlignment.START,
                                                    spacing=2,
                                                    ),
                                                bgcolor=PRIMARY_COLOR,
                                                height=40,
                                                expand=1,
                                                border_radius=BORDER_RADIUS
                                                ),
                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[ft.Container(width=15),
                                                        ft.Icon(name=ft.icons.MUSIC_NOTE_SHARP, color=TEXT_COLOR, size=16,),
                                                        ft.Text("Music Library", size=16,weight=ft.FontWeight.W_600, color=TEXT_COLOR,text_align=ft.TextAlign.LEFT),
                                                        ],
                                                    alignment=ft.MainAxisAlignment.START,
                                                    spacing=2,
                                                    ),
                                                bgcolor=PRIMARY_COLOR,
                                                height=40,
                                                expand=1,
                                                border_radius=BORDER_RADIUS
                                                ),
                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[ft.Container(width=15),
                                                        ft.Icon(name=ft.icons.PLAYLIST_PLAY_SHARP, color=TEXT_COLOR, size=16,),
                                                        ft.Text("Play Lists", size=16,weight=ft.FontWeight.W_600, color=TEXT_COLOR,text_align=ft.TextAlign.LEFT),
                                                        ],
                                                    alignment=ft.MainAxisAlignment.START,
                                                    spacing=2,
                                                    ),
                                                bgcolor=PRIMARY_COLOR,
                                                height=40,
                                                expand=1,
                                                border_radius=BORDER_RADIUS
                                                ),
                                        ],
                                    ),
                                    ft.Container(
                                        expand=True,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                content=ft.Row(
                                                    controls=[ft.Container(width=15),
                                                        ft.Icon(name=ft.icons.SETTINGS_SHARP, color=TEXT_COLOR, size=16,),
                                                        ft.Text("Setting", size=16,weight=ft.FontWeight.W_600, color=TEXT_COLOR,text_align=ft.TextAlign.LEFT),
                                                        ],
                                                    alignment=ft.MainAxisAlignment.START,
                                                    spacing=5,
                                                    ),
                                                bgcolor=PRIMARY_COLOR,
                                                height=40,
                                                expand=1,
                                                border_radius=BORDER_RADIUS
                                                ),
                                        ],
                                    )
                                    
                                    ],
                                ),
                            bgcolor=TRANSPARENT,
                            padding=ft.padding.only(0,10,10,10),
                            height=300,
                            alignment=ft.alignment.center,
                        ),
                        bgcolor=TRANSPARENT,
                        expand=1,
                        height=main_frame_height,
                        
                    ),
                    
                    #------------------------------------------------------------------------------------
                    right_main_container,

                ]
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                duration_passed_widget,
                                time_line_slider,
                                duration_left_widget,
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        current_thumbnail_widget,
                                        ft.Column(
                                            controls=[
                                                current_song_title_widget,
                                                current_song_artist_widget,
                                            ],
                                            spacing=5,
                                            alignment=ft.MainAxisAlignment.CENTER
                                        )
                                    ],
                                    alignment=ft.MainAxisAlignment.START,
                                    expand=1,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=shuffle_song_button,
                                            width=50,
                                            height=50,
                                            border_radius=25,
                                            padding=ft.padding.all(0),
                                        ),
                                        ft.Container(
                                            content=ft.IconButton(icon=previous_song, icon_color=TEXT_COLOR, icon_size=18,on_click=lambda e: previous_song_action(e)),
                                            width=50,
                                            height=50,
                                            border_radius=25,
                                            padding=ft.padding.all(0),
                                            
                                        ),
                                        ft.Container(
                                            content=play_song_button,
                                            width=60,
                                            height=60,
                                            border_radius=30,  # Corrected to 30 for a perfect circle
                                            padding=ft.padding.all(0),
                                        ),
                                        ft.Container(
                                            content=ft.IconButton(icon=next_song, icon_color=TEXT_COLOR, icon_size=18,on_click=lambda e: next_song_action(e)),
                                            width=50,
                                            height=50,
                                            border_radius=25,
                                            padding=ft.padding.all(0),
                                            
                                        ),
                                        ft.Container(
                                            content=repeat_song_button,
                                            width=50,
                                            height=50,
                                            border_radius=25,
                                            padding=ft.padding.all(0),
                                        ),
                                    ],
                                    spacing=10,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    expand=1,
                                ),
                                ft.Row(
                                    controls=[
                                        
                                        ft.Stack(
                                            controls=[
                                                volume_dropdown,
                                                #ft.Container(width=25),
                                                ft.IconButton(
                                                icon=volume_control_icon,
                                                icon_color=TEXT_COLOR,
                                                icon_size=18,
                                                on_click=lambda e:toggle_dropdown(e),
                                                ),
                                                      ],
                                            alignment=ft.alignment.center_right
                                            
                                        ),
                                    ],
                                    spacing=10,
                                    alignment=ft.MainAxisAlignment.END,
                                    expand=1,
                                ),
                            ],
                            spacing=10,
                            alignment=ft.MainAxisAlignment.CENTER
                        )
                    ]
                ),
                bgcolor=PRIMARY_COLOR,
                expand=1,
                height=150,
                border_radius=BORDER_RADIUS,
                padding=ft.padding.only(15,0,15,0),
            ),
            audio,
        ],
    )

    page.add(layout)
    
    # Media key listener
    def listen_for_media_keys():
        

        def on_press(key):
            nonlocal press_times,is_double_tap_handled

            try:
                if key == keyboard.Key.media_play_pause:
                    # Record the current time
                    current_time = time.time()
                    press_times.append(current_time)

                    # Remove timestamps older than 2 seconds
                    press_times = [t for t in press_times if current_time - t < 2]

                    if len(press_times) == 1:
                        pause_resume_action()  # Single press: Play/Pause

                    elif len(press_times) == 2:
                        if not is_double_tap_handled:
                            is_double_tap_handled = True

                            # Wait 1 second to see if a third tap occurs
                            def handle_double_tap():
                                nonlocal is_double_tap_handled
                                time.sleep(1)  # Wait for potential triple tap
                                if len(press_times) == 2:  # No third tap detected
                                    next_song_action()  # Execute double-tap action
                                press_times.clear()  # Clear after handling
                                
                                is_double_tap_handled = False

                            threading.Thread(target=handle_double_tap, daemon=True).start()

                    elif len(press_times) == 3:
                        previous_song_action()  # Triple press: Previous Track
                        press_times.clear()  # Clear after detecting triple press
                        is_double_tap_handled = False  # Reset the double-tap flag

            except AttributeError:
                pass

        # Start the listener
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    # Run media key listener in a separate thread
    threading.Thread(target=listen_for_media_keys, daemon=True).start()


if __name__ == '__main__':
    
    ft.app(target=main)
