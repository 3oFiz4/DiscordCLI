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

rich prompt_toolkit discord.py asyncio shutil tkinter

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

"@" while typing will list mentionable users
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
* Chat in servers / DMs
* Message forwarding
* Upload + auto-remove file attachments
* Display name + timestamp
* Emoji reactions
* Notification system (WIP)
* Rich config via `conf.json`

### 🚧 Planned / In Progress

* ⏳ Per-channel notification styling
* ⏳ Hotkey support
* ⏳ Change profile pic, bio, banner
* ⏳ Open files via browser
* ⏳ Colored text / markdown preview
* ⏳ Message edit / copy / pin / bookmark
* ⏳ Snippets like `{myutc}` → current time
* ⏳ Join/leave server
* ⏳ Multi-token login

---

## 📜 Changelog

<details>
<summary><strong>v25.06.17</strong> – Initial Release (~4.5h)</summary>

* Reply & Send
* DM support
* Basic CLI chat UI

</details>

<details>
<summary><strong>v25.06.19</strong> – Major UI Overhaul (~9.2h)</summary>

* Improved layout & color schemes
* Message timestamp, reply visibility
* New commands:

  * `-d`, `-up`, `-deup`, `-fw`, `-ntf`, `-gntf`
* Code refactor
* Experimental ping notifications

</details>

<details>
<summary><strong>v25.06.19.01</strong> – Minor Tweaks</summary>

* Shows file attachments in chat
* Added `conf.json` for config

</details>

<details>
<summary><strong>v25.06.21</strong> – Minor Bug Fixes</summary>
</details>
---

### 📌 Tip
