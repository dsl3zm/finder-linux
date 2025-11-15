## Linux Finder

This project is an attempt at a linux port of Mac's spotlight search
and Windows' Power Toys Run

### Local

Install uv https://github.com/astral-sh/uv

and then install the following on your linux distro (ubuntu tested and working)

```bash
sudo apt install libcairo2-dev libxt-dev libgirepository1.0-dev libgirepository-2.0-dev
sudo apt install libgtk-4-dev gir1.2-gtk-4.0
```

after this, simply run `uv run main.py`