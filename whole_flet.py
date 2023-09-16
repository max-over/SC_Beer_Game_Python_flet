import flet as ft

from network3 import Network
import pickle
import time
from xlwt import Workbook

DISABLED_COLOR = "#c8c8c8"
ENABLED_COLOR = "#fe96a0"
HOLDINGRATE = 2
BACKLOGRATE = 4
LEADTIMEUP = 2
LEADTIMEDOWN = 2
INVENTORY = 20

pg = None
n = None

xtime = str(round(time.time()))
current_period = 0
current_demand = 0
inventory = INVENTORY
leadtimeup = LEADTIMEUP
leadtimedown = LEADTIMEDOWN
sl = 1.00
costs = 0
backlog = 0
holdingrate = HOLDINGRATE
backlograte = BACKLOGRATE
backlogcount = 0
backlogtotal = 0
inventorycosts = 0
backlogcosts = 0
wb = Workbook()
sheet_whole = wb.add_sheet("Wholesaler")
sheet_whole.write(0, 0, "Period")
sheet_whole.write(0, 1, "Demand")
sheet_whole.write(0, 2, "Order")
sheet_whole.write(0, 3, "Shipment")
sheet_whole.write(0, 4, "Inventory")
sheet_whole.write(0, 5, "Total_Costs")
sheet_whole.write(0, 6, "Backlog")
sheet_whole.write(0, 7, "SL")
sheet_whole.write(0, 8, "Inventory_Costs")
sheet_whole.write(0, 9, "Lost_sales_Costs")


class ProcessData:
    def __init__(self, data_id, data_list, data_leadtimeup):
        self.data_id = data_id
        self.data_list = data_list
        self.data_leadtimeup = data_leadtimeup


def main(page: ft.Page):
    global pg
    pg = page
    pg.title = "Wholesaler"
    pg.bgcolor = "#e6e6e6"
    pg.window_width = 800
    pg.window_height = 600
    pg.expand = True
    pg.scroll = "ALWAYS"

    def on_button_whole_disconnect_pressed(e):
        n.send(pickle.dumps(ProcessData("disconnect", [0], 0)))
        button_whole_connect.disabled = False
        button_whole_disconnect.disabled = True
        button_whole_connect.update()
        button_whole_disconnect.update()
        label_whole_info.value = "Disconnected from server"
        label_whole_info.update()

    def on_button_whole_connect_pressed(e):
        global n
        password = textEditPassWhole.value
        server = textEditServerWhole.value
        port = int(textEditPortWhole.value)

        def is_valid_password(password):
            return password == "1"

        if is_valid_password(password):
            n = Network(server, port)
            run = True
            print(server)
            print(port)
            try:
                n.send(pickle.dumps(ProcessData("get_whole", [0], 0)))
                label_whole_info.value = f"Wholesaler connected to: {server}_{port}"
                label_whole_info.visible = True
                label_whole_info.update()
            except:
                run = False
            button_whole_connect.bgcolor = DISABLED_COLOR
            button_whole_connect.update()
            button_whole_connect.disabled = True
            button_whole_connect.update()
            button_whole_disconnect.disabled = False
            button_whole_disconnect.bgcolor = ENABLED_COLOR
            button_whole_disconnect.update()
            button_whole_update.disabled = False
            button_whole_update.bgcolor = ENABLED_COLOR
            button_whole_update.update()
            textEditPassWhole.value = ""
            textEditPassWhole.update()
        else:
            pass

    def on_button_whole_update_pressed(e):
        global current_period
        global inventory
        global current_demand
        server_period = n.send(pickle.dumps(ProcessData("upd_ret_period", [0], current_period)))
        distr_demand = n.send(pickle.dumps(ProcessData("upd_distr_whole_demand", [0], 0)))
        current_demand = distr_demand.data_leadtimeup
        label_whole_demand.value = f"Demand: {current_demand}"
        label_whole_demand.update()
        if int(server_period) == 0:
            label_whole_demand.value = "Demand: no data"
            label_whole_demand.update()

        if int(server_period) > current_period:
            button_whole_shipment.disabled = False
            button_whole_shipment.update()
            button_whole_shipment.bgcolor = ENABLED_COLOR
            button_whole_shipment.update()
            current_period = int(server_period)
            label_whole_period.value = f"Current Period: {current_period}"
            label_whole_period.update()
            sheet_whole.write(int(current_period), 0, int(current_period))
            wb.save(f"whole_stat{textEditPortWhole.value}_{xtime}.xls")

            if current_period > 1:
                shipment = n.send(pickle.dumps(ProcessData("upd_whole_plant_shipment", [current_period], leadtimeup)))
                if shipment.data_list != "":
                    inventory += int(shipment.data_list)

            update_costs()

            sheet_whole.write(int(current_period), 8, float(inventorycosts))
            sheet_whole.write(int(current_period), 9, float(backlogcosts))

            label_whole_costs.value = f"Costs(total): {costs}"
            label_whole_costs.update()
            label_whole_inventory.value = f"Inventory: {inventory}"
            label_whole_inventory.update()
            label_whole_backlog.value = f"Backlog(total): {backlogtotal}"
            label_whole_backlog.update()

        label_whole_status.value = n.send(pickle.dumps(ProcessData("check_status_node", [0], 0)))
        label_whole_status.update()

    def update_costs():
        global inventorycosts
        global backlogcosts
        global costs
        inventorycosts += inventory * holdingrate
        backlogcosts = backlogtotal * backlograte
        costs = inventorycosts + backlogcosts

    def on_button_whole_shipment_pressed(e):
        global sl
        try:
            wholeshipment = int(textEditShipmentWhole.value)
            wholeshipment = min(wholeshipment, inventory, current_demand + backlogtotal)
            wholeshipment = max(wholeshipment, 0) if wholeshipment >= 0 else 0

            update_backlog_and_inventory_demand(wholeshipment)

            n.send(pickle.dumps(ProcessData("whole_shipment", [0], wholeshipment)))
            sl = 1 - backlogcount / current_period
            sheet_whole.write(int(current_period), 1, int(current_demand))
            sheet_whole.write(int(current_period), 3, int(wholeshipment))
            sheet_whole.write(int(current_period), 4, int(inventory))
            sheet_whole.write(int(current_period), 5, int(costs))
            sheet_whole.write(int(current_period), 6, int(backlogtotal))
            sheet_whole.write(int(current_period), 7, float(sl))
            wb.save(f"whole_stat{textEditPortWhole.value}_{xtime}.xls")
            button_whole_shipment.bgcolor = DISABLED_COLOR
            button_whole_shipment.update()
            button_whole_shipment.disabled = True
            button_whole_shipment.update()
            label_whole_sl.value = f"Backlog periods: {backlogcount}"
            label_whole_sl.update()
            label_whole_inventory.value = f"Inventory: {inventory}"
            label_whole_inventory.update()
            label_whole_backlog.value = f"Backlog(total): {backlogtotal}"
            label_whole_backlog.update()
            button_whole_order.bgcolor = ENABLED_COLOR
            button_whole_order.update()
            button_whole_order.disabled = False
            button_whole_order.update()

        except ValueError:
            wholeshipment = 0
        textEditShipmentWhole.value = str(wholeshipment)
        textEditShipmentWhole.update()

    def update_backlog_and_inventory_demand(wholeshipment):
        global inventory
        global backlogtotal
        global backlogcount
        backlogtotal += current_demand - wholeshipment
        if int(current_demand) > wholeshipment:
            backlogcount += 1
            inventory = 0
        else:
            inventory += - wholeshipment

    def on_button_whole_order_pressed(e):
        try:
            whole_order = int(textEditOrderWhole.value)
            if whole_order >= 0:
                n.send(pickle.dumps(ProcessData("whole_order", [0], whole_order)))
                sheet_whole.write(int(current_period), 2, int(whole_order))
                wb.save(f'whole_stat{textEditPortWhole.value}_{xtime}.xls')
                button_whole_order.bgcolor = DISABLED_COLOR
                button_whole_order.update()
                button_whole_order.disabled = True
                button_whole_order.update()
            else:
                whole_order = 0
        except ValueError:
            whole_order = 0

        textEditOrderWhole.value = str(whole_order)

    label_whole_period = ft.Text(value="Current Period: 0", text_align=ft.TextAlign.LEFT, size=22,
                               weight=ft.FontWeight.BOLD)
    label_whole_status = ft.Text(value="Turn status info: ", text_align=ft.TextAlign.RIGHT, size=12, right=10, top=50)
    label_whole_ordersize = ft.Text(value="Order Size: ", text_align=ft.TextAlign.LEFT, size=18)
    label_whole_shipment = ft.Text(value="Shipment: ", text_align=ft.TextAlign.LEFT, size=18)
    label_whole_leadtime = ft.Text(value="Leadtime to Plant: " + str(LEADTIMEUP), text_align=ft.TextAlign.RIGHT,
                                 size=14,
                                 weight=ft.FontWeight.BOLD)
    label_whole_backlog = ft.Text(value="Backlog (total): ", text_align=ft.TextAlign.RIGHT, size=14,
                                weight=ft.FontWeight.BOLD)
    label_whole_inventory = ft.Text(value="Inventory: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD)
    label_whole_demand = ft.Text(value="Demand: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_whole_costs = ft.Text(value="Costs (total): ", text_align=ft.TextAlign.LEFT, size=18)
    label_whole_sl = ft.Text(value="SL: ", text_align=ft.TextAlign.LEFT, size=18)
    label_whole_structure = ft.Text(value="Stock structure: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD, visible=False)
    label_whole_stock_structure = ft.Text(value="stock: ", text_align=ft.TextAlign.RIGHT, size=12, visible=False)
    label_whole_holding_rate = ft.Text(value="Holding costs rate: " + str(HOLDINGRATE), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_whole_backlog_rate = ft.Text(value="Backlog costs rate: " + str(BACKLOGRATE), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_separator = ft.Text(value=" ", text_align=ft.TextAlign.LEFT, size=0, color="#e6e6e6")
    label_whole_pass = ft.Text(value="Password:", text_align=ft.TextAlign.LEFT, size=12)
    label_whole_server = ft.Text(value="Server:", text_align=ft.TextAlign.LEFT, size=12)
    label_whole_port = ft.Text(value="Port:", text_align=ft.TextAlign.LEFT, size=12)
    label_whole_info = ft.Text(value="Info", text_align=ft.TextAlign.LEFT, size=12)
    textEditOrderWhole = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditShipmentWhole = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditPassWhole = ft.TextField(value="passphrase", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditServerWhole = ft.TextField(value="localhost", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                     height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditPortWhole = ft.TextField(value="5556", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    button_whole_order = ft.ElevatedButton("Order", on_click=on_button_whole_order_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    button_whole_shipment = ft.ElevatedButton("Shipment", on_click=on_button_whole_shipment_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    #button_whole_disconnect = ft.ElevatedButton("Disconnect", on_click=on_button_whole_disconnect_pressed,
    #                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
    #                                                               side=ft.BorderSide(1, ft.colors.GREY)),
    #                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_whole_update = ft.ElevatedButton("Update", on_click=on_button_whole_update_pressed,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                               side=ft.BorderSide(1, ft.colors.GREY)),
                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_whole_connect = ft.ElevatedButton("Connect", on_click=on_button_whole_connect_pressed,
                                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                side=ft.BorderSide(1, ft.colors.GREY)),
                                           bgcolor=ENABLED_COLOR, color="#ffffff")
    #page.overlay.append(button_whole_disconnect)
    page.overlay.append(button_whole_update)
    page.overlay.append(label_whole_status)

    page.add(
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_period,
                    col={"xs": 12,"md": 7},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_ordersize,
                    padding=7,
                    col={"xs": 12,"md": 2},
                ),
                ft.Container(
                    textEditOrderWhole,
                    col={"xs": 3,"md": 1.5},
                ),
                ft.Container(
                    button_whole_order,
                    col={"xs": 5,"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_whole_leadtime,
                    col={"xs": 12,"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_shipment,
                    padding=7,
                    col={"xs": 12,"md": 2},
                ),
                ft.Container(
                    textEditShipmentWhole,
                    col={"xs": 3,"md": 1.5},
                ),
                ft.Container(
                    button_whole_shipment,
                    col={"xs": 5,"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_whole_backlog,
                    col={"xs": 12,"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_costs,
                    padding=7,
                    col={"xs": 6,"md": 3.5},
                ),
                ft.Container(
                    label_whole_inventory,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_sl,
                    col={"xs": 6,"md": 3.5},
                    padding=10,
                ),
                ft.Container(
                    label_whole_demand,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_whole_holding_rate,
                    col={"xs": 6,"md": 5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_stock_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_whole_backlog_rate,
                    col={"xs": 6,"md": 5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_separator,
                    col={"xs": 12,"md": 1},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_pass,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPassWhole,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_server,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditServerWhole,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_port,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPortWhole,
                    col={"xs": 8,"md": 1},
                ),
                ft.Container(
                    button_whole_connect,
                    padding=4,
                    col={"xs": 4,"md": 2},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_whole_info,
                    padding=10,
                    col={"xs": 12,"md": 8},
                ),
            ],
        ),
    )


# ft.app(target=main)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53862)
