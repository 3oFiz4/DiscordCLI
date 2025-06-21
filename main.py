import asyncio
import discord
import datetime
import shutil
import tkinter
from tkinter import filedialog
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.document import Document
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import get_app
from rich.console import Console
from rich.theme import Theme
# from rich.live import Live
from pathlib import Path
import os
import json
from playsound import playsound
import threading
import clipboard
import emoji
import re
import sys
import argparse

# TODO:
# 1. Minor Improivement on Chat UI, see fn[display_history, render_history], and mention stuff
# 2. Add Upload Command
# 3. Add Delete message Command
# 4. Add forward Command

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "upload"
UPLOAD_DIR.mkdir(exist_ok=True)
RINGTONE_DIR = BASE_DIR / "ringtone"
RINGTONE_DIR.mkdir(exist_ok=True)

with open(f"{BASE_DIR / 'conf.json'}", "r", encoding="utf-8") as f:
    _ = json.load(f)

cmdK = _["cmdKey"]
commands_config = _[
    "commands"
]  # New variable for easier access to commands configuration
# CONFIGURATION
theme = Theme(_["pallete"])
CONTEXT_WINDOW_SHOW_MESSAGE_TOTAL = _["events"]["history_render"]["message_total"]  # Total messages to show in a single buffer
# i promise ill add more configuration here, im just too lazy to add one

console = Console(theme=theme)
# live_history = Live("", console=console, refresh_per_second=4)
full_emoji_list = list(emoji.EMOJI_ALIAS_UNICODE_ENGLISH.keys())

# -------------- HELPER FUNC -------------------
# Clear screen
def clear():
    console.clear()


# Pasted from / Credit to: 3ofiz4/cli-interval-timer
def play_alarm(ringtone_name=None):
    def _play():
        if not os.path.exists(RINGTONE_DIR):  # impossible to happen anyway
            console.print("[red]Ringtone folder not found.[/red]")
            return
        files = [
            f for f in os.listdir(RINGTONE_DIR) if f.lower().endswith((".mp3", ".wav"))
        ]
        if not files:
            console.print("[red]No ringtones found.\nYou can create one by putting any .mp3 or .wav file in ringtone/, then name them as 'notification'[/red]")
            return
        if ringtone_name:
            candidates = [f for f in files if f.startswith(ringtone_name)]
            sound_file = candidates[0] if candidates else files[0]
        else:
            sound_file = files[0]
        full_path = RINGTONE_DIR / sound_file
        full_path = full_path
        playsound(str(full_path))

    threading.Thread(target=_play, daemon=True).start()

def pick_files():
    root = tkinter.Tk()
    root.withdraw()
    paths = filedialog.askopenfilenames(title="Choose file to Upload. Any types.")
    root.update()
    root.destroy()
    return [Path(p) for p in paths]


class CMDLexer(Lexer):
    global cmdK

    def lex_document(self, document: Document):
        text = document.text

        def get_line(lineno):
            if text.lstrip().startswith(cmdK):
                return [("class:command", text)]
            return [("class:default", text)]

        return get_line


class DiscordCompleter(Completer):
    # Access global variables for cmdK and commands_config
    global cmdK, commands_config

    def __init__(self, client):
        self.client = client

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.lstrip()

        # Helper to get the full command prefix for completion checks
        def get_cmd_prefix(command_name, include_space=True):
            aliases = commands_config.get(command_name, {}).get("aliases", [])
            if aliases:
                return f"{cmdK}{aliases[0]}{' ' if include_space else ''}"
            return ""

        # Server Nav: -s
        server_nav_prefix = get_cmd_prefix("server_nav")
        if text.startswith(server_nav_prefix):
            prefix = text[len(server_nav_prefix) :]
            for guild in self.client.guilds:
                if guild.name.lower().startswith(prefix.lower()):
                    yield Completion(guild.name, start_position=-len(prefix))

        # DM / Friend Nav: -cf (and potentially -dm if added as alias)
        dm_nav_aliases = commands_config.get("dm_nav", {}).get("aliases", [])
        dm_nav_prefixes = [f"{cmdK}{alias} " for alias in dm_nav_aliases]

        # Edit Command (e.g., -e)
        edit_prefix = get_cmd_prefix("edit")
        if text.startswith(edit_prefix):
            remaining = text[len(edit_prefix):].lstrip()
            parts = remaining.split(" ", 1)
            if parts and parts[0].isdigit():
                idx = int(parts[0])
                try:
                    orig = self.client.history_buffer[len(self.client.history_buffer) - idx].content
                except Exception:
                    orig = ""
                if len(parts) == 1 or parts[1] == "":
                    yield Completion(orig, start_position=0, display=f"{orig}")
                    yield Completion("", start_position=0, display="Empty")

        matched_dm_prefix_len = 0
        for p in dm_nav_prefixes:
            if text.startswith(p):
                matched_dm_prefix_len = len(p)
                break

        if matched_dm_prefix_len > 0:
            prefix = text[matched_dm_prefix_len:]
            for user in self.client.users:
                label = f"{user.display_name if hasattr(user,'display_name') else user.name} ({user.name})"
                if user.name.lower().startswith(prefix.lower()):
                    yield Completion(
                        user.name, display=label, start_position=-len(prefix)
                    )

        # Forward Nav: -fw
        forward_msg_prefix = get_cmd_prefix("forward_msg")
        if text.startswith(forward_msg_prefix):
            parts = text.split(" ", 2)
            if len(parts) < 3:
                return  # User still typing for index param
            pref = parts[-1]

            for user in self.client.users:
                label = f"{user.display_name if hasattr(user,'display_name') else user.name} ({user.name})"
                if user.name.lower().startswith(pref.lower()):
                    yield Completion(
                        user.name, display=label, start_position=-len(pref)
                    )

        # Emoji Picker (no cmdKey, so stays as is)
        if text.startswith(":"):
            prefix = text[1:]
            for emoji_code in full_emoji_list:
                # Remove the starting and ending ':' for matching.
                core_emoji = emoji_code.strip(":")
                if core_emoji.lower().startswith(prefix.lower()):
                    char = emoji.emojize(emoji_code, language="alias", variant="emoji_type")
                    display = f"{char} {emoji_code}"
                    yield Completion(emoji_code, display=display, start_position=-len(prefix)-1)

        # Channel Nav: -c
        channel_nav_prefix = get_cmd_prefix("channel_nav")
        if text.startswith(channel_nav_prefix):
            guild = self.client.current_guild
            if not guild:
                return
            prefix = text[len(channel_nav_prefix) :]
            for channel in guild.text_channels:
                if channel.name.lower().startswith(prefix.lower()):
                    yield Completion(channel.name, start_position=-len(prefix))

        # Mention (no cmdKey, so stays as is)
        elif "@" in text.split(" ")[-1]:
            partial = text.split(" ")[-1].split("@")[-1]
            if self.client.current_guild:
                for u in self.client.current_guild.members:
                    if u.name.lower().startswith(partial.lower()):
                        yield Completion(u.name, start_position=-len(partial))

        else:  # Snippets (no cmdKey, so stays as is)
            tokens = text.split()
            if tokens:
                last = tokens[-1]
                if "{" in last and "}" not in last:
                    snippet_keys = ["whoami"]
                    start = last.find("{") + 1
                    prefix = last[start:]
                    for key in snippet_keys:
                        if key.startswith(prefix):
                            yield Completion(
                                f"{key}}}", start_position=-len(prefix) - 1
                            )


class DiscordClient(discord.Client):
    global _

    # Temporary Variables
    def __init__(self):
        super().__init__()
        self.completer = DiscordCompleter(self)
        self.current_channel = None
        self.current_guild = None
        self.show_displayname = _["settings"]["show_displayname"]
        self.show_username = _["settings"]["show_username"]
        self.upload_staged = []
        self.history_buffer = []
        self.history_offset = 0
        self.pending_pings = []
        self.input_session = ""
        # self.blocked_members = [] # next update
        # self.ignored_members = []
        self.snippets = {
            "whoami": lambda: self.fmt_author(self.user) if self.user else "unknown"
        }

    # Still does not work.i
    def fmt_author(self, member):
        # Get the essentials - these should always exist
        user_id = getattr(member, 'id', '?')
        username = getattr(member, 'name', None) or f"[id:{user_id}]"
        
        # 1. First try to get server nickname
        nick = None
        if hasattr(member, 'guild') and member.guild:
            guild_member = member.guild.get_member(user_id)
            if guild_member:
                nick = getattr(guild_member, 'nick', None)
        
        # 2. Then try global display name
        global_name = getattr(member, 'global_name', None)
        
        # Determine display name (nick > global > username)
        display_name = nick or global_name or username
        
        if not self.show_displayname:
            return username
        
        if not self.show_username:
            return display_name
        
        # Only show parentheses if display name != username
        if display_name != username:
            return _["events"]["format"]["author"].format(
                display_name=display_name,
                name=username
            )
        return username

    # ... existing code ...
    # Timestamp Format
    def fmt_time(self, dt):
        global _
        now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
        age = now - dt
        if age.total_seconds() < 86_400:
            return dt.strftime(_["events"]["format"]["timestamp_time"])
        return dt.strftime(_["events"]["format"]["timestamp_date"])

    # ----- EVENTS -----
    # onReady Event
    async def on_ready(self):
        global _
        console.print(_["events"]["onReady"].format(user=self.user))
        user = self.user

    # onMessage Event
    async def on_message(self, message):
        # Ignore self
        if message.author == self.user:
            return

        # get_app().run_in_terminal(clear) # Safe-RUN. Kind of works I guess. 
        # Ping Notification
        if self.user in message.mentions:
            play_alarm("notification")
            console.print(
                _["events"]["onMessage"].format(
                    author=message.author, channel=message.channel
                )
            )
            self.pending_pings.append(message)
        # Refresh History on Channel
        if self.current_channel and message.channel.id == self.current_channel.id: 
            await self.refresh_history(live=True)

    # Refresh History
    async def refresh_history(self, live=False):
        if not self.current_channel:
            return
        buf = [m async for m in self.current_channel.history(limit=100)]
        self.history_buffer = list(reversed(buf))
        await self.render_history(live=live)

    # Display History
    async def render_history(
        self, live=False, window_size=CONTEXT_WINDOW_SHOW_MESSAGE_TOTAL
    ):
        global _

        current_input = ""
        if self.input_session:
            current_input = self.input_session.default_buffer.text
        total = len(self.history_buffer)
        
        clear()

        # this thing right here is the global 1-indexed positions:
        # end_index: the 1-indexed position of the last message in this window.
        # since self.history_buffer is 0-indexed and sorted oldest-first:
        #    global position = index + 1.
        # therefore,  buffer slice indexes.
        end_index = (
            total - self.history_offset * window_size
        )  # 1-indexed upper bound of the window.
        start_index = max(0, end_index - window_size)  # 0-indexed start of the window.

        header = _["events"]["history_render"]["header"].format(
            current_guild=self.current_guild,
            current_channel=self.current_channel,
            start_index=start_index + 1,  # converting from 0-index to 1-index.
            end_index=end_index,
            total=total,
        )
        console.print(header)

        # iterate in the natural order (oldest first)
        for global_i in range(start_index, end_index):
            message = self.history_buffer[global_i]
            # btw the Global Discord position (1-indexed) is: global_i + 1.
            # so display "inverted" indexes:
            #   dateisplay index = total - (global Discord position) + 1.
            # example, if global position is 1 (oldest) and total = 100, then display index = 100 - 1 + 1 = 100.
            # now if f global position is 100 (newest), display index = 100 - 100 + 1 = 1.
            display_index = (
                total - (global_i + 1) + 1
            )  # simplifies to: total - global_i

            # havent tested this out
            if (
                hasattr(self, "blocked_users")
                and message.author.id in self.blocked_users
            ) or (
                hasattr(self, "ignored_users")
                and message.author.id in self.ignored_users
            ):
                status = (
                    "Blocked"
                    if (
                        hasattr(self, "blocked_users")
                        and message.author.id in self.blocked_users
                    )
                    else "Ignored"
                )
                console.print(
                    f"<{display_index}> --- {status} User: {self.fmt_author(message.author)} (message hidden)"
                )
                continue

            timestamp = f"[time]{self.fmt_time(message.created_at)}[/time]"
            auth_name = self.fmt_author(message.author)
            author = (
                f"[self]{auth_name}[/self]"
                if message.author.id == self.user.id
                else f"[other]{auth_name}[/other]"
            )

            header_line = _["events"]["history_render"]["message_header"].format(
                index=display_index, timestamp=timestamp, author=author
            )

            # if the message is a reply, look up the global position and adjust its printed index similarly.
            if message.reference and message.reference.message_id:
                replied_index = "?"
                for j, m in enumerate(self.history_buffer):
                    if m.id == message.reference.message_id:
                        # compute display index for the reply target:
                        # global Discord index is j+1, so display is: total - (j+1) + 1 = total - j.
                        replied_index = total - j
                        break

                header_line = _["events"]["history_render"][
                    "message_header_reply"
                ].format(
                    index=display_index,
                    replied_index=replied_index,
                    timestamp=timestamp,
                    author=author,
                )

            if "\n" in message.content:
                console.print(header_line)
                console.rule()  # horizontal rule before message content
                console.print(message.content)
                console.rule()  # horizontal rule after message content
            else:
                console.print(f"{header_line} {message.content}")

            if message.attachments:
                attaches = " ".join(
                    f"[{i+1}] {att.filename}"
                    for i, att in enumerate(message.attachments)
                )
                console.print(
                    _["events"]["history_render"]["attachment"].format(
                        attaches=attaches
                    )
                )

            if message.reactions:
                reacts = " ".join(f"{r.emoji}×{r.count}" for r in message.reactions)
                console.print(f"     {reacts}")
            
        # ---- Restore user input ----
        if self.input_session:
            self.input_session.default_buffer.set_document(
                Document(current_input, cursor_position=len(current_input)),
                bypass_readonly=True,
            )


async def start_cli(client):
    global _, cmdK, commands_config  # Make sure commands_config is accessible
    style = Style.from_dict(_["colorInput"])
    session = PromptSession(completer=client.completer, lexer=CMDLexer(), style=style)
    client.input_session = session
    clear()
    console.print(_["events"]["preReady"])

    # Helper to check if command starts with any alias
    def get_command_prefix_len(text_input, command_name):
        cmd_aliases = commands_config.get(command_name, {}).get("aliases", [])
        for alias in cmd_aliases:
            full_cmd = f"{cmdK}{alias}"
            if text_input.startswith(f"{full_cmd} "):
                return len(full_cmd) + 1  # +1 for the space after command
            elif (
                text_input == full_cmd
            ):  # This handles the case where no argument is given
                return len(full_cmd)
        return 0  # Should not happen if check_command_start was true

    # Helper to get the command prefix length for extracting arguments
    def check_command_start(text_input, command_name, exact=False):
        cmd_aliases = commands_config.get(command_name, {}).get("aliases", [])
        for alias in cmd_aliases:
            full_cmd = f"{cmdK}{alias}"
            if exact:
                if text_input == full_cmd:
                    return True
            else:
                # Modified: Check if text_input is exactly the command OR starts with the command followed by a space
                if text_input == full_cmd or text_input.startswith(f"{full_cmd} "):
                    return True
        return False

    while True:
        try:
            import sys
            with patch_stdout(sys.__stdout__): # this handles when the on_message triggers, and the input remain in the input, but somehow the color in rich moudle turns into rwa code
                text = await session.prompt_async([('class:prompt', '> ')], style=style)
        except (EOFError, KeyboardInterrupt):
            await client.close()
            break

        C = text.strip()  # C(ommands)

        clear()  # Clear first

        # ---- CMDS -----
        # Exit
        if check_command_start(C, "exit", exact=True):
            console.print(commands_config["exit"]["logs"]["onExit"])
            await client.close()
            break
        # Changelog
        elif check_command_start(C, "changelog", exact=True):
            console.print("""
v25.06.17 (yy/mm/dd)
    - Initial release (took 4.5~ hours)
        a. Working Reply and Sending messages
        b. Ability to DM or Interact with friends
        c. Proper Chat UI
v25.06.19 (Major Tweaks and Improvement) (took ~9.2 hours)
    - Improved Chat UI
        a. Different color for user and other people
        b. Added timestamp
        c. Auto-clear for every command trigger
        d. Long message has horizontal bar
        e. Reply to message is visible
        f. Display name and User name shows (tweakable)
        g. Added more colors
        h. Color change upon command insert, the input I mean
    - More commands (check -h)
        a. -d(elete messages)
        b. -up(load file)
        c. -de(stage)up(load file)
        d. -f(or)w(ard) message
        e. -n(o)t(i)f
        f. -g(o to)n(o)t(i)f
    - Misc
        a. Minor revamp of code structure
        b. Added notifications for ping (untested)   
v25.06.19.01 (Minor tweaks)
    - Chat UI
        a. Attachment is shown
    - Misc
        a.  Added `conf.json` to configure the terminal
v25.06.21 (Minor bug fixes)
v25.06.21.01 (minor bug fixes)
v25.06.21.02 (added few features)
    - More commands
        a. -y(ank message) # Yank is Copy
        b. -p(in message)
        c. -d(eny)p(in message)
        d. -e(dit message)
                          """)
        # Help
        elif check_command_start(C, "help", exact=True):
            console.print(
                    """
-changelog   # Changelog
# Navigation:
-s [server] # Select a server
-c [channel] # Select a channel, (-s must be triggered already)
-cf [dm/friend/member_in_any_server] # Select a DM or a friend or anyone in the server

# Typing
-r [index] [msg] # Reply to selected message_index with a message. Also sends a file if -up is triggered before.
-d [index...] # Delete message index, can be in a list
-up # Staged a file for upload (via Explorer Pop-Up)
-deup # Unstage all file for upload
-fw [index] [dm/friend/member_in_any_server] # Forward/Send a message of index_message to DM, Friend, or Members
-y [index] # Copy or Yank a message
-p [index] # Pin a message, if authorized 
-dp [index] # Unpin a message, if authorized
-e [index] [edit] # Edit a message of index_message with new edit
"say" # Without (-) will say something in current_channel, also sends a file if -up is triggered before
"@" # List all mentionable users
-ct [index] [emoji] # React to message in index_message with emoji, ex: -ct 9 :sob:
":...:" # Show a list of emoji within ::

# Misc
-ntf/-notif # Show available notifications while the terminal is online
-gntf / -gonotif # Go to notif, (reuire -ntf/-notif to be triggered already)
-> OR -< # Scroll to latest OR oldest
                    """
                    )
        # Server Navigation
        elif check_command_start(C, "server_nav"):
            prefix_len = get_command_prefix_len(C, "server_nav")
            name = C[prefix_len:]
            guild = discord.utils.find(lambda g: g.name == name, client.guilds)
            if guild:
                client.current_guild = guild
                console.print(
                    commands_config["server_nav"]["logs"]["success"].format(
                        name=guild.name
                    )
                )
            else:
                console.print(
                    commands_config["server_nav"]["logs"]["not_exist"].format(name=name)
                )
        # Channel Navigation
        elif check_command_start(C, "channel_nav"):
            if not client.current_guild:
                console.print(
                    commands_config["channel_nav"]["logs"]["no_server_selected"]
                )
                continue
            prefix_len = get_command_prefix_len(C, "channel_nav")
            name = C[prefix_len:]
            channel = discord.utils.find(
                lambda c: c.name == name, client.current_guild.text_channels
            )
            try:
                if channel:
                    client.current_channel = channel
                    client.history_offset = 0
                    console.print(
                        commands_config["channel_nav"]["logs"]["success"].format(
                            name=channel.name
                        )
                    )
                    await client.refresh_history()
                else:
                    console.print(
                        commands_config["channel_nav"]["logs"]["not_exist"].format(
                            name=name
                        )
                    )
            except Exception:  # Catching generic Exception for "no access"
                console.print(commands_config["channel_nav"]["logs"]["no_access"])
        # Scrolling Old
        elif check_command_start(C, "scroll_old"):
            prefix_len = get_command_prefix_len(C, "scroll_old")
            num_str = C[prefix_len:]
            num = int(num_str) if num_str.isdigit() else 10
            client.history_offset = min(
                len(client.history_buffer) // num, client.history_offset + 1
            )
            await client.refresh_history()
            continue
        # Scrolling New
        elif check_command_start(C, "scroll_new"):
            prefix_len = get_command_prefix_len(C, "scroll_new")
            num_str = C[prefix_len:]
            num = int(num_str) if num_str.isdigit() else 10
            client.history_offset = max(0, client.history_offset - 1)
            await client.refresh_history()
            continue
        
        # React to Message
        elif check_command_start(C, "react"):
            prefix_len = get_command_prefix_len(C, "react")
            parts = C[prefix_len:].split(" ", 1)  # expecting something like: "react [message_index] [emoji]"
            # if len(parts) < 10:
                # console.print(commands_config["react"]["logs"]["moreThanThree"])
                # continue
            try:
                idx = int(parts[0])
            except ValueError as e:
                console.print(e)
                console.print(commands_config["react"]["logs"]["invalidIndex"])
                continue

            # convert colon emoji text (e.g. ":sob:") into its corresponding Unicode emoji.
            # if user accidentally types double-colons, normalize it to :..:.
            emoji_input = parts[1].replace("::", ":")
            unicode_emoji = emoji.emojize(emoji_input, language='alias')
            
            try:
                msg = client.history_buffer[len(client.history_buffer) - idx]
                await msg.add_reaction(unicode_emoji)
            except Exception as e:
                console.print(commands_config["react"]["logs"]["error"].format(e=e))
            await client.refresh_history()
            continue
        # ISSUE: Not work
        # Open attachments command
        elif check_command_start(C, "open_attachment"):  # Use check_command_start
            prefix_len = get_command_prefix_len(C, "open_attachment")
            parts = C[prefix_len:].split()  # Get arguments after command prefix

            if not parts:  # No arguments given, print usage
                console.print(
                    commands_config["open_attachment"]["logs"]["usage"].format(
                        cmdK=cmdK
                    )
                )
                continue

            try:
                msg_idx = int(parts[0])  # First argument is message number
            except ValueError:
                console.print(
                    commands_config["open_attachment"]["logs"]["invalid_msg_index"]
                )
                continue

            try:
                msg = client.history_buffer[msg_idx - 1]
            except IndexError:
                console.print(
                    commands_config["open_attachment"]["logs"]["msg_index_out_of_range"]
                )
                continue

            attachments = msg.attachments
            if not attachments:
                console.print(
                    commands_config["open_attachment"]["logs"]["no_attachments"]
                )
                continue

            # Determine which attachments to open.
            indices = []
            if len(parts) > 1:
                for p in parts[1:]:
                    try:
                        i = int(p)
                        indices.append(i)
                    except:
                        continue
            else:
                indices = list(
                    range(1, len(attachments) + 1)
                )  # Open all if no specific indices given

            for i in indices:
                if i < 1 or i > len(attachments):
                    console.print(
                        commands_config["open_attachment"]["logs"][
                            "attachment_index_out_of_range"
                        ].format(index=i)
                    )
                    continue
                attachment = attachments[i - 1]

                filepath = UPLOAD_DIR / attachment.filename
                try:
                    await attachment.save(filepath)
                except Exception as e:
                    console.print(
                        commands_config["open_attachment"]["logs"][
                            "error_saving"
                        ].format(error_msg=e)
                    )
                    continue

                # Check file extension for open method.
                if attachment.filename.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif")
                ):
                    webbrowser.open(filepath.as_uri())
                    console.print(
                        commands_config["open_attachment"]["logs"][
                            "opened_image"
                        ].format(filename=attachment.filename)
                    )
                elif attachment.filename.lower().endswith(".txt", ".md", ".py", ".js"):
                    try:
                        if os.name == "nt":  # For Windows
                            os.startfile(filepath)
                        else:  # For macOS/Linux
                            subprocess.run(
                                ["open", filepath]
                            )  # 'open' for macOS, 'xdg-open' for Linux (often default for 'open')
                        console.print(
                            commands_config["open_attachment"]["logs"][
                                "opened_text"
                            ].format(filename=attachment.filename)
                        )
                    except Exception as e:
                        console.print(
                            commands_config["open_attachment"]["logs"][
                                "error_opening_file"
                            ].format(error_msg=e)
                        )
                else:
                    console.print(
                        commands_config["open_attachment"]["logs"][
                            "no_open_command"
                        ].format(filename=attachment.filename)
                    )
            continue
        # ISSUE: Not work, not because of bugs, but I wanted to stop it here :). Next day, promise!
        # Configuration Editor command
        elif check_command_start(C, "config_editor", exact=True):
            console.print('Do not use me yet. I am not finished yet')    
        elif check_command_start(C, "reply"):
            prefix_len = get_command_prefix_len(C, "reply")
            parts = C[prefix_len:].split(
                " ", 1
            )  # Split only once to get index and rest of message
            if len(parts) < 2:
                console.print(
                    commands_config["reply"]["logs"]["error"].format(
                        error_msg="Missing message number or content"
                    )
                )
                await client.refresh_history()
                continue
            try:
                idx = int(parts[0])
                msg_content = parts[1]
                target = client.history_buffer[len(client.history_buffer) - idx]
                if hasattr(client, "upload_staged") and client.upload_staged:
                    F = [discord.File(p) for p in client.upload_staged]
                else:
                    F = None
                # Send the reply with or without files
                await target.reply(msg_content, files=F)
                client.upload_staged.clear()
            except Exception as e:
                console.print(
                    commands_config["reply"]["logs"]["error"].format(error_msg=str(e))
                )
            await client.refresh_history()
            continue

        # Deleting Message
        elif check_command_start(C, "delete_msg"):
            prefix_len = get_command_prefix_len(C, "delete_msg")
            indices_str = C[prefix_len:].split(" ")
            for each_ind_str in indices_str:
                try:
                    idx = int(each_ind_str)
                    msg = client.history_buffer[len(client.history_buffer) - idx]
                    if msg.author.id != client.user.id:
                        console.print(
                            commands_config["delete_msg"]["logs"]["not_own_message"]
                        )
                    else:
                        await msg.delete()
                except ValueError:
                    console.print(
                        commands_config["delete_msg"]["logs"]["invalid_index"].format(
                            index=each_ind_str
                        )
                    )
                except IndexError:
                    console.print(
                        commands_config["delete_msg"]["logs"]["out_of_range"].format(
                            index=each_ind_str
                        )
                    )
                except Exception as e:
                    console.print(
                        commands_config["delete_msg"]["logs"]["generic_error"].format(
                            index_str=each_ind_str, error_msg=str(e)
                        )
                    )

            await client.refresh_history()
            continue

        # Message forward
        elif check_command_start(C, "forward_msg"):
            prefix_len = get_command_prefix_len(C, "forward_msg")
            parts = C[prefix_len:].split(
                " ", 1
            )  # Split into message number and rest (user arg)
            if len(parts) < 2:
                console.print(commands_config["forward_msg"]["logs"]["usage_error"])
                continue
            msg_idx_str = parts[0]
            user_arg = parts[1].strip()

            try:
                idx = int(msg_idx_str)
            except ValueError:
                console.print(commands_config["forward_msg"]["logs"]["invalid_msg_num"])
                continue
            if not user_arg:
                console.print(
                    commands_config["forward_msg"]["logs"]["user_not_specified"]
                )
                continue
            try:
                msg = client.history_buffer[len(client.history_buffer) - idx]
                u = discord.utils.get(client.users, name=user_arg)
                if not u:
                    console.print(
                        commands_config["forward_msg"]["logs"]["no_such_user"].format(
                            user_arg=user_arg
                        )
                    )
                    continue
                dm = await u.create_dm()
                await dm.send(msg.content)
            except IndexError:
                console.print(
                    commands_config["forward_msg"]["logs"]["invalid_msg_num"]
                )  # Re-use for out of bounds
            except Exception as e:
                console.print(
                    commands_config["forward_msg"]["logs"]["generic_error"].format(
                        error_msg=str(e)
                    )
                )
            await client.refresh_history()
            continue
        
        elif check_command_start(C, "edit"):
            prefix_len = get_command_prefix_len(C, "edit")
            parts = C[prefix_len:].split(" ", 1)

            if not parts[0].isdigit():
                console.print(
                    commands_config["edit"]["logs"]["error"].format(
                        error_msg="Invalid message index."
                    )
                )
                await client.refresh_history()
                continue

            idx = int(parts[0])
            try:
                
                orig = client.history_buffer[len(client.history_buffer) - idx].content
            except Exception as err:
                console.print(
                    commands_config["edit"]["logs"]["error"].format(
                        error_msg="Message index not found."
                    )
                )
                await client.refresh_history()
                continue

            
            if len(parts) == 1 or parts[1].strip() == "":

                new_command = f"{cmdK}edit {idx} {orig}"

                client.input_session.default_buffer.set_document(
                    Document(new_command, cursor_position=len(new_command)),
                    bypass_readonly=True,
                )
                console.print("Auto-populated edit command with original message text.")
                continue

            new_text = parts[1]
            try:
                target = client.history_buffer[len(client.history_buffer) - idx]
                await target.edit(content=new_text)
            except Exception as e:
                console.print(
                    commands_config["edit"]["logs"]["error"].format(
                        error_msg=str(e)
                    )
                )
            await client.refresh_history()
            continue

        # Copy a message
        elif check_command_start(C, "copy"):
            prefix_len = get_command_prefix_len(C, "copy")
            # copy expects only a message index parameter
            parts = C[prefix_len:].split()
            if len(parts) < 1 or not parts[0].isdigit():
                console.print(
                    commands_config["copy"]["logs"]["error"].format(
                        error_msg="Missing or invalid message index."
                    )
                )
                await client.refresh_history()
                continue
            idx = int(parts[0])
            try:
                target = client.history_buffer[len(client.history_buffer) - idx]
                clipboard.copy(target.content)
                await client.refresh_history()
            except Exception as e:
                console.print(
                    commands_config["copy"]["logs"]["error"].format(error_msg=str(e))
                )
            continue  # No history refresh needed

        # Pin a message, if authorized
        elif check_command_start(C, "pin"):
            prefix_len = get_command_prefix_len(C, "pin")
            parts = C[prefix_len:].split()
            if len(parts) < 1 or not parts[0].isdigit():
                console.print(
                    commands_config["pin"]["logs"]["error"].format(
                        error_msg="Missing or invalid message index."
                    )
                )
                await client.refresh_history()
                continue
            idx = int(parts[0])
            try:
                target = client.history_buffer[len(client.history_buffer) - idx]
                # Attempt to pin the message
                await target.pin()
                await client.refresh_history()
            except Exception as e:
                console.print("Inauthorized. Type < or > to refresh")
            continue

        # Unpin message, if authorized
        elif check_command_start(C, "unpin"):
            prefix_len = get_command_prefix_len(C, "unpin")
            parts = C[prefix_len:].split()
            if len(parts) < 1 or not parts[0].isdigit():
                console.print(
                    commands_config["unpin"]["logs"]["error"].format(
                        error_msg="Missing or invalid message index."
                    )
                )
                await client.refresh_history()
                continue
            idx = int(parts[0])
            try:
                target = client.history_buffer[len(client.history_buffer) - idx]
                # Attempt to unpin the message
                await target.unpin()
                await client.refresh_history()
            except Exception as e:
                console.print("Inauthorized. Type < or > to refresh")
            continue

        # Upload staging
        elif check_command_start(C, "upload_stage", exact=True):
            client.upload_staged.clear()
            shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
            UPLOAD_DIR.mkdir(exist_ok=True)
            picked = pick_files()

            if not picked:  # Check if any files were picked
                console.print(commands_config["upload_stage"]["logs"]["null"])
                continue

            for p in picked:
                dst = UPLOAD_DIR / p.name
                shutil.copy2(p, dst)
                client.upload_staged.append(dst)
                console.print(
                    commands_config["upload_stage"]["logs"]["staged"].format(
                        filename=dst.name
                    )
                )
            continue
        elif check_command_start(C, "deupload_stage", exact=True):
            client.upload_staged.clear()
            shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
            UPLOAD_DIR.mkdir(exist_ok=True)
            console.print(commands_config["deupload_stage"]["logs"]["reset"])
            continue

        # DM / Friend Navigation
        elif check_command_start(C, "dm_nav"):
            prefix_len = get_command_prefix_len(C, "dm_nav")
            name = C[prefix_len:]
            user = discord.utils.find(lambda u: u.name == name, client.users)
            if user:
                client.current_guild = None  # Clear current guild when entering DM
                client.current_channel = None
                console.print(
                    commands_config["dm_nav"]["logs"]["success"].format(name=user.name)
                )
                channel = await user.create_dm()
                client.current_channel = channel
                client.history_offset = 0
                await client.refresh_history()
            else:
                console.print(
                    commands_config["dm_nav"]["logs"]["not_found"].format(name=name)
                )

        # Notifications
        elif check_command_start(C, "notifications", exact=True):
            if not client.pending_pings:
                console.print(commands_config["notifications"]["logs"]["no_pings"])
            for i, m in enumerate(client.pending_pings, 1):
                console.print(
                    commands_config["notifications"]["logs"]["ping_details"].format(
                        index=i,
                        author=client.fmt_author(m.author),
                        channel=m.channel,
                        content=m.content[:60],
                    )
                )
        elif check_command_start(C, "go_to_notification"):
            prefix_len = get_command_prefix_len(C, "go_to_notification")
            idx_str = C[prefix_len:].strip()
            if not idx_str.isdigit():
                console.print(
                    commands_config["go_to_notification"]["logs"]["bad_index"]
                )
                continue

            idx = int(idx_str) - 1
            if idx < 0 or idx >= len(client.pending_pings):
                console.print(
                    commands_config["go_to_notification"]["logs"]["bad_index"]
                )
                continue
            ping = client.pending_pings[idx]
            client.current_channel = ping.channel
            await client.refresh_history()
        else:  # Default send message
            if client.current_channel:
                try:
                    if client.upload_staged:
                        F = [discord.File(p) for p in client.upload_staged]
                    else:
                        F = None
                    await client.current_channel.send(
                        C, files=F
                    )  # Use C (stripped text) for sending
                    client.upload_staged.clear()
                    await client.refresh_history()
                except Exception as e:
                    console.print(
                        commands_config["message_send"]["logs"]["fail"].format(
                            error_msg=str(e)
                        )
                    )
            else:
                console.print(
                    commands_config["message_send"]["logs"]["no_channel_selected"]
                )

async def main_token(token: str) -> None:
    client = DiscordClient()
    try:
        await asyncio.gather(client.start(token), start_cli(client))
    except ValueError as e:
        console.print(
            f"[err]ERROR: {e}\nHave you set up your {_["file"]["account"]} properly? "
            "Ensure it is not surrounded by quotes.[/err]"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discord self-bot bootstrapper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-s", "--select",
        help=f"Select token from {_["file"]["account"]} by index or Displayname/Username",
        metavar="INDEX_OR_NAME"
    )

    # Token mode
    parser.add_argument(
        "-t", "--token",
        help="Login using a raw Discord token",
        metavar="TOKEN"
    )

    """
    A bit of elaboration here. Like a hour ago I was thinking of Log-In via Username and Password, and it do log-in, but it asks for CAPTCHA instead, which got me slightly confused as how to fix it. And therefore, voila.
    """
    # # Username / password mode
    # parser.add_argument(
    #     "-u", "--username",
    #     help="Gmail / e-mail username (requires -p)",
    #     metavar="USERNAME"
    # )
    # parser.add_argument(
    #     "-p", "--password",
    #     help="Gmail / e-mail password (requires -u)",
    #     metavar="PASSWORD"
    # )

    args = parser.parse_args(argv)

    using_token  = args.token is not None
    # using_creds  = args.username or args.password

    if using_token:
        parser.error("You can do -t/--token")

    # if using_creds and not (args.username and args.password):
    #     parser.error("-u/--username and -p/--password must be supplied together.")

    return args


def extract_tokens(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.findall(r"---\s*(.*?)\s*(?=---|$)", content, re.DOTALL)
    tokens = []

    for block in blocks:
        token_match = re.search(r"Token:\s*(.+)", block)
        name_match = re.search(r"Displayname:\s*(.+)", block)
        user_match = re.search(r"Username:\s*(.+)", block)

        if token_match:
            tokens.append({
                "token": token_match.group(1).strip(),
                "displayname": name_match.group(1).strip() if name_match else "",
                "username": user_match.group(1).strip() if user_match else "",
            })

    return tokens

def get_selected_token(index_or_name: str | None) -> str | None:
    token_file = os.path.join(BASE_DIR, f"{_["file"]["account"]}")
    tokens = extract_tokens(token_file)

    if not tokens:
        return None

    if index_or_name is None:
        return tokens[0]["token"]

    if index_or_name.isdigit():
        idx = int(index_or_name)
        if 0 <= idx < len(tokens):
            return tokens[idx]["token"]
        return None

    index_or_name = index_or_name.lower()
    for t in tokens:
        if index_or_name in (t["displayname"].lower(), t["username"].lower()):
            return t["token"]

    return None

async def main_token(token: str) -> None:
    client = DiscordClient()
    try:
        await asyncio.gather(client.start(token), start_cli(client))
    except ValueError as e:
        console.print(
            f"[err]ERROR: {e}\nHave you set up your {_["file"]["account"]} properly? "
            "Ensure it is not surrounded by quotes.[/err]"
        )

if __name__ == "__main__":
    cli = parse_args(sys.argv[1:])

    if cli.token:
        asyncio.run(main_token(cli.token))

    elif cli.select:
        token = get_selected_token(cli.select)
        if token:
            asyncio.run(main_token(token))
        else:
            console.print("[err]No token found for that selection.\nEach token starts from 0, 1, and so on.\nThe first token is therefore '-s 0'[/err]")
            sys.exit(1)

    else:
        token = get_selected_token(None)
        if token:
            asyncio.run(main_token(token))
        else:
            console.print(f"[err]No tokens found in {_["file"]["account"]}[/err]")
            sys.exit(1)
