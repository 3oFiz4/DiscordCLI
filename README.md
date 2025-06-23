![Preview](https://github.com/user-attachments/assets/8067db4a-0f02-457f-b6ef-3897aefdb14f)
# ⚙️ DiscordCLI
> A Discord terminal client built in ~4 hours. Functional: message, reply, upload — all from the command line.

---

## 🖼️ Thumbnail
![Banner](https://github.com/user-attachments/assets/e072021d-ab9c-4edd-beb6-d38d19f75b51)
Watch more of the showcase here:
> https://raw.githubusercontent.com/3oFiz4/DiscordCLI/lv_0_20250624003510.mp4
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
emoji==1.6.3 clipboard rich prompt_toolkit discord.py asyncio shutil tkinter playsound threading json
````

---

## 🚀 Setup
First of all. Set up your token first. There's 2 way.
> a. `python main.py -t [YOUR_TOKEN]` 
> b. 
1. Open / Create your token.txt. Insert this template:
```
---
Username: Account_Username_0
Token: Token_Username_0
---
Username: Account_Username_1
Token: Token_Username_1
---
```
2. And replace Token_Username_0 with each desired token. You can also add more entry if you want to.
3. Then do `python main.py -s [index_token]/[username]`
> Example:
> `python main.py -s 1` # Starts Token_Username_1
> `python main.py -s Account_Username_1` # Starts token of Account_Username_1
4. REMEMBER, it should be Username-Token as the template, do not skip it, not even the <Space> between Token and :.
c. `python main.py` # Is equal to `python main.py -s 0`
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
-ct [emoji]         React a message with emoji, ex: -ct 5 :sob:
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
":...:"             List all possible emoji
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

* emoji picker wont work on `react` command. *i can actually fix it, but my time is up already`
* @ mention won't work.
* (minor) Screen may scroll to top on mention
* (minor) Command auto-complete can break before API init (fix: press space and retype)
* (minor) Display name invisibility on some servers

🐛 Found a bug? [Submit an Issue](../../issues)

---

## ✅ Features

### ✔ Done

* Reply, send, delete messages
* Copy, Pin, Edit messages
* React to messages
* Chat in servers / DMs
* Message forwarding
* Upload + auto-remove file attachments
* Display name + timestamp
* Emoji reactions
* Notification system (WIP)
* Rich config via `conf.json`
* Multi-token login
* Multi-Access Login (either via ~~Username and Password (not possible apparently, it asked for CAPTCHA instead)~~ or Token)
### 🚧 Planned / In Progress
* ⏳ Per-channel notification sounds
* ⏳ Hotkey support
* ⏳ Change profile pic, bio, banner
* ⏳ Open files via browser
* ⏳ Colored text / markdown preview (via `rich` and `lexer`
* ⏳ Snippets like `{myutc}` → current time
* ⏳ Join/leave server
* ⏳ Bookmark message
* ⏳ Join & Leave a server
* ⏳ Color a text (similar to snippet, reference [Rebane Message Color](https://rebane2001.com/discord-colored-text-generator/)

---
<details>
<summary><strong>Changelog: </summary>
<pre>
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
    v25.06.21.03 (added react to message)
        - More commands
            a. -(rea)ct (message)
                > This won't display properly if your CMD unable to show emoji. It do works in Win 11.
        - Added Account Template
            a. You can now switch to different account easily through `token.txt`
            b. Input token via `-t` in CLI
<pre>
</details>
