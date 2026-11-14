"""One native palette opened from one of the five main color bubbles."""
from i18n import t
from tkinter import colorchooser, messagebox
from colors import MAIN_COLORS, save_colors, set_main_color


def choose_color(parent,theme,key,on_saved):
    label = dict(MAIN_COLORS)[key]
    selected = colorchooser.askcolor(theme[key],parent=parent,title=t('Cor: {label}',label=t(label)))[1]
    if not selected:
        return
    try:
        result = set_main_color(theme,key,selected)
        save_colors(result)
        on_saved(result)
    except (ValueError,OSError) as error:
        messagebox.showerror(t('Não foi possível salvar a cor'),str(error),parent=parent)
