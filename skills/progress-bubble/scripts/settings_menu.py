"""Unified desktop preferences; share visibility without changing task data."""
import json
import tkinter as tk
from tkinter import messagebox
from colors import config_path
from i18n import t
from sizing import populate_size_menu
from web_client import save_secret


def load_preferences(path=None):
    try:
        data=json.loads((path or config_path().with_name('settings.json')).read_text(encoding='utf-8'))
        value=data.get('show_usage')
        return {'show_usage':value if type(value) is bool else True}
    except (OSError,ValueError,AttributeError):return {'show_usage':True}


def save_preferences(show_usage,path=None):
    if type(show_usage) is not bool:raise ValueError('Expected a boolean visibility preference')
    data={'show_usage':show_usage}
    save_secret(path or config_path().with_name('settings.json'),data)
    return data


def show_settings_menu(app,event=None):
    app.tooltip.hide()
    previous=getattr(app,'settings_menu',None)
    if previous is not None:previous.destroy()
    menu=tk.Menu(app.root,tearoff=False)
    app.settings_menu=menu
    menu.add_command(label=t('Cores'),command=app.edit_colors)
    if app.colors_open:menu.add_command(label=t('Redefinir cores'),command=app.reset_theme)
    sizes=tk.Menu(menu,tearoff=False)
    populate_size_menu(sizes,app)
    menu.add_cascade(label=t('Tamanhos'),menu=sizes)
    menu.add_separator()
    variable=tk.BooleanVar(master=app.root,value=app.settings['show_usage'])
    menu.usage_variable=variable
    def change():
        try:app.settings=save_preferences(bool(variable.get()))
        except OSError as error:
            variable.set(app.settings['show_usage'])
            messagebox.showerror(t('Configurações'),t('Não foi possível salvar: {error}',error=error),parent=app.root)
            return
        app.draw()
    menu.add_checkbutton(label=t('Mostrar uso da assinatura'),variable=variable,command=change)
    x=event.x_root if event is not None else app.root.winfo_rootx()+round(app.layout['card_x']+296*app.layout['card'])
    y=event.y_root if event is not None else app.root.winfo_rooty()+round((40+app.layout['offset'])*app.layout['card'])
    try:menu.tk_popup(x,y)
    finally:menu.grab_release()


def settings_tooltip(app,event):
    app.canvas.configure(cursor='hand2')
    app.tooltip.show(t('Configurações'),event.x_root,event.y_root)
