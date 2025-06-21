![Banner](https://github.com/user-attachments/assets/e072021d-ab9c-4edd-beb6-d38d19f75b51)

# ⚙️ DiscordCLI
> A Discord terminal client built in ~4 hours. Functional: message, reply, upload — all from the command line.

---

## 🖼️ Thumbnail
![Preview](https://github.com/user-attachments/assets/8067db4a-0f02-457f-b6ef-3897aefdb14f)

---

## ⚠️ Caution
> ⚠️ **USE AT YOUR OWN RISK**

This client acts like a **selfbot**, and using it **violates Discord's TOS**.  
You **may get banned**.  
I am **not responsible** for any account loss.  

✅ Use an **alt account**, or use within a proper **Discord Bot** context.

---

## 📦 Requirements

```
clipboard rich prompt_toolkit discord.py asyncio shutil tkinter playsound threading json
````

---

## 🚀 Setup

### 🔹 Fresh Start
```bash
python main.py
# then use -h or -changelog
````

### 🔹 Add to System PATH (Recommended)

1. Clone this repo to:
   `C:/Users/[your-name]/DisCLI`
2. Open `System Properties` → `Advanced` → `Environment Variables`
3. Under **System Variables**, edit `Path`
4. Add:
   `C:\Users\[your-name]\DisCLI\`
5. Click `OK` on all windows.

Now you can run `main.py` from anywhere.

---

## 🧩 Command List

> `-h` → help
> `-changelog` → recent updates

<details>
<summary><strong>🧭 Navigation</strong></summary>

```
-s [server]         Pick a server
-c [channel]        Pick a chat channel (needs -s first)
-cf [friend]        Pick a friend to DM
-q / -e             Quit the CLI
```

</details>

<details>
<summary><strong>⌨️ Typing</strong></summary>

```
-r [index] [msg]    Reply to message by index
-d [idx ...]        Delete messages (list accepted)
-up                Upload a file (via Explorer popup)
-deup              Clear all staged uploads
-fw [idx] [target]  Forward message to someone
-y [index]           Copy or Yank a message
-p [index]          Pin a message, if authorized 
-dp [index]         Unpin a message, if authorized
-e [index] [edit]   Edit a message of index_message with new edit
"say"               Without (-) will say something in current_channel, also sends a file if -up is triggered before
"@"                 List all mentionable users
```

</details>

<details>
<summary><strong>🔔 Misc</strong></summary>

```
-ntf / -notif       Show notifications
-gntf / -gonotif    Jump to notif source
->n / -<n           Scroll newest/oldest by n messages
```

</details>

---

## 🐞 Known Bugs

> *Minor = doesn't affect core usage much*

* (minor) Screen may scroll to top on mention
* (minor) Command auto-complete can break before API init (fix: press space and retype)
* (minor) Display name invisibility on some servers

🐛 Found a bug? [Submit an Issue](../../issues)

---

## ✅ Features

### ✔ Done

* Reply, send, delete messages
* Copy, Pin, Edit messages
* Chat in servers / DMs
* Message forwarding
* Upload + auto-remove file attachments
* Display name + timestamp
* Emoji reactions
* Notification system (WIP)
* Rich config via `conf.json`

### 🚧 Planned / In Progress

* ⏳ Per-channel notification sounds
* ⏳ Hotkey support
* ⏳ Change profile pic, bio, banner
* ⏳ Open files via browser
* ⏳ Emoji picker (e.g., `:sob:`)
* ⏳ Colored text / markdown preview (via `rich` and `lexer`
* ⏳ Snippets like `{myutc}` → current time
* ⏳ Join/leave server
* ⏳ Multi-token login
* ⏳ Bookmark message
* ⏳ Join & Leave a server
* ⏳ Color a text (similar to snippet, reference [Rebane Message Color](https://rebane2001.com/discord-colored-text-generator/)
* ⏳ Login via Username & Passowrd
* ⏳ Multi-Access Login (either via Username and Password or Token)
---
<details>
<summary><strong>Changelog: </summary>
```
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
```
</details>
