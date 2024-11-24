import flet as ft

from network3 import Network
import pickle
import time
from xlwt import Workbook

DISABLED_COLOR = "#c8c8c8"
ENABLED_COLOR = "#9eb0fd"
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
sheet_distr = wb.add_sheet("Distributor")
sheet_distr.write(0, 0, "Period")
sheet_distr.write(0, 1, "Demand")
sheet_distr.write(0, 2, "Order")
sheet_distr.write(0, 3, "Shipment")
sheet_distr.write(0, 4, "Inventory")
sheet_distr.write(0, 5, "Total_Costs")
sheet_distr.write(0, 6, "Backlog")
sheet_distr.write(0, 7, "SL")
sheet_distr.write(0, 8, "Inventory_Costs")
sheet_distr.write(0, 9, "Lost_sales_Costs")


class ProcessData:
    def __init__(self, data_id, data_list, data_leadtimeup):
        self.data_id = data_id
        self.data_list = data_list
        self.data_leadtimeup = data_leadtimeup


def main(page: ft.Page):
    global pg
    pg = page
    pg.title = "Distributor"
    pg.bgcolor = "#e6e6e6"
    pg.window.width = 800
    pg.window.height = 600
    pg.expand = True
    pg.scroll = "ALWAYS"


    def on_button_distr_disconnect_pressed(e):
        n.send(pickle.dumps(ProcessData("disconnect", [0], 0)))
        button_distr_connect.disabled = False
        button_distr_disconnect.disabled = True
        button_distr_connect.update()
        button_distr_disconnect.update()
        label_distr_info.value = "Disconnected from server"
        label_distr_info.update()

    def on_button_distr_connect_pressed(e):
        global n
        global current_period
        global inventorycosts
        global backlogcosts
        global backlogtotal
        global costs
        global inventory
        password = textEditPassDistr.value
        server = textEditServerDistr.value
        port = int(textEditPortDistr.value)

        def is_valid_password(password):
            return password == "1"

        if is_valid_password(password):
            n = Network(server, port)
            run = True
            print(server)
            print(port)
            try:
                n.send(pickle.dumps(ProcessData("get_distr", [0], 0)))
                label_distr_info.value = f"Distributor connected to: {server}_{port}"
                label_distr_info.visible = True
                label_distr_info.update()
                current_period = n.send(pickle.dumps(ProcessData("get_distr_lastperiod", [0], current_period)))
                inventorycosts = n.send(pickle.dumps(ProcessData("get_distr_inventorycosts", [0], 0)))
                backlogcosts = n.send(pickle.dumps(ProcessData("get_distr_backlogcosts", [0], 0)))
                backlogtotal = n.send(pickle.dumps(ProcessData("get_distr_backlogtotal", [0], 0)))
                costs = n.send(pickle.dumps(ProcessData("get_distr_costs", [0], 0)))
                if current_period > 0:
                    inventory = n.send(pickle.dumps(ProcessData("get_distr_inventory", [0], 0)))
            except:
                run = False
            button_distr_connect.bgcolor = DISABLED_COLOR
            button_distr_connect.update()
            button_distr_connect.disabled = True
            button_distr_connect.update()
          #  button_distr_disconnect.disabled = False
          #  button_distr_disconnect.bgcolor = ENABLED_COLOR
          #  button_distr_disconnect.update()
            button_distr_update.disabled = False
            button_distr_update.bgcolor = ENABLED_COLOR
            button_distr_update.update()
            textEditPassDistr.value = ""
            textEditPassDistr.update()
        else:
            pass

    def on_button_distr_update_pressed(e):
        global current_period
        global inventory
        global current_demand
        server_period = n.send(pickle.dumps(ProcessData("upd_ret_period", [0], current_period)))
        ret_demand = n.send(pickle.dumps(ProcessData("upd_ret_distr_demand", [0], 0)))
        current_demand = ret_demand.data_leadtimeup
        label_distr_demand.value = f"Demand: {current_demand}"
        label_distr_demand.update()
        if int(server_period) == 0:
            label_distr_demand.value = "Demand: no data"
            label_distr_demand.update()

        if int(server_period) > current_period:
            button_distr_shipment.disabled = False
            button_distr_shipment.update()
            button_distr_shipment.bgcolor = ENABLED_COLOR
            button_distr_shipment.update()
            current_period = int(server_period)
            label_distr_period.value = f"Current Period: {current_period}"
            label_distr_period.update()
            sheet_distr.write(int(current_period), 0, int(current_period))
            wb.save(f"distr_stat{textEditPortDistr.value}_{xtime}.xls")

            if current_period > 1:
                shipment = n.send(pickle.dumps(ProcessData("upd_distr_whole_shipment", [current_period], leadtimeup)))
                if shipment.data_list != "":
                    inventory += int(shipment.data_list)

            update_costs()

            sheet_distr.write(int(current_period), 8, float(inventorycosts))
            sheet_distr.write(int(current_period), 9, float(backlogcosts))

            label_distr_costs.value = f"Costs(total): {costs}"
            label_distr_costs.update()
            label_distr_inventory.value = f"Inventory: {inventory}"
            label_distr_inventory.update()
            label_distr_backlog.value = f"Backlog(total): {backlogtotal}"
            label_distr_backlog.update()

        label_distr_status.value = n.send(pickle.dumps(ProcessData("check_status_node", [0], 0)))
        label_distr_status.update()

    def update_costs():
        global inventorycosts
        global backlogcosts
        global costs
        inventorycosts += inventory * holdingrate
        backlogcosts = backlogtotal * backlograte
        costs = inventorycosts + backlogcosts

    def on_button_distr_shipment_pressed(e):
        global sl
        try:
            distrshipment = int(textEditShipmentDistr.value)
            distrshipment = min(distrshipment, inventory, current_demand + backlogtotal)
            distrshipment = max(distrshipment, 0) if distrshipment >= 0 else 0

            update_backlog_and_inventory_demand(distrshipment)

            n.send(pickle.dumps(ProcessData("distr_shipment", [0], distrshipment)))
            sl = 1 - backlogcount / current_period
            sheet_distr.write(int(current_period), 1, int(current_demand))
            sheet_distr.write(int(current_period), 3, int(distrshipment))
            sheet_distr.write(int(current_period), 4, int(inventory))
            sheet_distr.write(int(current_period), 5, int(costs))
            sheet_distr.write(int(current_period), 6, int(backlogtotal))
            sheet_distr.write(int(current_period), 7, float(sl))
            wb.save(f"distr_stat{textEditPortDistr.value}_{xtime}.xls")
            button_distr_shipment.bgcolor = DISABLED_COLOR
            button_distr_shipment.update()
            button_distr_shipment.disabled = True
            button_distr_shipment.update()
            label_distr_sl.value = f"Backlog periods: {backlogcount}"
            label_distr_sl.update()
            label_distr_inventory.value = f"Inventory: {inventory}"
            label_distr_inventory.update()
            label_distr_backlog.value = f"Backlog(total): {backlogtotal}"
            label_distr_backlog.update()
            button_distr_order.bgcolor = ENABLED_COLOR
            button_distr_order.update()
            button_distr_order.disabled = False
            button_distr_order.update()

        except ValueError:
            distrshipment = 0
        textEditShipmentDistr.value = str(distrshipment)
        textEditShipmentDistr.update()

    def update_backlog_and_inventory_demand(distrshipment):
        global inventory
        global backlogtotal
        global backlogcount
        backlogtotal += current_demand - distrshipment
        if int(current_demand) > distrshipment:
            backlogcount += 1
            inventory = 0
        else:
            inventory += - distrshipment

    def on_button_distr_order_pressed(e):
        try:
            distr_order = int(textEditOrderDistr.value)
            if distr_order >= 0:
                n.send(pickle.dumps(ProcessData("distr_order", [0], distr_order)))
                n.send(pickle.dumps(ProcessData("upd_distr_inventorycosts", [0], inventorycosts)))
                n.send(pickle.dumps(ProcessData("upd_distr_backlogcosts", [0], backlogcosts)))
                n.send(pickle.dumps(ProcessData("upd_distr_costs", [0], costs)))
                n.send(pickle.dumps(ProcessData("upd_distr_lastperiod", [0], current_period)))
                n.send(pickle.dumps(ProcessData("upd_distr_backlogtotal", [0], backlogtotal)))
                n.send(pickle.dumps(ProcessData("upd_distr_inventory", [0], inventory)))
                sheet_distr.write(int(current_period), 2, int(distr_order))
                wb.save(f'distr_stat{textEditPortDistr.value}_{xtime}.xls')
                button_distr_order.bgcolor = DISABLED_COLOR
                button_distr_order.update()
                button_distr_order.disabled = True
                button_distr_order.update()
            else:
                distr_order = 0
        except ValueError:
            distr_order = 0

        textEditOrderDistr.value = str(distr_order)

    label_distr_period = ft.Text(value="Current Period: 0", text_align=ft.TextAlign.LEFT, size=22,
                               weight=ft.FontWeight.BOLD)
    label_distr_status = ft.Text(value="Turn status info: ", text_align=ft.TextAlign.RIGHT, size=12, right=10, top=50)
    label_distr_ordersize = ft.Text(value="Order Size: ", text_align=ft.TextAlign.LEFT, size=18)
    label_distr_shipment = ft.Text(value="Shipment: ", text_align=ft.TextAlign.LEFT, size=18)
    label_distr_leadtime = ft.Text(value="Leadtime to Wholesaler: " + str(LEADTIMEUP), text_align=ft.TextAlign.RIGHT,
                                 size=14,
                                 weight=ft.FontWeight.BOLD)
    label_distr_backlog = ft.Text(value="Backlog (total): ", text_align=ft.TextAlign.RIGHT, size=14,
                                weight=ft.FontWeight.BOLD)
    label_distr_inventory = ft.Text(value="Inventory: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD)
    label_distr_demand = ft.Text(value="Demand: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_distr_costs = ft.Text(value="Costs (total): ", text_align=ft.TextAlign.LEFT, size=18)
    label_distr_sl = ft.Text(value="SL: ", text_align=ft.TextAlign.LEFT, size=18)
    label_distr_structure = ft.Text(value="Stock structure: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD, visible=False)
    label_distr_stock_structure = ft.Text(value="stock: ", text_align=ft.TextAlign.RIGHT, size=12, visible=False)
    label_distr_holding_rate = ft.Text(value="Holding costs rate: " + str(HOLDINGRATE), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_distr_backlog_rate = ft.Text(value="Backlog costs rate: " + str(BACKLOGRATE), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_separator = ft.Text(value=" ", text_align=ft.TextAlign.LEFT, size=0, color="#e6e6e6")
    label_distr_pass = ft.Text(value="Password:", text_align=ft.TextAlign.LEFT, size=12)
    label_distr_server = ft.Text(value="Server:", text_align=ft.TextAlign.LEFT, size=12)
    label_distr_port = ft.Text(value="Port:", text_align=ft.TextAlign.LEFT, size=12)
    label_distr_info = ft.Text(value="Info", text_align=ft.TextAlign.LEFT, size=12)
    textEditOrderDistr = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.Colors.GREY)
    textEditShipmentDistr = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.Colors.GREY)
    textEditPassDistr = ft.TextField(value="passphrase", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.Colors.GREY)
    textEditServerDistr = ft.TextField(value="localhost", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                     height=40, text_size=12, content_padding=5, border_color=ft.Colors.GREY)
    textEditPortDistr = ft.TextField(value="5556", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.Colors.GREY)
    button_distr_order = ft.ElevatedButton("Order", on_click=on_button_distr_order_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.Colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    button_distr_shipment = ft.ElevatedButton("Shipment", on_click=on_button_distr_shipment_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.Colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    #button_distr_disconnect = ft.ElevatedButton("Disconnect", on_click=on_button_distr_disconnect_pressed,
    #                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
    #                                                               side=ft.BorderSide(1, ft.Colors.GREY)),
    #                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_distr_update = ft.ElevatedButton("Update", on_click=on_button_distr_update_pressed,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                               side=ft.BorderSide(1, ft.Colors.GREY)),
                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_distr_connect = ft.ElevatedButton("Connect", on_click=on_button_distr_connect_pressed,
                                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                side=ft.BorderSide(1, ft.Colors.GREY)),
                                           bgcolor=ENABLED_COLOR, color="#ffffff")
    #page.overlay.append(button_distr_disconnect)
    page.overlay.append(button_distr_update)
    page.overlay.append(label_distr_status)

    page.add(
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_period,
                    col={"xs": 12,"md": 7},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_ordersize,
                    padding=7,
                    col={"xs": 12,"md": 2},
                ),
                ft.Container(
                    textEditOrderDistr,
                    col={"xs": 3,"md": 1.5},
                ),
                ft.Container(
                    button_distr_order,
                    col={"xs": 5,"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_distr_leadtime,
                    col={"xs": 12,"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_shipment,
                    padding=7,
                    col={"xs": 12,"md": 2},
                ),
                ft.Container(
                    textEditShipmentDistr,
                    col={"xs": 3,"md": 1.5},
                ),
                ft.Container(
                    button_distr_shipment,
                    col={"xs": 5,"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_distr_backlog,
                    col={"xs": 12,"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_costs,
                    padding=7,
                    col={"xs": 6,"md": 3.5},
                ),
                ft.Container(
                    label_distr_inventory,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_sl,
                    col={"xs": 6,"md": 3.5},
                    padding=10,
                ),
                ft.Container(
                    label_distr_demand,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_distr_holding_rate,
                    col={"xs": 6,"md": 5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_stock_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_distr_backlog_rate,
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
                    label_distr_pass,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPassDistr,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_server,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditServerDistr,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_port,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPortDistr,
                    col={"xs": 8,"md": 1},
                ),
                ft.Container(
                    button_distr_connect,
                    padding=4,
                    col={"xs": 4,"md": 2},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_distr_info,
                    padding=10,
                    col={"xs": 12,"md": 8},
                ),
            ],
        ),
    )


# ft.app(target=main)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53861)
