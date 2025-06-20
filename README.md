![image](https://github.com/user-attachments/assets/e072021d-ab9c-4edd-beb6-d38d19f75b51)

# DiscordCLI
A Discord on a terminal I made within 4 hours, functional (able to reply, message). 
---
## Thumbnail
![cmd_lv7piEcLky-ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/8067db4a-0f02-457f-b6ef-3897aefdb14f)
---
## Caution
You are free to use this as a **selfbot**, although I need to remind you that it **is quite risky and may get your account banned**, since this violates Discord TOS. And **I AM NOT responsible if your account gets banned**.
Instead, use this on an alternative account, or within your Discord BOT.
---
## Requirements
`rich prompt_toolkit discord.py asyncio shutil tkinter `
---
## Set-Up
Make sure you installed the requirements already
### By Fresh Start
1. Go run `python main.py`, and do `-h` or `-changelog`

### By PATH (recommended, since you dont need to be in parent folder to run this script)
1. Clone this repo to your `C:/Users/[your-name]` as `DisCLI` (I assume you know how)
2. Go to `Computer`, right shift and click `Property`, go to `Advanced`, and `Click` Environmental Variables
3. On `System Variables`, choose Path and click `Edit`
4. Click `New`, and add this `C:\Users\[your-name]\DisCLI\`
5. Click `Ok`, and `Ok`, and `Ok`
---
# Command List
How to Use:
> -changelog to see changelog
> -h to see help
#### Navigation:
    -s [server]: Pick a server
    -c [channel]: Pick a channel to Chat (require -s to be triggered)
    -cf [friend]: Pick a friend to DM
    -q(uit) or -e(xit): Exit the CLI
#### Typing
    -r [message no.] [txt]: Reply to message no with txt
    -d [messages no.]: Delete messages index, accept list (e.g., -d 1 2 3)
    -up: Uploads a file, check your window list, there will be an explorer pop up, when you're done, it is saved into upload/, and you can send the file via '-r' or 'say' in which it will deletes after each -r or 'say'
    -deup: Delete all staged file upload
    -fw [message no.] [friend/member/dm]: Forward message index to somebody
    "@": Typing @ will gives a list of member in current channel to be mentioned
#### Misc
    -ntf/-notif: Checks notification (within the buffer)
    -gntf/-gonotif: Go to notification location
    ->n & -<n: Scroll > (newest) or < (oldest) to n messages
---
# Known bugs
- (minor) Whenever there's a ping the screen will scroll to the top for no reason
- (minor) Whenever the command `s` or `c` is used before the initialization of the account to the API, there is chances that the completer won't appear, until <Space> is entered and the command is re-input
- SOLVED (also delete input_session). Whenever any messages appear or that fn:render_history updates, while typing, the text may be cropped.
- (minor) There's a bug with how Displayname and Username is being shown at some specific server in which they appear to be invisible
- (minor) Instead of requesting user to initializate `token.txt`, it shows an error instead
- [ ] When `main.py` is triggered as PATH, the program does not work, likely issue in `dc.bat`
- *encounter a bug? Report to Issues please*
# Features
- [x] Replying
- [x] Sending messages (non-reply)
- [x] Traverse History
- [x] Chat on specific channel on a server
- [x] Chat on friends
- [x] Messages forwarding
- [x] Delete message
- [x] Message timestamp
- [x] Upload files and images
- [ ] Different notifications for different channels, user, server
- [ ] Support hotkeys
- [ ] React to Message (buggy)
- [ ] Ability to change profile picture, bio, banner, and more
- [x] Ability to show attached files in a message
- [ ] Ability to open attached files via browser (buggy)
- [ ] Better Notifications and Ping (with notification pop-up), with custom ping sound (might use `playsound` module)
- [x] More configurable variables 
- [ ] Ability to add Emoji (buggy)
- [ ] Snippet within a message (e.g., typing {myutc} will paste your current time within the message) (partial)
- [ ] Ability to Edit message (from an index)
- [ ] Ability to Copy a message (from an index)
- [ ] Ability to Join, Leave a server
- [ ] Markdown view on CMD (using `rich` and some Lexer)
- [ ] Ability to colorize a text within a message (similar to snippet, reference [Rebane Message Color](https://rebane2001.com/discord-colored-text-generator/)
- [ ] Improved Chat UI for Blocked/Ignored user, and user that replies to user (marked with lighter background)
- [ ] Ability to Pin, Bookmark messages
- [ ] Login via Username & Password
- [ ] Multi-Access to token, not just single
That's it I think.
# Changelog
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
