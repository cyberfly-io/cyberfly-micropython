import time, gc
from micropython import const

try:
    import ubluetooth as bluetooth
except ImportError:
    bluetooth = None

try:
    import ujson as json
except Exception:
    import json

try:
    from .config import save_config
except Exception:
    from config import save_config

try:
    from .platform_compat import Pin
except ImportError:
    try:
        from platform_compat import Pin
    except ImportError:
        try:
            from machine import Pin
        except ImportError:
            Pin = None

# === Frontend alignment constants ===
# (Must match React UI: SERVICE_UUID, RX_CHAR_UUID, TX_CHAR_UUID, MAX_JSON_SIZE=384, FRAGMENT_TIMEOUT_MS=2000)
_SERVICE_UUID_STR = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
_RX_UUID_STR      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # Write (client -> device)
_TX_UUID_STR      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Notify (device -> client)

_MAX_RX            = const(384)    # MUST stay in sync with frontend MAX_JSON_SIZE
_FRAGMENT_TIMEOUT_MS = const(2000) # Match frontend FRAGMENT_TIMEOUT_MS
_ADV_INTERVAL_MS   = const(100)

# Status / error strings expected by frontend
_STATUS_READY    = b'{"status":"ready"}'
_STATUS_SAVED    = b'{"status":"saved"}'
_ERROR_BAD_JSON  = b'{"status":"error","msg":"bad_json"}'
_ERROR_SAVE_FAIL = b'{"status":"error","msg":"save_failed"}'
# Missing fields pattern: {"status":"error","msg":"missing:<csv>"}

# IRQ constants (MicroPython)
_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

def _safe_decode(b):
    if not b:
        return ""
    try:
        return b.decode("utf-8", "ignore")
    except Exception:
        return ""

class BleProvisioner:
    __slots__ = (
        "name","timeout_s","log","auto_reset",
        "_ble","_conn","_rx_handle","_tx_handle",
        "_rx_buf","_last_frag_ms","_saved","_connected",
        "_svc_uuid","_rx_uuid","_tx_uuid","_last_ping",
        "_led_pin","_led_state","_last_blink",
        "_connection_attempts","_mtu_size","_advertising"
    )

    def __init__(self, name="CYBERFLY-SETUP", timeout_s=180, log=False, auto_reset=True):
        self.name        = (name or "CYBERFLY-SETUP")[:20]
        self.timeout_s   = int(max(30, min(timeout_s, 600)))
        self.log         = bool(log)
        self.auto_reset  = bool(auto_reset)

        self._ble        = None
        self._conn       = None
        self._rx_handle  = None
        self._tx_handle  = None
        self._rx_buf     = bytearray()
        self._last_frag_ms = 0
        self._saved      = False
        self._connected  = False
        self._last_ping  = 0
        self._connection_attempts = 0
        self._mtu_size   = 23  # Default MTU, updated after negotiation
        self._advertising = False  # Track advertising state

        self._svc_uuid = None
        self._rx_uuid  = None
        self._tx_uuid  = None
        
        # LED blinking setup (pin 2)
        self._led_pin = None
        self._led_state = False
        self._last_blink = 0
        try:
            if Pin:
                self._led_pin = Pin(2, Pin.OUT)
                self._led_pin.off()  # Start with LED off
        except Exception as e:
            self._log("LED setup failed:", e)

    def _log(self,*a):
        if self.log:
            try: print("[BLE]",*a)
            except: pass
    
    def _cleanup_ble(self):
        """Cleanup BLE resources and turn off LED"""
        self._log("cleaning up BLE...")
        
        # Turn off LED
        if self._led_pin:
            try:
                self._led_pin.off()
                self._log("LED off")
            except Exception as e:
                self._log("LED off failed:", e)
        
        # Stop advertising
        if self._ble:
            try:
                self._ble.gap_advertise(None)
                self._advertising = False
                self._log("advertising stopped")
            except Exception as e:
                self._log("stop advertising failed:", e)
            
            # Disconnect if connected
            if self._conn:
                try:
                    # There's no explicit disconnect in MicroPython BLE
                    # but we can clear the connection
                    self._conn = None
                    self._connected = False
                    self._log("connection cleared")
                except Exception as e:
                    self._log("disconnect failed:", e)
            
            # Deactivate BLE
            try:
                self._ble.active(False)
                self._log("BLE deactivated")
            except Exception as e:
                self._log("BLE deactivate failed:", e)
    
    def _blink_led(self):
        """Blink LED to indicate BLE mode is active"""
        if not self._led_pin:
            return
        
        now = time.ticks_ms()
        # Blink every 500ms (2Hz)
        if time.ticks_diff(now, self._last_blink) >= 500:
            self._led_state = not self._led_state
            if self._led_state:
                self._led_pin.on()
            else:
                self._led_pin.off()
            self._last_blink = now

    def _notify_bytes(self, data):
        """Send pre-formatted bytes directly (for status messages)"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        size = len(data)
        offset = 0
        step = max(20, self._mtu_size - 3)
        chunks_sent = 0
        while offset < size:
            chunk = data[offset : offset + step]
            try:
                self._ble.gatts_notify(self._conn, self._tx_handle, chunk)
            except Exception as e:
                self._log("notify failed:", e)
                return False
            offset += step
            chunks_sent += 1
            # Only delay every 3 chunks to reduce latency
            if offset < size and chunks_sent % 3 == 0:
                time.sleep_ms(20)
        if self.log:
            print(f"[BLE] Sent {chunks_sent} chunks ({size} bytes)")
        return True

    def _notify_json_str(self, obj, evt="data"):
        s = json.dumps({"event": evt, "data": obj})
        size = len(s)
        offset = 0
        # Use negotiated MTU minus ATT overhead (3 bytes)
        step = max(20, self._mtu_size - 3)
        chunks_sent = 0
        while offset < size:
            chunk = s[offset : offset + step]
            try:
                self._ble.gatts_notify(self._conn, self._tx_handle, chunk)
            except Exception as e:
                self._log("notify failed:", e)
                return False
            offset += step
            chunks_sent += 1
            # Only delay every 3 chunks to reduce latency
            if offset < size and chunks_sent % 3 == 0:
                time.sleep_ms(20)
        if self.log:
            print(f"[BLE] Sent {chunks_sent} chunks ({size} bytes)")
        return True

    # ---------- Fragment Accumulation (mirrors frontend logic) ----------
    def _reset_buffer(self):
        self._rx_buf[:] = b''
        self._last_frag_ms = time.ticks_ms()

    def _append_fragment(self, frag):
        if not frag:
            return
        now = time.ticks_ms()
        # Timeout -> discard stale partial
        if self._last_frag_ms and time.ticks_diff(now, self._last_frag_ms) > _FRAGMENT_TIMEOUT_MS:
            self._reset_buffer()
        # New JSON start char resets accumulation
        first = None
        for c in frag:
            if c in (32, 9, 10, 13):
                continue
            first = c
            break
        if first == 0x7B:  # '{'
            self._reset_buffer()
        # Append with size cap (keep newest tail)
        needed = len(self._rx_buf) + len(frag)
        if needed <= _MAX_RX:
            self._rx_buf.extend(frag)
        else:
            keep = max(0, _MAX_RX - len(frag))
            if keep:
                self._rx_buf[:] = self._rx_buf[-keep:] + frag
            else:
                self._rx_buf[:] = frag[-_MAX_RX:]
        self._last_frag_ms = now

    # ---------- JSON completeness (brace balance, supports quoted wrapper) ----------
    def _is_complete(self, txt):
        s = txt.strip()
        if not s:
            return False
        # unwrap one level if quoted JSON string
        if s[0] == '"' and s[-1] == '"':
            try:
                inner = json.loads(s)
                if isinstance(inner, str):
                    s = inner.strip()
            except Exception:
                return False
        if not (s.startswith('{') and s.endswith('}')):
            return False
        depth = 0
        in_str = False
        esc = False
        for c in s:
            if esc:
                esc = False
                continue
            if c == '\\':
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth < 0:
                    return False
        return depth == 0

    # ---------- Config Processing (fields align with UI form) ----------
    def _process_config(self, raw_txt):
        s = raw_txt.strip()
        # unwrap quoted
        if s.startswith('"') and s.endswith('"'):
            try:
                unq = json.loads(s)
                if isinstance(unq, str):
                    s = unq
            except Exception:
                pass
        try:
            cfg = json.loads(s)
            self._log("parsed config:", cfg.get("config_type", "device"))
        except Exception as e:
            self._log("json parse failed:", e)
            self._notify_bytes(_ERROR_BAD_JSON)
            self._reset_buffer()
            return

        # Process device configuration
        self._process_device_config(cfg)
    
    def _process_device_config(self, cfg):
        """Process device configuration (WiFi, keys, etc.)"""
        # Accept public key at key_pair.publicKey or publicKey
        pub = cfg.get("publicKey") or (cfg.get("key_pair") or {}).get("publicKey")
        sec = cfg.get("secretKey") or (cfg.get("key_pair") or {}).get("secretKey")
        missing = []
        if not cfg.get("device_id"): missing.append("device_id")
        if not cfg.get("ssid"): missing.append("ssid")
        if not pub: missing.append("publicKey")
        if missing:
            self._notify_json_str('{"status":"error","msg":"missing:' + ",".join(missing) + '"}')
            self._reset_buffer()
            return

        final = {
            "device_id": str(cfg["device_id"])[:64],
            "ssid": str(cfg["ssid"])[:32],
            "wifi_password": str(cfg.get("wifi_password") or cfg.get("password",""))[:64],
            "network_id": str(cfg.get("network_id","mainnet01"))[:32],
            "key_pair": {
                "publicKey": str(pub)[:128],
                "secretKey": str(sec or "")[:128]
            }
        }

        try:
            save_config(final)
            self._saved = True
            self._log("device config saved")
            
            # Send saved confirmation that UI expects
            self._notify_bytes(_STATUS_SAVED)
            
            # Give time for the response to be sent and filesystem to flush
            time.sleep_ms(800)  # Increased from 500ms to ensure filesystem flush
            
            # Auto reset after successful configuration
            if self.auto_reset:
                self._log("preparing to reset...")
                time.sleep_ms(200)
                try:
                    from .platform_compat import reset
                    self._log("resetting via platform_compat...")
                    reset()
                except ImportError:
                    try:
                        from platform_compat import reset
                        self._log("resetting via platform_compat (direct)...")
                        reset()
                    except ImportError:
                        self._log("resetting via machine.reset()...")
                        import machine
                        machine.reset()
            
        except Exception as e:
            self._log("save failed", e)
            import sys
            sys.print_exception(e)
            self._notify_bytes(_ERROR_SAVE_FAIL)
        finally:
            self._reset_buffer()
    


    # ---------- IRQ Handler ----------
    def _irq(self, event, data):
        try:
            if event == _IRQ_CENTRAL_CONNECT:
                # data: (conn_handle, addr_type, addr)
                self._conn = data[0] if isinstance(data,(tuple,list)) else data
                self._connected = True
                self._connection_attempts += 1
                self._last_ping = time.ticks_ms()
                self._reset_buffer()
                self._log(f"connected conn_handle: {self._conn} (attempt {self._connection_attempts})")
                
                # MTU is negotiated by the central (client/UI)
                # We already set our preferred MTU via config(mtu=512) during init
                # The actual MTU used will be min(our_mtu, client_mtu)
                # MicroPython doesn't provide a way to query the negotiated MTU on peripheral side
                # So we use our configured MTU as a reasonable assumption
                # Note: This is limited by the client's requested MTU
                self._log(f"using MTU: {self._mtu_size} (negotiated by central)")
                
                # Minimal settle time for faster response
                time.sleep_ms(30)
                success = self._notify_bytes(_STATUS_READY)
                self._log("ready status sent:", success)

            elif event == _IRQ_CENTRAL_DISCONNECT:
                self._log("disconnected")
                self._conn = None
                self._connected = False
                self._reset_buffer()
                if not self._saved:
                    # Quickly restart advertising for better reconnection
                    time.sleep_ms(50)
                    if self._start_advertising(fast=True):
                        self._log("re-advertising after disconnect")
                    else:
                        self._log("failed to restart advertising")

            elif event == _IRQ_GATTS_WRITE and self._connected:
                try:
                    _, attr = data
                except Exception:
                    attr = data
                    
                if attr == self._rx_handle:
                    frag = self._ble.gatts_read(self._rx_handle) or b''
                    self._log(f"received {len(frag)} bytes:", frag[:50] if len(frag) > 50 else frag)
                    self._append_fragment(frag)
                    txt = _safe_decode(self._rx_buf)
                    self._log(f"buffer now {len(txt)} chars")
                    
                    if self._is_complete(txt):
                        self._log("complete message received, processing...")
                        self._process_config(txt)
                    else:
                        self._log("waiting for more fragments...")
                        
        except Exception as e:
            self._log("irq error", e)

    # ---------- Advertising ----------
    def _adv_payload(self):
        name = self.name.encode("utf-8")
        # Enhanced advertising payload for better discoverability
        # Flags: General discoverable + BR/EDR not supported
        flags = b"\x02\x01\x06"
        # Complete local name
        name_data = bytes([len(name)+1, 0x09]) + name
        # Service UUID (16-bit shortened)
        service_uuid = b"\x03\x03\x01\x18"  # Generic Access Service
        # TX Power Level (0 dBm) for better RSSI calculation
        tx_power = b"\x02\x0A\x00"
        return flags + name_data + service_uuid + tx_power

    def _start_advertising(self, fast=True):
        if not self._ble:
            return False
        
        # Stop any existing advertising with reduced delay
        try:
            self._ble.gap_advertise(None)
            self._advertising = False
            time.sleep_ms(50)
        except Exception as e:
            self._log("stop advertising error:", e)
        
        adv = self._adv_payload()
        self._log("adv payload len:", len(adv), "data:", [hex(b) for b in adv])
        
        # Adaptive advertising: fast discovery then power-saving
        interval = 50000 if fast else 200000  # 50ms fast, 200ms slow
        
        try:
            self._ble.gap_advertise(interval, adv_data=adv)
            self._advertising = True
            self._log("advertising", self.name, f"at {interval//1000}ms interval")
            return True
        except Exception as e:
            self._log(f"adv fail {interval//1000}ms", e)
            try:
                # Fallback to 100ms interval
                self._ble.gap_advertise(100000, adv_data=adv)
                self._advertising = True
                self._log("advertising", self.name, "at 100ms interval")
                return True
            except Exception as e2:
                self._log("adv fail 100ms", e2)
                try:
                    # Last resort - minimal advertising
                    self._ble.gap_advertise(100)
                    self._advertising = True
                    self._log("advertising", self.name, "minimal mode")
                    return True
                except Exception as e3:
                    self._log("all advertising attempts failed:", e3)
                    self._advertising = False
                    return False

    # ---------- Start ----------
    def start(self):
        if not bluetooth:
            self._log("no bt")
            return False

        gc.collect()
        try:
            self._svc_uuid = bluetooth.UUID(_SERVICE_UUID_STR)
            self._rx_uuid  = bluetooth.UUID(_RX_UUID_STR)
            self._tx_uuid  = bluetooth.UUID(_TX_UUID_STR)
        except Exception as e:
            self._log("uuid fail", e)
            return False

        try:
            self._ble = bluetooth.BLE()
            self._ble.active(False)  # Reset BLE first
            time.sleep_ms(100)  # Faster init: 100ms instead of 200ms
            self._ble.active(True)
            time.sleep_ms(300)  # Faster stabilization: 300ms instead of 500ms
            self._log("ble activated")
        except Exception as e:
            self._log("ble init fail", e)
            return False

        # Enhanced BLE configuration for better discoverability
        try: 
            self._ble.config(gap_name=self.name)
            self._log("gap name set:", self.name)
        except Exception as e: 
            self._log("gap name fail", e)

        # Set connectable and discoverable with larger RX buffer
        try:
            self._ble.config(rxbuf=2048)  # Increased from 1024 to 2048
            self._log("rx buffer configured: 2048")
        except Exception:
            # rxbuf not supported in this build - safe to ignore
            pass

        # Request larger MTU for better throughput
        # This sets our maximum MTU that we'll accept from the central
        # The actual MTU used will be min(our_mtu, central_mtu)
        try: 
            self._ble.config(mtu=512)
            self._mtu_size = 512  # Track our configured MTU
            self._log("mtu configured: 512")
        except Exception:
            try:
                self._ble.config(mtu=180)
                self._mtu_size = 180  # Track our configured MTU
                self._log("mtu configured: 180")
            except Exception as e: 
                self._mtu_size = 23  # Default MTU
                self._log("mtu config fail, using default: 23", e)

        # Set connection parameters for responsiveness
        # (min_interval, max_interval, latency, timeout) in units of 1.25ms
        # 6-12 = 7.5ms-15ms intervals, 0 latency, 200*10ms = 2s timeout
        try:
            self._ble.config(conn_params=(6, 12, 0, 200))
            self._log("connection params configured")
        except Exception:
            pass  # Not all builds support this

        self._ble.irq(self._irq)

        # Register service: RX (write), then TX (notify)
        try:
            rx_flags = bluetooth.FLAG_WRITE | getattr(bluetooth,"FLAG_WRITE_NO_RESPONSE",0)
            tx_flags = getattr(bluetooth,"FLAG_NOTIFY",0) | getattr(bluetooth,"FLAG_READ",0)
            service = (self._svc_uuid, ((self._rx_uuid, rx_flags),
                                        (self._tx_uuid, tx_flags)))
            handles = self._ble.gatts_register_services((service,))
            if not handles or not handles[0] or len(handles[0]) < 2:
                self._log("bad handles", handles)
                return False
            self._rx_handle, self._tx_handle = handles[0][0], handles[0][1]
            self._log("handles rx", self._rx_handle, "tx", self._tx_handle)
        except Exception as e:
            self._log("service reg fail", e)
            return False

        if not self._start_advertising(fast=True):  # Start with fast advertising
            return False

        self._log("provisioner ready timeout", self.timeout_s, "s")
        start_ms = time.ticks_ms()
        last_gc = start_ms
        last_adv_check = start_ms
        fast_adv_until = start_ms + 60000  # Fast advertising for first 60 seconds (improved discoverability)
        
        while not self._saved:
            now = time.ticks_ms()
            if time.ticks_diff(now, start_ms) >= self.timeout_s * 1000:
                self._log("timeout")
                break
            
            # Ensure advertising is active if not connected (check every 10s)
            if not self._connected and time.ticks_diff(now, last_adv_check) > 10000:
                if not self._advertising:
                    self._log("advertising stopped unexpectedly, restarting...")
                    is_fast = now < fast_adv_until
                    self._start_advertising(fast=is_fast)
                last_adv_check = now
            
            # Switch to slow advertising after 60 seconds to save power
            if not self._connected and now > fast_adv_until:
                try:
                    self._ble.gap_advertise(None)
                    time.sleep_ms(50)
                    self._start_advertising(fast=False)
                    self._log("switched to slow advertising (power save)")
                    fast_adv_until = now + 3600000  # Don't switch again for 1 hour
                except Exception as e:
                    self._log("failed to switch to slow advertising:", e)
            
            # Connection health check every 5s (reduced frequency to avoid interference)
            if self._connected and time.ticks_diff(now, self._last_ping) > 5000:
                try:
                    # Simple ping: try to read TX handle (non-blocking)
                    self._ble.gatts_read(self._tx_handle)
                    self._last_ping = now
                except Exception as e:
                    self._log("connection health check failed:", e)
                    self._connected = False
                    self._conn = None
                    if not self._saved:
                        time.sleep_ms(50)
                        if self._start_advertising(fast=True):
                            self._log("re-advertising after connection lost")
                        else:
                            self._log("failed to restart advertising after connection lost")
            
            # GC every 15s (was 10s) to reduce overhead
            if time.ticks_diff(now, last_gc) > 15000:
                gc.collect()
                last_gc = now
            
            # Blink LED to indicate BLE mode
            self._blink_led()
            
            time.sleep_ms(100)  # Faster main loop: 100ms instead of 150ms

        # Only cleanup if we're not going to reset (which should have already happened)
        # If auto_reset=True and we reach here, something went wrong with reset
        if self._saved and self.auto_reset:
            self._log("WARNING: Expected reset but still running! Attempting manual reset...")
            try:
                import machine
                machine.reset()
            except Exception as e:
                self._log("Manual reset failed:", e)
        
        # Cleanup BLE resources (for timeout or auto_reset=False cases)
        self._log("exiting provisioning mode...")
        self._cleanup_ble()
        
        gc.collect()
        return self._saved

def provision(timeout_s=180, name="CYBERFLY-SETUP", log=True, auto_reset=True):
    p = BleProvisioner(name=name, timeout_s=timeout_s, log=log, auto_reset=auto_reset)
    return p.start()