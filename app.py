from flask import Flask, render_template_string, request, session, redirect
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = "ramsys-maroc-2026"

def get_db():
    con = sqlite3.connect("ramsys.db")
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = get_db()
    con.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, probleme TEXT, statut TEXT, priorite TEXT, date TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, qte INTEGER, prix INTEGER)")
    con.execute("CREATE TABLE IF NOT EXISTS factures (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, service TEXT, prix INTEGER, tva INTEGER, total INTEGER, date TEXT, statut TEXT)")
    if con.execute("SELECT COUNT(*) FROM stock").fetchone()[0] == 0:
        con.executemany("INSERT INTO stock (nom,qte,prix) VALUES (?,?,?)", [("SSD 512Go Kingston",2,450),("RAM 8Go DDR4",15,280),("Toner HP 85A",1,350),("Câble RJ45 10m",28,45)])
    if con.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 0:
        con.executemany("INSERT INTO tickets (client,probleme,statut,priorite,date) VALUES (?,?,?,?,?)", [
            ("Serveur principal hors ligne - Site Casablanca","Critique","En cours","Critique","Aujourd'hui 09:32"),
            ("Imprimante service RH - Bourrage papier","En cours","En cours","Moyenne","Aujourd'hui 08:15"),
            ("Installation logiciel Sage - Département Compta","Résolu","Résolu","Faible","Hier 17:40"),
            ("Réseau Wi-Fi instable - Open Space","En cours","En cours","Moyenne","Hier 14:20"),
        ])
    con.commit(); con.close()
init_db()

USERS = {
    "admin@ramsys.ma": {"pass":"123456","role":"admin","name":"Admin","initial":"AK"},
    "tech@ramsys.ma": {"pass":"123456","role":"tech","name":"Youssef","initial":"YI"},
    "client@ramsys.ma": {"pass":"123456","role":"client","name":"Client","initial":"CL"},
}

# ===== DESIGN HAKA BHAL TASWIRA =====
BASE = """
<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box} body{margin:0;font-family:Inter,Arial;background:#0b0f1a;color:white;display:flex}
.sidebar{width:230px;background:#11141f;min-height:100vh;padding:22px 14px;position:fixed;left:0;top:0}
.logo{font-size:28px;font-weight:900} .logo span{color:#f59e0b} .logo small{display:block;font-size:11px;letter-spacing:3px;color:#38bdf8;margin-top:-2px}
.menu{margin-top:30px} .menu a{display:flex;gap:10px;padding:12px;border-radius:10px;color:#9ca3af;text-decoration:none;margin:4px 0;font-size:14px}
.menu a.active{background:#7c3f0a;color:white;font-weight:bold} .menu a:hover{background:#1f2937;color:white}
.user{position:absolute;bottom:20px;left:14px;display:flex;gap:10px;align-items:center}
.avatar{width:38px;height:38px;border-radius:50%;background:#f97316;display:flex;align-items:center;justify-content:center;font-weight:900}
.main{margin-left:230px;flex:1;padding:22px 28px}
.top{display:flex;justify-content:space-between;align-items:center}
.search{background:#1a2030;border:1px solid #2a3348;padding:10px 14px;border-radius:20px;width:340px;color:white;border:none;outline:none}
.cards{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;margin:18px 0}
.card{background:#151a27;border:1px solid #232a3d;border-radius:16px;padding:18px;text-align:center}
.card b{font-size:32px;display:block;margin-top:6px} .green{color:#22c55e;font-size:12px} .blue{color:#38bdf8;font-size:12px} .orange{color:#f59e0b;font-size:12px}
.grid{display:grid;grid-template-columns:1.6fr 1fr;gap:14px}
.box{background:#151a27;border:1px solid #232a3d;border-radius:16px;padding:18px}
table{width:100%;border-collapse:collapse} td{padding:11px 6px;border-bottom:1px solid #232a3d;font-size:13px}
.badge{padding:4px 8px;border-radius:6px;font-size:11px;font-weight:bold} .crit{background:#ef4444} .enc{background:#f97316} .res{background:#22c55e}
input,select{padding:11px;border-radius:10px;border:1px solid #2a3348;background:#0f172a;color:white;margin:5px;width:210px}
button{background:#f97316;color:white;padding:11px 18px;border:none;border-radius:10px;font-weight:bold;cursor:pointer}
.pie{width:150px;height:150px;border-radius:50%;background:conic-gradient(#22c55e 0 35%, #f97316 35% 75%, #ef4444 75% 100%);margin:auto;display:flex;align-items:center;justify-content:center}
.pie div{width:80px;height:80px;background:#151a27;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:900}
.bar{height:10px;background:#1f2937;border-radius:20px;overflow:hidden;margin:8px 0} .bar div{height:100%;background:#38bdf8}
@media(max-width:800px){.sidebar{display:none}.main{margin-left:0}.cards{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.search{width:180px}}
</style></head>
<body>
<div class="sidebar">
<div class="logo">🔧 Ramsys <small>MAROC</small></div>
<div class="menu">
<a href="/dashboard" class="{a1}">📊 Tableau de bord</a>
<a href="/dashboard" class="{a2}">🎫 Tickets</a>
<a href="/stock" class="{a3}">📦 Inventaire</a>
<a href="/factures" class="{a4}">🧾 Factures</a>
<a href="/dashboard">⚙️ Paramètres</a>
<a href="/logout">🚪 Déconnexion</a>
</div>
<div class="user"><div class="avatar">{ini}</div><div><b>{name}</b><br><small style="color:#9ca3af">admin@ramsys.ma</small></div></div>
</div>
<div class="main">{content}</div>
</body></html>
"""

def render(content, active="dashboard", name="Admin", ini="AK"):
    a1 = "active" if active=="a1" else ""
    a2 = "active" if active=="a2" else ""
    a3 = "active" if active=="a3" else ""
    a4 = "active" if active=="a4" else ""
    html = BASE.replace("{content}", content).replace("{name}", name).replace("{ini}", ini)
    html = html.replace("{a1}", a1).replace("{a2}", a2).replace("{a3}", a3).replace("{a4}", a4)
    return html
@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=USERS.get(request.form.get("email"))
        if u and u["pass"]==request.form.get("pass"):
            session["user"]=request.form.get("email"); session["role"]=u["role"]; session["name"]=u["name"]; session["ini"]=u["initial"]
            return redirect("/dashboard")
        return "Incorrect! <a href='/'>Retour</a>"
    return """<body style="background:#0b0f1a;color:white;font-family:Arial;text-align:center;padding:60px"><h1 style="font-size:42px">🔧 Ramsys <span style="color:#f59e0b">MAROC</span></h1>
    <form method="POST" style="background:#151a27;padding:30px;border-radius:16px;max-width:360px;margin:auto"><input name="email" value="admin@ramsys.ma" style="padding:12px;width:100%;margin:8px 0;border-radius:10px;border:1px solid #333;background:#0f172a;color:white"><br><input name="pass" type="password" value="123456" style="padding:12px;width:100%;margin:8px 0;border-radius:10px;border:1px solid #333;background:#0f172a;color:white"><br><button style="background:#f97316;color:white;padding:12px;width:100%;border:none;border-radius:10px;font-weight:bold">Se Connecter</button></form></body>"""

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session: return redirect("/")
    con=get_db()
    if request.method=="POST":
        con.execute("INSERT INTO tickets (client,probleme,statut,priorite,date) VALUES (?,?,?,?,?)",(request.form.get("client"),request.form.get("probleme"),"En cours",request.form.get("priorite"),"Aujourd'hui")); con.commit()
        tid=con.execute("SELECT last_insert_rowid()").fetchone()[0]; con.close()
        msg=f"Nouveau Ticket Ramsys - {request.form.get('client')} - {request.form.get('probleme')} - TKT-{tid}"
        wa=f"https://wa.me/212672041697?text={msg.replace(' ','%20')}"
        return f"<script>window.open('{wa}','_blank');window.location.href='/dashboard';</script>"
    tickets=con.execute("SELECT * FROM tickets ORDER BY id DESC LIMIT 4").fetchall()
    total=con.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    en_cours=con.execute("SELECT COUNT(*) FROM tickets WHERE statut='En cours'").fetchone()[0]
    revenu=con.execute("SELECT COALESCE(SUM(total),0) FROM factures").fetchone()[0]
    con.close()
    rows=""
    for t in tickets:
        badge="crit" if t["priorite"]=="Critique" else "enc" if t["statut"]=="En cours" else "res"
        label=t["priorite"] if t["priorite"]=="Critique" else t["statut"]
        rows+=f"<tr><td><span class='badge {badge}'>TKT-{t['id']:04d}</span></td><td>{t['client']} - {t['probleme']}</td><td><span class='badge {badge}'>{label}</span></td><td>{t['date']}</td></tr>"
    content=f"""
    <div class="top"><div><h1 style="margin:0;font-size:30px">Tableau de bord</h1><p style="color:#9ca3af;margin:4px 0">Vue générale de l'activité technique • Jeudi 03 Octobre 2024</p></div>
    <div style="display:flex;gap:10px;align-items:center"><input class="search" placeholder="Rechercher un ticket, technicien... 🔍"><span style="font-size:22px">🔔</span><span>⚙️</span><b>Admin ▾</b></div></div>

    <div class="cards">
      <div class="card" style="border-top:3px solid #f97316">🎫<br>Tickets Aujourd'hui<b>{total+20}</b><span class="green">+12% vs hier</span></div>
      <div class="card" style="border-top:3px solid #38bdf8">🛠️<br>Interventions en cours<b>{en_cours+6}</b><span class="blue">3 urgentes • 5 en cours</span></div>
      <div class="card" style="border-top:3px solid #22c55e">👥<br>Techniciens actifs<b>12</b><span class="green">9 disponibles • 3 en mission</span></div>
      <div class="card" style="border-top:3px solid #f59e0b">💰<br>Revenu du mois<b>{revenu if revenu else 42500} MAD</b><span class="orange">+8.2% vs mois dernier</span></div>
    </div>

    <div class="grid">
      <div class="box"><h3>Évolution des tickets <span style="float:right;font-size:12px;background:#232a3d;padding:4px 8px;border-radius:8px">Cette période ▾</span></h3><p style="color:#9ca3af;font-size:12px">30 derniers jours</p>
      <div style="height:110px;display:flex;align-items:flex-end;gap:18px;padding:10px 0;border-bottom:1px solid #333"><div style="flex:1;background:#38bdf8;height:35%;border-radius:8px 8px 0 0"></div><div style="flex:1;background:#38bdf8;height:55%;border-radius:8px 8px 0 0"></div><div style="flex:1;background:#38bdf8;height:45%;border-radius:8px 8px 0 0"></div><div style="flex:1;background:#38bdf8;height:70%;border-radius:8px 8px 0 0"></div><div style="flex:1;background:#38bdf8;height:60%;border-radius:8px 8px 0 0"></div><div style="flex:1;background:#38bdf8;height:85%;border-radius:8px 8px 0 0"></div></div>
      <p style="font-size:12px">Sept &nbsp;&nbsp;&nbsp; Semaine 2 &nbsp;&nbsp;&nbsp; Semaine 3 &nbsp;&nbsp;&nbsp; Semaine 4 &nbsp;&nbsp;&nbsp; Oct</p><p style="font-size:12px;color:#38bdf8">● Créés: 98 &nbsp; <span style="color:#f97316">● Résolus: 84</span></p>
      <h3 style="margin-top:22px">+ Nouveau Ticket</h3><form method="POST"><input name="client" placeholder="Client - ex: Clinique" required><input name="probleme" placeholder="Problème" required><select name="priorite"><option>Critique</option><option>Moyenne</option><option>Faible</option></select><button>Créer + WhatsApp 📱</button></form>
      </div>
      <div class="box"><h3>Répartition par priorité</h3><div class="pie"><div>128<br><small>Tickets</small></div></div><p>🟢 Faible 35% &nbsp; 🟠 Moyenne 40% &nbsp; 🔴 Critique 25%</p></div>
    </div>

    <div class="grid" style="margin-top:14px">
      <div class="box"><h3>Tickets récents <span style="float:right;color:#f97316;font-size:13px">Voir tout →</span></h3><table>{rows}</table></div>
      <div class="box"><h3>Techniciens actifs <span style="float:right;color:#38bdf8;font-size:13px">Gérer équipe →</span></h3>
      <p>🔵 <b>Lamia Benali</b> - Technicien Réseau &nbsp; <span style="color:#22c55e;float:right">● Disponible</span></p>
      <p>🟠 <b>Mehdi Tahiri</b> - Support Technique &nbsp; <span style="color:#f97316;float:right">● En intervention</span></p>
      <p>🔵 <b>Younes Idrissi</b> - Technicien IT &nbsp; <span style="color:#22c55e;float:right">● Disponible</span></p>
      <p>⚪ <b>Sara Fassi</b> - Technicien Matériel &nbsp; <span style="color:#9ca3af;float:right">● Hors ligne</span></p>
      </div>
    </div>
    """
    return render(content, "a1", session.get("name","Admin"), session.get("ini","AK"))

@app.route("/stock", methods=["GET","POST"])
def stock():
    if "user" not in session: return redirect("/")
    con=get_db()
    if request.method=="POST":
        con.execute("INSERT INTO stock (nom,qte,prix) VALUES (?,?,?)",(request.form.get("nom"),int(request.form.get("qte") or 0),int(request.form.get("prix") or 0))); con.commit()
    items=con.execute("SELECT * FROM stock ORDER BY id DESC").fetchall(); con.close()
    rows="".join([f"<tr><td>{s['nom']}</td><td>{s['qte']}</td><td>{s['prix']} MAD</td><td>{'<span class=badge crit>Stock Faible !</span>' if s['qte']<=3 else '<span class=badge res>Disponible</span>'}</td></tr>" for s in items])
    content=f"""<h1>📦 Inventaire - Stock</h1><div class="box"><form method="POST"><input name="nom" placeholder="Ex: SSD 512Go" required><input name="qte" type="number" placeholder="Quantité" required><input name="prix" type="number" placeholder="Prix MAD" required><button>Ajouter</button></form></div><div class="box" style="margin-top:14px"><table><tr><th>Article</th><th>Qté</th><th>Prix</th><th>Statut</th></tr>{rows}</table></div>"""
    return render(content,"a3",session.get("name"),session.get("ini"))

@app.route("/factures", methods=["GET","POST"])
def factures():
    if "user" not in session: return redirect("/")
    con=get_db(); last=None
    if request.method=="POST":
        prix=int(request.form.get("prix") or 0); tva=round(prix*0.2); total=prix+tva
        cur=con.execute("INSERT INTO factures (client,service,prix,tva,total,date,statut) VALUES (?,?,?,?,?,?,?)",(request.form.get("client"),request.form.get("service"),prix,tva,total,str(date.today()),"En attente")); con.commit()
        last=con.execute("SELECT * FROM factures WHERE id=?",(cur.lastrowid,)).fetchone()
    items=con.execute("SELECT * FROM factures ORDER BY id DESC").fetchall(); con.close()
    rows="".join([f"<tr><td>FAC-2026-{f['id']}</td><td>{f['client']}</td><td>{f['service']}</td><td>{f['total']} MAD</td></tr>" for f in items])
    fac=""
    if last: fac=f"""<div class="box" style="background:white;color:black"><h1 style="color:#0ea5e9">RAMSYS <span style="color:#f59e0b">MAROC</span></h1><p>Client: {last['client']} - {last['service']}<br>Total: {last['total']} MAD (TVA {last['tva']} MAD)</p><button onclick="window.print()">Imprimer / PDF</button></div>"""
    content=f"""<h1>🧾 Facturation</h1><div class="box"><form method="POST"><input name="client" placeholder="Client" required><input name="service" placeholder="Service" required><input name="prix" type="number" placeholder="Prix MAD" required><button>Générer Facture</button></form></div>{fac}<div class="box" style="margin-top:14px"><table><tr><th>N°</th><th>Client</th><th>Service</th><th>Total</th></tr>{rows}</table></div>"""
    return render(content,"a4",session.get("name"),session.get("ini"))

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__=="__main__":
    app.run(debug=True)