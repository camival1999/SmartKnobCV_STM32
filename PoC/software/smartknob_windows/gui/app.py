"""
SmartKnob GUI — Tkinter frontend for SmartKnobDriver.

All serial communication is handled by SmartKnobDriver (smartknob.driver).
This file is pure GUI: widgets, layout, and event wiring.
"""

import tkinter as tk
from tkinter import ttk

from smartknob.driver import SmartKnobDriver
from smartknob.protocol import HapticMode

try:
    from smartknob_windows.windows_link import WindowsLink
    WINDOWS_LINK_AVAILABLE = True
except ImportError:
    WINDOWS_LINK_AVAILABLE = False

class SmartKnobGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SmartKnob Simple")
        self.root.geometry("600x700")  # Smaller window, content is scrollable
        
        # Serial driver (GUI-independent, thread-safe)
        self.driver = SmartKnobDriver()
        self.driver.on_position = self._on_driver_position
        self.driver.on_ack = self._on_driver_ack
        self.driver.on_seek_done = self._on_driver_seek_done
        self.driver.on_raw = self._on_driver_raw

        self.current_angle = 0.0
        self._pending_zoom_data: dict | None = None  # Tracks pending zoom link
        
        # Windows integration
        if WINDOWS_LINK_AVAILABLE:
            self.windows_link = WindowsLink()
        else:
            self.windows_link = None
        self.mode_buttons = []  # Store mode radio buttons for disable/enable
        
        self._build_ui()
    
    def _build_ui(self):
        # === Scrollable Container ===
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.main_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.main_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Bind mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # === Connection Frame ===
        conn_frame = ttk.LabelFrame(self.main_frame, text="Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=15)
        self.port_combo.pack(side="left", padx=5)
        
        ttk.Button(conn_frame, text="Refresh", command=self._refresh_ports).pack(side="left", padx=2)
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self._toggle_connect)
        self.connect_btn.pack(side="left", padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.pack(side="right")
        
        # === Mode Frame ===
        mode_frame = ttk.LabelFrame(self.main_frame, text="Mode", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)
        
        self.mode_var = tk.StringVar(value="HAPTIC")
        
        btn_haptic = ttk.Radiobutton(mode_frame, text="Haptic", variable=self.mode_var, 
                                     value="HAPTIC", command=self._set_mode)
        btn_haptic.pack(side="left", padx=10)
        
        btn_inertia = ttk.Radiobutton(mode_frame, text="Inertia", variable=self.mode_var,
                                      value="INERTIA", command=self._set_mode)
        btn_inertia.pack(side="left", padx=10)
        
        btn_spring = ttk.Radiobutton(mode_frame, text="Spring", variable=self.mode_var,
                                     value="SPRING", command=self._set_mode)
        btn_spring.pack(side="left", padx=10)
        
        btn_bounded = ttk.Radiobutton(mode_frame, text="Bounded", variable=self.mode_var,
                                      value="BOUNDED", command=self._set_mode)
        btn_bounded.pack(side="left", padx=10)
        
        self.mode_buttons = [btn_haptic, btn_inertia, btn_spring, btn_bounded]
        
        # === Angle Display ===
        angle_frame = ttk.LabelFrame(self.main_frame, text="Position", padding=10)
        angle_frame.pack(fill="x", padx=10, pady=5)
        
        self.angle_label = ttk.Label(angle_frame, text="0.0°", font=("Consolas", 24))
        self.angle_label.pack()
        
        # === Haptic Parameters ===
        haptic_frame = ttk.LabelFrame(self.main_frame, text="Haptic Parameters", padding=10)
        haptic_frame.pack(fill="x", padx=10, pady=5)
        
        # Detent Count
        ttk.Label(haptic_frame, text="Detent Count:").grid(row=0, column=0, sticky="w")
        self.detent_count_var = tk.IntVar(value=36)
        self.detent_count_scale = ttk.Scale(haptic_frame, from_=2, to=72, variable=self.detent_count_var,
                                            orient="horizontal", length=200)
        self.detent_count_scale.grid(row=0, column=1, padx=5)
        self.detent_count_label = ttk.Label(haptic_frame, text="36")
        self.detent_count_label.grid(row=0, column=2)
        self.detent_count_scale.bind("<ButtonRelease-1>", self._send_detent_count)
        self.detent_count_var.trace_add("write", lambda *_: self.detent_count_label.config(text=str(int(self.detent_count_var.get()))))
        
        # Detent Strength
        ttk.Label(haptic_frame, text="Detent Strength:").grid(row=1, column=0, sticky="w")
        self.detent_strength_var = tk.DoubleVar(value=1.5)
        self.detent_strength_scale = ttk.Scale(haptic_frame, from_=0.5, to=6.0, variable=self.detent_strength_var,
                                               orient="horizontal", length=200)
        self.detent_strength_scale.grid(row=1, column=1, padx=5)
        self.detent_strength_label = ttk.Label(haptic_frame, text="1.5")
        self.detent_strength_label.grid(row=1, column=2)
        self.detent_strength_scale.bind("<ButtonRelease-1>", self._send_detent_strength)
        self.detent_strength_var.trace_add("write", lambda *_: self.detent_strength_label.config(text=f"{self.detent_strength_var.get():.1f}"))
        
        # === Inertia Parameters ===
        inertia_frame = ttk.LabelFrame(self.main_frame, text="Inertia Parameters", padding=10)
        inertia_frame.pack(fill="x", padx=10, pady=5)
        
        # Inertia (mass)
        ttk.Label(inertia_frame, text="Inertia (J):").grid(row=0, column=0, sticky="w")
        self.inertia_var = tk.DoubleVar(value=5.0)
        self.inertia_scale = ttk.Scale(inertia_frame, from_=1, to=20, variable=self.inertia_var,
                                       orient="horizontal", length=200)
        self.inertia_scale.grid(row=0, column=1, padx=5)
        self.inertia_label = ttk.Label(inertia_frame, text="5.0")
        self.inertia_label.grid(row=0, column=2)
        self.inertia_scale.bind("<ButtonRelease-1>", self._send_inertia)
        self.inertia_var.trace_add("write", lambda *_: self.inertia_label.config(text=f"{self.inertia_var.get():.1f}"))
        
        # Damping
        ttk.Label(inertia_frame, text="Damping (B):").grid(row=1, column=0, sticky="w")
        self.damping_var = tk.DoubleVar(value=1.0)
        self.damping_scale = ttk.Scale(inertia_frame, from_=0, to=5, variable=self.damping_var,
                                       orient="horizontal", length=200)
        self.damping_scale.grid(row=1, column=1, padx=5)
        self.damping_label = ttk.Label(inertia_frame, text="1.0")
        self.damping_label.grid(row=1, column=2)
        self.damping_scale.bind("<ButtonRelease-1>", self._send_damping)
        self.damping_var.trace_add("write", lambda *_: self.damping_label.config(text=f"{self.damping_var.get():.1f}"))
        
        # Coupling
        ttk.Label(inertia_frame, text="Coupling (K):").grid(row=2, column=0, sticky="w")
        self.coupling_var = tk.DoubleVar(value=40.0)
        self.coupling_scale = ttk.Scale(inertia_frame, from_=10, to=100, variable=self.coupling_var,
                                        orient="horizontal", length=200)
        self.coupling_scale.grid(row=2, column=1, padx=5)
        self.coupling_label = ttk.Label(inertia_frame, text="40.0")
        self.coupling_label.grid(row=2, column=2)
        self.coupling_scale.bind("<ButtonRelease-1>", self._send_coupling)
        self.coupling_var.trace_add("write", lambda *_: self.coupling_label.config(text=f"{self.coupling_var.get():.1f}"))
        
        # === Spring Parameters ===
        spring_frame = ttk.LabelFrame(self.main_frame, text="Spring Parameters", padding=10)
        spring_frame.pack(fill="x", padx=10, pady=5)
        
        # Stiffness
        ttk.Label(spring_frame, text="Stiffness:").grid(row=0, column=0, sticky="w")
        self.spring_stiffness_var = tk.DoubleVar(value=10.0)
        self.spring_stiffness_scale = ttk.Scale(spring_frame, from_=0.5, to=30.0, variable=self.spring_stiffness_var,
                                                orient="horizontal", length=200)
        self.spring_stiffness_scale.grid(row=0, column=1, padx=5)
        self.spring_stiffness_label = ttk.Label(spring_frame, text="10.0")
        self.spring_stiffness_label.grid(row=0, column=2)
        self.spring_stiffness_scale.bind("<ButtonRelease-1>", self._send_spring_stiffness)
        self.spring_stiffness_var.trace_add("write", lambda *_: self.spring_stiffness_label.config(text=f"{self.spring_stiffness_var.get():.1f}"))
        
        # Damping
        ttk.Label(spring_frame, text="Damping:").grid(row=1, column=0, sticky="w")
        self.spring_damping_var = tk.DoubleVar(value=0.1)
        self.spring_damping_scale = ttk.Scale(spring_frame, from_=0, to=2.0, variable=self.spring_damping_var,
                                              orient="horizontal", length=200)
        self.spring_damping_scale.grid(row=1, column=1, padx=5)
        self.spring_damping_label = ttk.Label(spring_frame, text="0.1")
        self.spring_damping_label.grid(row=1, column=2)
        self.spring_damping_scale.bind("<ButtonRelease-1>", self._send_spring_damping)
        self.spring_damping_var.trace_add("write", lambda *_: self.spring_damping_label.config(text=f"{self.spring_damping_var.get():.1f}"))
        
        # Center display and button
        ttk.Label(spring_frame, text="Center:").grid(row=2, column=0, sticky="w")
        self.spring_center_label = ttk.Label(spring_frame, text="0.0°", font=("Consolas", 10))
        self.spring_center_label.grid(row=2, column=1, sticky="w", padx=5)
        ttk.Button(spring_frame, text="Set Center Here", command=self._send_set_center).grid(row=2, column=2, padx=5)
        
        # === Bounded Parameters ===
        bounded_frame = ttk.LabelFrame(self.main_frame, text="Bounded Parameters", padding=10)
        bounded_frame.pack(fill="x", padx=10, pady=5)
        
        # Lower Bound
        ttk.Label(bounded_frame, text="Lower Bound:").grid(row=0, column=0, sticky="w")
        self.bound_lower_var = tk.StringVar(value="-60")
        self.bound_lower_entry = ttk.Entry(bounded_frame, textvariable=self.bound_lower_var, width=8)
        self.bound_lower_entry.grid(row=0, column=1, padx=5, sticky="w")
        self.bound_lower_entry.bind("<Return>", self._send_lower_bound)
        ttk.Label(bounded_frame, text="°").grid(row=0, column=2, sticky="w")
        ttk.Button(bounded_frame, text="Set", command=self._send_lower_bound, width=5).grid(row=0, column=3, padx=5)
        
        # Upper Bound
        ttk.Label(bounded_frame, text="Upper Bound:").grid(row=1, column=0, sticky="w")
        self.bound_upper_var = tk.StringVar(value="60")
        self.bound_upper_entry = ttk.Entry(bounded_frame, textvariable=self.bound_upper_var, width=8)
        self.bound_upper_entry.grid(row=1, column=1, padx=5, sticky="w")
        self.bound_upper_entry.bind("<Return>", self._send_upper_bound)
        ttk.Label(bounded_frame, text="°").grid(row=1, column=2, sticky="w")
        ttk.Button(bounded_frame, text="Set", command=self._send_upper_bound, width=5).grid(row=1, column=3, padx=5)
        
        # Wall Strength
        ttk.Label(bounded_frame, text="Wall Strength:").grid(row=2, column=0, sticky="w")
        self.wall_strength_var = tk.DoubleVar(value=20.0)
        self.wall_strength_scale = ttk.Scale(bounded_frame, from_=1.0, to=30.0, variable=self.wall_strength_var,
                                             orient="horizontal", length=150)
        self.wall_strength_scale.grid(row=2, column=1, columnspan=2, padx=5, sticky="w")
        self.wall_strength_label = ttk.Label(bounded_frame, text="20.0")
        self.wall_strength_label.grid(row=2, column=3)
        self.wall_strength_scale.bind("<ButtonRelease-1>", self._send_wall_strength)
        self.wall_strength_var.trace_add("write", lambda *_: self.wall_strength_label.config(text=f"{self.wall_strength_var.get():.1f}"))
        
        # Note: Bounded mode uses Haptic Parameters for detent count/strength
        ttk.Label(bounded_frame, text="(Uses Haptic detent count/strength)", 
                  font=("TkDefaultFont", 8, "italic")).grid(row=3, column=0, columnspan=4, pady=(5,0))
        
        # === Position Control ===
        pos_frame = ttk.LabelFrame(self.main_frame, text="Position Control", padding=10)
        pos_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(pos_frame, text="Go to angle:").pack(side="left")
        self.target_angle_var = tk.StringVar(value="0")
        self.target_entry = ttk.Entry(pos_frame, textvariable=self.target_angle_var, width=8)
        self.target_entry.pack(side="left", padx=5)
        self.target_entry.bind("<Return>", self._send_seek_angle)
        ttk.Label(pos_frame, text="°").pack(side="left")
        
        ttk.Button(pos_frame, text="Go", command=self._send_seek_angle, width=5).pack(side="left", padx=5)
        ttk.Button(pos_frame, text="Go to 0°", command=self._send_seek_zero, width=8).pack(side="left", padx=5)
        
        # === PID Tuning ===
        pid_frame = ttk.LabelFrame(self.main_frame, text="Position PID Tuning", padding=10)
        pid_frame.pack(fill="x", padx=10, pady=5)
        
        # P gain (using tk.Scale for resolution support)
        ttk.Label(pid_frame, text="P Gain:").grid(row=0, column=0, sticky="w")
        self.pid_p_var = tk.DoubleVar(value=50.0)
        self.pid_p_scale = tk.Scale(pid_frame, from_=0, to=100, variable=self.pid_p_var,
                                    orient="horizontal", length=200, resolution=0.5,
                                    showvalue=False, command=lambda v: self._on_pid_p_change(v))
        self.pid_p_scale.grid(row=0, column=1, padx=5)
        self.pid_p_label = ttk.Label(pid_frame, text="50.00", width=6)
        self.pid_p_label.grid(row=0, column=2)
        self.pid_p_scale.bind("<ButtonRelease-1>", self._send_pid_p)
        
        # I gain
        ttk.Label(pid_frame, text="I Gain:").grid(row=1, column=0, sticky="w")
        self.pid_i_var = tk.DoubleVar(value=0.0)
        self.pid_i_scale = tk.Scale(pid_frame, from_=0, to=5, variable=self.pid_i_var,
                                    orient="horizontal", length=200, resolution=0.05,
                                    showvalue=False, command=lambda v: self._on_pid_i_change(v))
        self.pid_i_scale.grid(row=1, column=1, padx=5)
        self.pid_i_label = ttk.Label(pid_frame, text="0.00", width=6)
        self.pid_i_label.grid(row=1, column=2)
        self.pid_i_scale.bind("<ButtonRelease-1>", self._send_pid_i)
        
        # D gain
        ttk.Label(pid_frame, text="D Gain:").grid(row=2, column=0, sticky="w")
        self.pid_d_var = tk.DoubleVar(value=0.3)
        self.pid_d_scale = tk.Scale(pid_frame, from_=0, to=5, variable=self.pid_d_var,
                                    orient="horizontal", length=200, resolution=0.1,
                                    showvalue=False, command=lambda v: self._on_pid_d_change(v))
        self.pid_d_scale.grid(row=2, column=1, padx=5)
        self.pid_d_label = ttk.Label(pid_frame, text="0.30", width=6)
        self.pid_d_label.grid(row=2, column=2)
        self.pid_d_scale.bind("<ButtonRelease-1>", self._send_pid_d)
        
        # Velocity limit
        ttk.Label(pid_frame, text="Vel Limit:").grid(row=3, column=0, sticky="w")
        self.vel_limit_var = tk.DoubleVar(value=40.0)
        self.vel_limit_scale = tk.Scale(pid_frame, from_=0, to=100, variable=self.vel_limit_var,
                                        orient="horizontal", length=200, resolution=1,
                                        showvalue=False, command=lambda v: self._on_vel_limit_change(v))
        self.vel_limit_scale.grid(row=3, column=1, padx=5)
        self.vel_limit_label = ttk.Label(pid_frame, text="40.00", width=6)
        self.vel_limit_label.grid(row=3, column=2)
        self.vel_limit_scale.bind("<ButtonRelease-1>", self._send_vel_limit)
        self.vel_limit_var.trace_add("write", lambda *_: self.vel_limit_label.config(text=f"{self.vel_limit_var.get():.2f}"))
        
        # === Windows Link ===
        if WINDOWS_LINK_AVAILABLE:
            self._build_windows_link_frame()
        
        # === Log ===
        log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding=5)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Initial port refresh
        self._refresh_ports()
    
    def _refresh_ports(self):
        ports = SmartKnobDriver.list_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _build_windows_link_frame(self):
        """Build the Windows Link section for binding motor to system functions."""
        link_frame = ttk.LabelFrame(self.main_frame, text="Windows Link", padding=10)
        link_frame.pack(fill="x", padx=10, pady=5)
        
        # Row 0: Function dropdown
        ttk.Label(link_frame, text="Windows Function:").grid(row=0, column=0, sticky="w")
        self.win_function_var = tk.StringVar(value="System Volume")
        self.win_function_combo = ttk.Combobox(link_frame, textvariable=self.win_function_var,
                                                values=["System Volume", "Display Brightness", "Mouse Scroll", "Lens Zoom", "None"], 
                                                state="readonly", width=17)
        self.win_function_combo.grid(row=0, column=1, columnspan=2, padx=5, sticky="w")
        
        # Row 1: Status
        ttk.Label(link_frame, text="Status:").grid(row=1, column=0, sticky="w")
        self.win_link_status = ttk.Label(link_frame, text="○ Not Linked", foreground="gray")
        self.win_link_status.grid(row=1, column=1, columnspan=2, sticky="w", padx=5)
        
        # Row 2: Volume display (when linked)
        self.win_volume_label = ttk.Label(link_frame, text="", font=("Consolas", 12))
        self.win_volume_label.grid(row=2, column=0, columnspan=3, pady=(5, 0))
        
        # Row 3: Link/Unlink buttons
        btn_frame = ttk.Frame(link_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        
        self.link_btn = ttk.Button(btn_frame, text="Link", command=self._link_windows, width=10)
        self.link_btn.pack(side="left", padx=5)
        
        self.unlink_btn = ttk.Button(btn_frame, text="Unlink", command=self._unlink_windows, 
                                     width=10, state="disabled")
        self.unlink_btn.pack(side="left", padx=5)
    
    def _link_windows(self):
        """Link motor to selected Windows function."""
        if not self.windows_link or not self.driver.is_connected:
            self._log("Cannot link: Not connected or Windows link unavailable")
            return
        
        func = self.win_function_var.get()
        if func == "None":
            self._unlink_windows()
            return
        
        if func == "System Volume":
            try:
                # Sync bounds from GUI settings
                lower = float(self.bound_lower_var.get())
                upper = float(self.bound_upper_var.get())
                self.windows_link.update_bounds(lower, upper)
                
                # Get current volume and calculate target angle
                target_angle = self.windows_link.link_volume()
                current_val = self.windows_link.get_current_volume_percent()
                
                self._log(f"Linking to volume (currently {current_val}%)")
                
                # Switch to Bounded mode and seek to current volume position
                self.driver.set_mode(HapticMode.BOUNDED)
                self.driver.seek(target_angle)
                
                # Update UI
                self.win_link_status.config(text="● Volume", foreground="green")
                self.win_volume_label.config(text=f"Volume: {current_val}%")
                self.link_btn.config(state="disabled")
                self.unlink_btn.config(state="normal")
                
                # Disable mode buttons (motor is now controlled by Windows link)
                for btn in self.mode_buttons:
                    btn.config(state="disabled")
                
                self._log(f"Linked! Motor seeking to {target_angle:.1f}° → Bounded mode")
                
            except Exception as e:
                self._log(f"Link failed: {e}")
                self.windows_link.unlink()
        
        elif func == "Display Brightness":
            try:
                # Check if brightness control is available
                if not self.windows_link.is_brightness_available():
                    self._log("Brightness control not available (typically laptop-only)")
                    return
                
                # Sync bounds from GUI settings
                lower = float(self.bound_lower_var.get())
                upper = float(self.bound_upper_var.get())
                self.windows_link.update_bounds(lower, upper)
                
                # Get current brightness and calculate target angle
                target_angle = self.windows_link.link_brightness()
                current_val = self.windows_link.get_current_brightness_percent()
                
                self._log(f"Linking to brightness (currently {current_val}%)")
                
                # Switch to Bounded mode and seek to current brightness position
                self.driver.set_mode(HapticMode.BOUNDED)
                self.driver.seek(target_angle)
                
                # Update UI
                self.win_link_status.config(text="● Brightness", foreground="green")
                self.win_volume_label.config(text=f"Brightness: {current_val}%")
                self.link_btn.config(state="disabled")
                self.unlink_btn.config(state="normal")
                
                # Disable mode buttons
                for btn in self.mode_buttons:
                    btn.config(state="disabled")
                
                self._log(f"Linked! Motor seeking to {target_angle:.1f}° → Bounded mode")
                
            except Exception as e:
                self._log(f"Brightness link failed: {e}")
                self.windows_link.unlink()
        
        elif func == "Mouse Scroll":
            try:
                # Link to scroll (no position sync needed - infinite rotation)
                self.windows_link.link_scroll()
                
                self._log("Linking to mouse scroll (Inertia mode)")
                
                # Switch to Inertia mode for infinite rotation with momentum
                self.driver.set_mode(HapticMode.INERTIA)
                
                # Update UI
                self.win_link_status.config(text="● Scroll", foreground="green")
                self.win_volume_label.config(text="Spin to scroll")
                self.link_btn.config(state="disabled")
                self.unlink_btn.config(state="normal")
                
                # Disable mode buttons
                for btn in self.mode_buttons:
                    btn.config(state="disabled")
                
                self._log("Linked! Motor in Inertia mode - spin to scroll")
                
            except Exception as e:
                self._log(f"Scroll link failed: {e}")
                self.windows_link.unlink()
        
        elif func == "Lens Zoom":
            try:
                # Check if zoom control is available
                if not self.windows_link.is_zoom_available():
                    self._log("Zoom control not available")
                    return
                
                # Link to lens zoom (magnifying glass follows cursor)
                self.windows_link.link_zoom()
                current_zoom = self.windows_link.get_current_zoom_percent()
                
                self._log(f"Linking to lens zoom (follows cursor)")
                
                # Disable buttons during seek
                self.link_btn.config(state="disabled")
                for btn in self.mode_buttons:
                    btn.config(state="disabled")
                
                # Store zoom data — on_seek_done will complete the link
                self._pending_zoom_data = {"zoom_percent": current_zoom}
                
                # Seek to 0°; on_seek_done callback will finish setup
                self.driver.seek_zero()
                self._log("Seeking to 0°...")
                self.win_link_status.config(text="○ Seeking...", foreground="orange")
                self.win_volume_label.config(text="Target: 0°")
                
            except Exception as e:
                self._log(f"Lens zoom link failed: {e}")
                self._pending_zoom_data = None
                self.windows_link.unlink()
    
    def _unlink_windows(self):
        """Unlink motor from Windows function."""
        if self.windows_link:
            self.windows_link.unlink()
        
        # Cancel any pending zoom link
        self._pending_zoom_data = None
        
        # Update UI
        self.win_link_status.config(text="○ Not Linked", foreground="gray")
        self.win_volume_label.config(text="")
        self.link_btn.config(state="normal")
        self.unlink_btn.config(state="disabled")
        
        # Re-enable mode buttons
        for btn in self.mode_buttons:
            btn.config(state="normal")
        
        self._log("Windows link disconnected")
    
    def _complete_zoom_link(self, current_zoom):
        """Called when motor has reached 0° — activate spring mode for zoom."""
        self.driver.set_mode(HapticMode.SPRING)
        
        # Update UI
        self.win_link_status.config(text="● Lens", foreground="green")
        self.win_volume_label.config(text=f"Lens: {current_zoom}%")
        self.unlink_btn.config(state="normal")
        
        self._log("Seek done! Spring mode active. Turn to zoom")

    def _toggle_connect(self):
        if self.driver.is_connected:
            self._disconnect()
        else:
            self._connect()
    
    def _connect(self):
        port = self.port_var.get()
        if not port:
            self._log("No port selected")
            return
        try:
            self.driver.connect(port)
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="Connected", foreground="green")
            self._log(f"Connected to {port}")
            
            # Query state
            self.driver.query_state()
        except Exception as e:
            self._log(f"Connection failed: {e}")
    
    def _disconnect(self):
        self.driver.disconnect()
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Disconnected", foreground="red")
        self._log("Disconnected")
    
    # === Driver callbacks (called from reader thread — schedule to GUI) ===
    
    def _on_driver_position(self, angle_deg: float) -> None:
        """Handle position update from driver (reader thread)."""
        self.current_angle = angle_deg
        self.root.after(0, lambda a=angle_deg: self._update_position_display(a))

    def _on_driver_ack(self, ack_text: str) -> None:
        """Handle acknowledgment from driver (reader thread)."""
        self._log(f"ACK: {ack_text}")

    def _on_driver_seek_done(self) -> None:
        """Handle seek completion from driver (reader thread)."""
        if self._pending_zoom_data:
            zoom_pct = self._pending_zoom_data["zoom_percent"]
            self._pending_zoom_data = None
            self.root.after(0, lambda: self._complete_zoom_link(zoom_pct))

    def _on_driver_raw(self, line: str) -> None:
        """Handle unrecognised serial line from driver (reader thread)."""
        self._log(f"RX: {line}")
    
    def _update_position_display(self, angle):
        """Update position display and process Windows link if active."""
        self.angle_label.config(text=f"{angle:.1f}°")
        
        # Process Windows link if active
        if self.windows_link and self.windows_link.is_linked:
            result = self.windows_link.process_position(angle)
            if result and hasattr(self, 'win_volume_label'):
                func = result.get("function")
                percent = result.get("percent", 0)
                if func == "volume":
                    self.win_volume_label.config(text=f"Volume: {percent}%")
                elif func == "brightness":
                    self.win_volume_label.config(text=f"Brightness: {percent}%")
                elif func == "scroll":
                    units = result.get("units", 0)
                    direction = result.get("direction", "none")
                    if units != 0:
                        arrow = "↑" if direction == "up" else "↓"
                        # Show approximate lines (120 units = 1 line)
                        lines = abs(units) / 120
                        if lines >= 1:
                            self.win_volume_label.config(text=f"Scroll: {arrow} {lines:.1f} lines")
                        else:
                            self.win_volume_label.config(text=f"Scroll: {arrow}")
                elif func == "zoom":
                    action = result.get("action", "hold")
                    if action == "zoom_in":
                        self.win_volume_label.config(text=f"Zoom: {percent}% 🔍+")
                    elif action == "zoom_out":
                        self.win_volume_label.config(text=f"Zoom: {percent}% 🔍-")
                    else:
                        self.win_volume_label.config(text=f"Zoom: {percent}%")
    
    def _log(self, msg):
        def _append():
            self.log_text.insert("end", f"{msg}\n")
            self.log_text.see("end")
            # Trim if too long
            if int(self.log_text.index("end-1c").split(".")[0]) > 100:
                self.log_text.delete("1.0", "50.0")
        self.root.after(0, _append)
    
    # === Command senders (delegate to driver) ===
    def _set_mode(self):
        mode = self.mode_var.get()
        if mode == "HAPTIC":
            self.driver.set_mode(HapticMode.HAPTIC)
        elif mode == "INERTIA":
            self.driver.set_mode(HapticMode.INERTIA)
        elif mode == "SPRING":
            self.driver.set_mode(HapticMode.SPRING)
            # Update center display when entering spring mode
            self.spring_center_label.config(text=f"{self.current_angle:.1f}°")
        elif mode == "BOUNDED":
            self.driver.set_mode(HapticMode.BOUNDED)
    
    def _send_detent_count(self, event=None):
        self.driver.set_detent_count(int(self.detent_count_var.get()))
    
    def _send_detent_strength(self, event=None):
        self.driver.set_detent_strength(self.detent_strength_var.get())
    
    def _send_inertia(self, event=None):
        self.driver.set_inertia(self.inertia_var.get())
    
    def _send_damping(self, event=None):
        self.driver.set_damping(self.damping_var.get())
    
    def _send_coupling(self, event=None):
        self.driver.set_coupling(self.coupling_var.get())
    
    def _send_spring_stiffness(self, event=None):
        self.driver.set_spring_stiffness(self.spring_stiffness_var.get())
    
    def _send_spring_damping(self, event=None):
        self.driver.set_spring_damping(self.spring_damping_var.get())
    
    def _send_set_center(self):
        self.driver.set_spring_center()  # None = use current position
        # Update the center display with current angle
        self.spring_center_label.config(text=f"{self.current_angle:.1f}°")
    
    def _send_lower_bound(self, event=None):
        try:
            val = float(self.bound_lower_var.get())
            self.driver.set_lower_bound(val)
        except ValueError:
            self._log("Invalid lower bound value")
    
    def _send_upper_bound(self, event=None):
        try:
            val = float(self.bound_upper_var.get())
            self.driver.set_upper_bound(val)
        except ValueError:
            self._log("Invalid upper bound value")
    
    def _send_wall_strength(self, event=None):
        self.driver.set_wall_strength(self.wall_strength_var.get())
    
    def _send_seek_angle(self, event=None):
        try:
            angle = float(self.target_angle_var.get())
            self.driver.seek(angle)
        except ValueError:
            self._log("Invalid angle value")
    
    def _send_seek_zero(self):
        self.target_angle_var.set("0")
        self.driver.seek_zero()
    
    def _send_pid_p(self, event=None):
        self.driver.set_pid_p(self.pid_p_var.get())
    
    def _send_pid_i(self, event=None):
        self.driver.set_pid_i(self.pid_i_var.get())
    
    def _send_pid_d(self, event=None):
        self.driver.set_pid_d(self.pid_d_var.get())
    
    def _send_vel_limit(self, event=None):
        self.driver.set_velocity_limit(self.vel_limit_var.get())
    
    # PID label update callbacks (called on every slider change)
    def _on_pid_p_change(self, val):
        self.pid_p_label.config(text=f"{float(val):.2f}")
    
    def _on_pid_i_change(self, val):
        self.pid_i_label.config(text=f"{float(val):.2f}")
    
    def _on_pid_d_change(self, val):
        self.pid_d_label.config(text=f"{float(val):.2f}")
    
    def _on_vel_limit_change(self, val):
        self.vel_limit_label.config(text=f"{float(val):.2f}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartKnobGUI(root)
    root.mainloop()
