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
        "_led_pin","_led_state","_last_blink"
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

    def _notify_json_str(self, s):
        if not (self._ble and self._connected and self._tx_handle is not None and self._conn is not None):
            self._log("notify failed - not connected")
            return False
        
        try:
            if isinstance(s, str):
                payload = s.encode("utf-8")
            else:
                payload = bytes(s)
            
            self._log(f"notifying {len(payload)} bytes:", payload[:100] if len(payload) > 100 else payload)
            
            # For large payloads, send in chunks
            max_chunk = 180  # MTU size
            if len(payload) <= max_chunk:
                # Single notification
                self._ble.gatts_write(self._tx_handle, payload)
                self._ble.gatts_notify(self._conn, self._tx_handle)
                self._log("notification sent successfully")
                return True
            else:
                # Chunked notifications
                self._log(f"chunking large payload: {len(payload)} bytes")
                for i in range(0, len(payload), max_chunk):
                    chunk = payload[i:i+max_chunk]
                    self._ble.gatts_write(self._tx_handle, chunk)
                    self._ble.gatts_notify(self._conn, self._tx_handle)
                    time.sleep_ms(50)  # Small delay between chunks
                    self._log(f"sent chunk {i//max_chunk + 1}")
                self._log("chunked notification complete")
                return True
                
        except Exception as e:
            self._log("notify fail", e)
            return False

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
            self._notify_json_str(_ERROR_BAD_JSON)
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
            self._notify_json_str(_STATUS_SAVED)
            
            # Auto reset after successful configuration
            if self.auto_reset:
                time.sleep_ms(1200)
                try:
                    import machine
                    machine.reset()
                except Exception:
                    pass
            
        except Exception as e:
            self._log("save failed", e)
            self._notify_json_str(_ERROR_SAVE_FAIL)
        finally:
            self._reset_buffer()
    


    # ---------- IRQ Handler ----------
    def _irq(self, event, data):
        try:
            if event == _IRQ_CENTRAL_CONNECT:
                # data: (conn_handle, addr_type, addr)
                self._conn = data[0] if isinstance(data,(tuple,list)) else data
                self._connected = True
                self._last_ping = time.ticks_ms()
                self._reset_buffer()
                self._log("connected conn_handle:", self._conn)
                
                # Shorter settle time and immediate response
                time.sleep_ms(100)
                success = self._notify_json_str(_STATUS_READY)
                self._log("ready status sent:", success)

            elif event == _IRQ_CENTRAL_DISCONNECT:
                self._log("disconnected")
                self._conn = None
                self._connected = False
                self._reset_buffer()
                if not self._saved:
                    time.sleep_ms(150)
                    self._start_advertising()

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
        return flags + name_data + service_uuid

    def _start_advertising(self):
        if not self._ble:
            return False
        
        # Stop any existing advertising
        try:
            self._ble.gap_advertise(None)
            time.sleep_ms(100)
        except:
            pass
        
        adv = self._adv_payload()
        self._log("adv payload len:", len(adv), "data:", [hex(b) for b in adv])
        
        try:
            # Try with longer interval for better discoverability
            self._ble.gap_advertise(200000, adv_data=adv)  # 200ms interval
            self._log("advertising", self.name, "at 200ms interval")
            return True
        except Exception as e:
            self._log("adv fail 200ms", e)
            try:
                # Fallback to shorter interval
                self._ble.gap_advertise(100000, adv_data=adv)  # 100ms interval
                self._log("advertising", self.name, "at 100ms interval")
                return True
            except Exception as e2:
                self._log("adv fail 100ms", e2)
                try:
                    # Last resort - minimal advertising
                    self._ble.gap_advertise(100)
                    self._log("advertising", self.name, "minimal mode")
                    return True
                except Exception:
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
            time.sleep_ms(200)
            self._ble.active(True)
            time.sleep_ms(500)  # Allow BLE to stabilize
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

        # Set connectable and discoverable
        try:
            # Enable both scanning and advertising
            self._ble.config(rxbuf=1024)  # Increase RX buffer
            self._log("rx buffer configured")
        except Exception as e: 
            self._log("rxbuf config fail", e)

        # Request larger MTU
        try: 
            self._ble.config(mtu=180)
            self._log("mtu set to 180")
        except Exception as e: 
            self._log("mtu config fail", e)

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

        if not self._start_advertising():
            return False

        self._log("provisioner ready timeout", self.timeout_s, "s")
        start_ms = time.ticks_ms()
        last_gc = start_ms
        while not self._saved:
            now = time.ticks_ms()
            if time.ticks_diff(now, start_ms) >= self.timeout_s * 1000:
                self._log("timeout")
                break
            # Connection health check every 2s
            if self._connected and time.ticks_diff(now, self._last_ping) > 2000:
                try:
                    # Simple ping: try to read TX handle (non-blocking)
                    self._ble.gatts_read(self._tx_handle)
                    self._last_ping = now
                except Exception:
                    self._log("connection lost")
                    self._connected = False
                    self._conn = None
                    if not self._saved:
                        time.sleep_ms(150)
                        self._start_advertising()
            if time.ticks_diff(now, last_gc) > 10000:
                gc.collect()
                last_gc = now
            
            # Blink LED to indicate BLE mode
            self._blink_led()
            
            time.sleep_ms(150)

        try:
            self._ble.gap_advertise(None)
            self._ble.active(False)
        except Exception:
            pass
        
        # Turn off LED when exiting BLE mode
        if self._led_pin:
            try:
                self._led_pin.off()
            except Exception:
                pass
        
        gc.collect()
        return self._saved

def provision(timeout_s=180, name="CYBERFLY-SETUP", log=True, auto_reset=True):
    p = BleProvisioner(name=name, timeout_s=timeout_s, log=log, auto_reset=auto_reset)
    return p.start()