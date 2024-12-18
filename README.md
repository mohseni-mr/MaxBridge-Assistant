# MaxBridge Assistant

_Files and instructions for fixing Quixel Bridge connection with newer version of 3ds Max._

---

Quixel Bridge's official plugin has compatibility issues with newer versions of 3ds Max, particularly 2024 and 2025. This repository provides updated files and an optional assistant app to address these issues.
This project is licensed under the MIT License, granting full freedom to use, modify, and distribute this work.

I hope Quixel will officially fix these problems soon and they are welcome to use my simple code in any way if they want to.

> [Get in touch with me](https://bio.mohseni.info/)<br><small>Mohammadreza Mohseni</small>

---

## [Issues](#issues)

1. Version Limitation:

   - The plugin version file limits compatibility to 3ds Max 2023, preventing connections for newer versions like 2024 or 2025.

2. API Changes in 3ds Max 2025:

   - Starting from 2023, MaxPlus is no longer shipped with 3ds Max.
   - In 2025, Python APIs underwent significant changes, including updates to PySide2 and added support for PySide6. Quixel's plugin hasn't been updated to reflect these changes.

3. Code Duplication:
   - The original plugin code contains unnecessary duplication, which hasn't been addressed.

## [Changes](#changes)

### What’s New:

- Reduced code duplication with minor refactoring.

- Unified compatibility for 3ds Max 2025 and higher, while maintaining support for older versions.

- Added functionality to handle menu creation for 3ds Max 2025+, accounting for API changes while ensuring seamless functionality across versions.

---

## [How to Use](#how-to)

You have two options to fix the issues:

1. Use the MaxBridge Assistant App (easy and automated).
2. Follow the manual process (slightly more involved).

<br>

### [1. MaxBridge Assistant (Easy Method)](#easy)

1. Close `"Quixel Bridge" & "3ds Max"`
   <br>

2. Download the app from release section of this repository.<br>[DOWNLOAD LATEST VERSION](https://github.com/mohseni-mr/MaxBridge-Assistant/releases/latest/download/MaxBridge_Assistant.exe)
   <br>
   > Use v1.1 if you do not want your `%localappdata%` attributes to change, because from v2 the app remove system attribute from this folder so 3ds Max act as it should be.<br>download other from [release section](https://github.com/mohseni-mr/MaxBridge-Assistant/releases)<br><br>Windows 11 24h2 add system attributes to `%localappdata%` so many application restricted to access this folder like 3ds Max this make many scripts not to work as expected
   <br>
3. Run the app (portable, no installation needed).
   <br>
   
4. Check the the 3ds Max versions you want to connect to Quixel Bridge.
   <br>
   
5. Click `"Select Megascans Library"` button and select your library folder
   <br><small>*must be exact match as you library in `Quixel Bridge` settings*</small><br>

6. Click "Start Setup"
   <br>
   
7. Wait for the app to download and replace the necessary files.
   <br>
8. Reopen `"Quixel Bridge" & "3ds Max"` and continue your workflow as usual.

![Screenshot for MaxBridge Assistant to fix issues of Quixel Bridge and 3dsMax connection](https://raw.githubusercontent.com/mohseni-mr/MaxBridge-Assistant/main/app/screenshot-v2.png)

<small>*screenshot of the GUI*</small>


## [2. Manual Method](#manual)

1. Close `"Quixel Bridge" & "3ds Max"`
   <br>

2. Locate the `"Megascans Library Folder"` on your system. Then navigate to:

   ```php
   <Megascans Library Folder>\support\plugins
   ```

   <small>_Example: If your library is at D:\Megascans, go to `D:\Megascans\support\plugins`_</small>
   <br>

3. Delete or rename the `"plugin_versions_12.json"` file.

   - Replace it with the version from this repository:

   ```php
   modified > plugin_versions_12.json
   ```

   <br>

4. Delete or rename the `"max"` folder (if it exists).
   <br>

5. Open `Quixel Bridge` then go to `"Edit" > "Manage Plugins"` menu and download the official plugin.

   - <small>_This step will reinstall the plugin and create the necessary connector script, even for 3ds Max 2025._</small>
     <br>

6. RReplace the following file on your system:

```php
<Megascans Library Folder>\support\plugins\max\5.5\MSLiveLink\MS_API.py
```

Replace it with the version from this repository:

```php
modified > max > 5.5 > MSLiveLink > MS_API.py
```

1. Reopen `"Quixel Bridge"` and `"3ds Max"` and continue your workflow as usual.

---

## [License](#license)

This project is licensed under the [MIT License](https://github.com/mohseni-mr/MaxBridge-Assistant/blob/main/LICENSE). Feel free to use, modify, and distribute.

---

## [Feedback and Contact](#contact)

I hope this project helps you restore functionality between Quixel Bridge and newer 3ds Max versions. If you encounter any issues or have suggestions, feel free to [contact me](https://bio.mohseni.info/).
