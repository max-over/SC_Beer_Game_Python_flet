import flet as ft

from network3 import Network
import pickle
import time
from xlwt import Workbook

DISABLED_COLOR = "#c8c8c8"
ENABLED_COLOR = "#00c8c8"
HOLDINGRATE = 4
BACKLOGRATE = 10
LEADTIMEUP = 2
INVENTORY = 20

pg = None
n = None
xtime = str(round(time.time()))
current_period = 0
current_demand = 0
inventory = INVENTORY
leadtimeup = LEADTIMEUP
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
sheet_ret = wb.add_sheet("Retailer")
sheet_ret.write(0, 0, "Period")
sheet_ret.write(0, 1, "Demand")
sheet_ret.write(0, 2, "Order")
sheet_ret.write(0, 3, "Shipment")
sheet_ret.write(0, 4, "Inventory")
sheet_ret.write(0, 5, "Total_Costs")
sheet_ret.write(0, 6, "Lost sales")
sheet_ret.write(0, 7, "SL")
sheet_ret.write(0, 8, "Inventory_Costs")
sheet_ret.write(0, 9, "Lost_sales_Costs")


class ProcessData:
    def __init__(self, data_id, data_list, data_leadtimeup):
        self.data_id = data_id
        self.data_list = data_list
        self.data_leadtimeup = data_leadtimeup


def main(page: ft.Page):
    global pg
    pg = page
    pg.title = "Retailer"
    pg.bgcolor = "#e6e6e6"
    pg.window_width = 800
    pg.window_height = 600
    pg.expand = True
    pg.scroll = "ALWAYS"

    def on_button_ret_disconnect_pressed(e):
        n.send(pickle.dumps(ProcessData("disconnect", [0], 0)))
        button_ret_connect.disabled = False
        button_ret_disconnect.disabled = True
        button_ret_connect.update()
        button_ret_disconnect.update()
        label_ret_info.value = "Disconnected from server"
        label_ret_info.update()

    def on_button_ret_connect_pressed(e):
        global n
        password = textEditPassRet.value
        server = textEditServerRet.value
        port = int(textEditPortRet.value)

        def is_valid_password(password):
            return password == "1"

        if is_valid_password(password):
            n = Network(server, port)
            run = True
            print(server)
            print(port)
            try:
                n.send(pickle.dumps(ProcessData("get_ret", [0], 0)))
                label_ret_info.value = f"Retailer connected to: {server}_{port}"
                label_ret_info.visible = True
                label_ret_info.update()
            except:
                run = False
            button_ret_connect.bgcolor = DISABLED_COLOR
            button_ret_connect.update()
            button_ret_connect.disabled = True
            button_ret_connect.update()
            button_ret_disconnect.disabled = False
            button_ret_disconnect.bgcolor = ENABLED_COLOR
            button_ret_disconnect.update()
            button_ret_update.disabled = False
            button_ret_update.bgcolor = ENABLED_COLOR
            button_ret_update.update()
            textEditPassRet.value = ""
            textEditPassRet.update()
        else:
            pass

    def on_button_ret_update_pressed(e):
        global current_period
        global current_demand
        global sl
        server_period = n.send(pickle.dumps(ProcessData("upd_ret_period", [0], current_period)))

        if int(server_period) > current_period:
            button_ret_order.disabled = False
            button_ret_order.bgcolor = ENABLED_COLOR
            button_ret_order.update()
            current_period = int(server_period)
            label_ret_period.value = f"Current Period: {server_period}"
            label_ret_period.update()
            sheet_ret.write(int(current_period), 0, int(current_period))
            wb.save(f'ret_stat{textEditPortRet.value}_{xtime}.xls')

            if current_period > 1:
                shipment = n.send(pickle.dumps(ProcessData("upd_ret_distr_shipment", [current_period], leadtimeup)))
                update_backlog_and_inventory_shipment(shipment)

            demand = n.send(pickle.dumps(ProcessData("upd_ret_cust_demand", [0], 0)))
            current_demand = demand.data_leadtimeup
            print(current_demand)

            update_costs()
            update_backlog_and_inventory_demand()
            sl = 1 - backlogcount / current_period
            label_ret_costs.value = f"Costs(total): {costs}"
            label_ret_costs.update()
            label_ret_demand.value = f"Demand: {current_demand}"
            label_ret_demand.update()
            label_ret_sl.value = f"Lost sales periods: {backlogcount}"
            label_ret_sl.update()
            label_ret_inventory.value = f"Inventory: {inventory}"
            label_ret_inventory.update()
            label_ret_backlog.value = f"Lost sales(total): {backlogtotal}"
            label_ret_backlog.update()

            sheet_ret.write(int(current_period), 1, int(current_demand))
            sheet_ret.write(int(current_period), 4, int(inventory))
            sheet_ret.write(int(current_period), 5, int(costs))
            sheet_ret.write(int(current_period), 6, int(backlogtotal))
            sheet_ret.write(int(current_period), 7, float(sl))
            sheet_ret.write(int(current_period), 8, float(inventorycosts))
            sheet_ret.write(int(current_period), 9, float(backlogcosts))
            wb.save(f'ret_stat{textEditPortRet.value}_{xtime}.xls')

        label_ret_status.value = n.send(pickle.dumps(ProcessData("check_status_node", [0], 0)))
        label_ret_status.update()

    def update_backlog_and_inventory_shipment(shipment):
        global inventory
        global backlog
        if shipment.data_list != "":
            if backlog > int(shipment.data_list):
                backlog -= int(shipment.data_list)
                inventory = 0
            else:
                inv_remaining = int(shipment.data_list) - backlog
                backlog = 0
                inventory += inv_remaining

    def update_costs():
        global inventorycosts
        global backlogcosts
        global costs
        inventorycosts += inventory * holdingrate
        backlogcosts = backlogtotal * backlograte
        costs = inventorycosts + backlogcosts

    def update_backlog_and_inventory_demand():
        global inventory
        global backlog
        global backlogtotal
        global backlogcount

        if int(current_demand) > int(inventory):
            backlog = int(current_demand) - int(inventory)
            backlogtotal += backlog
            inventory = 0
        else:
            inventory -= int(current_demand)
            backlog = 0
        if backlog > 0:
            backlogcount += 1

    def on_button_ret_place_order_pressed(e):
        try:
            ret_order = int(textEditOrderRetailer.value)
            if ret_order >= 0:
                n.send(pickle.dumps(ProcessData("ret_order", [0], ret_order)))
                sheet_ret.write(int(current_period), 2, int(ret_order))
                wb.save(f'ret_stat{textEditPortRet.value}_{xtime}.xls')
                button_ret_order.bgcolor = DISABLED_COLOR
                button_ret_order.update()
                button_ret_order.disabled = True
                button_ret_order.update()
            else:
                ret_order = 0
        except ValueError:
            ret_order = 0

        textEditOrderRetailer.value = str(ret_order)

    label_ret_period = ft.Text(value="Current Period: 0", text_align=ft.TextAlign.LEFT, size=22,
                               weight=ft.FontWeight.BOLD)
    label_ret_status = ft.Text(value="Turn status info: ", text_align=ft.TextAlign.RIGHT, size=12, right=10, top=50)
    label_ret_ordersize = ft.Text(value="Order Size: ", text_align=ft.TextAlign.LEFT, size=18)
    label_ret_leadtime = ft.Text(value="Leadtime to Distributor: " + str(LEADTIMEUP), text_align=ft.TextAlign.RIGHT, size=14,
                                 weight=ft.FontWeight.BOLD)
    label_ret_backlog = ft.Text(value="Lost sales (total): ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_ret_inventory = ft.Text(value="Inventory: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD)
    label_ret_demand = ft.Text(value="Demand: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_ret_costs = ft.Text(value="Costs (total): ", text_align=ft.TextAlign.LEFT, size=18)
    label_ret_sl = ft.Text(value="SL: ", text_align=ft.TextAlign.LEFT, size=18)
    label_ret_structure = ft.Text(value="Stock structure: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD, visible=False)
    label_ret_stock_structure = ft.Text(value="stock: ", text_align=ft.TextAlign.RIGHT, size=12, visible=False)
    label_ret_holding_rate = ft.Text(value="Holding costs rate: " + str(HOLDINGRATE), text_align=ft.TextAlign.RIGHT, size=12)
    label_ret_backlog_rate = ft.Text(value="Lost sales costs rate: " + str(BACKLOGRATE), text_align=ft.TextAlign.RIGHT, size=12)
    label_separator = ft.Text(value=" ", text_align=ft.TextAlign.LEFT, size=0, color="#e6e6e6")
    label_ret_pass = ft.Text(value="Password:", text_align=ft.TextAlign.LEFT, size=12)
    label_ret_server = ft.Text(value="Server:", text_align=ft.TextAlign.LEFT, size=12)
    label_ret_port = ft.Text(value="Port:", text_align=ft.TextAlign.LEFT, size=12)
    label_ret_info = ft.Text(value="Info", text_align=ft.TextAlign.LEFT, size=12)
    textEditOrderRetailer = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditPassRet = ft.TextField(value="passphrase", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditServerRet = ft.TextField(value="localhost", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                     height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditPortRet = ft.TextField(value="5556", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    button_ret_order = ft.ElevatedButton("Order", on_click=on_button_ret_place_order_pressed,
                                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                  side=ft.BorderSide(1, ft.colors.GREY)),
                                             bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    #button_ret_disconnect = ft.ElevatedButton("Disconnect", on_click=on_button_ret_disconnect_pressed,
    #                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
    #                                                               side=ft.BorderSide(1, ft.colors.GREY)),
    #                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_ret_update = ft.ElevatedButton("Update", on_click=on_button_ret_update_pressed,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                               side=ft.BorderSide(1, ft.colors.GREY)),
                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_ret_connect = ft.ElevatedButton("Connect", on_click=on_button_ret_connect_pressed,
                                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                side=ft.BorderSide(1, ft.colors.GREY)),
                                           bgcolor=ENABLED_COLOR, color="#ffffff")
    #page.overlay.append(button_ret_disconnect)
    page.overlay.append(button_ret_update)
    page.overlay.append(label_ret_status)

    page.add(
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_period,
                    col={"xs": 12,"md": 7},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_ordersize,
                    padding=7,
                    col={"xs": 12,"md": 2},
                ),
                ft.Container(
                    textEditOrderRetailer,
                    col={"xs": 3,"md": 1.5},
                ),
                ft.Container(
                    button_ret_order,
                    col={"xs": 4,"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_ret_leadtime,
                    col={"xs": 12,"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [

                ft.Container(
                    label_ret_backlog,
                    col={"xs": 12,"md": 9},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_costs,
                    padding=7,
                    col={"xs": 6,"md": 3.5},
                ),
                ft.Container(
                    label_ret_inventory,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_sl,
                    col={"xs": 6,"md": 3.5},
                    padding=10,
                ),
                ft.Container(
                    label_ret_demand,
                    col={"xs": 6,"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_ret_holding_rate,
                    col={"xs": 6,"md": 5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_stock_structure,
                    col={"xs": 6,"md": 7},
                    padding=10,
                ),
                ft.Container(
                    label_ret_backlog_rate,
                    col={"xs": 6,"md": 5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_separator,
                    col={"xs": 12,"md": 12},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_pass,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPassRet,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_server,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditServerRet,
                    col={"xs": 8,"md": 3},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_port,
                    padding=10,
                    col={"xs": 4,"md": 1.5},
                ),
                ft.Container(
                    textEditPortRet,
                    col={"xs": 8,"md": 1},
                ),
                ft.Container(
                    button_ret_connect,
                    padding=4,
                    col={"xs": 4,"md": 2},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_ret_info,
                    padding=10,
                    col={"xs": 12,"md": 8},
                ),
            ],
        ),
    )


# ft.app(target=main)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53860)
