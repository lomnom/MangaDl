# MangaDl, a tool to download manga from *certain manga websites*
## Usage
### Running it
Run as `python Download.py [[site][range]]+`  
For example, run `python Download.py https://toilet-bound-hanako-kun.com 1,36-82` to download chapters 1 and 36-82 of 'toilet-bound hanako-kun' into the current folder
### What sites are valid
Sites that have headers that look like these:  
![Hanako](Screenshots/HanakoHeader.png)  
![Neverland](Screenshots/NeverlandHeader.png)  
![Hanako](Screenshots/BeastarsHeader.png)  
Can be used with the script
## Installation
```bash
pip install Pillow PyPDF2 requests beautifulsoup4
git clone https://github.com/lomnom/MangaDl
```
## Uninstallation
Just remove the folder that was cloned
## Screenshots
![Downloading](Screenshots/Downloading.png)  
![Product](Screenshots/Product.png)  