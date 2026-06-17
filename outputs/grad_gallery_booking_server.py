import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("GRAD_GALLERY_DATA_DIR", str(BASE_DIR)))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "grad-gallery-bookings.sqlite"
ADMIN_PASSWORD = os.environ.get("GRAD_GALLERY_ADMIN_PASSWORD", "").strip()

BOOKING_STATUSES = ["New inquiry", "Needs follow-up", "Photographer pending", "Awaiting payment", "Confirmed", "Session completed", "Gallery delivered", "Photographer paid", "Canceled"]
PAYMENT_STATUSES = ["Not paid", "Deposit paid", "Paid in full", "Refunded"]
DELIVERY_STATUSES = ["Not started", "Editing", "Gallery delivered", "Revision needed", "Complete"]
PACKAGES = [
    {"name": "Budget", "label": "Budget - $150", "price": 150, "time": "30 minutes", "locations": "1 location", "images": "5 edited images", "best_for": "Students who need a few clean cap and gown photos."},
    {"name": "Standard", "label": "Standard - $250", "price": 250, "time": "1 hour", "locations": "1-2 locations", "images": "10 edited images", "best_for": "Students who want the best balance of price, time, and variety."},
    {"name": "Premium", "label": "Premium - $400", "price": 400, "time": "1.5 hours", "locations": "2-3 locations", "images": "18 edited images", "best_for": "Students who want the strongest experience and premium photographer options."},
]
PHOTOGRAPHERS = [
    {"name": "artwithinfocus", "instagram": "@artwithinfocus", "level": "Beginner-Level", "packages": "Budget"},
    {"name": "Mahmoud", "instagram": "", "level": "Beginner-Level", "packages": "Budget"},
    {"name": "shotsfromsea", "instagram": "@shotsfromsea", "level": "Beginner-Level", "packages": "Budget"},
    {"name": "shotbydavi", "instagram": "@shotbydavi", "level": "Mid-Level", "packages": "Standard"},
    {"name": "pheonlens", "instagram": "@pheonlens", "level": "Mid-Level", "packages": "Standard"},
    {"name": "shellshphoto", "instagram": "@shellshphoto", "level": "Heavy Hitter", "packages": "Premium"},
    {"name": "jayhutch", "instagram": "@jayhutch", "level": "Heavy Hitter", "packages": "Premium"},
]

STYLE = """
:root{--ink:#121826;--muted:#5b6675;--line:#d7dfe9;--blue:#1f3a5f;--green:#2f5d50;--gold:#7a5a18}*{box-sizing:border-box}body{margin:0;background:#edf1f5;color:var(--ink);font-family:Arial,Helvetica,sans-serif;line-height:1.48}.topbar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;gap:18px;align-items:center;padding:14px 28px;background:#fff;border-bottom:1px solid var(--line)}.brand{font-weight:800;font-size:20px;text-decoration:none}.nav{display:flex;gap:8px;flex-wrap:wrap}.nav a,.button{border-radius:6px;padding:9px 12px;text-decoration:none;font-weight:700}.nav a{color:#273244}.button,button{display:inline-flex;align-items:center;justify-content:center;border:0;background:var(--blue);color:#fff;cursor:pointer;font:inherit;font-weight:700}.button.secondary,button.secondary{background:#e6ecf3;color:var(--ink)}.shell{width:min(1160px,calc(100% - 28px));margin:0 auto}.hero{min-height:520px;display:grid;grid-template-columns:1.1fr .9fr;gap:34px;align-items:center;padding:54px 0 42px}.hero h1{margin:0;font-size:clamp(42px,6vw,74px);line-height:.98}.hero p,.muted{color:var(--muted)}.hero-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}.preview,.card,.panel,.kpi{background:#fff;border:1px solid var(--line);border-radius:8px;overflow:hidden}.preview-art{min-height:260px;background:linear-gradient(135deg,#dbe5ef,#f7f9fb 55%,#c8d4df)}.preview-list{padding:18px;display:grid;gap:12px}.row{display:grid;grid-template-columns:1fr auto;gap:12px;border:1px solid var(--line);border-radius:6px;padding:12px;background:#fbfcfe}.section{padding:34px 0}.section-head{display:flex;justify-content:space-between;gap:18px;align-items:end;margin-bottom:16px}.section h2{margin:0;font-size:30px}.grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.band{padding:12px 16px;color:#fff;font-weight:800;font-size:20px}.Budget{background:var(--blue)}.Standard{background:var(--green)}.Premium{background:var(--gold)}.card-pad{padding:16px}.price{font-size:34px;font-weight:800;margin:8px 0}.tag{display:inline-block;border-radius:999px;background:#eef4fa;color:#1f3a5f;padding:4px 8px;font-size:12px;font-weight:700;margin:3px}.flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.flow-step{background:#fff;border:1px solid var(--line);border-radius:8px;padding:15px}.notice{border:1px solid #cbd5e1;border-radius:8px;background:#eef4fa;padding:14px;color:var(--muted)}input,select,textarea{width:100%;border:1px solid #c7d0dc;border-radius:6px;padding:11px 12px;font:inherit;background:#fff;color:var(--ink)}textarea{min-height:95px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.field{display:flex;flex-direction:column;gap:7px}.full{grid-column:1/-1}fieldset{border:1px solid #c7d0dc;border-radius:6px;background:#fbfcfe;padding:14px}.options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px 14px}.option{display:flex;gap:8px;font-weight:400}.option input{width:auto}.actions{display:flex;gap:12px;flex-wrap:wrap;padding-top:20px}.table-wrap{overflow:auto;max-height:68vh}table{width:100%;border-collapse:collapse;font-size:14px}th,td{border-bottom:1px solid var(--line);padding:10px;text-align:left;vertical-align:top}th{background:var(--blue);color:#fff}.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:16px}.kpi{padding:15px}.kpi strong{font-size:28px}.login-panel{display:none;margin-bottom:16px;padding:14px;background:#fff8e8;border:1px solid #ead49a;border-radius:8px}@media(max-width:900px){.hero,.grid-3,.flow,.form-grid,.options,.kpis{grid-template-columns:1fr}.section-head,.topbar{align-items:flex-start;flex-direction:column}}
"""

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, client_name TEXT, email TEXT, phone TEXT, package TEXT, preferred_date TEXT, backup_date TEXT, payment_readiness TEXT, assigned_photographer TEXT, booking_status TEXT NOT NULL DEFAULT 'New inquiry', payment_status TEXT NOT NULL DEFAULT 'Not paid', delivery_status TEXT NOT NULL DEFAULT 'Not started', form_json TEXT NOT NULL)""")

def page(title, body):
    return f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title><style>{STYLE}</style></head><body><nav class='topbar'><a class='brand' href='/'>Grad Gallery</a><div class='nav'><a href='/packages'>Packages</a><a href='/photographers'>Photographers</a><a href='/book'>Book</a><a href='/admin'>Admin</a></div></nav>{body}</body></html>"

def home_page():
    cards = package_cards()
    body = f"<main class='shell'><section class='hero'><div><h1>Grad photos made simple.</h1><p>Choose a package, browse trusted photographers, and request your graduation session without chasing random DMs.</p><div class='hero-actions'><a class='button' href='/book'>Start booking</a><a class='button secondary' href='/photographers'>Browse photographers</a></div></div><div class='preview'><div class='preview-art'></div><div class='preview-list'><div class='row'><strong>Standard Session</strong><span class='tag'>$250</span></div><div class='row'><strong>Choose Photographer</strong><span class='tag'>Roster</span></div><div class='row'><strong>Status Tracking</strong><span class='tag'>Admin</span></div></div></div></section><section class='section'><div class='section-head'><div><h2>Packages</h2><p class='muted'>Simple tiers for different budgets and expectations.</p></div><a class='button secondary' href='/packages'>Compare all</a></div><div class='grid-3'>{cards}</div></section><section class='section'><div class='flow'><div class='flow-step'><strong>1. Pick</strong><br>Choose your package and preferred style.</div><div class='flow-step'><strong>2. Match</strong><br>Choose a photographer or ask for recommendations.</div><div class='flow-step'><strong>3. Confirm</strong><br>Grad Gallery confirms availability and payment steps.</div><div class='flow-step'><strong>4. Track</strong><br>The booking moves through the dashboard.</div></div></section><section class='section'><div class='notice'>Independent service. Not affiliated with Old Dominion University.</div></section></main>"
    return page("Grad Gallery", body)

def package_cards():
    html = []
    for p in PACKAGES:
        html.append(f"<article class='card'><div class='band {p['name']}'>{p['name']}</div><div class='card-pad'><div class='price'>${p['price']}</div><p>{p['best_for']}</p><p>{p['time']}<br>{p['locations']}<br>{p['images']}</p><a class='button' href='/book?package={p['label'].replace(' ', '%20').replace('$','%24')}'>Book {p['name']}</a></div></article>")
    return "".join(html)

def packages_page():
    return page("Packages", f"<main class='shell'><section class='section'><div class='section-head'><div><h2>Choose your package</h2><p class='muted'>Budget gets students in. Standard is the main value. Premium gives the strongest experience.</p></div><a class='button' href='/book'>Start booking</a></div><div class='grid-3'>{package_cards()}</div></section></main>")

def photographers_page():
    cards = []
    for ph in PHOTOGRAPHERS:
        cards.append(f"<article class='card'><div class='preview-art'></div><div class='card-pad'><h3>{ph['name']}</h3><p>{ph['instagram'] or 'Instagram pending'}</p><span class='tag'>{ph['level']}</span><span class='tag'>{ph['packages']}</span><div class='hero-actions'><a class='button secondary' href='/book?photographer={ph['name']}'>Choose photographer</a></div></div></article>")
    return page("Photographers", f"<main class='shell'><section class='section'><div class='section-head'><div><h2>Browse photographers</h2><p class='muted'>Students can choose a photographer or ask Grad Gallery for a recommendation.</p></div><a class='button' href='/book'>Request a session</a></div><div class='grid-3'>{''.join(cards)}</div></section></main>")

def booking_form(query):
    package = parse_qs(query).get('package', [''])[0]
    photographer = parse_qs(query).get('photographer', [''])[0]
    checked = lambda label: 'checked' if package == label else ''
    body = f"""<main class='shell'><section class='section'><h2>Book a Grad Gallery session</h2><p class='muted'>Submit your request and Grad Gallery will confirm availability.</p><form id='bookingForm'><div class='form-grid'><div class='field'><label>Full name *</label><input name='Full name' required></div><div class='field'><label>Email *</label><input name='Email address' type='email' required></div><div class='field'><label>Phone *</label><input name='Phone number' required></div><div class='field'><label>Instagram</label><input name='Instagram handle'></div><div class='field'><label>Graduation semester</label><input name='Expected graduation semester' placeholder='Spring 2027'></div><div class='field'><label>Preferred photographer</label><input name='Preferred photographer' value='{photographer}'></div><fieldset class='full'><legend>Package *</legend><label class='option'><input type='radio' name='Package' value='Budget - $150' {checked('Budget - $150')} required> Budget - $150</label><label class='option'><input type='radio' name='Package' value='Standard - $250' {checked('Standard - $250')}> Standard - $250</label><label class='option'><input type='radio' name='Package' value='Premium - $400' {checked('Premium - $400')}> Premium - $400</label></fieldset><div class='field'><label>Preferred date</label><input name='Preferred session date' type='date'></div><div class='field'><label>Backup date</label><input name='Backup session date' type='date'></div><fieldset class='full'><legend>Preferred locations</legend><div class='options'><label class='option'><input type='checkbox' name='Preferred locations' value='ODU campus'> ODU campus</label><label class='option'><input type='checkbox' name='Preferred locations' value='Fountain area'> Fountain area</label><label class='option'><input type='checkbox' name='Preferred locations' value='Webb Center area'> Webb Center</label><label class='option'><input type='checkbox' name='Preferred locations' value='Lion statue'> Lion statue</label></div></fieldset><fieldset class='full'><legend>Add-ons</legend><div class='options'><label class='option'><input type='checkbox' name='Add-ons' value='Extra edited photos'> Extra edited photos</label><label class='option'><input type='checkbox' name='Add-ons' value='Rush delivery'> Rush delivery</label><label class='option'><input type='checkbox' name='Add-ons' value='Prints'> Prints</label><label class='option'><input type='checkbox' name='Add-ons' value='Extra locations'> Extra locations</label></div></fieldset><div class='field'><label>Payment readiness</label><select name='Payment readiness'><option></option><option>Yes</option><option>Not yet</option><option>I have questions first</option></select></div><div class='field full'><label>Questions or notes</label><textarea name='Questions or notes'></textarea></div><fieldset class='full'><legend>Agreement</legend><label class='option'><input type='checkbox' required> I understand my booking is not confirmed until payment or deposit is received.</label><label class='option'><input type='checkbox' required> I understand Grad Gallery is independent and not affiliated with Old Dominion University.</label></fieldset></div><div id='notice' class='notice'>Ready to submit.</div><div class='actions'><button type='submit'>Submit Booking Request</button><button type='reset' class='secondary'>Clear Form</button></div></form></section></main><script>document.getElementById('bookingForm').addEventListener('submit',async e=>{{e.preventDefault();const data={{}};for(const [k,v] of new FormData(e.target).entries()){{(data[k]??=[]).push(v)}};const r=await fetch('/api/bookings',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(data)}});const j=await r.json();document.getElementById('notice').textContent=j.ok?'Saved. Booking ID: GG-'+String(j.booking_id).padStart(3,'0'):'Submission failed';if(j.ok)e.target.reset();}})</script>"""
    return page("Book Grad Gallery", body)

def admin_page():
    return page("Admin", """<main class='shell'><section class='section'><h2>Admin Dashboard</h2><div id='login' class='login-panel'><strong>Admin password required</strong><div class='actions'><input id='pw' type='password' placeholder='Admin password'><button onclick='savePw()'>Unlock</button></div></div><div class='kpis'><div class='kpi'><span>Total inquiries</span><strong id='total'>0</strong></div><div class='kpi'><span>Awaiting payment</span><strong id='pay'>0</strong></div><div class='kpi'><span>Confirmed</span><strong id='conf'>0</strong></div><div class='kpi'><span>Gallery delivered</span><strong id='del'>0</strong></div></div><div class='actions'><button onclick='load()'>Refresh</button><button onclick='exportCsv()'>Export CSV</button></div><div class='panel table-wrap'><table><thead><tr><th>ID</th><th>Client</th><th>Package</th><th>Dates</th><th>Status</th><th>Assigned Photographer</th></tr></thead><tbody id='rows'></tbody></table></div></section></main><script>let statuses=[],payments=[],deliveries=[];function headers(){const p=localStorage.getItem('ggAdmin')||'';return p?{'X-Admin-Password':p}:{}}function savePw(){localStorage.setItem('ggAdmin',document.getElementById('pw').value);load()}function opts(list,val){return list.map(x=>`<option ${x==val?'selected':''}>${x}</option>`).join('')}async function patch(id,field,value){await fetch('/api/bookings/'+id,{method:'PATCH',headers:{'Content-Type':'application/json',...headers()},body:JSON.stringify({[field]:value})});load()}async function load(){const c=await(await fetch('/api/config')).json();statuses=c.booking_statuses;payments=c.payment_statuses;deliveries=c.delivery_statuses;document.getElementById('login').style.display=c.admin_password_required?'block':'none';const r=await fetch('/api/bookings',{headers:headers()});if(r.status==401){document.getElementById('rows').innerHTML='';return}const j=await r.json();const b=j.bookings||[];document.getElementById('total').textContent=b.length;document.getElementById('pay').textContent=b.filter(x=>x.booking_status=='Awaiting payment').length;document.getElementById('conf').textContent=b.filter(x=>x.booking_status=='Confirmed').length;document.getElementById('del').textContent=b.filter(x=>x.booking_status=='Gallery delivered').length;document.getElementById('rows').innerHTML=b.map(x=>`<tr><td>GG-${String(x.id).padStart(3,'0')}</td><td><b>${x.client_name||''}</b><br>${x.email||''}<br>${x.phone||''}</td><td>${x.package||''}</td><td>${x.preferred_date||''}<br>${x.backup_date||''}</td><td><select onchange="patch(${x.id},'booking_status',this.value)">${opts(statuses,x.booking_status)}</select><select onchange="patch(${x.id},'payment_status',this.value)">${opts(payments,x.payment_status)}</select><select onchange="patch(${x.id},'delivery_status',this.value)">${opts(deliveries,x.delivery_status)}</select></td><td><input value='${x.assigned_photographer||''}' onblur="patch(${x.id},'assigned_photographer',this.value)"></td></tr>`).join('')}async function exportCsv(){const r=await fetch('/api/bookings.csv',{headers:headers()});const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='grad-gallery-bookings.csv';a.click();URL.revokeObjectURL(url)}load()</script>""")

def normalize(payload):
    return {k: ', '.join(v) if isinstance(v, list) else str(v) for k, v in payload.items()}

def save_booking(payload):
    n = normalize(payload)
    created_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    with connect() as con:
        cur = con.execute("INSERT INTO bookings (created_at, client_name, email, phone, package, preferred_date, backup_date, payment_readiness, form_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (created_at, n.get('Full name',''), n.get('Email address',''), n.get('Phone number',''), n.get('Package',''), n.get('Preferred session date',''), n.get('Backup session date',''), n.get('Payment readiness',''), json.dumps(payload)))
        return cur.lastrowid, created_at

def serialize(row):
    d = dict(row)
    d['form'] = json.loads(d.pop('form_json'))
    return d

class Handler(SimpleHTTPRequestHandler):
    def send_text(self, text, status=200, ctype='text/html'):
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def send_json(self, payload, status=200):
        self.send_text(json.dumps(payload), status, 'application/json')
    def admin_ok(self):
        return (not ADMIN_PASSWORD) or self.headers.get('X-Admin-Password','') == ADMIN_PASSWORD
    def do_GET(self):
        parsed = urlparse(self.path)
        route = parsed.path
        if route == '/': return self.send_text(home_page())
        if route == '/packages': return self.send_text(packages_page())
        if route == '/photographers': return self.send_text(photographers_page())
        if route == '/book': return self.send_text(booking_form(parsed.query))
        if route == '/admin': return self.send_text(admin_page())
        if route == '/api/config': return self.send_json({'ok': True, 'booking_statuses': BOOKING_STATUSES, 'payment_statuses': PAYMENT_STATUSES, 'delivery_statuses': DELIVERY_STATUSES, 'admin_password_required': bool(ADMIN_PASSWORD)})
        if route == '/api/packages': return self.send_json({'ok': True, 'packages': PACKAGES})
        if route == '/api/photographers': return self.send_json({'ok': True, 'photographers': PHOTOGRAPHERS})
        if route == '/api/bookings':
            if not self.admin_ok(): return self.send_json({'ok': False, 'error': 'Admin password required'}, 401)
            with connect() as con:
                rows = con.execute('SELECT * FROM bookings ORDER BY created_at DESC').fetchall()
            return self.send_json({'ok': True, 'bookings': [serialize(r) for r in rows]})
        if route == '/api/bookings.csv':
            if not self.admin_ok(): return self.send_text('Admin password required', 401, 'text/plain')
            with connect() as con:
                rows = con.execute('SELECT * FROM bookings ORDER BY created_at DESC').fetchall()
            out = BASE_DIR / 'grad-gallery-bookings-export.csv'
            with out.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f); w.writerow(['id','created_at','client_name','email','phone','package','preferred_date','backup_date','booking_status','payment_status','delivery_status','assigned_photographer'])
                for r in rows: w.writerow([r['id'],r['created_at'],r['client_name'],r['email'],r['phone'],r['package'],r['preferred_date'],r['backup_date'],r['booking_status'],r['payment_status'],r['delivery_status'],r['assigned_photographer'] or ''])
            return self.send_text(out.read_text(encoding='utf-8'), 200, 'text/csv')
        return self.send_text('Not found', 404, 'text/plain')
    def do_POST(self):
        if urlparse(self.path).path != '/api/bookings': return self.send_json({'ok': False}, 404)
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))).decode('utf-8'))
        booking_id, created_at = save_booking(payload)
        return self.send_json({'ok': True, 'booking_id': booking_id, 'created_at': created_at})
    def do_PATCH(self):
        route = urlparse(self.path).path
        if not route.startswith('/api/bookings/'): return self.send_json({'ok': False}, 404)
        if not self.admin_ok(): return self.send_json({'ok': False, 'error': 'Admin password required'}, 401)
        booking_id = int(route.rsplit('/',1)[-1])
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))).decode('utf-8'))
        allowed = {'booking_status','payment_status','delivery_status','assigned_photographer'}
        updates = {k: str(v) for k,v in payload.items() if k in allowed}
        if not updates: return self.send_json({'ok': False, 'error': 'No valid updates'}, 400)
        with connect() as con:
            con.execute('UPDATE bookings SET ' + ', '.join(f'{k}=?' for k in updates) + ' WHERE id=?', [*updates.values(), booking_id])
            row = con.execute('SELECT * FROM bookings WHERE id=?', (booking_id,)).fetchone()
        return self.send_json({'ok': True, 'booking': serialize(row)})

def main():
    init_db()
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', os.environ.get('GRAD_GALLERY_PORT', '8765')))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f'Grad Gallery running on port {port}')
    server.serve_forever()

if __name__ == '__main__':
    main()
