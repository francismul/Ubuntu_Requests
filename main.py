from kivy.lang import Builder
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import mainthread
from kivy.uix.modalview import ModalView

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDFloatingActionButton, MDRaisedButton
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.fitimage import FitImage
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout

import os
import threading
import requests
import random
import string


KV = """
<DynamicBackground@FitImage>:
    source: app.bg_image if app.bg_image else ""
    size_hint: (1, 1)
"""


class DynamicBackground(FitImage):
    pass


class GalleryCard(MDCard):
    def __init__(self, image_path, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.app_instance = app_instance
        self.md_bg_color = (46/255, 46/255, 62/255, 1)
        self.elevation = 3
        self.size_hint_y = None
        self.height = dp(150)
        self.radius = [15]
        self.ripple_behavior = True

        layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Image container with overlay
        image_container = MDBoxLayout(orientation='vertical', size_hint_y=0.8)

        img = FitImage(
            source=image_path,
            size_hint=(1, 1)
        )
        image_container.add_widget(img)

        # Wisdom text overlay
        wisdom_label = MDLabel(
            text=self.app_instance.get_random_ubuntu_wisdom(),
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Caption",
            size_hint=(1, None),
            height=dp(30),
            bold=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        image_container.add_widget(wisdom_label)

        layout.add_widget(image_container)

        # Filename label
        filename = os.path.basename(image_path)
        if len(filename) > 20:
            filename = filename[:17] + "..."

        label = MDLabel(
            text=filename,
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Caption",
            size_hint_y=0.2
        )
        layout.add_widget(label)

        self.add_widget(layout)
        self.bind(on_release=self.open_single_view)

    def open_single_view(self, *args):
        self.app_instance.open_single_photo_view(self.image_path)


class SinglePhotoView(MDScreen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.name = "single_photo"
        self.app_instance = app_instance
        self.current_image_path = None

        # Background
        self.bg = DynamicBackground()
        self.add_widget(self.bg)

        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')

        # Top bar
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            padding=dp(10)
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.go_back
        )
        top_bar.add_widget(back_btn)

        title_label = MDLabel(
            text="Ubuntu Community View",
            theme_text_color="Custom",
            text_color="#FF6B35",
            halign="center",
            font_style="H6"
        )
        top_bar.add_widget(title_label)

        top_bar.add_widget(MDBoxLayout())  # spacer

        main_layout.add_widget(top_bar)

        # Image container
        self.image_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=0.7,
            padding=dp(10)
        )

        # Image with overlay container
        image_overlay_container = MDBoxLayout(
            orientation='vertical', size_hint=(1, 0.9))

        self.image_widget = FitImage(
            source="",
            size_hint=(1, 1)
        )
        image_overlay_container.add_widget(self.image_widget)

        # Ubuntu wisdom overlay
        self.wisdom_overlay = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="H6",
            size_hint=(1, None),
            height=dp(60),
            bold=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        image_overlay_container.add_widget(self.wisdom_overlay)

        self.image_container.add_widget(image_overlay_container)

        # Navigation buttons
        nav_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            spacing=dp(20)
        )

        self.prev_btn = MDIconButton(
            icon="chevron-left",
            theme_icon_color="Custom",
            icon_color="#FF6B35",
            size_hint_x=0.4,
            on_release=self.show_previous
        )
        nav_layout.add_widget(self.prev_btn)

        nav_layout.add_widget(MDBoxLayout(size_hint_x=0.2))  # spacer

        self.next_btn = MDIconButton(
            icon="chevron-right",
            theme_icon_color="Custom",
            icon_color="#FF6B35",
            size_hint_x=0.4,
            on_release=self.show_next
        )
        nav_layout.add_widget(self.next_btn)

        self.image_container.add_widget(nav_layout)
        main_layout.add_widget(self.image_container)

        # Quote section
        quote_label = MDLabel(
            text=self.app_instance.get_random_ubuntu_wisdom(),
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Body2",
            size_hint_y=None,
            height=dp(60)
        )
        main_layout.add_widget(quote_label)

        self.add_widget(main_layout)

    def set_image(self, image_path):
        self.current_image_path = image_path
        self.image_widget.source = image_path
        # Update wisdom overlay with new random quote
        self.wisdom_overlay.text = self.app_instance.get_random_ubuntu_wisdom()
        self.update_navigation_buttons()

    def update_navigation_buttons(self):
        if self.current_image_path and self.app_instance.save_directory:
            image_files = [f for f in os.listdir(self.app_instance.save_directory)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            image_files.sort()

            try:
                current_index = image_files.index(
                    os.path.basename(self.current_image_path))
                self.prev_btn.disabled = current_index == 0
                self.next_btn.disabled = current_index == len(image_files) - 1
            except ValueError:
                self.prev_btn.disabled = True
                self.next_btn.disabled = True

    def show_next(self, *args):
        if self.current_image_path and self.app_instance.save_directory:
            image_files = [f for f in os.listdir(self.app_instance.save_directory)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            image_files.sort()

            try:
                current_index = image_files.index(
                    os.path.basename(self.current_image_path))
                if current_index < len(image_files) - 1:
                    next_image = os.path.join(
                        self.app_instance.save_directory, image_files[current_index + 1])
                    self.set_image(next_image)
            except ValueError:
                pass

    def show_previous(self, *args):
        if self.current_image_path and self.app_instance.save_directory:
            image_files = [f for f in os.listdir(self.app_instance.save_directory)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
            image_files.sort()

            try:
                current_index = image_files.index(
                    os.path.basename(self.current_image_path))
                if current_index > 0:
                    prev_image = os.path.join(
                        self.app_instance.save_directory, image_files[current_index - 1])
                    self.set_image(prev_image)
            except ValueError:
                pass

    def go_back(self, *args):
        self.app_instance.screen_manager.current = "gallery"


class GalleryScreen(MDScreen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.name = "gallery"
        self.app_instance = app_instance

        # Background
        self.bg = DynamicBackground()
        self.add_widget(self.bg)

        # Main layout
        main_layout = MDBoxLayout(orientation='vertical')

        # Top bar
        top_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            padding=dp(10)
        )

        back_btn = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.go_back
        )
        top_bar.add_widget(back_btn)

        title_label = MDLabel(
            text="Ubuntu Community Gallery",
            theme_text_color="Custom",
            text_color="#FF6B35",
            halign="center",
            font_style="H6"
        )
        top_bar.add_widget(title_label)

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.refresh_gallery
        )
        top_bar.add_widget(refresh_btn)

        main_layout.add_widget(top_bar)

        # Gallery grid
        self.scroll = MDScrollView()
        self.gallery_layout = MDGridLayout(
            cols=2,
            spacing=dp(10),
            padding=dp(15),
            adaptive_height=True
        )
        self.scroll.add_widget(self.gallery_layout)
        main_layout.add_widget(self.scroll)

        self.add_widget(main_layout)
        # Don't refresh gallery immediately to avoid errors
        # self.refresh_gallery()

    def refresh_gallery(self, *args):
        self.gallery_layout.clear_widgets()

        if not self.app_instance.save_directory or not os.path.exists(self.app_instance.save_directory):
            empty_label = MDLabel(
                text="📁 No community images yet\nShare some images to build our collection!",
                theme_text_color="Custom",
                text_color="#FFFFFF",
                halign="center",
                font_style="Body1"
            )
            self.gallery_layout.add_widget(empty_label)
            return

        image_files = [f for f in os.listdir(self.app_instance.save_directory)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]

        if not image_files:
            empty_label = MDLabel(
                text="📁 Gallery is empty\nAdd some images to get started!",
                theme_text_color="Custom",
                text_color="#FFFFFF",
                halign="center",
                font_style="Body1"
            )
            self.gallery_layout.add_widget(empty_label)
            return

        image_files.sort(reverse=True)  # Show newest first

        for filename in image_files:
            image_path = os.path.join(
                self.app_instance.save_directory, filename)
            card = GalleryCard(image_path, self.app_instance)
            self.gallery_layout.add_widget(card)

    def go_back(self, *args):
        self.app_instance.screen_manager.current = "main"


class MainScreen(MDScreen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.name = "main"
        self.app_instance = app_instance

        # Background
        self.bg = DynamicBackground()
        self.add_widget(self.bg)

        # Layout
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(15),
            padding=dp(15)
        )

        # Header
        header_label = MDLabel(
            text="Ubuntu Image Fetcher",
            theme_text_color="Custom",
            text_color="#FF6B35",
            halign="center",
            font_style="H5",
            size_hint_y=None,
            height=dp(30)
        )
        subtitle_label = MDLabel(
            text="\"I am because we are\"",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Body2",
            size_hint_y=None,
            height=dp(20)
        )
        main_layout.add_widget(header_label)
        main_layout.add_widget(subtitle_label)

        # URL input container
        url_container = MDCard(
            md_bg_color=(46/255, 46/255, 62/255, 1),
            elevation=3,
            radius=[20],
            size_hint_y=None,
            height=dp(60),
            padding=dp(15)
        )
        url_layout = MDBoxLayout(orientation='horizontal', spacing=dp(10))

        self.url_field = MDTextField(
            hint_text="Share image URL with community...",
            mode="fill",
            size_hint_x=0.85,
            font_size=dp(16),
            multiline=False
        )
        self.url_field.bind(on_text_validate=self.fetch_image)

        search_btn = MDIconButton(
            icon="magnify",
            theme_icon_color="Custom",
            icon_color="#FF6B35",
            size_hint_x=0.15,
            on_release=lambda x: self.fetch_image()
        )

        url_layout.add_widget(self.url_field)
        url_layout.add_widget(search_btn)
        url_container.add_widget(url_layout)
        main_layout.add_widget(url_container)

        # Progress section
        self.progress_bar = MDProgressBar(
            size_hint_y=None,
            height=dp(6),
            opacity=0,
            color="#FF6B35"
        )
        self.status_label = MDLabel(
            text="Ready to connect with community",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Body2",
            size_hint_y=None,
            height=dp(30)
        )
        main_layout.add_widget(self.progress_bar)
        main_layout.add_widget(self.status_label)

        # Stats
        self.stats_label = MDLabel(
            text="Community Images: 0\nShared Resources: 0 MB",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Body2",
            size_hint_y=None,
            height=dp(60)
        )
        main_layout.add_widget(self.stats_label)

        main_layout.add_widget(MDBoxLayout())  # spacer
        self.add_widget(main_layout)

        # Floating folder FAB
        self.folder_btn = MDFloatingActionButton(
            icon="folder-multiple-image",
            md_bg_color="#FF6B35",
            pos_hint={"right": 0.95, "y": 0.05},
            on_release=self.app_instance.open_gallery
        )
        self.add_widget(self.folder_btn)

    def fetch_image(self, *args):
        url = self.url_field.text.strip()
        if not url:
            self.app_instance.show_error_dialog(
                "Ubuntu wisdom: Please share a meaningful URL with our community"
            )
            return

        # Basic client-side validation
        if len(url) < 10:
            self.app_instance.show_error_dialog(
                "URL seems too short. Please provide a complete image URL."
            )
            return

        if " " in url:
            self.app_instance.show_error_dialog(
                "URL contains spaces. Please provide a valid URL without spaces."
            )
            return

        # Reset UI state
        self._update_ui_state(loading=True)

        threading.Thread(target=self._validate_and_preview,
                         args=(url,), daemon=True).start()

    @mainthread
    def _update_ui_state(self, loading=False, error=None):
        """Update UI state from main thread"""
        if loading:
            Animation(opacity=1, duration=0.3).start(self.progress_bar)
            self.status_label.text = "🌐 Connecting with community resource..."
        else:
            Animation(opacity=0, duration=0.3).start(self.progress_bar)
            if error:
                self.status_label.text = f"❌ {error}"
            else:
                self.status_label.text = "Ready again"

    def _validate_and_preview(self, url):
        try:
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                raise ValueError(
                    "Invalid URL format - must start with http:// or https://")

            # Additional URL validation
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if not parsed.netloc:
                    raise ValueError("Invalid URL format - missing domain")
            except Exception:
                raise ValueError("Invalid URL format")

            # Make request with better error handling
            r = None
            try:
                r = requests.get(url, stream=True, timeout=15, headers={
                    'User-Agent': 'Ubuntu-Image-Fetcher/1.0'
                })
                r.raise_for_status()
            except requests.exceptions.Timeout:
                raise ValueError("Connection timed out - please try again")
            except requests.exceptions.ConnectionError:
                raise ValueError(
                    "Network connection failed - check your internet")
            except requests.exceptions.HTTPError as e:
                if r and hasattr(r, 'status_code'):
                    if r.status_code == 404:
                        raise ValueError(
                            "Image not found (404) - check the URL")
                    elif r.status_code == 403:
                        raise ValueError(
                            "Access forbidden (403) - image may be private")
                    elif r.status_code >= 500:
                        raise ValueError(
                            "Server error - please try again later")
                    else:
                        raise ValueError(f"HTTP error {r.status_code}")
                else:
                    raise ValueError("Failed to connect to server")

            # Check if we got a response
            if not r:
                raise ValueError("No response received from server")

            # Check content type
            content_type = r.headers.get("content-type", "").lower()
            if not content_type:
                raise ValueError("Could not determine content type")

            if "image" not in content_type:
                raise ValueError(
                    f"Not an image - detected type: {content_type}")

            # Check content length
            content_length = r.headers.get("content-length")
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > 100:  # 100MB limit
                    raise ValueError(
                        f"File too large: {size_mb:.1f} MB exceeds 100MB limit")

            # Success - show preview
            self._show_preview_success(url)

        except ValueError as e:
            # User-friendly error messages
            self._show_error(str(e))
        except Exception as e:
            # Generic error for unexpected issues
            self._show_error(f"Unexpected error: {str(e)}")

    @mainthread
    def _show_preview_success(self, url):
        """Show preview dialog on main thread"""
        self.app_instance.show_preview_dialog(url)
        self._update_ui_state(loading=False)

    @mainthread
    def _show_error(self, message):
        """Show error on main thread"""
        self.app_instance.show_error_dialog(message)
        self._update_ui_state(loading=False, error="Failed to load image")


class UbuntuImageFetcherApp(MDApp):
    bg_image = None
    save_dir = None

    # Ubuntu wisdom quotes for dynamic text overlays
    UBUNTU_WISDOM = [
        "I am because we are",
        "Community over competition",
        "Share knowledge, grow together",
        "Ubuntu: My humanity is bound up in yours",
        "Together we create, together we grow",
        "Respect guides our digital interactions",
        "Every connection enriches the collective",
        "Mindful consumption honors our shared resources",
        "Community strengthens our shared humanity",
        "In unity, we find our greatest strength",
        "Knowledge shared is knowledge multiplied",
        "Compassion creates lasting connections",
        "Wisdom flows from open hearts",
        "Together we build a better tomorrow",
        "Harmony begins with understanding"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.save_directory = self.get_save_directory()
        self.save_dir = self.save_directory  # Sync both attributes

    def get_random_ubuntu_wisdom(self):
        """Get a random Ubuntu wisdom quote"""
        return random.choice(self.UBUNTU_WISDOM)

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"

        Builder.load_string(KV)

        # Screen manager
        self.screen_manager = MDScreenManager()

        # Create screens
        self.main_screen = MainScreen(app_instance=self)
        self.gallery_screen = GalleryScreen(app_instance=self)
        self.single_photo_screen = SinglePhotoView(app_instance=self)

        # Add screens
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.gallery_screen)
        self.screen_manager.add_widget(self.single_photo_screen)

        # Initialize stats
        self.update_stats()

        return self.screen_manager

    def get_save_directory(self):
        # Try to load from config file
        config_file = "ubuntu_fetcher_config.json"
        if os.path.exists(config_file):
            try:
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if 'save_directory' in config and os.path.exists(config['save_directory']):
                        return config['save_directory']
            except:
                pass

        # Default to Fetched_Images folder
        default_dir = os.path.join(os.getcwd(), "Fetched_Images")
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
        return default_dir

    def show_error_dialog(self, message):
        """Show error dialog with proper reference handling"""
        if hasattr(self, '_current_dialog') and self._current_dialog:
            try:
                self._current_dialog.dismiss()
            except:
                pass

        self._current_dialog = MDDialog(
            title="Ubuntu Community",
            text=str(message),
            buttons=[MDRaisedButton(
                text="Close",
                on_release=self._close_error_dialog
            )]
        )
        self._current_dialog.open()

    def _close_error_dialog(self, *args):
        """Close the current error dialog"""
        if hasattr(self, '_current_dialog') and self._current_dialog:
            self._current_dialog.dismiss()
            self._current_dialog = None

    @mainthread
    def show_preview_dialog(self, url):
        # Background becomes the image
        self.bg_image = url
        self.main_screen.bg.source = url

        preview = ModalView(size_hint=(0.85, 0.6))
        box = MDBoxLayout(orientation="vertical",
                          spacing=dp(10), padding=dp(15))

        # Image container with overlay
        image_container = MDBoxLayout(
            orientation="vertical", size_hint=(1, 0.8))

        img = FitImage(source=url, size_hint=(1, 1))
        image_container.add_widget(img)

        # Ubuntu wisdom overlay on preview
        wisdom_label = MDLabel(
            text=self.get_random_ubuntu_wisdom(),
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="H6",
            size_hint=(1, None),
            height=dp(40),
            bold=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        image_container.add_widget(wisdom_label)

        box.add_widget(image_container)

        btns = MDBoxLayout(size_hint=(1, 0.2), spacing=dp(10))
        btns.add_widget(MDRaisedButton(
            text="Save", on_release=lambda x: self.save_image(url, preview)))
        btns.add_widget(MDRaisedButton(
            text="Discard", on_release=lambda x: self.discard_preview(preview)))
        box.add_widget(btns)

        preview.add_widget(box)
        preview.open()

    def discard_preview(self, preview):
        # Clear background image when discarding
        self.bg_image = None
        self.main_screen.bg.source = ""
        preview.dismiss()

    def save_image(self, url, popup):
        if not self.save_directory:
            self.ask_for_directory(url, popup)
        else:
            self._download_and_save(url, popup)

    def ask_for_directory(self, url, popup):
        # Use MDFileManager to pick a folder
        def select_path(path):
            if path and os.path.isdir(path):
                self.save_dir = path
                self.save_directory = path  # Sync both attributes
                # Save to config file
                try:
                    import json
                    config = {'save_directory': path}
                    with open("ubuntu_fetcher_config.json", 'w') as f:
                        json.dump(config, f)
                except:
                    pass
                self.file_manager.close()
                self._download_and_save(url, popup)
            else:
                self.show_error_dialog("❌ Invalid directory selected")

        self.file_manager = MDFileManager(
            select_path=select_path,
            exit_manager=lambda x: self._handle_file_manager_cancel(popup),
            preview=False
        )
        self.file_manager.show(os.path.expanduser("~"))  # start at home dir

    def _handle_file_manager_cancel(self, popup):
        self.file_manager.close()
        popup.dismiss()
        self.show_error_dialog("Directory selection cancelled")

    def _download_and_save(self, url, popup):
        if not self.save_directory:
            self.show_error_dialog("❌ No save directory selected")
            return

        try:
            r = requests.get(url, timeout=30)  # Add timeout
            r.raise_for_status()  # Raise exception for bad status codes

            # Ensure we have content
            if not r.content:
                raise ValueError("Empty response from server")

            # Get content type for proper extension
            content_type = r.headers.get("content-type", "").lower()

            # Sanitize filename from URL with content type info
            filename = self._sanitize_filename(url, content_type)
            filepath = os.path.join(self.save_directory, filename)

            with open(filepath, "wb") as f:
                f.write(r.content)

            # Verify file was written
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                raise ValueError("File was not saved properly")

            popup.dismiss()
            self.show_error_dialog(f"✅ Saved to community collection!")
            self.update_stats()
            # Clear the URL field
            self.main_screen.url_field.text = ""

        except requests.exceptions.Timeout:
            self.show_error_dialog("❌ Download timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            self.show_error_dialog(f"❌ Network error: {e}")
        except OSError as e:
            self.show_error_dialog(f"❌ File system error: {e}")
        except Exception as e:
            self.show_error_dialog(f"❌ Failed: {e}")

    def _sanitize_filename(self, url, content_type=""):
        """Generate Ubuntu-themed filename with random numbers"""
        # Generate random string of numbers (6-8 digits)
        random_numbers = ''.join(random.choices(
            string.digits, k=random.randint(6, 8)))

        # Get file extension from content type
        extension = self._get_extension_from_content_type(content_type)

        # Create Ubuntu-themed filename
        filename = f"ubuntu_image_{random_numbers}{extension}"

        return filename

    def _get_extension_from_content_type(self, content_type):
        """Get appropriate file extension from content type"""
        content_type = content_type.lower()

        if "jpeg" in content_type or "jpg" in content_type:
            return ".jpg"
        elif "png" in content_type:
            return ".png"
        elif "gif" in content_type:
            return ".gif"
        elif "webp" in content_type:
            return ".webp"
        elif "bmp" in content_type:
            return ".bmp"
        elif "svg" in content_type:
            return ".svg"
        else:
            # Default to jpg for unknown image types
            return ".jpg"

    def update_stats(self):
        if self.save_directory and os.path.exists(self.save_directory):
            image_files = [f for f in os.listdir(self.save_directory)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]

            total_size = 0
            for filename in image_files:
                filepath = os.path.join(self.save_directory, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass

            size_mb = total_size / (1024 * 1024)
            self.main_screen.stats_label.text = f"Community Images: {len(image_files)}\nShared Resources: {size_mb:.1f} MB"

    def open_gallery(self, *args):
        # Always refresh gallery when opening
        self.gallery_screen.refresh_gallery()
        self.screen_manager.current = "gallery"

    def open_single_photo_view(self, image_path):
        self.single_photo_screen.set_image(image_path)
        self.screen_manager.current = "single_photo"


if __name__ == "__main__":
    Window.size = (400, 700)
    UbuntuImageFetcherApp().run()
