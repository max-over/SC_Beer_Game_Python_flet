# SC_Beer_Game_Python_flet

Updated [SC_Beer_Game_Python](https://github.com/max-over/SC_Beer_Game_Python) package. Deployment sequence is the same. Runs with [Flet](https://flet.dev/) instead of [Remi](https://github.com/rawpython/remi). Still testing.

Requirements:
```
flet==0.9.0
xlwt==1.3.0
```

Passphrase for connection is set to "1". Default port for a server is "5556". Game statistics is written in Excel files

Ports (last line in py source files):

```
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=53859)
```

Ports: Administrator: 53859  
Retailer: 53860  
Distributor: 53861  
Wholesaler: 53862  
Plant: 53863  
