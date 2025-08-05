import flet as ft

# I've assumed some of your constants. You can move them to a config file later.
TEXT_COLOR = ft.colors.WHITE
PRIMARY_COLOR = ft.colors.with_opacity(0.85, ft.colors.BLACK12) # Example color
BORDER_RADIUS = ft.border_radius.all(8)

class NavRail(ft.NavigationRail):
    def __init__(self, on_change_route):
        super().__init__(
            selected_index=0,
            min_width=100,
            min_extended_width=250,
            extended=True, # Shows labels next to icons
            bgcolor=ft.colors.TRANSPARENT,
            on_change=lambda e: on_change_route(e.control.selected_index)
        )

        # Define the navigation destinations
        self.destinations = [
            ft.NavigationRailDestination(
                icon=ft.icons.HOME_OUTLINED,
                selected_icon=ft.icons.HOME,
                label="Home",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.LIBRARY_MUSIC_OUTLINED,
                selected_icon=ft.icons.LIBRARY_MUSIC,
                label="Music Library",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.PLAYLIST_PLAY_OUTLINED,
                selected_icon=ft.icons.PLAYLIST_PLAY,
                label="Play Lists",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.SETTINGS_OUTLINED,
                selected_icon=ft.icons.SETTINGS,
                label="Settings",
            ),
        ]

    def set_selected_index(self, index):
        """Allows the main app to programmatically change the selected tab."""
        self.selected_index = index
        self.update()