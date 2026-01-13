from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import sqlite3
from datetime import datetime
import json
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'rainbow-waffel-secret-2025')

DATABASE = 'rainbow_waffel.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                items TEXT NOT NULL,
                subtotal REAL NOT NULL,
                tax REAL NOT NULL,
                discount REAL DEFAULT 0,
                total REAL NOT NULL,
                customer_name TEXT,
                customer_phone TEXT,
                payment_method TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        db.close()

MENU = {
    'waffles': [
        {'id': 'hw', 'name': 'Honey Waffel', 'price': 149},
        {'id': 'hcw', 'name': 'Hot Chocolate Waffel', 'price': 160},
        {'id': 'bbw', 'name': 'Brownie Belgium Waffel', 'price': 180},
        {'id': 'kkw', 'name': 'Kit-Kat Waffel', 'price': 200},
        {'id': 'ow', 'name': 'Oreo Waffel', 'price': 200},
        {'id': 'nnw', 'name': 'Nakol Nutella', 'price': 210},
    ],
    'extras': [
        {'id': 'oreo', 'name': 'Oreo', 'price': 30},
        {'id': 'kkb', 'name': 'Kit-Kat Bites', 'price': 40},
        {'id': 'nutella', 'name': 'Extra Nutella', 'price': 50},
    ]
}

HTML_TEMPLATE = '''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Rainbow Waffel</title><link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"><style>*{margin:0;padding:0;box-sizing:border-box}:root{--primary:#ff6b6b;--secondary:#4ecdc4;--success:#51cf66;--danger:#ff6b6b;--dark:#2d3436;--light:#f8f9fa;--border:#dee2e6;--shadow:rgba(0,0,0,0.1)}body{font-family:Poppins,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}.header{background:#fff;padding:30px;border-radius:15px;margin-bottom:20px;box-shadow:0 10px 30px var(--shadow);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:20px}.logo-section h1{font-size:2.5rem;font-weight:700;margin-bottom:5px}.rainbow-text{background:linear-gradient(90deg,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#4b0082,#9400d3);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}.tagline{color:#666;font-size:.9rem}.stats-section{display:flex;gap:20px}.stat-card{background:linear-gradient(135deg,var(--primary),var(--secondary));padding:15px 25px;border-radius:10px;color:#fff;display:flex;align-items:center;gap:15px}.stat-card i{font-size:2rem;opacity:.8}.stat-label{display:block;font-size:.8rem;opacity:.9}.stat-value{display:block;font-size:1.5rem;font-weight:700}.main-content{display:grid;grid-template-columns:1fr 400px;gap:20px;margin-bottom:20px}.menu-section,.bill-section{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px var(--shadow)}.section-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;padding-bottom:15px;border-bottom:2px solid var(--border)}.section-header h2{font-size:1.5rem;color:var(--dark);display:flex;align-items:center;gap:10px}.section-header h2 i{color:var(--primary)}.tabs{display:flex;gap:10px}.tab-btn{padding:10px 20px;border:none;background:var(--light);border-radius:8px;cursor:pointer;font-weight:500;transition:all .3s;display:flex;align-items:center;gap:8px}.tab-btn:hover{background:var(--border)}.tab-btn.active{background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff}.tab-content{display:none}.tab-content.active{display:block}.menu-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:15px}.menu-item{background:var(--light);padding:20px;border-radius:10px;cursor:pointer;transition:all .3s;border:2px solid transparent}.menu-item:hover{transform:translateY(-5px);box-shadow:0 5px 20px var(--shadow);border-color:var(--primary)}.menu-item-name{font-weight:600;color:var(--dark);margin-bottom:8px;font-size:1rem}.menu-item-price{font-size:1.3rem;font-weight:700;color:var(--primary)}.customer-details{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}.form-group input{width:100%;padding:12px;border:2px solid var(--border);border-radius:8px;font-size:.95rem;transition:all .3s}.form-group input:focus{outline:none;border-color:var(--primary)}.bill-items{max-height:300px;overflow-y:auto;margin-bottom:20px;padding-right:10px}.bill-items::-webkit-scrollbar{width:6px}.bill-items::-webkit-scrollbar-track{background:var(--light);border-radius:10px}.bill-items::-webkit-scrollbar-thumb{background:var(--primary);border-radius:10px}.empty-bill{text-align:center;padding:40px 20px;color:#999}.empty-bill i{font-size:3rem;margin-bottom:10px;opacity:.5}.bill-item{background:var(--light);padding:15px;border-radius:8px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}.bill-item-info{flex:1}.bill-item-name{font-weight:600;color:var(--dark);margin-bottom:5px}.bill-item-price{color:#666;font-size:.9rem}.bill-item-controls{display:flex;align-items:center;gap:10px}.qty-btn{width:30px;height:30px;border:none;background:#fff;border-radius:50%;cursor:pointer;font-weight:700;transition:all .3s;box-shadow:0 2px 5px var(--shadow)}.qty-btn:hover{background:var(--primary);color:#fff;transform:scale(1.1)}.qty-display{min-width:30px;text-align:center;font-weight:700;font-size:1.1rem}.btn-remove{width:30px;height:30px;border:none;background:var(--danger);color:#fff;border-radius:50%;cursor:pointer;transition:all .3s}.btn-remove:hover{transform:scale(1.1);box-shadow:0 3px 10px rgba(255,107,107,.4)}.bill-summary{background:var(--light);padding:20px;border-radius:10px;margin-bottom:20px}.discount-section,.tax-section{display:flex;justify-content:space-between;align-items:center;margin-bottom:15px}.discount-section label,.tax-section label{font-weight:500;display:flex;align-items:center;gap:8px}.discount-section input,.tax-section input{width:100px;padding:8px;border:2px solid var(--border);border-radius:6px;text-align:center;font-weight:600}.summary-line{display:flex;justify-content:space-between;padding:10px 0;font-size:1rem}.discount-line{color:var(--success)}.total-line{font-size:1.4rem;font-weight:700;color:var(--primary);border-top:2px solid var(--border);padding-top:15px;margin-top:10px}.payment-method{margin-bottom:20px}.payment-method label{display:block;font-weight:500;margin-bottom:8px;display:flex;align-items:center;gap:8px}.payment-method select{width:100%;padding:12px;border:2px solid var(--border);border-radius:8px;font-size:1rem;cursor:pointer;background:#fff}.action-buttons{display:grid;grid-template-columns:1fr 1fr;gap:10px}.btn{padding:15px;border:none;border-radius:8px;font-weight:600;cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;gap:8px;font-size:1rem}.btn-primary{background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff}.btn-primary:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(255,107,107,.4)}.btn-secondary{background:#fff;border:2px solid var(--primary);color:var(--primary)}.btn-secondary:hover{background:var(--primary);color:#fff}.btn-clear,.btn-refresh{padding:8px 15px;border:none;background:var(--danger);color:#fff;border-radius:6px;cursor:pointer;transition:all .3s;display:flex;align-items:center;gap:8px;font-weight:500}.btn-clear:hover,.btn-refresh:hover{transform:translateY(-2px);box-shadow:0 3px 10px var(--shadow)}.btn-refresh{background:var(--secondary)}.orders-section{background:#fff;border-radius:15px;padding:25px;box-shadow:0 10px 30px var(--shadow)}.orders-list{max-height:400px;overflow-y:auto}.order-card{background:var(--light);padding:20px;border-radius:10px;margin-bottom:15px;cursor:pointer;transition:all .3s;border:2px solid transparent}.order-card:hover{border-color:var(--primary);transform:translateX(5px)}.order-header{display:flex;justify-content:space-between;margin-bottom:10px}.order-number{font-weight:700;color:var(--primary);font-size:1.1rem}.order-total{font-weight:700;font-size:1.2rem;color:var(--dark)}.order-info{display:flex;justify-content:space-between;font-size:.9rem;color:#666}.order-actions{display:flex;gap:10px;margin-top:10px}.btn-small{padding:6px 12px;border:none;border-radius:6px;cursor:pointer;font-size:.85rem;transition:all .3s;display:flex;align-items:center;gap:5px}.btn-view{background:var(--secondary);color:#fff}.btn-pdf{background:var(--success);color:#fff}.btn-delete{background:var(--danger);color:#fff}.btn-small:hover{transform:scale(1.05)}.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.7);z-index:1000;align-items:center;justify-content:center}.modal.active{display:flex}.modal-content{background:#fff;border-radius:15px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto}.modal-header{padding:20px;border-bottom:2px solid var(--border);display:flex;justify-content:space-between;align-items:center}.modal-header h3{font-size:1.5rem;color:var(--dark)}.modal-close{width:35px;height:35px;border:none;background:var(--danger);color:#fff;border-radius:50%;cursor:pointer;font-size:1.2rem;transition:all .3s}.modal-close:hover{transform:rotate(90deg)}.modal-body{padding:20px}.toast{position:fixed;top:20px;right:20px;background:#fff;padding:20px 30px;border-radius:10px;box-shadow:0 10px 30px var(--shadow);transform:translateX(400px);transition:all .3s;z-index:2000;display:flex;align-items:center;gap:15px;font-weight:500}.toast.show{transform:translateX(0)}.toast.success{border-left:4px solid var(--success)}.toast.error{border-left:4px solid var(--danger)}@media (max-width:1024px){.main-content{grid-template-columns:1fr}.bill-section{order:-1}}@media (max-width:768px){.header{text-align:center}.stats-section{flex-direction:column;width:100%}.menu-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}.customer-details{grid-template-columns:1fr}.action-buttons{grid-template-columns:1fr}}@media print{body{background:#fff;padding:0}.header,.menu-section,.orders-section,.action-buttons{display:none}.main-content{grid-template-columns:1fr}.bill-section{box-shadow:none;border:1px solid #000}}</style></head><body><div class="container"><header class="header"><div class="logo-section"><h1 class="rainbow-text">RAINBOW WAFFEL</h1><p class="tagline">Where every bite brings a smile!</p></div><div class="stats-section"><div class="stat-card"><i class="fas fa-calendar-day"></i><div><span class="stat-label">Today's Orders</span><span class="stat-value" id="todayOrders">0</span></div></div><div class="stat-card"><i class="fas fa-rupee-sign"></i><div><span class="stat-label">Today's Revenue</span><span class="stat-value" id="todayRevenue">₹0</span></div></div></div></header><div class="main-content"><div class="menu-section"><div class="section-header"><h2><i class="fas fa-utensils"></i> Menu</h2><div class="tabs"><button class="tab-btn active" data-tab="waffles"><i class="fas fa-cookie-bite"></i> Waffles</button><button class="tab-btn" data-tab="extras"><i class="fas fa-plus-circle"></i> Extras</button></div></div><div class="tab-content active" id="waffles-tab"><div class="menu-grid" id="waffles-grid"></div></div><div class="tab-content" id="extras-tab"><div class="menu-grid" id="extras-grid"></div></div></div><div class="bill-section"><div class="section-header"><h2><i class="fas fa-receipt"></i> Current Bill</h2><button class="btn-clear" onclick="clearBill()"><i class="fas fa-trash"></i> Clear</button></div><div class="customer-details"><div class="form-group"><input type="text" id="customerName" placeholder="Customer Name (Optional)"></div><div class="form-group"><input type="tel" id="customerPhone" placeholder="Phone Number (Optional)"></div></div><div class="bill-items" id="billItems"><div class="empty-bill"><i class="fas fa-shopping-cart"></i><p>No items added yet</p></div></div><div class="bill-summary"><div class="discount-section"><label><i class="fas fa-percent"></i> Discount %</label><input type="number" id="discountPercent" min="0" max="100" value="0" step="1"></div><div class="tax-section"><label><i class="fas fa-file-invoice-dollar"></i> Tax %</label><input type="number" id="taxPercent" min="0" max="100" value="5" step="0.5"></div><div class="summary-line"><span>Subtotal:</span><span id="subtotal">₹0.00</span></div><div class="summary-line discount-line" style="display:none"><span>Discount:</span><span id="discount">-₹0.00</span></div><div class="summary-line"><span>Tax:</span><span id="tax">₹0.00</span></div><div class="summary-line total-line"><span>Total:</span><span id="total">₹0.00</span></div></div><div class="payment-method"><label><i class="fas fa-money-bill-wave"></i> Payment Method</label><select id="paymentMethod"><option value="Cash">Cash</option><option value="Card">Card</option><option value="UPI">UPI</option><option value="PhonePe">PhonePe</option><option value="GPay">Google Pay</option><option value="Paytm">Paytm</option></select></div><div class="action-buttons"><button class="btn btn-secondary" onclick="printBill()"><i class="fas fa-print"></i> Print</button><button class="btn btn-primary" onclick="saveOrder()"><i class="fas fa-save"></i> Save Order</button></div></div></div><div class="orders-section"><div class="section-header"><h2><i class="fas fa-history"></i> Recent Orders</h2><button class="btn-refresh" onclick="loadOrders()"><i class="fas fa-sync-alt"></i> Refresh</button></div><div class="orders-list" id="ordersList"></div></div></div><div class="modal" id="orderModal"><div class="modal-content"><div class="modal-header"><h3>Order Details</h3><button class="modal-close" onclick="closeModal()"><i class="fas fa-times"></i></button></div><div class="modal-body" id="orderDetails"></div></div></div><div class="toast" id="toast"></div><script>let menu={waffles:[],extras:[]},billItems=[],currentBill={subtotal:0,discount:0,tax:0,total:0};function setupEventListeners(){document.querySelectorAll(".tab-btn").forEach(t=>{t.addEventListener("click",()=>switchTab(t.dataset.tab))}),document.getElementById("discountPercent").addEventListener("input",calculateBill),document.getElementById("taxPercent").addEventListener("input",calculateBill)}function switchTab(t){document.querySelectorAll(".tab-btn").forEach(t=>t.classList.remove("active")),document.querySelectorAll(".tab-content").forEach(t=>t.classList.remove("active")),document.querySelector(`[data-tab="${t}"]`).classList.add("active"),document.getElementById(`${t}-tab`).classList.add("active")}async function loadMenu(){try{const t=await fetch("/api/menu");menu=await t.json(),renderMenu()}catch(t){showToast("Failed to load menu","error")}}function renderMenu(){const t=document.getElementById("waffles-grid"),e=document.getElementById("extras-grid");t.innerHTML=menu.waffles.map(t=>`<div class="menu-item" onclick="addToBill('${t.id}','${t.name}',${t.price})"><div class="menu-item-name">${t.name}</div><div class="menu-item-price">₹${t.price}</div></div>`).join(""),e.innerHTML=menu.extras.map(t=>`<div class="menu-item" onclick="addToBill('${t.id}','${t.name}',${t.price})"><div class="menu-item-name">${t.name}</div><div class="menu-item-price">₹${t.price}</div></div>`).join("")}function addToBill(t,e,n){const a=billItems.find(e=>e.id===t);a?a.quantity++:billItems.push({id:t,name:e,price:n,quantity:1}),renderBill(),calculateBill()}function removeFromBill(t){billItems=billItems.filter(e=>e.id!==t),renderBill(),calculateBill()}function updateQuantity(t,e){const n=billItems.find(e=>e.id===t);n&&(n.quantity+=e,n.quantity<=0?removeFromBill(t):(renderBill(),calculateBill()))}function renderBill(){const t=document.getElementById("billItems");0===billItems.length?t.innerHTML='<div class="empty-bill"><i class="fas fa-shopping-cart"></i><p>No items added yet</p></div>':t.innerHTML=billItems.map(t=>`<div class="bill-item"><div class="bill-item-info"><div class="bill-item-name">${t.name}</div><div class="bill-item-price">₹${t.price} each</div></div><div class="bill-item-controls"><button class="qty-btn" onclick="updateQuantity('${t.id}',-1)">-</button><span class="qty-display">${t.quantity}</span><button class="qty-btn" onclick="updateQuantity('${t.id}',1)">+</button><button class="btn-remove" onclick="removeFromBill('${t.id}')"><i class="fas fa-times"></i></button></div></div>`).join("")}async function calculateBill(){if(0===billItems.length)return currentBill={subtotal:0,discount:0,tax:0,total:0},void updateBillDisplay();const t=parseFloat(document.getElementById("discountPercent").value)||0,e=parseFloat(document.getElementById("taxPercent").value)||5;try{const n=await fetch("/api/calculate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({items:billItems,discount:t,tax:e})}),a=await n.json();a.success&&(currentBill=a,updateBillDisplay())}catch(t){showToast("Failed to calculate bill","error")}}function updateBillDisplay(){document.getElementById("subtotal").textContent=`₹${currentBill.subtotal.toFixed(2)}`,document.getElementById("discount").textContent=`-₹${currentBill.discount.toFixed(2)}`,document.getElementById("tax").textContent=`₹${currentBill.tax.toFixed(2)}`,document.getElementById("total").textContent=`₹${currentBill.total.toFixed(2)}`;const t=document.querySelector(".discount-line");t.style.display=currentBill.discount>0?"flex":"none"}function clearBill(){0!==billItems.length&&confirm("Are you sure you want to clear the current bill?")&&(billItems=[],document.getElementById("customerName").value="",document.getElementById("customerPhone").value="",document.getElementById("discountPercent").value="0",document.getElementById("taxPercent").value="5",renderBill(),calculateBill(),showToast("Bill cleared","success"))}async function saveOrder(){if(0===billItems.length)return void showToast("Add items to the bill first","error");const t=document.getElementById("customerName").value.trim(),e=document.getElementById("customerPhone").value.trim(),n=document.getElementById("paymentMethod").value;try{const a=await fetch("/api/save-order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({items:billItems,subtotal:currentBill.subtotal,tax:currentBill.tax,discount:currentBill.discount,total:currentBill.total,customer_name:t,customer_phone:e,payment_method:n})}),s=await a.json();s.success?(showToast(`Order saved: ${s.order_number}`,"success"),clearBill(),loadOrders(),loadStats()):showToast(s.error||"Failed to save order","error")}catch(t){showToast("Failed to save order","error")}}function printBill(){0===billItems.length?showToast("Add items to the bill first","error"):window.print()}async function loadOrders(){try{const t=await fetch("/api/orders"),e=await t.json();e.success&&renderOrders(e.orders)}catch(t){showToast("Failed to load orders","error")}}function renderOrders(t){const e=document.getElementById("ordersList");0===t.length?e.innerHTML='<div class="empty-bill"><p>No orders yet</p></div>':e.innerHTML=t.map(t=>`<div class="order-card"><div class="order-header"><div class="order-number">${t.order_number}</div><div class="order-total">₹${t.total.toFixed(2)}</div></div><div class="order-info"><span>${t.customer_name||"Walk-in"}</span><span>${new Date(t.created_at).toLocaleString()}</span></div><div class="order-actions"><button class="btn-small btn-view" onclick="viewOrder('${t.order_number}')"><i class="fas fa-eye"></i> View</button><button class="btn-small btn-pdf" onclick="downloadPDF('${t.order_number}')"><i class="fas fa-file-pdf"></i> PDF</button><button class="btn-small btn-delete" onclick="deleteOrder('${t.order_number}')"><i class="fas fa-trash"></i> Delete</button></div></div>`).join("")}async function viewOrder(t){try{const e=await fetch(`/api/order/${t}`),n=await e.json();if(n.success){const t=n.order,e=document.getElementById("orderModal"),a=document.getElementById("orderDetails");a.innerHTML=`<div style="margin-bottom:20px"><h4>Order #${t.order_number}</h4><p>Date: ${new Date(t.created_at).toLocaleString()}</p>${t.customer_name?`<p>Customer: ${t.customer_name}</p>`:""}${t.customer_phone?`<p>Phone: ${t.customer_phone}</p>`:""}<p>Payment: ${t.payment_method}</p></div><div class="bill-items" style="max-height:300px">${t.items.map(t=>`<div class="bill-item"><div class="bill-item-info"><div class="bill-item-name">${t.name}</div><div class="bill-item-price">₹${t.price} × ${t.quantity}</div></div><div style="font-weight:700">₹${(t.price*t.quantity).toFixed(2)}</div></div>`).join("")}</div><div class="bill-summary" style="margin-top:20px"><div class="summary-line"><span>Subtotal:</span><span>₹${t.subtotal.toFixed(2)}</span></div>${t.discount>0?`<div class="summary-line discount-line"><span>Discount:</span><span>-₹${t.discount.toFixed(2)}</span></div>`:""}<div class="summary-line"><span>Tax:</span><span>₹${t.tax.toFixed(2)}</span></div><div class="summary-line total-line"><span>Total:</span><span>₹${t.total.toFixed(2)}</span></div></div>`,e.classList.add("active")}}catch(t){showToast("Failed to load order details","error")}}function closeModal(){document.getElementById("orderModal").classList.remove("active")}function downloadPDF(t){window.open(`/api/generate-pdf/${t}`,"_blank")}async function deleteOrder(t){if(!confirm("Are you sure you want to delete this order?"))return;try{const e=await fetch(`/api/delete-order/${t}`,{method:"DELETE"}),n=await e.json();n.success&&(showToast("Order deleted","success"),loadOrders(),loadStats())}catch(t){showToast("Failed to delete order","error")}}async function loadStats(){try{const t=await fetch("/api/stats"),e=await t.json();e.success&&(document.getElementById("todayOrders").textContent=e.today.orders,document.getElementById("todayRevenue").textContent=`₹${e.today.revenue.toFixed(2)}`)}catch(t){console.error("Failed to load stats")}}function showToast(t,e="success"){const n=document.getElementById("toast");n.textContent=t,n.className=`toast ${e} show`,setTimeout(()=>n.classList.remove("show"),3e3)}document.addEventListener("DOMContentLoaded",()=>{loadMenu(),loadStats(),loadOrders(),setupEventListeners()}),document.getElementById("orderModal").addEventListener("click",t=>{"orderModal"===t.target.id&&closeModal()});</script></body></html>'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/menu')
def get_menu():
    return jsonify(MENU)

@app.route('/api/calculate', methods=['POST'])
def calculate_bill():
    try:
        data = request.json
        items = data.get('items', [])
        discount_percent = float(data.get('discount', 0))
        tax_percent = float(data.get('tax', 5))
        subtotal = sum(item['price'] * item['quantity'] for item in items)
        discount_amount = (subtotal * discount_percent) / 100
        taxable_amount = subtotal - discount_amount
        tax_amount = (taxable_amount * tax_percent) / 100
        total = taxable_amount + tax_amount
        return jsonify({'success': True, 'subtotal': round(subtotal, 2), 'discount': round(discount_amount, 2), 'tax': round(tax_amount, 2), 'total': round(total, 2)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/save-order', methods=['POST'])
def save_order():
    try:
        data = request.json
        order_number = f"RW{datetime.now().strftime('%Y%m%d%H%M%S')}"
        db = get_db()
        db.execute('INSERT INTO orders (order_number, items, subtotal, tax, discount, total, customer_name, customer_phone, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (order_number, json.dumps(data['items']), data['subtotal'], data['tax'], data.get('discount', 0), data['total'], data.get('customer_name', ''), data.get('customer_phone', ''), data.get('payment_method', 'Cash')))
        db.commit()
        db.close()
        return jsonify({'success': True, 'order_number': order_number})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/orders')
def get_orders():
    try:
        db = get_db()
        orders = db.execute('SELECT * FROM orders ORDER BY created_at DESC LIMIT 100').fetchall()
        db.close()
        return jsonify({'success': True, 'orders': [{'id': o['id'], 'order_number': o['order_number'], 'items': json.loads(o['items']), 'subtotal': o['subtotal'], 'tax': o['tax'], 'discount': o['discount'], 'total': o['total'], 'customer_name': o['customer_name'], 'customer_phone': o['customer_phone'], 'payment_method': o['payment_method'], 'created_at': o['created_at']} for o in orders]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/order/<order_number>')
def get_order(order_number):
    try:
        db = get_db()
        order = db.execute('SELECT * FROM orders WHERE order_number = ?', (order_number,)).fetchone()
        db.close()
        if order:
            return jsonify({'success': True, 'order': {'id': order['id'], 'order_number': order['order_number'], 'items': json.loads(order['items']), 'subtotal': order['subtotal'], 'tax': order['tax'], 'discount': order['discount'], 'total': order['total'], 'customer_name': order['customer_name'], 'customer_phone': order['customer_phone'], 'payment_method': order['payment_method'], 'created_at': order['created_at']}})
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/delete-order/<order_number>', methods=['DELETE'])
def delete_order(order_number):
    try:
        db = get_db()
        db.execute('DELETE FROM orders WHERE order_number = ?', (order_number,))
        db.commit()
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/stats')
def get_stats():
    try:
        db = get_db()
        today = datetime.now().strftime('%Y-%m-%d')
        today_orders = db.execute('SELECT COUNT(*) as count, SUM(total) as revenue FROM orders WHERE DATE(created_at) = ?', (today,)).fetchone()
        total_stats = db.execute('SELECT COUNT(*) as count, SUM(total) as revenue FROM orders').fetchone()
        db.close()
        return jsonify({'success': True, 'today': {'orders': today_orders['count'] or 0, 'revenue': today_orders['revenue'] or 0}, 'total': {'orders': total_stats['count'] or 0, 'revenue': total_stats['revenue'] or 0}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/generate-pdf/<order_number>')
def generate_pdf(order_number):
    try:
        db = get_db()
        order = db.execute('SELECT * FROM orders WHERE order_number = ?', (order_number,)).fetchone()
        db.close()
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "RAINBOW WAFFEL")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "NIMS MELA - Where every bite brings a smile!")
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, height - 100, f"Order #: {order['order_number']}")
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 115, f"Date: {order['created_at']}")
        if order['customer_name']:
            c.drawString(50, height - 130, f"Customer: {order['customer_name']}")
        if order['customer_phone']:
            c.drawString(50, height - 145, f"Phone: {order['customer_phone']}")
        y = height - 180
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Item")
        c.drawString(350, y, "Qty")
        c.drawString(420, y, "Price")
        c.drawString(500, y, "Total")
        c.line(50, y - 5, width - 50, y - 5)
        y -= 20
        c.setFont("Helvetica", 10)
        items = json.loads(order['items'])
        for item in items:
            c.drawString(50, y, item['name'][:40])
            c.drawString(350, y, str(item['quantity']))
            c.drawString(420, y, f"₹{item['price']}")
            c.drawString(500, y, f"₹{item['price'] * item['quantity']}")
            y -= 15
        y -= 20
        c.line(50, y, width - 50, y)
        y -= 20
        c.drawString(400, y, "Subtotal:")
        c.drawString(500, y, f"₹{order['subtotal']:.2f}")
        y -= 15
        if order['discount'] > 0:
            c.drawString(400, y, "Discount:")
            c.drawString(500, y, f"-₹{order['discount']:.2f}")
            y -= 15
        c.drawString(400, y, "Tax:")
        c.drawString(500, y, f"₹{order['tax']:.2f}")
        y -= 15
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y, "Total:")
        c.drawString(500, y, f"₹{order['total']:.2f}")
        y -= 30
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Payment: {order['payment_method']}")
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, 50, "Thank you! Celebrate sweetness at waffles and friends.")
        c.save()
        buffer.seek(0)
        return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f'order_{order_number}.pdf')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
