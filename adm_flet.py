import flet as ft

from network3 import Network
import pickle
import time

DISABLED_COLOR = "#c8c8c8"
ENABLED_COLOR = "#646464"

#DEFAULT_FLET_PORT = 8502

pg = None
n = None
xtime = str(round(time.time()))

current_period = 1
adm_period = 0


class ProcessData:
    def __init__(self, data_id, data_list, data_leadtimeup):
        self.data_id = data_id
        self.data_list = data_list
        self.data_leadtimeup = data_leadtimeup


def main(page: ft.Page):
    global pg
    pg = page
    pg.title = "Administrator"
    pg.bgcolor = "#e6e6e6"
    pg.window_width = 800
    pg.window_height = 600

    def on_button_adm_disconnect_pressed(e):        
        n.send(pickle.dumps(ProcessData("disconnect", [0], 0)))
        button_adm_connect.disabled = False
        button_adm_disconnect.disabled = True
        button_adm_connect.update()
        button_adm_disconnect.update()
    
    def on_button_adm_connect_pressed(e):
        global n
        password = textEditPassAdm.value
        server = textEditServerAdm.value
        port = int(textEditPortAdm.value)

        def is_valid_password(password):
            return password == "1"

        if is_valid_password(password):  
            n = Network(server, port)
            run = True
            print(server)
            print(port)
            try:
                n.send(pickle.dumps(ProcessData("get_adm", [0], 0))) 
                label_adm_info.value = f"Administrator connected to:  {server} {str(port)}"
                label_adm_info.update()
            except Exception as e:
                run = False
            button_adm_connect.bgcolor = DISABLED_COLOR
            button_adm_connect.update()
            button_adm_connect.disabled = True
            button_adm_connect.update()
            button_adm_disconnect.disabled = False
            button_adm_disconnect.update()
            button_adm_disconnect.bgcolor = ENABLED_COLOR
            button_adm_disconnect.update()
            button_adm_setperiod.disabled = False
            button_adm_setperiod.update()
            button_adm_setperiod.bgcolor = ENABLED_COLOR
            button_adm_setperiod.update()
            textEditPassAdm.value = ""
            textEditPassAdm.update()            
        else:
            pass
            # self.logger.error("Invalid password")

    def on_button_adm_set_period_pressed(e):
        new_period = int(textEditSetPeriod.value) 
        global adm_period
        global current_period
        if int(adm_period) < new_period:
            adm_period = new_period
            current_period = new_period
            label_adm_period.value = f"Current Period: {current_period}"
            label_adm_period.update()
            #label_adm_turnstatus.value = f"{current_period} Turn Status"
            #label_adm_turnstatus.update()
            n.send(pickle.dumps(ProcessData("set_period", [0], adm_period)))
            adm_demand = textEditSetCustDemand.value
            n.send(pickle.dumps(ProcessData("set_demand", [0], adm_demand)))
            button_adm_update.disabled = False
            button_adm_update.bgcolor = ENABLED_COLOR
            button_adm_update.update()
        else:
            pass
        
    def on_button_adm_update_pressed(e):        
        status_text = n.send(pickle.dumps(ProcessData("check_status", [0], 0)))        
        label_adm_status.value = status_text
        label_adm_status.update()

    label_adm_period = ft.Text(value="Current Period: ", text_align=ft.TextAlign.LEFT, size=22, weight=ft.FontWeight.BOLD)
    label_adm_turnstatus = ft.Text(value="Turn status: ", text_align=ft.TextAlign.RIGHT, size=22, weight=ft.FontWeight.BOLD)
    label_adm_status = ft.Text(value="Turn status info: ", text_align=ft.TextAlign.RIGHT, size=12, right=10, top=50)
    label_adm_setperiod = ft.Text(value="Period: ", text_align=ft.TextAlign.LEFT, size=18)
    label_adm_setcustdemand = ft.Text(value="Demand: ", text_align=ft.TextAlign.LEFT, size=18)
    label_adm_leadtime = ft.Text(value="Lead Time: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_adm_backlog = ft.Text(value="Backlog: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_adm_inventory = ft.Text(value="Inventory: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_adm_demand = ft.Text(value="Demand: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_separator = ft.Text(value=" ", text_align=ft.TextAlign.LEFT, size=60, color="#e6e6e6")
    label_adm_pass = ft.Text(value="Password:", text_align=ft.TextAlign.LEFT, size=12)
    label_adm_server = ft.Text(value="Server:", text_align=ft.TextAlign.LEFT, size=12)
    label_adm_port = ft.Text(value="Port:", text_align=ft.TextAlign.LEFT, size=12)
    label_adm_info = ft.Text(value="Info", text_align=ft.TextAlign.LEFT, size=12)
    textEditSetPeriod = ft.TextField(value="1", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75, height=40,
                                     text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditSetCustDemand = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditPassAdm = ft.TextField(value="passphrase", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditServerAdm = ft.TextField(value="localhost", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                     height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditPortAdm = ft.TextField(value="5556", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    button_adm_setperiod = ft.ElevatedButton("Set period and demand", on_click=on_button_adm_set_period_pressed,
                                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), side=ft.BorderSide(1, ft.colors.GREY)),
                                              bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    button_adm_disconnect = ft.ElevatedButton("Disconnect", on_click=on_button_adm_disconnect_pressed,
                                               style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), side=ft.BorderSide(1, ft.colors.GREY)),
                                               bgcolor=DISABLED_COLOR, color="#ffffff",  right=10, top=10, disabled=True)
    button_adm_update = ft.ElevatedButton("Update all", on_click=on_button_adm_update_pressed, 
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), side=ft.BorderSide(1, ft.colors.GREY)),
                                          bgcolor=DISABLED_COLOR, color="#ffffff",  right=10, bottom=10, disabled=True)
    button_adm_connect = ft.ElevatedButton("Connect", on_click=on_button_adm_connect_pressed,
                                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5), side=ft.BorderSide(1, ft.colors.GREY)),
                                           bgcolor=ENABLED_COLOR, color="#ffffff")
    page.overlay.append(button_adm_disconnect)
    page.overlay.append(button_adm_update)
    page.overlay.append(label_adm_status)

    page.add(
        ft.ResponsiveRow(
                [
                    ft.Container(
                        label_adm_period,
                        col={"md": 7},
                    ),
                ],
            ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_setperiod,
                    padding=7,
                    col={"md": 2},
                ),
                ft.Container(
                    textEditSetPeriod,
                    col={"md": 1.5},
                ),
                ft.Container(
                    label_adm_leadtime,
                    col={"md": 3.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_setcustdemand,
                    padding=7,
                    col={"md": 2},
                ),
                ft.Container(
                    textEditSetCustDemand,
                    col={"md": 1.5},
                ),
                ft.Container(
                    label_adm_backlog,
                    col={"md": 3.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    button_adm_setperiod,
                    col={"md": 3.5},
                ),
                ft.Container(
                    label_adm_inventory,
                    col={"md": 3.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [

                ft.Container(
                    label_adm_demand,
                    col={"md": 7},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_separator,
                    col={"md": 1},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_pass,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditPassAdm,
                    col={"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_server,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditServerAdm,
                    col={"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_port,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditPortAdm,
                    col={"md": 1},
                ),
                ft.Container(
                    button_adm_connect,
                    padding=4,
                    col={"md": 2},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_adm_info,
                    padding=10,
                    col={"md": 8},
                ),
            ],
        ),
        )

#ft.app(target=main)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53859)
