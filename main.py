from kivy.lang import Builder
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import mainthread, Clock
from kivy.uix.image import AsyncImage
from kivy.uix.modalview import ModalView

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDFloatingActionButton, MDRaisedButton, MDFlatButton
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.fitimage import FitImage
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.recycleview import MDRecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivymd.uix.behaviors.focus_behavior import FocusBehavior
from kivymd.uix.behaviors.hover_behavior import HoverBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

import os
import threading
import requests
import random
import string
import platform
import concurrent.futures

try:
    from plyer import storagepath
except ImportError:
    storagepath = None

try:
    from PIL import Image as PILImage
except Exception:
    PILImage = None

KV = """
<DynamicBackground@FitImage>:
    source: app.bg_image if app.bg_image else ""
    size_hint: (1, 1)
"""


class DynamicBackground(FitImage):
    pass


class GalleryCard(MDCard):
    def __init__(self, image_path, app_instance, selection_mode=False, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.app_instance = app_instance
        self.md_bg_color = (46/255, 46/255, 62/255, 1)
        self.elevation = 3
        self.size_hint_y = None
        self.height = dp(150)
        self.radius = [15]
        self.ripple_behavior = True

        # Long press detection for Android
        self._touch_start_time = 0
        self._touch_start_pos = None
        self._long_press_threshold = 1.0  # 1 second
        self._touch_move_threshold = dp(20)  # 20dp movement threshold
        self._long_press_event = None

        layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Image container with overlay
        image_container = MDBoxLayout(orientation='vertical', size_hint_y=0.8)

        # Async image for non-blocking load (use thumbnail when available)
        self.img = AsyncImage(
            source="",
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
        )
        image_container.add_widget(self.img)

        # Checkbox for selection mode (hidden by default)
        self.checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"right": 1, "top": 1},
            opacity=0 if not selection_mode else 1,
        )
        self.checkbox.bind(active=self._on_checkbox_active)
        image_container.add_widget(self.checkbox)

        # Kick off thumbnail generation/loading
        self.app_instance.ensure_thumbnail(
            image_path, self._on_thumbnail_ready)

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

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Handle both desktop right-click and mobile long press
            if hasattr(touch, 'button') and touch.button == 'right':
                # Desktop right-click - enter selection mode immediately
                self.app_instance.gallery_screen.enter_selection_mode()
                return True
            elif touch.is_double_tap:
                # Double tap - enter selection mode immediately  
                self.app_instance.gallery_screen.enter_selection_mode()
                return True
            else:
                # Start long press detection for mobile
                import time
                self._touch_start_time = time.time()
                self._touch_start_pos = touch.pos
                
                # Schedule long press check
                if self._long_press_event:
                    self._long_press_event.cancel()
                self._long_press_event = Clock.schedule_once(
                    self._check_long_press, self._long_press_threshold
                )
                
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        # Cancel long press if touch moves too much
        if (self._touch_start_pos and 
            self.collide_point(*touch.pos) and
            self._long_press_event):
            
            # Calculate distance moved
            dx = abs(touch.x - self._touch_start_pos[0])
            dy = abs(touch.y - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > self._touch_move_threshold:
                # Moved too much, cancel long press
                self._cancel_long_press()
                
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        # Cancel long press when touch is released
        if self.collide_point(*touch.pos):
            self._cancel_long_press()
        return super().on_touch_up(touch)
    
    def _check_long_press(self, dt):
        """Called after long press threshold time has passed"""
        if self.app_instance:
            # Long press detected - enter selection mode
            self.app_instance.gallery_screen.enter_selection_mode()
        self._long_press_event = None
    
    def _cancel_long_press(self):
        """Cancel the long press detection"""
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        self._touch_start_time = 0
        self._touch_start_pos = None

    def _on_checkbox_active(self, checkbox, value):
        if value:
            self.app_instance.gallery_screen._selected_images.add(
                self.image_path)
        else:
            self.app_instance.gallery_screen._selected_images.discard(
                self.image_path)

    def open_single_view(self, *args):
        if self.app_instance.gallery_screen._selection_mode:
            # In selection mode, toggle checkbox instead of opening
            self.checkbox.active = not self.checkbox.active
        else:
            self.app_instance.open_single_photo_view(self.image_path)

    @mainthread
    def _on_thumbnail_ready(self, thumb_path: str):
        # Update image source on main thread
        if thumb_path and os.path.exists(thumb_path):
            self.img.source = thumb_path
        else:
            # Fallback to original if thumbnail missing
            self.img.source = self.image_path

    def show_checkbox(self):
        self.checkbox.opacity = 1

    def hide_checkbox(self):
        self.checkbox.opacity = 0
        self.checkbox.active = False


class RecycleGalleryCard(RecycleDataViewBehavior, MDCard, FocusBehavior, HoverBehavior):
    """Efficient recyclable gallery card for RecycleView"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = (46/255, 46/255, 62/255, 1)
        self.elevation = 3
        self.size_hint_y = None
        self.height = dp(150)
        self.radius = [15]
        self.ripple_behavior = True
        
        # Initialize empty state
        self.image_path = ""
        self.app_instance = None
        self._thumbnail_loaded = False
        self._is_empty_state = False
        
        # Long press detection for Android
        self._touch_start_time = 0
        self._touch_start_pos = None
        self._long_press_threshold = 1.0  # 1 second
        self._touch_move_threshold = dp(20)  # 20dp movement threshold
        self._long_press_event = None
        
        # Build UI once
        self._build_ui()
    
    def _build_ui(self):
        """Build UI components once - they will be reused"""
        layout = MDBoxLayout(orientation='vertical', spacing=0)

        # Image container with overlay
        image_container = MDBoxLayout(orientation='vertical', size_hint_y=0.8)

        # Image for displaying thumbnails/images
        self.img = FitImage(
            source="",
            size_hint=(1, 1),
        )
        image_container.add_widget(self.img)

        # Checkbox for selection mode (hidden by default)
        self.checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(24), dp(24)),
            pos_hint={"right": 1, "top": 1},
            opacity=0,
        )
        self.checkbox.bind(active=self._on_checkbox_active)
        image_container.add_widget(self.checkbox)

        # Wisdom text overlay
        self.wisdom_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Caption",
            size_hint=(1, None),
            height=dp(30),
            bold=True,
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        image_container.add_widget(self.wisdom_label)

        layout.add_widget(image_container)

        # Filename label (doubles as empty state message)
        self.filename_label = MDLabel(
            text="",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Caption",
            size_hint_y=0.2
        )
        layout.add_widget(self.filename_label)

        self.add_widget(layout)
        self.bind(on_release=self.open_single_view)

    def refresh_view_attrs(self, rv, index, data):
        """Called when RecycleView assigns new data to this card"""
        # Update data
        self.image_path = data.get('image_path', '')
        self.app_instance = data.get('app_instance')
        selection_mode = data.get('selection_mode', False)
        self._is_empty_state = data.get('is_empty_state', False)
        
        # Reset thumbnail loaded state
        self._thumbnail_loaded = False
        
        # Handle empty state
        if self._is_empty_state:
            self._setup_empty_state()
            return super().refresh_view_attrs(rv, index, data)
        
        # Update filename
        if self.image_path:
            filename = os.path.basename(self.image_path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            self.filename_label.text = filename
        else:
            self.filename_label.text = ""
        
        # Update wisdom text
        if self.app_instance:
            self.wisdom_label.text = self.app_instance.get_random_ubuntu_wisdom()
        else:
            self.wisdom_label.text = ""
        
        # Update selection mode
        if selection_mode:
            self.checkbox.opacity = 1
        else:
            self.checkbox.opacity = 0
            self.checkbox.active = False
        
        # Load thumbnail lazily (only if not already loaded)
        if self.image_path and self.app_instance and not self._thumbnail_loaded:
            self._thumbnail_loaded = True
            # Reset image first
            self.img.source = ""
            # Then load thumbnail
            self.app_instance.ensure_thumbnail(self.image_path, self._on_thumbnail_ready)
        
        return super().refresh_view_attrs(rv, index, data)

    def _setup_empty_state(self):
        """Setup card for empty state display"""
        # Clear image
        self.img.source = ""
        # Hide checkbox
        self.checkbox.opacity = 0
        # Set empty state messages
        save_dir = self.app_instance.save_directory if self.app_instance else None
        if not save_dir or not os.path.exists(save_dir):
            self.wisdom_label.text = "📁 No community images yet"
            self.filename_label.text = "Share some images to build our collection!"
        else:
            self.wisdom_label.text = "📁 Gallery is empty"
            self.filename_label.text = "Add some images to get started!"
        
        # Disable interaction for empty state
        self.ripple_behavior = False

    def on_touch_down(self, touch):
        if self._is_empty_state:
            return False  # Don't handle touches in empty state
            
        if self.collide_point(*touch.pos):
            # Handle both desktop right-click and mobile long press
            if hasattr(touch, 'button') and touch.button == 'right':
                # Desktop right-click - enter selection mode immediately
                if self.app_instance:
                    self.app_instance.gallery_screen.enter_selection_mode()
                return True
            elif touch.is_double_tap:
                # Double tap - enter selection mode immediately  
                if self.app_instance:
                    self.app_instance.gallery_screen.enter_selection_mode()
                return True
            else:
                # Start long press detection for mobile
                import time
                self._touch_start_time = time.time()
                self._touch_start_pos = touch.pos
                
                # Schedule long press check
                if self._long_press_event:
                    self._long_press_event.cancel()
                self._long_press_event = Clock.schedule_once(
                    self._check_long_press, self._long_press_threshold
                )
                
        return super().on_touch_down(touch)
    
    def on_touch_move(self, touch):
        # Cancel long press if touch moves too much
        if (self._touch_start_pos and 
            self.collide_point(*touch.pos) and
            self._long_press_event):
            
            # Calculate distance moved
            dx = abs(touch.x - self._touch_start_pos[0])
            dy = abs(touch.y - self._touch_start_pos[1])
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > self._touch_move_threshold:
                # Moved too much, cancel long press
                self._cancel_long_press()
                
        return super().on_touch_move(touch)
    
    def on_touch_up(self, touch):
        # Cancel long press when touch is released
        if self.collide_point(*touch.pos):
            self._cancel_long_press()
        return super().on_touch_up(touch)
    
    def _check_long_press(self, dt):
        """Called after long press threshold time has passed"""
        if self.app_instance and not self._is_empty_state:
            # Long press detected - enter selection mode
            self.app_instance.gallery_screen.enter_selection_mode()
        self._long_press_event = None
    
    def _cancel_long_press(self):
        """Cancel the long press detection"""
        if self._long_press_event:
            self._long_press_event.cancel()
            self._long_press_event = None
        self._touch_start_time = 0
        self._touch_start_pos = None

    def _on_checkbox_active(self, checkbox, value):
        if self._is_empty_state:
            return
            
        if self.app_instance and self.image_path:
            if value:
                self.app_instance.gallery_screen._selected_images.add(self.image_path)
            else:
                self.app_instance.gallery_screen._selected_images.discard(self.image_path)

    def open_single_view(self, *args):
        if self._is_empty_state:
            return  # Don't open anything for empty state
            
        if self.app_instance and self.image_path:
            if self.app_instance.gallery_screen._selection_mode:
                # In selection mode, toggle checkbox instead of opening
                self.checkbox.active = not self.checkbox.active
            else:
                self.app_instance.open_single_photo_view(self.image_path)

    @mainthread
    def _on_thumbnail_ready(self, thumb_path: str):
        """Update image source on main thread"""
        if self._is_empty_state:
            return  # Don't load images for empty state
            
        if thumb_path and os.path.exists(thumb_path):
            self.img.source = thumb_path
        elif self.image_path:
            # Fallback to original if thumbnail missing
            self.img.source = self.image_path


class SinglePhotoView(MDScreen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.name = "single_photo"
        self.app_instance = app_instance
        self.current_image_path = None
        # swipe detection
        self._touch_start_x = None
        self._touch_start_y = None
        self._swipe_threshold = dp(60)  # min pixels for horizontal swipe

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

    # --- Swipe gesture handling ---
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_start_x, self._touch_start_y = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        try:
            if self._touch_start_x is not None and self.collide_point(*touch.pos):
                dx = touch.x - self._touch_start_x
                dy = touch.y - self._touch_start_y if self._touch_start_y is not None else 0
                # Prefer horizontal gesture; ignore mostly vertical drags
                if abs(dx) > self._swipe_threshold and abs(dx) > abs(dy):
                    if dx < 0:
                        # swipe left -> next image
                        self.show_next()
                    else:
                        # swipe right -> previous image
                        self.show_previous()
        finally:
            self._touch_start_x = None
            self._touch_start_y = None
        return super().on_touch_up(touch)

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
        self.app_instance.handle_back()


class GalleryScreen(MDScreen):
    def __init__(self, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.name = "gallery"
        self.app_instance = app_instance
        self._selection_mode = False
        self._selected_images = set()

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

        # Delete button (hidden by default)
        self.delete_btn = MDIconButton(
            icon="delete",
            theme_icon_color="Custom",
            icon_color="#FF6B35",
            opacity=0,
            on_release=self.delete_selected
        )
        top_bar.add_widget(self.delete_btn)

        refresh_btn = MDIconButton(
            icon="refresh",
            theme_icon_color="Custom",
            icon_color="#FFFFFF",
            on_release=self.refresh_gallery
        )
        top_bar.add_widget(refresh_btn)

        main_layout.add_widget(top_bar)

        # Efficient RecycleView for gallery
        self.rv = MDRecycleView(
            size_hint=(1, 1),
            bar_width=dp(4),
            bar_color="#FF6B35",
            bar_inactive_color="#CCCCCC",
        )
        
        # Create the layout manager first
        layout_manager = RecycleGridLayout(
            cols=2,
            spacing=dp(10),
            padding=dp(15),
            default_size=(None, dp(150)),
            default_size_hint=(1, None),
            size_hint_y=None,
        )
        
        # Important: Add as child first, then set as layout_manager
        self.rv.add_widget(layout_manager)
        self.rv.layout_manager = layout_manager
        
        # Set the viewclass AFTER the layout manager is set
        self.rv.viewclass = RecycleGalleryCard
        self.rv.data = []
        
        # Bind minimum_height to height for proper scrolling
        layout_manager.bind(minimum_height=layout_manager.setter('height'))
        
        main_layout.add_widget(self.rv)
        self.add_widget(main_layout)

    def refresh_gallery(self, *args):
        """Efficiently refresh gallery using RecycleView"""
        save_dir = self.app_instance.save_directory
        
        if not save_dir or not os.path.exists(save_dir):
            # Show empty state
            self.rv.data = [{
                'image_path': '',
                'app_instance': self.app_instance,
                'selection_mode': False,
                'is_empty_state': True
            }]
            return

        # Get all image files
        image_files = [f for f in os.listdir(save_dir)
                       if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'))]
        
        if not image_files:
            # Show empty gallery state
            self.rv.data = [{
                'image_path': '',
                'app_instance': self.app_instance,
                'selection_mode': False,
                'is_empty_state': True
            }]
            return

        # Sort files and create data list
        image_files.sort()
        
        # Create data for RecycleView - this is very fast
        self.rv.data = [
            {
                'image_path': os.path.join(save_dir, filename),
                'app_instance': self.app_instance,
                'selection_mode': self._selection_mode,
            }
            for filename in image_files
        ]

    def enter_selection_mode(self):
        """Enter selection mode - update all visible items"""
        self._selection_mode = True
        self._selected_images.clear()
        self.delete_btn.opacity = 1
        
        # Update data to trigger refresh of visible items
        for item in self.rv.data:
            item['selection_mode'] = True
        self.rv.refresh_from_data()

    def exit_selection_mode(self):
        """Exit selection mode - update all visible items"""
        self._selection_mode = False
        self._selected_images.clear()
        self.delete_btn.opacity = 0
        
        # Update data to trigger refresh of visible items
        for item in self.rv.data:
            item['selection_mode'] = False
        self.rv.refresh_from_data()

    def delete_selected(self, *args):
        if not self._selected_images:
            return

        # Show confirmation dialog
        dialog = MDDialog(
            title="Delete Images",
            text=f"Delete {len(self._selected_images)} selected image(s)?",
            buttons=[
                MDFlatButton(
                    text="Cancel", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="Delete", on_release=lambda x: (
                    self._perform_delete(), dialog.dismiss()))
            ]
        )
        dialog.open()

    def _perform_delete(self):
        deleted_count = 0

        for image_path in self._selected_images.copy():
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_count += 1
                    # Also remove thumbnail if exists
                    filename = os.path.basename(image_path)
                    thumb_path = self.app_instance._thumb_path_for(filename)
                    if os.path.exists(thumb_path):
                        os.remove(thumb_path)
            except Exception as e:
                print(f"Error deleting {image_path}: {e}")

        # Update stats
        self.app_instance.update_stats()

        # Exit selection mode and refresh
        self.exit_selection_mode()
        self.refresh_gallery()

        # Show success message
        if deleted_count > 0:
            snackbar = MDSnackbar(
                MDLabel(text=f"Deleted {deleted_count} image(s)"),
                duration=2.0
            )
            snackbar.open()

    def go_back(self, *args):
        if self._selection_mode:
            self.exit_selection_mode()
        else:
            self.app_instance.handle_back()


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
            hint_text="Enter image URL(s) - use ; for multiple",
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
        url_input = self.url_field.text.strip()
        if not url_input:
            self.app_instance.show_error_dialog(
                "Ubuntu wisdom: Please share a meaningful URL with our community"
            )
            return

        # Split URLs by semicolon and clean them
        urls = [url.strip() for url in url_input.split(';') if url.strip()]

        if not urls:
            self.app_instance.show_error_dialog(
                "Ubuntu wisdom: Please share a meaningful URL with our community"
            )
            return

        # Validate each URL
        valid_urls = []
        invalid_urls = []

        for url in urls:
            if len(url) < 10:
                invalid_urls.append(f"URL too short: {url}")
                continue

            if " " in url:
                invalid_urls.append(f"URL contains spaces: {url}")
                continue

            if not url.startswith(('http://', 'https://')):
                invalid_urls.append(f"Invalid format (must start with http:// or https://): {url}")
                continue

            valid_urls.append(url)

        if not valid_urls:
            self.app_instance.show_error_dialog(
                f"No valid URLs found:\n" + "\n".join(invalid_urls[:3])  # Show first 3 errors
            )
            return

        if invalid_urls:
            # Show warning about invalid URLs but proceed with valid ones
            self.app_instance.show_error_dialog(
                f"Warning: {len(invalid_urls)} invalid URL(s) skipped. Proceeding with {len(valid_urls)} valid URL(s).\n"
                f"First error: {invalid_urls[0]}"
            )

        # Reset UI state
        self._update_ui_state(loading=True, multiple=len(valid_urls) > 1)

        # Start downloading multiple URLs
        threading.Thread(target=self._download_multiple_images,
                         args=(valid_urls,), daemon=True).start()

    @mainthread
    def _update_ui_state(self, loading=False, error=None, multiple=False):
        """Update UI state from main thread"""
        if loading:
            Animation(opacity=1, duration=0.3).start(self.progress_bar)
            if multiple:
                self.status_label.text = "🌐 Connecting with community resources..."
            else:
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

    def _download_multiple_images(self, urls):
        """Download multiple images with progress tracking"""
        if len(urls) == 1:
            # For single URL, show preview first
            self._validate_and_preview(urls[0])
        else:
            # For multiple URLs, download directly
            self._download_multiple_directly(urls)

    def _download_multiple_directly(self, urls):
        """Download multiple images directly without preview"""
        if not self.app_instance.save_directory:
            self._show_error("❌ No save directory selected")
            return

        total_urls = len(urls)
        successful_downloads = 0
        failed_downloads = 0
        errors = []

        # Update progress for multiple downloads - ensure main thread
        def update_progress(current, total, status):
            Clock.schedule_once(lambda dt: setattr(
                self.status_label, 'text', f"📥 Downloading {current}/{total}: {status}"
            ), 0)

        try:
            for i, url in enumerate(urls, 1):
                try:
                    update_progress(i, total_urls, "Connecting...")

                    # Make request
                    r = requests.get(url, stream=True, timeout=15, headers={
                        'User-Agent': 'Ubuntu-Image-Fetcher/1.0'
                    })
                    r.raise_for_status()

                    # Check content type
                    content_type = r.headers.get("content-type", "").lower()
                    if not content_type or "image" not in content_type:
                        raise ValueError(f"Not an image: {content_type}")

                    # Check file size
                    content_length = r.headers.get("content-length")
                    if content_length:
                        size_mb = int(content_length) / (1024 * 1024)
                        if size_mb > 100:
                            raise ValueError(f"File too large: {size_mb:.1f} MB exceeds 100MB limit")

                    # Download the file
                    update_progress(i, total_urls, "Downloading...")

                    # Generate filename
                    filename = self.app_instance._sanitize_filename(url, content_type)
                    filepath = os.path.join(self.app_instance.save_directory, filename)

                    # Download
                    with open(filepath, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    # Verify file
                    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                        raise ValueError("File was not saved properly")

                    # Notify media scanner for Android
                    self.app_instance._notify_media_scanner(filepath)

                    successful_downloads += 1
                    update_progress(i, total_urls, "✅ Saved!")

                except Exception as e:
                    failed_downloads += 1
                    error_msg = f"URL {i}: {str(e)}"
                    errors.append(error_msg)
                    update_progress(i, total_urls, f"❌ Failed")

            # Final update - schedule on main thread
            Clock.schedule_once(lambda dt: self._update_ui_state(loading=False), 0)

            # Show results - schedule on main thread
            def show_results(dt):
                if successful_downloads > 0:
                    self.app_instance.update_stats()
                    self.url_field.text = ""

                    # Refresh gallery if open
                    if self.app_instance.screen_manager.current == "gallery":
                        self.app_instance.gallery_screen.refresh_gallery()

                    if failed_downloads == 0:
                        self.app_instance.show_error_dialog(
                            f"✅ Successfully downloaded {successful_downloads} image(s)!"
                        )
                    else:
                        self.app_instance.show_error_dialog(
                            f"✅ Downloaded {successful_downloads} image(s)\n"
                            f"❌ Failed {failed_downloads} image(s)"
                        )
                else:
                    self._show_error(f"❌ All downloads failed")

            Clock.schedule_once(show_results, 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f"❌ Download process failed: {e}"), 0)
        finally:
            Clock.schedule_once(lambda dt: self._update_ui_state(loading=False), 0)


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
        # Thumbnail cache dir and executor for background work
        self._thumb_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2)
        self._thumb_cache_dir = os.path.join(
            self.save_directory or os.getcwd(), ".thumbnails")
        try:
            os.makedirs(self._thumb_cache_dir, exist_ok=True)
        except Exception:
            pass

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

        # Bind Android hardware back key
        Window.bind(on_keyboard=self._on_keyboard)

        return self.screen_manager

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        # Android back is key==27 or 1001 depending on provider
        if key in (27, 1001):
            self.handle_back()
            return True
        return False

    def handle_back(self):
        current = self.screen_manager.current
        if current == "single_photo":
            # Go back to gallery
            self.screen_manager.current = "gallery"
        elif current == "gallery":
            # Go back to main
            self.screen_manager.current = "main"
        else:
            # On main screen: confirm exit
            self._confirm_exit()

    def _confirm_exit(self):
        # Avoid stacking multiple dialogs
        existing = getattr(self, "_exit_dialog", None)
        if existing:
            try:
                existing.dismiss()
            except Exception:
                pass
            self._exit_dialog = None

        def _do_exit(*_):
            try:
                from kivy.app import App
                app = App.get_running_app()
                if app:
                    app.stop()
                else:
                    import sys
                    sys.exit(0)
            except Exception:
                import sys
                sys.exit(0)

        dialog = MDDialog(
            title="Exit",
            text="Do you want to exit the app?",
            buttons=[
                MDRaisedButton(
                    text="Cancel", on_release=lambda *_: dialog.dismiss()),
                MDRaisedButton(text="Exit", on_release=_do_exit),
            ],
        )
        self._exit_dialog = dialog
        dialog.open()

    def get_save_directory(self):
        """Automatically use appropriate directory based on platform"""
        # 1) Config override if user previously selected a folder
        try:
            import json
            if os.path.exists("ubuntu_fetcher_config.json"):
                with open("ubuntu_fetcher_config.json", "r") as f:
                    cfg = json.load(f)
                    path = cfg.get("save_directory")
                    if path and os.path.isdir(path):
                        return path
        except Exception:
            pass

        # Check if running on Android
        is_android = platform.system() == 'Linux' and 'ANDROID_ARGUMENT' in os.environ

        if is_android and storagepath:
            try:
                # Prefer Android's public Downloads directory, fallback to Pictures
                if storagepath is not None:
                    base_path = None
                    try:
                        get_downloads = getattr(
                            storagepath, 'get_downloads_dir', None)
                        if callable(get_downloads):
                            base_path = get_downloads()
                    except Exception:
                        base_path = None
                    if not base_path:
                        try:
                            get_pictures = getattr(
                                storagepath, 'get_pictures_dir', None)
                            if callable(get_pictures):
                                base_path = get_pictures()
                        except Exception:
                            base_path = None
                    if base_path:
                        # Ensure string path for type checkers and os.path
                        try:
                            base_path_str = str(base_path)
                        except Exception:
                            base_path_str = f"{base_path}"
                        ubuntu_folder = os.path.join(
                            base_path_str, "Ubuntu-Image-Fetcher")
                        if not os.path.exists(ubuntu_folder):
                            os.makedirs(ubuntu_folder)
                        return ubuntu_folder

                # Last resort fallback on Android
                fallback_folder = os.path.join(
                    os.path.expanduser("~/Downloads"), "Ubuntu-Image-Fetcher")
                if not os.path.exists(fallback_folder):
                    os.makedirs(fallback_folder)
                return fallback_folder
            except Exception as e:
                print(f"Failed to get Android pictures directory: {e}")

        # Desktop platforms - use Downloads folder
        try:
            # Get the user's Downloads folder
            if os.name == 'nt':  # Windows
                downloads_path = os.path.join(
                    os.path.expanduser("~"), "Downloads")
            else:  # Linux/Mac
                downloads_path = os.path.join(
                    os.path.expanduser("~"), "Downloads")

            # Create Ubuntu-Image-Fetcher subfolder
            ubuntu_folder = os.path.join(
                downloads_path, "Ubuntu-Image-Fetcher")

            # Create the folder if it doesn't exist
            if not os.path.exists(ubuntu_folder):
                os.makedirs(ubuntu_folder)

            return ubuntu_folder

        except Exception as e:
            # Fallback to current directory if Downloads folder is not accessible
            fallback_folder = os.path.join(os.getcwd(), "Ubuntu-Image-Fetcher")
            if not os.path.exists(fallback_folder):
                os.makedirs(fallback_folder)
            return fallback_folder

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

        # Inline progress UI (hidden until saving starts)
        progress_label = MDLabel(
            text="Saving...",
            theme_text_color="Custom",
            text_color="#FFFFFF",
            halign="center",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
            opacity=0
        )
        progress_bar = MDProgressBar(
            size_hint_y=None,
            height=dp(4),
            opacity=0,
            value=0
        )
        box.add_widget(progress_label)
        box.add_widget(progress_bar)

        btns = MDBoxLayout(size_hint=(1, 0.2), spacing=dp(10))
        save_btn = MDRaisedButton(text="Save")
        discard_btn = MDRaisedButton(text="Discard")
        btns.add_widget(save_btn)
        btns.add_widget(discard_btn)
        box.add_widget(btns)

        preview.add_widget(box)
        # Wire up actions with UI refs for responsive save
        ui_refs = {
            'save_btn': save_btn,
            'discard_btn': discard_btn,
            'progress_label': progress_label,
            'progress_bar': progress_bar,
        }
        save_btn.bind(on_release=lambda x: self.save_image(
            url, preview, ui_refs))
        discard_btn.bind(on_release=lambda x: self.discard_preview(preview))
        preview.open()

    def discard_preview(self, preview):
        # Clear background image when discarding
        self.bg_image = None
        self.main_screen.bg.source = ""
        preview.dismiss()

    def save_image(self, url, popup, ui_refs=None):
        if not os.path.exists(self.save_directory):
            self.ask_for_directory(url, popup, ui_refs)
        else:
            # Non-blocking save with UI feedback
            if ui_refs:
                self._set_saving_ui(ui_refs, True)
            threading.Thread(target=self._download_and_save, args=(
                url, popup, ui_refs), daemon=True).start()

    def ask_for_directory(self, url, popup, ui_refs=None):
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
                if ui_refs:
                    self._set_saving_ui(ui_refs, True)
                threading.Thread(target=self._download_and_save, args=(
                    url, popup, ui_refs), daemon=True).start()
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

    def _download_and_save(self, url, popup, ui_refs=None):
        if not self.save_directory:
            self.show_error_dialog("❌ No save directory selected")
            return

        try:
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()

            # Ensure we have content
            # For streamed responses, content may not be preloaded; validate via headers/chunks
            content_length = r.headers.get("content-length")
            total_bytes = int(
                content_length) if content_length and content_length.isdigit() else 0

            # Get content type for proper extension
            content_type = r.headers.get("content-type", "").lower()

            # Sanitize filename from URL with content type info
            filename = self._sanitize_filename(url, content_type)
            os.makedirs(self.save_directory, exist_ok=True)
            filepath = os.path.join(self.save_directory, filename)

            bytes_downloaded = 0
            last_percent = -1
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if total_bytes:
                        percent = int(bytes_downloaded * 100 / total_bytes)
                        if percent != last_percent:
                            last_percent = percent
                            if ui_refs:
                                self._update_modal_progress(ui_refs, percent)

            # Verify file was written
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                raise ValueError("File was not saved properly")

            # Let Gallery see it (Android)
            self._notify_media_scanner(filepath)

            self._dismiss_preview(popup)
            self.show_error_dialog(f"✅ Saved to community collection!")
            self.update_stats()
            # Clear the URL field
            self.main_screen.url_field.text = ""
            # Refresh gallery if it's open
            if self.screen_manager.current == "gallery":
                self.gallery_screen.refresh_gallery()
            # Reset saving UI state if still visible
            if ui_refs:
                self._set_saving_ui(ui_refs, False)

        except requests.exceptions.Timeout:
            self.show_error_dialog("❌ Download timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            self.show_error_dialog(f"❌ Network error: {e}")
        except OSError as e:
            self.show_error_dialog(f"❌ File system error: {e}")
        except Exception as e:
            self.show_error_dialog(f"❌ Failed: {e}")
        finally:
            if ui_refs:
                self._set_saving_ui(ui_refs, False)

    @mainthread
    def _set_saving_ui(self, ui_refs, saving: bool):
        try:
            save_btn = ui_refs.get('save_btn')
            discard_btn = ui_refs.get('discard_btn')
            progress_label = ui_refs.get('progress_label')
            progress_bar = ui_refs.get('progress_bar')
            if save_btn:
                save_btn.disabled = saving
                save_btn.text = "Saving..." if saving else "Save"
            if discard_btn:
                discard_btn.disabled = saving
            if progress_label:
                progress_label.opacity = 1 if saving else 0
                progress_label.text = "Saving..." if saving else ""
            if progress_bar:
                progress_bar.opacity = 1 if saving else 0
                progress_bar.value = 0 if saving else progress_bar.value
        except Exception:
            pass

    @mainthread
    def _update_modal_progress(self, ui_refs, percent: int):
        try:
            progress_label = ui_refs.get('progress_label')
            progress_bar = ui_refs.get('progress_bar')
            if progress_bar:
                progress_bar.value = max(0, min(100, percent))
            if progress_label:
                progress_label.text = f"Saving... {percent}%"
        except Exception:
            pass

    @mainthread
    def _dismiss_preview(self, popup):
        try:
            popup.dismiss()
        except Exception:
            pass

    def _notify_media_scanner(self, filepath: str):
        """Ask Android MediaScanner to index the new image so Gallery can see it."""
        try:
            # Only meaningful on Android
            if not (platform.system() == 'Linux' and 'ANDROID_ARGUMENT' in os.environ):
                return
            import importlib
            jnius = importlib.import_module('jnius')
            autoclass = jnius.autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            File = autoclass('java.io.File')
            intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
            file = File(filepath)
            uri = Uri.fromFile(file)
            intent.setData(uri)
            PythonActivity.mActivity.sendBroadcast(intent)
        except Exception as e:
            # Safe to ignore on non-Android/dev environments
            print(f"MediaScanner notify failed: {e}")

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

    # ---------- Thumbnails ----------
    def _thumb_path_for(self, image_path: str) -> str:
        base = os.path.basename(image_path)
        name, ext = os.path.splitext(base)
        return os.path.join(self._thumb_cache_dir, f"{name}_thumb.jpg")

    def ensure_thumbnail(self, image_path: str, callback):
        """Ensure a small thumbnail exists, generate asynchronously if needed.
        callback will be called on main thread with the thumbnail path (or original path on failure).
        """
        thumb_path = self._thumb_path_for(image_path)
        
        # If exists and is recent, call back immediately
        if os.path.exists(thumb_path):
            try:
                # Check if thumbnail is newer than original (or same age)
                thumb_mtime = os.path.getmtime(thumb_path)
                orig_mtime = os.path.getmtime(image_path)
                if thumb_mtime >= orig_mtime:
                    self._dispatch_thumb(callback, thumb_path)
                    return
            except OSError:
                pass  # Fall through to regenerate
        
        # If PIL not available, fallback immediately
        if PILImage is None:
            self._dispatch_thumb(callback, image_path)
            return

        def work():
            try:
                if PILImage is None:
                    return image_path
                    
                # Generate optimized small thumbnail to reduce memory/IO
                with PILImage.open(image_path) as im:
                    # Convert to RGB if needed (for RGBA, P mode images)
                    if im.mode not in ('RGB', 'L'):
                        im = im.convert('RGB')
                    
                    # Create smaller thumbnail for even better performance
                    im.thumbnail((120, 120), PILImage.Resampling.LANCZOS)
                    
                    # Ensure cache dir exists
                    os.makedirs(self._thumb_cache_dir, exist_ok=True)
                    
                    # Save with optimized JPEG quality for faster loading
                    im.save(thumb_path, format='JPEG', quality=85, optimize=True)
                    
                return thumb_path
            except Exception as e:
                print(f"Thumbnail generation failed for {image_path}: {e}")
                return image_path

        # Run in executor
        future = self._thumb_executor.submit(work)

        def done(_):
            result = future.result()
            self._dispatch_thumb(callback, result)

        future.add_done_callback(done)

    @mainthread
    def _dispatch_thumb(self, callback, path: str):
        try:
            callback(path)
        except Exception:
            pass


if __name__ == "__main__":
    UbuntuImageFetcherApp().run()
