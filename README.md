# 🎵 Music-player

**Player** is a modern and customizable music player for Windows, built with Python using PyQt5 and pygame.

The application is focused on local music and allows you not only to play tracks, but also to fully customize the appearance of the player to your liking.

## ✨ Features

* 🎧 Local music file playback
* 📂 Personal music library
* 🎶 Playlist creation and management
* 🔀 Track shuffle
* 🔊 Volume control
* 🎚️ Equalizer with built-in presets
* 🎛️ Bass, treble, balance, and preamp adjustment
* 🖼️ Custom track covers
* 🎞️ GIF cover support
* 🌌 Custom application background
* 🎞️ Animated GIF background support
* ✨ Background particle system
* 🎨 Accent color customization
* 🌑 Dark and light themes
* 🔤 Font and font size selection
* 🪟 Interface transparency settings
* 🖼️ Cover size and corner radius customization
* 💫 Cover shadows
* 🎨 Customizable interface elements
* 🖥️ Integration with the Windows system title bar

Settings, playlists, themes, and additional data are stored locally in JSON format, allowing user preferences to persist between application launches.

## 🛠️ Technologies

The project is written in **Python**.

Main libraries:

* **PyQt5** — graphical user interface
* **pygame** — audio playback
* **Mutagen** — retrieving information from music files
* **yt-dlp** — working with supported online sources
* **Pillow** — image processing
* **Requests** — network requests

All major dependencies are listed directly in the source code.

## 📦 Installation

Install Python first, then install the required dependencies:

```bash
python -m pip install PyQt5 pygame yt-dlp mutagen Pillow requests
```

Clone the repository:

```bash
git clone https://github.com/gamesnekit4-source/music-player.git
cd music-player
```

Run the application:

```bash
python music-player.py
```

## ⚙️ Application Data

On the first launch, MPlayer automatically creates the following folder:

```text
mplayer_data/
```

It contains user application data, including:

* `playlists.json` — playlists and music library
* `settings.json` — interface and player settings
* `themes.json` — custom themes
* `covers/` — saved covers
* `assets/` — additional resources

This allows settings to be stored separately from the program's source code.

## 🎨 Customization

MPlayer was created with a strong focus on personalization.

You can customize almost the entire appearance of the application: background, panel transparency, accent color, font, cover art, cover size and corner radius, effects, particles, and equalizer settings. The background supports both regular images and GIF animations.

## 🚧 Project Status

The project is currently under development.

MPlayer is being developed as an experimental customizable music player, so some features may change, be improved, or occasionally behave unstably.

If you find a bug or want to suggest a new feature, create an **Issue** in the repository.
