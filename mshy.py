#!/usr/bin/env python3

import argparse
import base64
import os
import threading

import meshtastic
import meshtastic.serial_interface
from meshtastic import portnums_pb2
from pubsub import pub

from nacl.secret import SecretBox
from nacl.exceptions import CryptoError
import nacl.utils


# A LoRa data payload is capped at 237 bytes. XSalsa20-Poly1305 (SecretBox)
# prepends a 24-byte nonce and appends a 16-byte auth tag, so our ciphertext
# costs 40 bytes over the plaintext — leaving 197 bytes of UTF-8 to play with.
MAX_MESH_PAYLOAD = 237
CIPHER_OVERHEAD = SecretBox.NONCE_SIZE + 16          # 24 + 16
MAX_PLAINTEXT = MAX_MESH_PAYLOAD - CIPHER_OVERHEAD   # 197

def load_key():
    raw = os.environ.get("MESH_KEY")
    if not raw:
        return None
    key = base64.b64decode(raw)
    if len(key) != SecretBox.KEY_SIZE:
        raise ValueError(
            f"MESH_KEY must decode to {SecretBox.KEY_SIZE} bytes, got {len(key)}")
    return key

class Cipher:
    def __init__(self, key: bytes):
        self._box = SecretBox(key)

    def encrypt(self, text: str) -> bytes:
        return self._box.encrypt(text.encode("utf-8"))

    def decrypt(self, blob: bytes) -> str:
        return self._box.decrypt(bytes(blob)).decode("utf-8")


class MeshChat:
    def __init__(self, interface, cipher):
        self.interface = interface
        self.cipher = cipher
        self._print_lock = threading.Lock()

        pub.subscribe(self.on_receive, "meshtastic.receive")
        pub.subscribe(self.on_connection, "meshtastic.connection.established")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        me = interface.getMyNodeInfo()
        name = me["user"]["longName"] if me else "unknown"
        self.say(f"[connected as {name}]")

    def on_receive(self, packet, interface):
        decoded = packet.get("decoded", {})
        if decoded.get("portnum") not in ["PRIVATE_APP", "TEXT_MESSAGE_APP"]:
            return
        if decoded.get("portnum") == "PRIVATE_APP":
            try:
                text = self.cipher.decrypt(decoded["payload"])
            except (CryptoError, KeyError, UnicodeDecodeError):
                self.say("error decrypting our onion crypto")
                return  # not ours, wrong key, or tampered — drop silently
            sender = self.node_name(packet.get("from"))
            self.say(f"<PRIVATE> [@{sender}] {text}")
        elif decoded.get("portnum") == "TEXT_MESSAGE_APP":
            blob = bytes(decoded["payload"]).decode("utf-8")
            channel_num = packet.get("channel", 0)
            self.say(f"<BRDCST> [CH-{channel_num}] {blob}")

    def node_name(self, node_num):
        if node_num is None:
            return "?"
        node_id = f"!{node_num:08x}"
        node = self.interface.nodes.get(node_id)
        if node and "user" in node:
            return node["user"].get("longName") or node_id
        return node_id

    def say(self, line):
        with self._print_lock:
            print(f"\r{line}")
            print("> ", end="", flush=True)

    def send(self, text, dest=meshtastic.BROADCAST_ADDR):
        if len(text.encode("utf-8")) > MAX_PLAINTEXT:
            print(f"message too long (max {MAX_PLAINTEXT} bytes of plaintext) "
                  "— not sent")
            return
        blob = self.cipher.encrypt(text)
        self.interface.sendData(
            blob, destinationId=dest,
            portNum=portnums_pb2.PortNum.PRIVATE_APP, wantAck=True)

    def shout(self, text, channel):
        if len(text.encode("utf-8")) > MAX_MESH_PAYLOAD:
            print(f"message too long (max {MAX_MESH_PAYLOAD} bytes of plaintext) "
                  "— not sent")
            return
        self.interface.sendText(
            text, channelIndex=channel)
        
    def run(self):
        try:
            while True:
                line = input("> ").strip()
                if not line:
                    continue
                if line.startswith("/"):
                    if self.handle_command(line):
                        break
                else:
                    self.send(line)
        except (EOFError, KeyboardInterrupt):
            pass
        finally:
            self.interface.close()
            print("\ndisconnected.")

    def handle_command(self, line):
        parts = line.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ("/quit", "/exit"):
            return True

        elif cmd == "/help":
            print("""
Commands:
    - /info
    - /channels
    - /nodes
    - /dm <!hexid|nodenum> <message>
    - /shout <channel-idx> <message>
            """)

        elif cmd == "/info":
            print(self.interface.getMyNodeInfo())

        elif cmd == "/channels":
            self.interface.getNode(meshtastic.LOCAL_ADDR).showChannels()

        elif cmd == "/nodes":
            self.interface.showNodes(includeSelf=False, showFields=["user.longName", "user.id", "channel", "lastHeard", "since"])

        elif cmd == "/dm":
            if len(parts) < 3:
                print("usage: /dm <!hexid|nodenum> <message>")
            else:
                dest, msg = parts[1], parts[2]
                if dest.isdigit():
                    dest = int(dest)
                self.send(msg, dest=dest)
        elif cmd == "/shout":
            if len(parts) < 3:
                print("usage: /shout <channel-idx> <message>")
            else:
                dest, msg = parts[1], parts[2]
                self.shout(text=msg, channel=int(dest))
        else:
            print(f"unknown command: {cmd}")

        return False


def make_interface(args):
    return meshtastic.serial_interface.SerialInterface(devPath=args.port)


def main():
    parser = argparse.ArgumentParser(
        description="Minimal encrypted Meshtastic CLI chat client")
    parser.add_argument("--port", help="serial device path (default: auto-detect)")
    parser.add_argument("--genkey", action="store_true",
                        help="print a fresh base64 key for MESH_KEY, then exit")
    args = parser.parse_args()

    if args.genkey:
        print(f"Add this to your .bashrc file or somethin: export MESH_KEY='{base64.b64encode(nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)).decode()}'")
        return

    key = load_key()
    if key is None:
        parser.error("MESH_KEY not set — run with --genkey to make one, then "
                     "export it (the same value) on every node.")
    cipher = Cipher(key)

    print("connecting…")
    interface = make_interface(args)   # blocks until the node config is loaded
    MeshChat(interface, cipher).run()


if __name__ == "__main__":
    main()
