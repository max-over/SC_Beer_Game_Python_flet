import flet as ft

from network3 import Network
import pickle
import time
from xlwt import Workbook

DISABLED_COLOR = "#c8c8c8"
ENABLED_COLOR = "#b8b869"
LEADTIMEUP = 2
LEADTIMEDOWN = 2
HOLDINGRATE_RAW = 1
HOLDINGRATE_FINISHED = 2
BACKLOGRATE = 4
INVENTORY_RAW = 25
INVENTORY_FINISHED = 20
PRODUCTIONTIME = 2

pg = None
n = None

xtime = str(round(time.time()))
current_period = 0
current_demand = 0
leadtimeup = LEADTIMEUP
leadtimedown = LEADTIMEDOWN
inventory_raw = INVENTORY_RAW
inventory_finished = INVENTORY_FINISHED
holdingrate_raw = HOLDINGRATE_RAW
holdingrate_finished = HOLDINGRATE_FINISHED
backlograte = BACKLOGRATE
productiontime = PRODUCTIONTIME
shipment_plant_queue = []
production_plant_queue = []
prodshipmentList = []
supplier_order = 0
produced_lot = 0
sl = 1.00
costs = 0
backlog = 0
backlogtotal = 0
backlogcount = 0
backlogcosts = 0
inventorycosts = 0

wb = Workbook()
sheet_plant = wb.add_sheet("Plant")
sheet_plant.write(0, 0, "Period")
sheet_plant.write(0, 1, "Demand")
sheet_plant.write(0, 2, "Order")
sheet_plant.write(0, 3, "Shipment")
sheet_plant.write(0, 4, "Inventory_raw")
sheet_plant.write(0, 5, "Inventory_finished")
sheet_plant.write(0, 6, "Production")
sheet_plant.write(0, 7, "Total_costs")
sheet_plant.write(0, 8, "Backlog")
sheet_plant.write(0, 9, "SL")
sheet_plant.write(0, 10, "Inventory_costs")
sheet_plant.write(0, 11, "Lost_sales_costs")


class ProcessData:
    def __init__(self, data_id, data_list, data_leadtimeup):
        self.data_id = data_id
        self.data_list = data_list
        self.data_leadtimeup = data_leadtimeup


def main(page: ft.Page):
    global pg
    pg = page
    pg.title = "Plant"
    pg.bgcolor = "#e6e6e6"
    pg.window_width = 800
    pg.window_height = 600

    def on_button_plant_disconnect_pressed(e):
        n.send(pickle.dumps(ProcessData("disconnect", [0], 0)))
        button_plant_connect.disabled = False
        button_plant_disconnect.disabled = True
        button_plant_connect.update()
        button_plant_disconnect.update()
        label_plant_info.value = "Disconnected from server"
        label_plant_info.update()

    def on_button_plant_connect_pressed(e):
        global n
        password = textEditPassPlant.value
        server = textEditServerPlant.value
        port = int(textEditPortPlant.value)

        def is_valid_password(password):
            return password == "1"

        if is_valid_password(password):
            n = Network(server, port)
            run = True
            print(server)
            print(port)
            try:
                n.send(pickle.dumps(ProcessData("get_plant", [0], 0)))
                label_plant_info.value = f"Plant connected to: {server}_{port}"
                label_plant_info.visible = True
                label_plant_info.update()
            except:
                run = False
            button_plant_connect.bgcolor = DISABLED_COLOR
            button_plant_connect.update()
            button_plant_connect.disabled = True
            button_plant_connect.update()
            button_plant_disconnect.disabled = False
            button_plant_disconnect.bgcolor = ENABLED_COLOR
            button_plant_disconnect.update()
            button_plant_update.disabled = False
            button_plant_update.bgcolor = ENABLED_COLOR
            button_plant_update.update()
            textEditPassPlant.value = ""
            textEditPassPlant.update()
        else:
            pass

    def on_button_plant_produce_pressed(e):
        global inventory_raw
        global production_plant_queue
        try:
            prodlot = int(textEditProdlotPlant.value)
            prodlot = min(prodlot, int(inventory_raw) if prodlot >= 0 else 0)
            n.send(pickle.dumps(ProcessData("plant_prodlot", [0], prodlot)))
            inventory_raw -= prodlot
            label_plant_inventory_raw.value = f"Inventory raw: {inventory_raw}"
            label_plant_inventory_raw.update()
            production_plant_queue.append([prodlot, current_period + productiontime])
            button_plant_produce.bgcolor = DISABLED_COLOR
            button_plant_produce.update()
            button_plant_produce.disabled = True
            button_plant_produce.update()
        except ValueError:
            prodlot = 0
        textEditProdlotPlant.value = str(prodlot)
        button_plant_order.bgcolor = ENABLED_COLOR
        button_plant_order.update()
        button_plant_order.disabled = False
        button_plant_order.update()

    def on_button_plant_update_pressed(e):
        global current_demand
        global current_period
        global supplier_order
        global inventory_raw
        global inventory_finished
        global produced_lot
        server_period = n.send(pickle.dumps(ProcessData("upd_ret_period", [0], current_period)))
        whole_demand = n.send(pickle.dumps(ProcessData("upd_whole_plant_demand", [0], 0)))
        current_demand = whole_demand.data_leadtimeup
        label_plant_demand.value = f"Demand: {current_demand}"
        label_plant_demand.update()
        if int(server_period) == 0:
            label_plant_demand.value = "Demand: no data"
            label_plant_demand.update()
        if int(server_period) > current_period:
            button_plant_shipment.bgcolor = ENABLED_COLOR
            button_plant_shipment.update()
            button_plant_shipment.disabled = False
            button_plant_shipment.update()
            current_period = int(server_period)
            label_plant_period.value = f"Current Period: {current_period}"
            label_plant_period.update()
            sheet_plant.write(int(current_period), 0, int(current_period))
            wb.save(f"plant_stat{textEditPortPlant.value}_{xtime}.xls")

            supplier_order = next((int(row[0]) for row in shipment_plant_queue if int(row[1]) == current_period - leadtimeup), 0)
            inventory_raw += supplier_order

            if len(shipment_plant_queue) > 20:
                shipment_plant_queue.pop(0)

            produced_lot = next((int(row[0]) for row in production_plant_queue if int(row[1]) == current_period), 0)

            if len(production_plant_queue) > 20:
                production_plant_queue.pop(0)

            inventory_finished += produced_lot
            update_costs()

            sheet_plant.write(int(current_period), 10, float(inventorycosts))
            sheet_plant.write(int(current_period), 11, float(backlogcosts))
            label_plant_costs.value = f"Costs(total): {costs}"
            label_plant_costs.update()
            label_plant_inventory_finished.value = f"Inventory finished: {inventory_finished}"
            label_plant_inventory_finished.update()
            label_plant_inventory_raw.value = f"Inventory raw: {inventory_raw}"
            label_plant_inventory_raw.update()
            label_plant_backlog.value = f"Backlog(total): {backlogtotal}"
            label_plant_backlog.update()

        label_plant_status.value = n.send(pickle.dumps(ProcessData("check_status_node", [0], 0)))
        label_plant_status.update()

    def update_costs():
        global inventorycosts
        global backlogcosts
        global costs
        inventorycosts += inventory_raw * holdingrate_raw + inventory_finished * holdingrate_finished
        backlogcosts += backlogtotal * backlograte
        costs = inventorycosts + backlogcosts

    def on_button_plant_shipment_pressed(e):
        global sl
        try:
            prodshipment = int(textEditShipmentPlant.value)
            prodshipment = min(prodshipment, inventory_finished, current_demand + backlogtotal)
            prodshipment = max(prodshipment, 0) if prodshipment >= 0 else 0

            update_backlog_and_inventory_demand(prodshipment)
            sl = 1 - backlogcount / current_period
            n.send(pickle.dumps(ProcessData("plant_shipment", [0], prodshipment)))

            sheet_plant.write(int(current_period), 1, int(current_demand))
            sheet_plant.write(int(current_period), 3, prodshipment)
            sheet_plant.write(int(current_period), 4, int(inventory_raw))
            sheet_plant.write(int(current_period), 5, int(inventory_finished))
            sheet_plant.write(int(current_period), 6, int(produced_lot))
            sheet_plant.write(int(current_period), 7, int(costs))
            sheet_plant.write(int(current_period), 8, int(backlog))
            sheet_plant.write(int(current_period), 9, float(sl))
            wb.save(f"plant_stat{textEditPortPlant.value}_{xtime}.xls")
            label_plant_sl.value = f"Backlog periods: {backlogcount}"
            label_plant_sl.update()
            label_plant_inventory_finished.value = f"Inventory finished: {inventory_finished}"
            label_plant_inventory_finished.update()
            label_plant_backlog.value = f"Backlog(total): {backlogtotal}"
            label_plant_backlog.update()
            button_plant_shipment.bgcolor = DISABLED_COLOR
            button_plant_shipment.update()
            button_plant_shipment.disabled = True
            button_plant_shipment.update()
            button_plant_produce.bgcolor = ENABLED_COLOR
            button_plant_produce.update()
            button_plant_produce.disabled = False
            button_plant_produce.update()
        except ValueError:
            prodshipment = 0
        textEditShipmentPlant.value = str(prodshipment)
        textEditShipmentPlant.update()

    def update_backlog_and_inventory_demand(prodshipment):
        global backlog
        global backlogcount
        global inventory_finished
        global backlogtotal
        if int(current_demand) > int(prodshipment):
            backlog = int(current_demand) - int(prodshipment)
            backlogtotal += - (prodshipment - current_demand)
            backlogcount += 1
            inventory_finished = 0
        else:
            backlogtotal = backlogtotal - (prodshipment - current_demand)
            inventory_finished += - int(prodshipment)

    def on_button_plant_order_pressed(e):
        try:
            prod_order = int(textEditOrderPlant.value)
            if prod_order >= 0:
                n.send(pickle.dumps(ProcessData("plant_order", [0], prod_order)))
                shipment_plant_queue.append((prod_order, current_period))
                sheet_plant.write(int(current_period), 2, int(prod_order))
                wb.save(f"plant_stat{textEditPortPlant.value}_{xtime}.xls")
                button_plant_order.bgcolor = DISABLED_COLOR
                button_plant_order.update()
                button_plant_order.disabled = True
                button_plant_order.update()
            else:
                prod_order = 0
        except ValueError:
            prod_order = 0
        textEditOrderPlant.value = str(prod_order)

    label_plant_period = ft.Text(value="Current Period: 0", text_align=ft.TextAlign.LEFT, size=22,
                               weight=ft.FontWeight.BOLD)
    label_plant_status = ft.Text(value="Turn status info: ", text_align=ft.TextAlign.RIGHT, size=12, right=10, top=50)
    label_plant_ordersize = ft.Text(value="Order Size: ", text_align=ft.TextAlign.LEFT, size=18)
    label_plant_prodlot = ft.Text(value="Prod.lot: ", text_align=ft.TextAlign.LEFT, size=18)
    label_plant_shipment = ft.Text(value="Shipment: ", text_align=ft.TextAlign.LEFT, size=18)
    label_plant_leadtime = ft.Text(value="Leadtime to Supplier: " + str(LEADTIMEUP), text_align=ft.TextAlign.RIGHT,
                                 size=14,
                                 weight=ft.FontWeight.BOLD)
    label_plant_backlog = ft.Text(value="Backlog (total): ", text_align=ft.TextAlign.RIGHT, size=14,
                                weight=ft.FontWeight.BOLD)
    label_plant_inventory_raw = ft.Text(value="Inventory raw: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD)
    label_plant_inventory_finished = ft.Text(value="Inventory finished: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD)
    label_plant_demand = ft.Text(value="Demand: ", text_align=ft.TextAlign.RIGHT, size=14, weight=ft.FontWeight.BOLD)
    label_plant_costs = ft.Text(value="Costs (total): ", text_align=ft.TextAlign.LEFT, size=18)
    label_plant_sl = ft.Text(value="SL: ", text_align=ft.TextAlign.LEFT, size=18)
    label_plant_structure = ft.Text(value="Stock structure: ", text_align=ft.TextAlign.RIGHT, size=14,
                                  weight=ft.FontWeight.BOLD, visible=False)
    # label_plant_stock_structure = ft.Text(value="stock: ", text_align=ft.TextAlign.RIGHT, size=12, visible=False)
    label_plant_holding_rate_raw = ft.Text(value="Holding raw costs rate: " + str(HOLDINGRATE_RAW), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_plant_holding_rate_finished = ft.Text(value="Holding FG costs rate: " + str(HOLDINGRATE_FINISHED), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_plant_backlog_rate = ft.Text(value="Backlog costs rate: " + str(BACKLOGRATE), text_align=ft.TextAlign.RIGHT,
                                     size=12)
    label_separator = ft.Text(value=" ", text_align=ft.TextAlign.LEFT, size=0, color="#e6e6e6")
    label_plant_pass = ft.Text(value="Password:", text_align=ft.TextAlign.LEFT, size=12)
    label_plant_server = ft.Text(value="Server:", text_align=ft.TextAlign.LEFT, size=12)
    label_plant_port = ft.Text(value="Port:", text_align=ft.TextAlign.LEFT, size=12)
    label_plant_info = ft.Text(value="Info", text_align=ft.TextAlign.LEFT, size=12)
    textEditOrderPlant = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditProdlotPlant = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                      height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditShipmentPlant = ft.TextField(value="5", bgcolor="#ffffff", text_align=ft.TextAlign.RIGHT, width=75,
                                         height=40, text_size=20, content_padding=5, border_color=ft.colors.GREY)
    textEditPassPlant = ft.TextField(value="passphrase", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditServerPlant = ft.TextField(value="localhost", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                     height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    textEditPortPlant = ft.TextField(value="5556", bgcolor="#ffffff", text_align=ft.TextAlign.CENTER, width=75,
                                   height=40, text_size=12, content_padding=5, border_color=ft.colors.GREY)
    button_plant_order = ft.ElevatedButton("Order", on_click=on_button_plant_order_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    button_plant_produce = ft.ElevatedButton("Produce", on_click=on_button_plant_produce_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)
    button_plant_shipment = ft.ElevatedButton("Shipment", on_click=on_button_plant_shipment_pressed,
                                         style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                              side=ft.BorderSide(1, ft.colors.GREY)),
                                         bgcolor=DISABLED_COLOR, color="#ffffff", disabled=True)

    button_plant_disconnect = ft.ElevatedButton("Disconnect", on_click=on_button_plant_disconnect_pressed,
                                              style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                   side=ft.BorderSide(1, ft.colors.GREY)),
                                              bgcolor=DISABLED_COLOR, color="#ffffff", right=10, top=10, disabled=True)
    button_plant_update = ft.ElevatedButton("Update", on_click=on_button_plant_update_pressed,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                               side=ft.BorderSide(1, ft.colors.GREY)),
                                          bgcolor=DISABLED_COLOR, color="#ffffff", right=10, bottom=10, disabled=True)
    button_plant_connect = ft.ElevatedButton("Connect", on_click=on_button_plant_connect_pressed,
                                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5),
                                                                side=ft.BorderSide(1, ft.colors.GREY)),
                                           bgcolor=ENABLED_COLOR, color="#ffffff")
    page.overlay.append(button_plant_disconnect)
    page.overlay.append(button_plant_update)
    page.overlay.append(label_plant_status)

    page.add(
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_period,
                    col={"md": 7},
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_ordersize,
                    padding=7,
                    col={"md": 2},
                ),
                ft.Container(
                    textEditOrderPlant,
                    col={"md": 1.5},
                ),
                ft.Container(
                    button_plant_order,
                    col={"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_plant_leadtime,
                    col={"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_prodlot,
                    padding=7,
                    col={"md": 2},
                ),
                ft.Container(
                    textEditProdlotPlant,
                    col={"md": 1.5},
                ),
                ft.Container(
                    button_plant_produce,
                    col={"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_plant_backlog,
                    col={"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_shipment,
                    padding=7,
                    col={"md": 2},
                ),
                ft.Container(
                    textEditShipmentPlant,
                    col={"md": 1.5},
                ),
                ft.Container(
                    button_plant_shipment,
                    col={"md": 2.25},
                    padding=5,
                ),
                ft.Container(
                    label_plant_inventory_raw,
                    col={"md": 3.25},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_costs,
                    padding=7,
                    col={"md": 3.5},
                ),
                ft.Container(
                    label_plant_inventory_finished,
                    col={"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_sl,
                    col={"md": 3.5},
                    padding=10,
                ),
                ft.Container(
                    label_plant_demand,
                    col={"md": 5.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_structure,
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
                    label_plant_pass,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditPassPlant,
                    col={"md": 3},
                ),
                ft.Container(
                    label_plant_holding_rate_raw,
                    col={"md": 7.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_server,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditServerPlant,
                    col={"md": 3},
                ),
                ft.Container(
                    label_plant_holding_rate_finished,
                    col={"md": 7.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_port,
                    padding=10,
                    col={"md": 1.5},
                ),
                ft.Container(
                    textEditPortPlant,
                    col={"md": 1},
                ),
                ft.Container(
                    button_plant_connect,
                    padding=4,
                    col={"md": 2},
                ),
                ft.Container(
                    label_plant_backlog_rate,
                    col={"md": 7.5},
                    padding=10,
                ),
            ],
        ),
        ft.ResponsiveRow(
            [
                ft.Container(
                    label_plant_info,
                    padding=10,
                    col={"md": 8},
                ),
            ],
        ),
    )


# ft.app(target=main)
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53863)
