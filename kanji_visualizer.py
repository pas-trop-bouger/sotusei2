import pygame
import json
import random
import math
import os
import ctypes

def set_ime_mode(window_handle, active=True):
    try:
        imm32 = ctypes.windll.imm32
        h_imc = imm32.ImmGetContext(window_handle)
        if h_imc:
            # IME_CMODE_NATIVE | IME_CMODE_FULLSHAPE for Kana?
            # IME_CMODE_ROMAN (0x00) vs Kana?
            # Actually ImmSetOpenStatus(h_imc, True) opens IME.
            imm32.ImmSetOpenStatus(h_imc, int(active))
            
            # To force Hiragana: IME_CMODE_NATIVE (0x0001) | IME_CMODE_FULLSHAPE (0x0008)??
            # Usually just turning it ON is enough if user's default is Kana.
            # But let's try to set conversion mode if we can.
            # IME_CMODE_NATIVE = 0x0001
            # IME_CMODE_FULLSHAPE = 0x0008
            # IME_CMODE_ROMAN = 0x0010
            
            # 0x0009 = Native + Fullshape (Zen-Kaku Hiragana usually)
            imm32.ImmSetConversionStatus(h_imc, 0x0009, 0) 
            
            imm32.ImmReleaseContext(window_handle, h_imc)
    except Exception as e:
        print(f"IME Set Failed: {e}")

# ==== CONFIG ====
DEFAULT_WINDOW_SIZE = (1600, 900)
MARGIN = 120
FONT_PATH = "C:/Windows/Fonts/ヒラギノ角ゴ STDN W0.otf"
# Improved quality: Increased font size
FONT_SIZE = 42 
HOVER_FONT_SIZE = 84
UI_FONT_SIZE = 24



# Font Presets Configuration
# List of (Label, List of Candidate Paths)
# Updated as per user request
FONT_PRESETS = [
    ("Hiragino", ["C:/Windows/Fonts/ヒラギノ角ゴ STDN W0.otf", "C:/Windows/Fonts/msgothic.ttc"]), # Default
    ("Kizahashi", ["C:/Windows/Fonts/A-OTF-KizahashiKinryoStd-Regular.otf", "C:/Windows/Fonts/AP-OTF-Kizakinryoustd-med.otf"]),
    ("Ryumin", ["C:/Windows/Fonts/A-OTF-RyuminPr6-Light.otf", "C:/Windows/Fonts/AP-OTF-RyuminPr6-Light.otf"]), 
    ("A1Mincho", ["C:/Windows/Fonts/A-OTF-A1MinchoStd-Bold.otf"]), 
    ("Haruhi", ["C:/Windows/Fonts/A-OTF-HaruGakuStd-LIGHT.otf"]), 
    ("Reisho", ["C:/Windows/Fonts/A-OTF-ReishoE1Std-Regular.otf"]),
]

# Theme Configuration (White Mode)
BG_COLOR = (255, 255, 255)
AXIS_COLOR = (200, 200, 200)
UI_BG_COLOR = (245, 245, 245, 240)
UI_BORDER_COLOR = (220, 220, 220)
UI_TEXT_COLOR = (20, 20, 20) # Darker text
ACCENT_COLOR = (60, 120, 180) # Muted Blue/Teal
HOVER_BG_COLOR = (255, 255, 255, 230)
HOVER_BORDER_COLOR = (180, 180, 180)
LERP_FACTOR = 0.08  # Slower, smoother

def find_font_path(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return None # Fallback to system default if None



# Metrics Keys
METRICS = [
    "horizontal_ratio",
    "vertical_ratio", 
    "diagonal_ratio",
    "scale_factor",
    "density",
    "cog_x",
    "cog_y",
    "skeleton_length",
    "holes",
    "discreteness",
    "inertia",
    "endpoints"
]

# Metric Labels
METRIC_LABELS = {
    "horizontal_ratio": "Horizontal (横線率)",
    "vertical_ratio": "Vertical (縦線率)",
    "diagonal_ratio": "Diagonal (斜線率)",
    "scale_factor": "Scale (スケール)",
    "density": "Density (画素密度)",
    "cog_x": "Center of Gravity X (重心X)",
    "cog_y": "Center of Gravity Y (重心Y)",
    "skeleton_length": "Skeleton Length (骨格長)",
    "holes": "Holes (閉領域数)",
    "discreteness": "Discreteness (パーツ数)",
    "inertia": "Inertia (拡散率)",
    "endpoints": "Endpoints (端点数)"
}

class KanjiSprite:
    def __init__(self, data, font):
        self.char = data['char']
        self.metrics = data['metrics']
        
        # Start random
        self.x = random.randint(0, 1000)
        self.y = random.randint(0, 1000)
        self.target_x = self.x
        self.target_y = self.y
        
        # Color based on strokes (Darker as requested)
        # Was 150+80, now 150+80 to be "slightly darker"
        r = int(self.metrics['horizontal_ratio'] * 150 + 80)
        g = int(self.metrics['vertical_ratio'] * 150 + 80)
        b = int(self.metrics['diagonal_ratio'] * 150 + 80)
        self.color = (r, g, b)
        
        # High Quality Rendering Technique
        # Render large, then smoothscale down
        # This keeps the "Light" font looking sharp but thin, without pixelation
        original_surface = font.render(self.char, True, self.color)
        
        # Calculate target size (e.g. 24px height) based on ratios
        target_h = 24
        w, h = original_surface.get_size()
        scale = target_h / h
        target_w = int(w * scale)
        
        self.image = pygame.transform.smoothscale(original_surface, (target_w, target_h))
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.x), int(self.y))
        
        # Cache precise float pos
        self.fx = float(self.x)
        self.fy = float(self.y)

    def update(self):
        # Smooth Lerp
        dx = self.target_x - self.fx
        dy = self.target_y - self.fy
        
        # Distance check for sleeping? For now just always lerp
        self.fx += dx * LERP_FACTOR
        self.fy += dy * LERP_FACTOR
        
        self.rect.centerx = int(self.fx)
        self.rect.centery = int(self.fy)

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def reload_image(self, font):
        # High Quality Rendering Technique
        # Identical to __init__ logic but updates self.image
        
        # 1. Update Image
        r = int(self.metrics['horizontal_ratio'] * 150 + 80)
        g = int(self.metrics['vertical_ratio'] * 150 + 80)
        b = int(self.metrics['diagonal_ratio'] * 150 + 80)
        self.color = (r, g, b)
        
        try:
            original_surface = font.render(self.char, True, self.color)
        except Exception:
            # Fallback if char not in font?
            print(f"Failed to render {self.char}")
            return

        target_h = 24
        w, h = original_surface.get_size()
        scale = target_h / h
        target_w = int(w * scale)
        if target_w < 1: target_w = 1 
        
        self.image = pygame.transform.smoothscale(original_surface, (target_w, target_h))
        # Keep center position
        center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = center
        
        # Density is already in self.metrics loaded from JSON



class UIElement:
    def __init__(self, x, y, w, h, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        return False
        
    def draw(self, surface):
        pass

class Button(UIElement):
    def __init__(self, x, y, w, h, text, callback, font):
        super().__init__(x, y, w, h, font)
        self.text = text
        self.callback = callback
        
    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and event.button == 1:
                self.callback()
                return True
        return False

    def draw(self, surface, active=False):
        # Light theme styling
        if active:
            bg = (200, 220, 255) # Light Blue
            border = ACCENT_COLOR
            text_col = (0, 0, 100)
        else:
            bg = (230, 230, 230) if self.hovered else (250, 250, 250)
            border = ACCENT_COLOR if self.hovered else UI_BORDER_COLOR
            text_col = UI_TEXT_COLOR
        
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2 if active else 1, border_radius=6)
        
        text_surf = self.font.render(self.text, True, text_col)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class TextInput(UIElement):
    def __init__(self, x, y, w, h, font, placeholder="Search..."):
        super().__init__(x, y, w, h, font)
        self.text = ""
        self.composition_text = "" # For IME composition
        self.placeholder = placeholder
        self.focused = False
        self.select_all_mode = False # If true, next input overwrites text
        
        # Clear button rect (relative to self.rect)
        self.clear_btn_size = h - 10
        self.clear_rect = pygame.Rect(x + w - self.clear_btn_size - 5, y + 5, self.clear_btn_size, self.clear_btn_size)
        
    def handle_event(self, event):
        super().handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Check clear button first
                if self.text and self.clear_rect.collidepoint(event.pos):
                    self.text = ""
                    self.composition_text = ""
                    # Keep focus if we want, or not. Let's keep focus.
                    self.focused = True
                    self.select_all_mode = False
                    pygame.key.start_text_input()
                    pygame.key.set_text_input_rect(self.rect)
                    return True
                
                was_focused = self.focused
                self.focused = self.rect.collidepoint(event.pos)
                if self.focused:
                    pygame.key.start_text_input()
                    pygame.key.set_text_input_rect(self.rect)
                    # If clicked, enable select-all mode so user can easily replace text
                    self.select_all_mode = True
                    
                    # FORCE IME ON
                    try:
                        hwnd = pygame.display.get_wm_info()['window']
                        set_ime_mode(hwnd, True)
                    except Exception:
                        pass
                        
                elif was_focused:
                    pygame.key.stop_text_input()
                    self.select_all_mode = False
            return self.focused
            
        if self.focused:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    if self.select_all_mode:
                        self.text = ""
                        self.select_all_mode = False
                    elif len(self.composition_text) > 0:
                         # Let IME handle backspace in composition usually, but if we manage it:
                         self.composition_text = self.composition_text[:-1]
                    else:
                         # Allow deleting committed text
                         self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    self.select_all_mode = False
                    # We do NOT add text here. Return is just a control key.
                else: 
                     # Any other key disables select all mode if it's not text input
                     pass
                
            elif event.type == pygame.TEXTINPUT:
                if self.select_all_mode:
                    self.text = "" # Overwrite
                    self.select_all_mode = False
                
                # Double input fix: Debounce rapid duplicate inputs
                current_time = pygame.time.get_ticks()
                if hasattr(self, 'last_input_text') and self.last_input_text == event.text:
                    if current_time - getattr(self, 'last_input_time', 0) < 50:
                        return True # Ignore duplicate

                # Ignore control characters
                if event.text == '\r' or event.text == '\n' or event.text == '\t':
                    return True
                
                self.text += event.text
                self.composition_text = "" # Clear composition on commit
                
                self.last_input_text = event.text
                self.last_input_time = current_time
                return True

            elif event.type == pygame.TEXTEDITING:
                if self.select_all_mode:
                     self.text = "" # Overwrite
                     self.select_all_mode = False
                     
                # Debounce: If this editing event is the exact same text as just committed
                # and happens very quickly, ignore it.
                if hasattr(self, 'last_commit_text') and self.last_commit_text:
                    if event.text == self.last_commit_text:
                        # Check time
                        if pygame.time.get_ticks() - getattr(self, 'last_commit_time', 0) < 100:
                            # Likely a ghost event from IME confirmation
                            self.composition_text = ""
                            return True
                
                # This is the active composition
                self.composition_text = event.text
                self.composition_start = event.start
                self.composition_length = event.length
                return True
                
        return False

    def draw(self, surface):
        # Light theme styling
        bg = (255, 255, 255)
        border = ACCENT_COLOR if self.focused else UI_BORDER_COLOR
        
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2 if self.focused else 1, border_radius=6)
        
        # Text Construction (Committed + Composition)
        full_text = self.text + self.composition_text
        display_text = full_text if full_text else self.placeholder
        color = UI_TEXT_COLOR if full_text else (150, 150, 150)
        
        # Clip text if too long (simple version)
        text_surf = self.font.render(display_text, True, color)
        # Left align with padding
        target_rect = text_surf.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        
        # Draw Selection Highlight if needed
        if self.select_all_mode and self.text:
             # Basic select all highlight
             sel_rect = target_rect.copy()
             if sel_rect.width > self.rect.width - 20:
                 sel_rect.width = self.rect.width - 20
                 sel_rect.x = self.rect.x + 10
             
             s = pygame.Surface((sel_rect.width, sel_rect.height), pygame.SRCALPHA)
             s.fill((60, 120, 180, 100)) # ACCENT_COLOR with alpha
             surface.blit(s, sel_rect.topleft)

        # Simple clipping
        if target_rect.width > self.rect.width - 20:
             # Just show end if typing
             area = pygame.Rect(target_rect.width - (self.rect.width - 20), 0, self.rect.width - 20, target_rect.height)
             surface.blit(text_surf, (self.rect.x + 10, target_rect.y), area)
        else:
             surface.blit(text_surf, target_rect)
             
        # Underline composition text
        if self.composition_text and self.focused:
             # We need to calculate width of committed text to know where to start underline
             committed_part = self.font.render(self.text, True, color)
             comp_part = self.font.render(self.composition_text, True, color)
             
             start_x = self.rect.x + 10 + committed_part.get_width()
             
             # Adjust if clipped (basic approximation)
             if target_rect.width > self.rect.width - 20:
                 offset = target_rect.width - (self.rect.width - 20)
                 start_x -= offset
                 
             # Only draw if visible
             if start_x < self.rect.right:
                 end_x = start_x + comp_part.get_width()
                 if end_x > self.rect.right - 10: end_x = self.rect.right - 10
                 
                 pygame.draw.line(surface, ACCENT_COLOR, (start_x, self.rect.bottom - 8), (end_x, self.rect.bottom - 8), 2)

        # Draw Clear Button if text exists
        if self.text or self.composition_text:
            # Simple X
            msg = "×"
            btn_surf = self.font.render(msg, True, (150, 150, 150))
            btn_rect = btn_surf.get_rect(center=self.clear_rect.center)
            
            # Hover effect for clear button?
            mx, my = pygame.mouse.get_pos()
            if self.clear_rect.collidepoint(mx, my):
                 pygame.draw.circle(surface, (230, 230, 230), self.clear_rect.center, self.clear_btn_size//2)
                 btn_surf = self.font.render(msg, True, (100, 100, 100))
            
            surface.blit(btn_surf, btn_rect)

class App:
    def __init__(self):
        pygame.init()
        
        # Fullscreen setup
        info = pygame.display.Info()
        self.w, self.h = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN)
        pygame.display.set_caption("Kanji Layout")
        
        # Enable key repeat for backspace
        pygame.key.set_repeat(500, 50)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_font_idx = 0
        
        # Idle Logic
        self.last_interaction_time = pygame.time.get_ticks()
        self.last_auto_switch_time = 0
        self.idle_timeout = 10000 # 10 seconds
        self.auto_switch_interval = random.randint(350, 800) 
        
        # Load Initial Font
        self.load_font(self.current_font_idx)
        
        # Load Relationships
        self.relationships = {}
        self.load_relationships()
        
        # Init UI and State
        self.init_ui_and_state()

    def load_font(self, font_idx):
        print(f"Loading font preset {font_idx}: {FONT_PRESETS[font_idx][0]}")
        label, candidates = FONT_PRESETS[font_idx]
        path = find_font_path(candidates)
        
        RENDER_SIZE = 64
        
        try:
            if path:
                self.render_font = pygame.font.Font(path, RENDER_SIZE)
                self.header_font = pygame.font.Font(path, 48)
                # Keep UI font standard if possible, or use same? 
                # Better to use a readable UI font always, maybe keep system default or specific UI font?
                # User asked to compare fonts, implying sprites change. UI readability is important.
                # Let's keep UI font as fallback or specific safe font to ensure buttons are readable.
                # BUT using the "Font" for everything is also cool.
                # Let's just use the loaded font for headers, and try to keep UI legible.
                # If the font is super weird, UI might break. Let's stick to safe font for UI interactions if possible.
                # However, existing code used FONT_PATH for everything.
                self.ui_font = pygame.font.Font(path, 16) 
            else:
                print("No candidate found, using SysFont")
                self.render_font = pygame.font.SysFont("Yu Gothic UI", RENDER_SIZE)
                self.header_font = pygame.font.SysFont("Yu Gothic UI", 48)
                self.ui_font = pygame.font.SysFont("Yu Gothic UI", 16)
                
            self.hover_font = pygame.font.SysFont("Yu Gothic UI", 24)
            
        except OSError:
            print(f"Font loading failed, falling back.")
            self.render_font = pygame.font.SysFont("Yu Gothic UI", RENDER_SIZE)
            self.header_font = pygame.font.SysFont("Yu Gothic UI", 48)
            self.ui_font = pygame.font.SysFont("Yu Gothic UI", 16)
            self.hover_font = pygame.font.SysFont("Yu Gothic UI", 24)

            
        # Load Data
        print(f"Loading data... (Font Index: {font_idx})")
        # Try specific JSON first
        json_path = f"kanji_metrics_{label}.json"
        if not os.path.exists(json_path):
             print(f"Metrics file {json_path} not found, defaulting to kanji_metrics.json")
             json_path = "kanji_metrics.json"

        with open(json_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            
        # If this is not the first load (self.sprites exists), we need to update sprites
        if hasattr(self, 'sprites') and self.sprites:
             # Map new data by char
             new_data_map = {d['char']: d['metrics'] for d in new_data}
             
             for s in self.sprites:
                 if s.char in new_data_map:
                     s.metrics = new_data_map[s.char]
                     # No need to recalc density manually anymore!
                     # Just force colour update?
                     # Color is based on Ratio, which is also in JSON.
                     
             print("Metrics updated from JSON.")
        else:
             # First load
             self.raw_data = new_data
             if hasattr(self, 'render_font'):
                 self.sprites = [KanjiSprite(d, self.render_font) for d in self.raw_data]
                 self.sprite_map = {s.char: s for s in self.sprites}
        
        # Precompute Ranges (Strict Min/Max as requested)
        self.ranges = {}
        first = self.raw_data[0]['metrics']
        for k in first.keys():
            vals = [d['metrics'][k] for d in self.raw_data]
            v_min = min(vals)
            v_max = max(vals)
            
            # Fallback if range is zero
            if v_max == v_min:
                v_max += 0.001
                
            self.ranges[k] = (v_min, v_max)

    def init_ui_and_state(self):
        # Initial Keys
        self.x_key = "density"
        self.y_key = "skeleton_length"
        
        self.selected_sprite = None
        self.hovered_sprite = None
        
        self.ui_elements = []
        self.create_ui()
        self.update_targets()

    def create_ui(self):
        self.ui_elements = []
        
        # Increase width for labels, or use smaller font
        # Increase width for labels, or use smaller font
        panel_x, panel_y = 30, 30
        btn_w, btn_h = 300, 40 # Slightly wider
        spacing = 0 # Zero spacing as requested
        
        self.btn_x = Button(panel_x, panel_y, btn_w, btn_h, 
                           self.get_label("X", self.x_key), 
                           self.next_x, self.ui_font)
        
        self.btn_y = Button(panel_x, panel_y + btn_h + spacing, btn_w, btn_h, 
                           self.get_label("Y", self.y_key), 
                           self.next_y, self.ui_font)
                           
        # Search Input - Below buttons
        self.text_input = TextInput(panel_x, panel_y + (btn_h + spacing) * 2 + 10, btn_w, btn_h, self.ui_font, "Type to filter...")
        
        self.ui_elements.extend([self.btn_x, self.btn_y, self.text_input])

        self.ui_elements.extend([self.btn_x, self.btn_y, self.text_input])

        # Font Selection Grid
        # Create buttons for each font preset
        label_y = panel_y + (btn_h + spacing) * 2 + 10 + btn_h + 10
        
        # Grid layout: 2 columns
        col_count = 2
        col_w = (btn_w - 10) // col_count
        row_h = 35
        
        self.font_buttons = []
        for i, (label, _) in enumerate(FONT_PRESETS):
            row = i // col_count
            col = i % col_count
            
            bx = panel_x + col * (col_w + 10)
            by = label_y + row * (row_h + 5)
            
            # Capture closure for callback
            # Default argument hack to bind 'i'
            cb = lambda idx=i: self.change_font(idx)
            
            btn = Button(bx, by, col_w, row_h, label, cb, self.ui_font)
            self.font_buttons.append(btn)
            self.ui_elements.append(btn)



    def get_label(self, axis_name, key):
        name = METRIC_LABELS[key]
        return f"{axis_name}: {name}"

    def next_x(self):
        # Cycle to next metric
        curr_idx = METRICS.index(self.x_key)
        next_idx = (curr_idx + 1) % len(METRICS)
        
        # Skip if same as Y
        if METRICS[next_idx] == self.y_key:
            next_idx = (next_idx + 1) % len(METRICS)
            
        self.x_key = METRICS[next_idx]
        self.btn_x.text = self.get_label("X", self.x_key)
        self.update_targets()

    def next_y(self):
        # Cycle to next metric
        curr_idx = METRICS.index(self.y_key)
        next_idx = (curr_idx + 1) % len(METRICS)
        
        # Skip if same as X
        if METRICS[next_idx] == self.x_key:
            next_idx = (next_idx + 1) % len(METRICS)
            
        self.y_key = METRICS[next_idx]
        self.btn_y.text = self.get_label("Y", self.y_key)
        self.update_targets()

    def auto_switch_axis(self):
        # Randomly choose axis to switch
        if random.random() < 0.5:
            # Switch X
            new_key = random.choice(METRICS)
            # Avoid same as Y or current
            while new_key == self.y_key or new_key == self.x_key:
                 new_key = random.choice(METRICS)
            
            self.x_key = new_key
            self.btn_x.text = self.get_label("X", self.x_key)
        else:
            # Switch Y
            new_key = random.choice(METRICS)
            while new_key == self.x_key or new_key == self.y_key:
                 new_key = random.choice(METRICS)
                 
            self.y_key = new_key
            self.btn_y.text = self.get_label("Y", self.y_key)
            
        self.update_targets()
        
    def quit_app(self):
        self.running = False

    def load_relationships(self):
        print("Loading relationships...")
        try:
            with open('histogram_data.js', 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove "const HISTOGRAM_DATA = " and trailing semicolon
                json_str = content.replace("const HISTOGRAM_DATA = ", "").strip().rstrip(";")
                data = json.loads(json_str)
                
                for item in data.get('characters', []):
                    char = item['char']
                    self.relationships[char] = {
                        'parents': item.get('parents', []),
                        'children': item.get('children', [])
                    }
            print(f"Loaded relationships for {len(self.relationships)} characters.")
        except Exception as e:
            print(f"Error loading relationships: {e}")

    def change_font(self, index):
        if index == self.current_font_idx:
            return
            
        print(f"Switching to font {index}")
        self.current_font_idx = index
        self.load_font(index)
        
        # Reload Sprites Images ONLY (Metrics already updated in load_font)
        for s in self.sprites:
            s.reload_image(self.render_font)
            
        # Re-calc Ranges for Density (based on NEW metrics loaded from JSON)
        densities = [s.metrics['density'] for s in self.sprites]
        d_min = min(densities)
        d_max = max(densities)
        if d_max == d_min: d_max += 0.001
        
        # Update range
        self.ranges['density'] = (d_min, d_max)

        # Update CoG ranges too as they change
        for key in ['cog_x', 'cog_y']:
             vals = [s.metrics[key] for s in self.sprites]
             self.ranges[key] = (min(vals), max(vals))
        
        # Trigger layout update to reflect new density range if Density is current axis
        self.update_targets()



    def update_targets(self):
        x_min, x_max = self.ranges[self.x_key]
        y_min, y_max = self.ranges[self.y_key]
        
        # Avoid div by zero
        if x_max <= x_min: x_max = x_min + 0.001
        if y_max <= y_min: y_max = y_min + 0.001
        
        # Drawing Area (leave padding for UI)
        # Pad left quite a bit to account for controls, Pad all around for aesthetics
        pad_l = 60
        pad_r = 60
        pad_t = 60
        pad_b = 60
        
        avail_w = self.w - (pad_l + pad_r)
        avail_h = self.h - (pad_t + pad_b)
        
        for s in self.sprites:
            vx = s.metrics[self.x_key]
            vy = s.metrics[self.y_key]
            
            # Normalize and CLAMP
            nx = (vx - x_min) / (x_max - x_min)
            ny = (vy - y_min) / (y_max - y_min)
            
            nx = max(0.0, min(1.0, nx))
            ny = max(0.0, min(1.0, ny))
            
            # Flip Y (Screen coords)
            ny = 1.0 - ny
            
            s.target_x = pad_l + nx * avail_w
            s.target_y = pad_t + ny * avail_h

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            for event in events:
                if event.type in (pygame.QUIT, pygame.KEYDOWN):
                     # Interaction detected on keydown too (except QUIT which breaks loop anyway)
                     if event.type == pygame.KEYDOWN:
                         self.last_interaction_time = pygame.time.get_ticks()
                     continue
                
                # Interaction detection for mouse
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    self.last_interaction_time = pygame.time.get_ticks()
                
                # Check UI first
                ui_handled = False
                for el in self.ui_elements:
                    if el.handle_event(event):
                        ui_handled = True
                        
                if ui_handled:
                    continue

                # Sprite Selection
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = event.pos
                        clicked = None
                        for i in range(len(self.sprites)-1, -1, -1):
                            if self.sprites[i].rect.collidepoint(mx, my):
                                clicked = self.sprites[i]
                                break
                        
                        self.selected_sprite = clicked

            # Update Logic
            current_time = pygame.time.get_ticks()
            
            # Idle Auto-Switch
            if current_time - self.last_interaction_time > self.idle_timeout:
                if current_time - self.last_auto_switch_time > self.auto_switch_interval:
                    self.auto_switch_axis()
                    self.last_auto_switch_time = current_time
                    # Randomize next interval (0.3s to 0.8s)
                    self.auto_switch_interval = random.randint(350, 800)

            mx, my = pygame.mouse.get_pos()
            
            # Hover Check
            self.hovered_sprite = None
            for i in range(len(self.sprites)-1, -1, -1):
                if self.sprites[i].rect.collidepoint(mx, my):
                    self.hovered_sprite = self.sprites[i]
                    break

            # Update Sprites
            for s in self.sprites:
                s.update()

            # DRAW
            self.screen.fill(BG_COLOR)
            
            # Axes lines
            pygame.draw.line(self.screen, AXIS_COLOR, (60, self.h - 60), (self.w - 60, self.h - 60), 1)
            pygame.draw.line(self.screen, AXIS_COLOR, (60, 60), (60, self.h - 60), 1)
            
            # Draw Sprites FIRST
            for s in self.sprites:
                # Highlight check
                is_search_match = False
                if self.text_input.text:
                    if s.char in self.text_input.text:
                        is_search_match = True
                
                # Draw logic
                if is_search_match:
                    # Glow (using separate surface for alpha)
                    glow_size = 60
                    glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (100, 100, 255, 100), (glow_size//2, glow_size//2), glow_size//3)
                    self.screen.blit(glow_surf, (s.rect.centerx - glow_size//2, s.rect.centery - glow_size//2))
                
                s.draw(self.screen)
                
                if is_search_match:
                    # Border on top
                    pygame.draw.rect(self.screen, (50, 50, 255), s.rect, 1)

            # Draw Constellation Lines ON TOP of Unrelated Sprites
            related_nodes = set()
            
            if self.selected_sprite:
                char = self.selected_sprite.char
                if char in self.relationships:
                    rels = self.relationships[char]
                    
                    # Highlight color (Light Blue)
                    line_color = (100, 100, 255)
                    
                    # Add to related set for later highlighting
                    related_nodes.add(self.selected_sprite)
                    
                    # Parents
                    for p_char in rels['parents']:
                        if p_char in self.sprite_map:
                            target_s = self.sprite_map[p_char]
                            pygame.draw.line(self.screen, line_color, self.selected_sprite.rect.center, target_s.rect.center, 1)
                            related_nodes.add(target_s)

                    # Children
                    for c_char in rels['children']:
                        if c_char in self.sprite_map:
                            target_s = self.sprite_map[c_char]
                            pygame.draw.line(self.screen, line_color, self.selected_sprite.rect.center, target_s.rect.center, 1)
                            related_nodes.add(target_s)
            
            # Re-draw related nodes on top with blue highlight
            for s in related_nodes:
                # Render text in blue
                # We can't easily change the sprite's internal cached image without re-rendering every frame which is slow?
                # Actually, 50 chars is fine.
                
                # Create a temporary surface for the highlight
                # Use the same font logic as KanjiSprite
                # We need the original font size... let's just use self.render_font or s.image with tint?
                # Tinting is hard in Pygame <= 1.9 (if user has old one), but add/mult blend works.
                # Easiest: just re-render.
                
                highlight_color = (80, 80, 255) # Blue-ish
                
                # Reuse the existing image if possible? No, color is baked.
                # Let's assume re-render is fast enough for <100 chars.
                # If s.image size is known...
                
                # To match exactly:
                target_h = s.rect.height
                # We need to re-render in high res and scale down to match s.image logic
                original_surface = self.render_font.render(s.char, True, highlight_color)
                scale = target_h / original_surface.get_height()
                target_w = int(original_surface.get_width() * scale)
                
                # Ensure we match the current rect size exactly or it might jitter
                # Actually s.rect matches the final size.
                high_s = pygame.transform.smoothscale(original_surface, (s.rect.width, s.rect.height))
                
                self.screen.blit(high_s, s.rect)



            self.draw_ui()
            
            if self.selected_sprite:
                self.draw_info_panel(self.selected_sprite)
            
            # Draw simple tooltip
            if self.hovered_sprite and not (self.selected_sprite and mx > self.w - 300):
                 self.draw_tooltip(self.hovered_sprite, mx, my)
            
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()

    def draw_tooltip(self, sprite, mx, my):
        # Lightweight tooltip near mouse
        text = sprite.char
        surf = self.header_font.render(text, True, (80, 80, 80)) # Dark gray text
        
        # Add a small background
        padding = 10
        w, h = surf.get_size()
        bg_rect = pygame.Rect(mx + 15, my - 40, w + padding*2, h + padding*2)
        
        # Keep on screen
        if bg_rect.right > self.w: bg_rect.right = self.w - 10
        if bg_rect.top < 0: bg_rect.top = 10
        
        # Shadow
        shadow_rect = bg_rect.copy()
        shadow_rect.move_ip(2, 2)
        s = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        s.fill((0, 0, 0, 30))
        self.screen.blit(s, shadow_rect)
        
        pygame.draw.rect(self.screen, HOVER_BG_COLOR, bg_rect, border_radius=4)
        pygame.draw.rect(self.screen, HOVER_BORDER_COLOR, bg_rect, width=1, border_radius=4)
        
        self.screen.blit(surf, (bg_rect.x + padding, bg_rect.y + padding))

    def draw_info_panel(self, sprite):
        # Panel on the right side
        panel_w = 300
        panel_h = self.h
        
        # Transparent Background
        s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        s.fill(UI_BG_COLOR)
        self.screen.blit(s, (self.w - panel_w, 0))
        
        # Border
        pygame.draw.line(self.screen, UI_BORDER_COLOR, (self.w - panel_w, 0), (self.w - panel_w, self.h), 1)
        
        # Content
        cx = self.w - panel_w + 30
        cy = 50
        
        # Big Char
        char_surf = self.header_font.render(sprite.char, True, ACCENT_COLOR)
        self.screen.blit(char_surf, (cx, cy))
        cy += 80
        
        # Metrics
        for key in METRICS:
            label = METRIC_LABELS[key]
            # Use smaller font for label
            lsurf = self.ui_font.render(label, True, (100, 100, 100))
            self.screen.blit(lsurf, (cx, cy))
            cy += 20
            
            val = sprite.metrics[key]
            # Darker text for value
            vsurf = self.ui_font.render(f"{val:.4f}", True, (20, 20, 20))
            self.screen.blit(vsurf, (cx, cy))
            cy += 30
            
            pygame.draw.line(self.screen, (220, 220, 220), (cx, cy - 5), (self.w - 30, cy - 5), 1)
            cy += 10

    def draw_ui(self):
        # Hide UI if idle
        current_time = pygame.time.get_ticks()
        if current_time - self.last_interaction_time > self.idle_timeout:
            return

        for el in self.ui_elements:
            # Check if it's a font button
            active = False
            if hasattr(self, 'font_buttons') and el in self.font_buttons:
                # Find index
                idx = self.font_buttons.index(el)
                if idx == self.current_font_idx:
                    active = True
                    
            if isinstance(el, Button):
                 if active:
                     el.draw(self.screen, active=True)
                 else:
                     el.draw(self.screen)
            else:
                 el.draw(self.screen)

if __name__ == "__main__":
    App().run()